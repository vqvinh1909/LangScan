# -*- coding: utf-8 -*-
"""
caidat_tiengnhat.py - Cai tu dien tieng Nhat cho LangScan.

Vi sao can file nay: goi 'jamdict-data' tren PyPI bi loi khi cai bang pip
tren Windows (no tu giai nen file .db ngay trong luc pip doc goi, roi bao
"WinError 32: file dang bi tien trinh khac dung"). Loi cua goi do, khong
phai cua may ban.

Cach lam o day: tai thang file .tar.gz ve, rut file jamdict.db.xz ra,
giai nen vao data/jamdict.db roi bao cho LangScan dung file do.

Chay:  python caidat_tiengnhat.py    (hoac nhay dup caidat_tiengnhat.bat)
"""

import json
import lzma
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
import urllib.request

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "data")
DB_PATH = os.path.join(DATA, "jamdict.db")
PYPI = "https://pypi.org/pypi/jamdict-data/json"
HEADERS = {"User-Agent": "Mozilla/5.0 (LangScan setup)"}


def step(n, total, text):
    print("\n[{}/{}] {}".format(n, total, text))


def pip_install(args):
    cmd = [sys.executable, "-m", "pip", "install"] + args
    print("    > " + " ".join(cmd[2:]))
    return subprocess.call(cmd) == 0


def find_sdist_url():
    with urllib.request.urlopen(
            urllib.request.Request(PYPI, headers=HEADERS), timeout=60) as r:
        data = json.load(r)
    for item in data.get("urls", []):
        if item.get("packagetype") == "sdist":
            return item["url"], item.get("size", 0)
    # Ban moi nhat khong co sdist thi lui ve cac ban truoc
    for version in sorted(data.get("releases", {}), reverse=True):
        for item in data["releases"][version]:
            if item.get("packagetype") == "sdist":
                return item["url"], item.get("size", 0)
    return None, 0


def download(url, dest, size_hint=0):
    print("    Tai: {}".format(url.rsplit("/", 1)[-1]))
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=600) as r, open(dest, "wb") as f:
        done = 0
        while True:
            chunk = r.read(1024 * 256)
            if not chunk:
                break
            f.write(chunk)
            done += len(chunk)
            if size_hint:
                sys.stdout.write("\r    {:.0f}% ({:.0f}/{:.0f} MB)".format(
                    done * 100.0 / size_hint, done / 1e6, size_hint / 1e6))
            else:
                sys.stdout.write("\r    {:.0f} MB".format(done / 1e6))
            sys.stdout.flush()
    print()


def extract_db(tar_path):
    with tarfile.open(tar_path, "r:*") as tar:
        member = None
        for m in tar.getmembers():
            if m.name.endswith("jamdict.db.xz"):
                member = m
                break
        if member is None:
            raise RuntimeError("khong thay jamdict.db.xz trong goi")
        print("    Giai nen {:.0f} MB -> {} (co the mat vai phut)".format(
            member.size / 1e6, DB_PATH))
        src = tar.extractfile(member)
        with lzma.open(src) as xz, open(DB_PATH, "wb") as out:
            shutil.copyfileobj(xz, out, length=1024 * 1024)


def verify():
    try:
        from jamdict import Jamdict
    except ImportError:
        print("[X] Chua cai duoc thu vien jamdict.")
        return False
    try:
        jam = Jamdict(db_file=DB_PATH) if os.path.exists(DB_PATH) else Jamdict()
        res = jam.lookup("食べる")
        if res.entries:
            print("[OK] Tu dien tieng Nhat chay duoc: 食べる = {}".format(
                str(res.entries[0].senses[0])[:40]))
            return True
        print("[X] Tra thu khong ra ket qua.")
    except Exception as e:
        print("[X] Loi khi tra thu:", e)
    return False


def main():
    print("=" * 60)
    print("  Cai tu dien tieng Nhat cho LangScan")
    print("=" * 60)
    os.makedirs(DATA, exist_ok=True)

    step(1, 4, "Cai thu vien jamdict va janome (nhe, vai MB)")
    if not pip_install(["jamdict>=0.1a11", "janome>=0.5.0"]):
        print("[X] Cai thu vien that bai. Kiem tra mang roi chay lai.")
        return 1

    if os.path.exists(DB_PATH) and os.path.getsize(DB_PATH) > 100 * 1024 * 1024:
        step(2, 4, "Da co san data/jamdict.db, bo qua phan tai")
    else:
        step(2, 4, "Tim ban tai cua jamdict-data tren PyPI")
        url, size = find_sdist_url()
        if not url:
            print("[X] Khong tim thay ban tai. Kiem tra mang roi chay lai.")
            return 1

        tmp = tempfile.mkdtemp(prefix="jamdict_")
        tar_path = os.path.join(tmp, "jamdict-data.tar.gz")
        try:
            step(3, 4, "Tai va giai nen tu dien (~54 MB tai ve, ~310 MB tren dia)")
            download(url, tar_path, size)
            extract_db(tar_path)
        except Exception as e:
            print("[X] That bai:", e)
            return 1
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    step(4, 4, "Kiem tra lai")
    ok = verify()
    print()
    if ok:
        print("XONG. Thoat LangScan (Ctrl+Alt+Q) roi mo lai run_hidden.bat.")
    else:
        print("Chua xong - gui toan bo man hinh nay de duoc giup.")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
