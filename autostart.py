# -*- coding: utf-8 -*-
"""
autostart.py - Bat/tat che do khoi dong cung Windows cho LangScan.

Dung Task Scheduler, chay voi quyen thuong (/RL LIMITED). KHONG dung quyen cao
nhat: file cua app nam o thu muc nguoi dung ghi duoc, chuong trinh nao cung thay
duoc file roi nhan quyen admin khong qua UAC. Cai gia: phim tat khong an khi dang
o trong app chay quyen admin.
Tao/xoa task can quyen admin -> script tu goi lai chinh no qua UAC.

Dung tu dong lenh:
    python autostart.py status
    python autostart.py install
    python autostart.py uninstall
"""

import os
import subprocess
import sys
import time

from paths import APP_DIR, FROZEN

TASK_NAME = "LangScan"
OLD_TASK_NAMES = ("ChineseScan",)   # ban cu - go bo khi cai lai
BASE_DIR = APP_DIR
SCRIPT = os.path.join(BASE_DIR, "langscan.py")

# Khong hien cua so console den khi goi schtasks
_NO_WINDOW = 0x08000000 if os.name == "nt" else 0


def pythonw_exe():
    """Duong dan pythonw.exe (chay khong hien console); khong co thi dung python.exe."""
    exe = sys.executable or "python"
    cand = os.path.join(os.path.dirname(exe), "pythonw.exe")
    return cand if os.path.exists(cand) else exe


def python_exe():
    exe = sys.executable or "python"
    cand = os.path.join(os.path.dirname(exe), "python.exe")
    return cand if os.path.exists(cand) else exe


def _run(args):
    return subprocess.run(args, capture_output=True, text=True,
                          creationflags=_NO_WINDOW)


def is_installed():
    """Task da ton tai chua?"""
    if os.name != "nt":
        return False
    try:
        return _run(["schtasks", "/Query", "/TN", TASK_NAME]).returncode == 0
    except Exception:
        return False


def is_admin():
    if os.name != "nt":
        return False
    try:
        import ctypes
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def _elevate(action):
    """Goi lai chinh file nay bang quyen admin (hien hop thoai UAC)."""
    import ctypes
    if FROZEN:                         # LangScan.exe --autostart install
        exe, params = sys.executable, "--autostart {}".format(action)
    else:
        exe, params = python_exe(), '"{}" {}'.format(os.path.abspath(__file__), action)
    rc = ctypes.windll.shell32.ShellExecuteW(None, "runas", exe, params, BASE_DIR, 0)
    if rc <= 32:                       # <=32 = nguoi dung bam No hoac loi
        return False
    want = (action == "install")
    for _ in range(30):                # cho toi da ~6 giay roi kiem tra lai
        time.sleep(0.2)
        if is_installed() == want:
            return True
    return is_installed() == want


def install():
    """Tao task chay luc dang nhap Windows, quyen thuong."""
    if os.name != "nt":
        print("Chi ho tro Windows.")
        return False
    if not is_admin():
        return _elevate("install")
    for old in OLD_TASK_NAMES:            # don task cua ban cu neu con
        _run(["schtasks", "/Delete", "/TN", old, "/F"])
    cmd = ('"{}"'.format(sys.executable) if FROZEN
           else '"{}" "{}"'.format(pythonw_exe(), SCRIPT))
    r = _run(["schtasks", "/Create", "/TN", TASK_NAME, "/SC", "ONLOGON",
              "/RL", "LIMITED", "/F", "/TR", cmd])
    if r.returncode != 0:
        print("Loi tao task:", (r.stderr or r.stdout).strip())
        return False
    print("Da bat khoi dong cung Windows.")
    return True


def task_command():
    """Lenh ma task dang chay (de biet task co phai cua ban nay khong)."""
    try:
        r = _run(["schtasks", "/Query", "/TN", TASK_NAME, "/XML"])
        if r.returncode != 0:
            return ""
        import re
        m = re.search(r"<Command>(.*?)</Command>", r.stdout or "", re.S)
        return (m.group(1) if m else "").strip().strip('"')
    except Exception:
        return ""


def uninstall():
    if os.name != "nt":
        return False
    if not is_installed():
        return True
    # Ban .exe go cai dat: chi xoa task tro vao CHINH file .exe nay. Task cua
    # ban chay bang Python (hoac ban cai o thu muc khac) thi de nguyen.
    if FROZEN and os.path.normcase(task_command()) != os.path.normcase(sys.executable):
        return True
    if not is_admin():
        return _elevate("uninstall")
    r = _run(["schtasks", "/Delete", "/TN", TASK_NAME, "/F"])
    if r.returncode != 0:
        print("Loi xoa task:", (r.stderr or r.stdout).strip())
        return False
    print("Da tat khoi dong cung Windows.")
    return True


def toggle():
    return uninstall() if is_installed() else install()


def main(argv):
    action = (argv[1] if len(argv) > 1 else "status").lower()
    if action == "install":
        ok = install()
    elif action == "uninstall":
        ok = uninstall()
    elif action == "toggle":
        ok = toggle()
    else:
        print("Khoi dong cung Windows: {}".format(
            "DANG BAT" if is_installed() else "dang tat"))
        return 0
    print("Trang thai hien tai: {}".format(
        "DANG BAT" if is_installed() else "dang tat"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
