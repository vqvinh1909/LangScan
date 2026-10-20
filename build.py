# -*- coding: utf-8 -*-
"""
build.py - Dong goi LangScan thanh LangScan.exe va trinh cai dat.

Can:  pip install pyinstaller
      Inno Setup 6 (tuy chon, de tao file cai dat): https://jrsoftware.org/isdl.php
Chay: python build.py            -> dist/LangScan/LangScan.exe (chay thang duoc)
                                  + dist/LangScan-Setup.exe (neu co Inno Setup)
      python build.py --no-setup -> chi dong goi, khong tao file cai dat

Du lieu tu dien (data/) duoc chep ra canh LangScan.exe chu khong nhet vao
trong .exe: app can ghi cache / log / kich thuoc popup vao day.
"""

import glob
import os
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
DIST = os.path.join(ROOT, "dist")
APP_DIST = os.path.join(DIST, "LangScan")
ICON = os.path.join(ROOT, "build", "langscan.ico")

# Du lieu di kem. Cache (.pickle), log, am thanh, kich thuoc popup thi khong:
# app tu tao lai lan chay dau tren may nguoi dung.
DATA_FILES = ["cedict.txt", "cvdict.u8", "hsk.json", "cefr.json", "en_ipa.tsv",
              "envi.tsv", "it_terms.tsv", "jlpt.json", "kengdic.tsv",
              "jamdict.db"]           # tu dien Nhat ~310MB, nen lai con ~50MB
# Thu vien co file du lieu / module nap dong ma PyInstaller khong tu thay
COLLECT_ALL = ["jieba", "janome", "jamdict", "puchikarui", "chirptext",
               "rapidocr_onnxruntime", "onnxruntime", "gtts", "pystray", "winrt"]
HIDDEN = ["pystray._win32", "PIL._tkinter_finder"]
INNO_CANDIDATES = [
    os.path.join(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)"),
                 "Inno Setup 6", "ISCC.exe"),
    os.path.join(os.environ.get("ProgramFiles", r"C:\Program Files"),
                 "Inno Setup 6", "ISCC.exe"),
    os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs", "Inno Setup 6",
                 "ISCC.exe"),
]


def make_icon():
    """Logo chu ky "Vinh" (logo.py); co nho trong file .ico la chu V."""
    import logo
    logo.save_ico(ICON)


def have_module(name):
    try:
        __import__(name)
        return True
    except ImportError:
        return False


def pyinstaller():
    args = [sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean",
            "--windowed", "--name", "LangScan", "--icon", ICON,
            "--distpath", DIST, "--workpath", os.path.join(ROOT, "build", "work"),
            "--specpath", os.path.join(ROOT, "build")]
    for mod in COLLECT_ALL:
        if have_module(mod):
            args += ["--collect-all", mod]
        else:
            print("    (bo qua {} - chua cai)".format(mod))
    for mod in HIDDEN:
        args += ["--hidden-import", mod]
    args.append(os.path.join(ROOT, "langscan.py"))
    print("> PyInstaller ...")
    subprocess.check_call(args, cwd=ROOT)


def copy_data():
    src = os.path.join(ROOT, "data")
    dst = os.path.join(APP_DIST, "data")
    shutil.rmtree(dst, ignore_errors=True)     # bo cache / log cua lan chay thu truoc
    os.makedirs(dst)
    for name in DATA_FILES:
        path = os.path.join(src, name)
        if not os.path.exists(path):
            print("    (thieu data/{} - ban dong goi se khong co phan nay)".format(name))
            continue
        shutil.copy2(path, dst)
    for name in ("README.md", "caidat_ocr_tiengviet.bat"):
        shutil.copy2(os.path.join(ROOT, name), APP_DIST)


def inno_setup():
    iscc = next((p for p in INNO_CANDIDATES if os.path.exists(p)), None)
    if iscc is None:
        print("\n(Khong thay Inno Setup 6 -> bo qua buoc tao file cai dat.\n"
              " Cai tu https://jrsoftware.org/isdl.php roi chay lai build.py)")
        return None
    print("> Inno Setup ...")
    subprocess.check_call([iscc, "/Q", os.path.join(ROOT, "installer.iss")], cwd=ROOT)
    out = glob.glob(os.path.join(DIST, "LangScan-Setup*.exe"))
    return out[0] if out else None


def main(argv):
    make_icon()
    pyinstaller()
    copy_data()
    exe = os.path.join(APP_DIST, "LangScan.exe")
    print("\n[OK] {}".format(exe))
    if "--no-setup" not in argv:
        setup = inno_setup()
        if setup:
            print("[OK] {}  ({:.0f} MB)".format(setup, os.path.getsize(setup) / 1e6))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
