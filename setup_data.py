# -*- coding: utf-8 -*-
"""
setup_data.py - Tai du lieu tu dien ve may (chi can chay 1 lan).

Trung: cvdict.u8 + cedict.txt + hsk.json | Han: kengdic.tsv | Nhat: jlpt.json
(Tu dien tieng Nhat JMdict nam trong goi pip 'jamdict-data', khong tai o day.)

Tai ve thu muc ./data:
  - cedict.txt : tu dien CC-CEDICT (Trung -> Anh, co pinyin)
  - hsk.json   : danh sach tu vung HSK 1-6 (de hien cap do)

Chay:  python setup_data.py
"""

import gzip
import io
import json
import os
import re
import sys
import urllib.request

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
CEDICT_PATH = os.path.join(DATA_DIR, "cedict.txt")
CVDICT_PATH = os.path.join(DATA_DIR, "cvdict.u8")
HSK_PATH = os.path.join(DATA_DIR, "hsk.json")

CEDICT_URL = "https://www.mdbg.net/chinese/export/cedict/cedict_1_0_ts_utf-8_mdbg.txt.gz"
# Tu dien Trung-Viet CVDICT (Phong Phan, CC BY-SA 4.0) - dua tren CC-CEDICT
CVDICT_URL = "https://raw.githubusercontent.com/ph0ngp/CVDICT/main/CVDICT.u8"
# Tu dien Han-Anh kengdic (MPL 2.0 / LGPL)
KENGDIC_PATH = os.path.join(DATA_DIR, "kengdic.tsv")
KENGDIC_URL = "https://raw.githubusercontent.com/garfieldnate/kengdic/master/kengdic.tsv"
# Tu vung JLPT N1-N5
JLPT_PATH = os.path.join(DATA_DIR, "jlpt.json")
JLPT_URL = "https://raw.githubusercontent.com/jamsinclair/open-anki-jlpt-decks/main/src/n{n}.csv"

# Nhieu nguon du phong cho danh sach HSK - thu lan luot cho den khi duoc
HSK_SOURCES = [
    "https://raw.githubusercontent.com/glxxyz/hskhsk.com/main/data/lists/HSK%20Official%20With%20Definitions%202012%20L{n}.txt",
    "https://raw.githubusercontent.com/clem109/hsk-vocabulary/master/hsk-level-{n}.json",
    "https://raw.githubusercontent.com/gigacool/hanyu-shuiping-kaoshi/master/hsk-level-{n}.json",
]

HEADERS = {"User-Agent": "Mozilla/5.0 (ChineseScan setup)"}
HANZI_RE = re.compile(r"[一-鿿]+")


def fetch(url, timeout=60):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def cedict_from_pip():
    """Du phong: goi pip tai package 'chinese-english-lookup' (co kem CC-CEDICT)
    roi rut file tu dien ra tu file .whl."""
    import subprocess
    import tempfile
    import zipfile

    tmp = tempfile.mkdtemp(prefix="cedict_")
    try:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "download", "chinese-english-lookup",
             "--no-deps", "-d", tmp, "-q"])
    except Exception as e:
        print("[!] pip download that bai:", e)
        return None
    for name in os.listdir(tmp):
        if not name.endswith(".whl"):
            continue
        with zipfile.ZipFile(os.path.join(tmp, name)) as z:
            for member in z.namelist():
                if member.endswith(".txt") and "cedict" in member.lower():
                    return z.read(member).decode("utf-8")
    return None


def download_cedict():
    if os.path.exists(CEDICT_PATH) and os.path.getsize(CEDICT_PATH) > 1_000_000:
        print("[=] cedict.txt da co san, bo qua.")
        return True
    print("[>] Dang tai CC-CEDICT (~4 MB)...")
    try:
        raw = fetch(CEDICT_URL, timeout=120)
        text = gzip.GzipFile(fileobj=io.BytesIO(raw)).read().decode("utf-8")
    except Exception as e:
        print("[!] Tai truc tiep that bai:", e)
        print("[>] Thu nguon du phong qua pip...")
        text = cedict_from_pip()
        if not text:
            print("[!] Van khong lay duoc CC-CEDICT.")
            print("    Cach thu cong: tai " + CEDICT_URL)
            print("    giai nen (.gz) va luu thanh: " + CEDICT_PATH)
            return False
    with open(CEDICT_PATH, "w", encoding="utf-8") as f:
        f.write(text)
    print("[+] Da luu {} ({:.1f} MB)".format(CEDICT_PATH, os.path.getsize(CEDICT_PATH) / 1e6))
    return True


def parse_hsk_payload(data_bytes):
    """Tra ve tap hop tu Han tu tu mot file JSON hoac TXT bat ky."""
    try:
        text = data_bytes.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = data_bytes.decode("utf-8", "ignore")

    words = set()
    stripped = text.strip()
    if stripped.startswith("[") or stripped.startswith("{"):
        try:
            obj = json.loads(stripped)
        except Exception:
            obj = None
        if obj is not None:
            def walk(node):
                if isinstance(node, dict):
                    for k, v in node.items():
                        if k in ("hanzi", "simplified", "word", "chinese", "s"):
                            if isinstance(v, str):
                                words.update(HANZI_RE.findall(v))
                        else:
                            walk(v)
                elif isinstance(node, list):
                    for it in node:
                        walk(it)
            walk(obj)
            if words:
                return words

    # Dang TXT: moi dong bat dau bang tu Han tu
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        first = line.split("\t")[0].split()[0] if line.split() else ""
        m = HANZI_RE.findall(first)
        if m:
            words.add("".join(m))
    return words


def download_hsk():
    if os.path.exists(HSK_PATH) and os.path.getsize(HSK_PATH) > 1000:
        print("[=] hsk.json da co san, bo qua.")
        return True
    levels = {}
    total = 0
    for n in range(1, 7):
        got = set()
        for tpl in HSK_SOURCES:
            url = tpl.format(n=n)
            try:
                got = parse_hsk_payload(fetch(url, timeout=45))
            except Exception:
                got = set()
            if got:
                break
        if got:
            levels[str(n)] = sorted(got)
            total += len(got)
            print("[+] HSK{}: {} tu".format(n, len(got)))
        else:
            print("[!] HSK{}: khong tai duoc (se hien 'HSK: --' cho muc nay)".format(n))
    if not levels:
        print("[!] Khong tai duoc danh sach HSK nao. App van chay binh thuong,")
        print("    chi la khong hien duoc cap do HSK.")
        return False
    with open(HSK_PATH, "w", encoding="utf-8") as f:
        json.dump(levels, f, ensure_ascii=False)
    print("[+] Da luu {} ({} tu)".format(HSK_PATH, total))
    return True


def download_cvdict():
    if os.path.exists(CVDICT_PATH) and os.path.getsize(CVDICT_PATH) > 1_000_000:
        print("[=] cvdict.u8 (Trung-Viet) da co san, bo qua.")
        return True
    print("[>] Dang tai tu dien Trung-Viet CVDICT (~11 MB)...")
    try:
        text = fetch(CVDICT_URL, timeout=180).decode("utf-8")
    except Exception as e:
        print("[!] Tai CVDICT that bai:", e)
        print("    Tai tay tai: " + CVDICT_URL)
        print("    Luu thanh: " + CVDICT_PATH)
        return False
    with open(CVDICT_PATH, "w", encoding="utf-8") as f:
        f.write(text)
    print("[+] Da luu {} ({:.1f} MB)".format(CVDICT_PATH,
                                             os.path.getsize(CVDICT_PATH) / 1e6))
    return True


def download_kengdic():
    """Tu dien tieng Han (kengdic)."""
    if os.path.exists(KENGDIC_PATH) and os.path.getsize(KENGDIC_PATH) > 1_000_000:
        print("[=] kengdic.tsv (tieng Han) da co san, bo qua.")
        return True
    print("[>] Dang tai tu dien tieng Han kengdic (~11 MB)...")
    try:
        text = fetch(KENGDIC_URL, timeout=180).decode("utf-8")
    except Exception as e:
        print("[!] Tai kengdic that bai:", e)
        return False
    with open(KENGDIC_PATH, "w", encoding="utf-8") as f:
        f.write(text)
    print("[+] Da luu {}".format(KENGDIC_PATH))
    return True


def download_jlpt():
    """Danh sach tu vung JLPT N1-N5 -> {tu: cap do}."""
    if os.path.exists(JLPT_PATH) and os.path.getsize(JLPT_PATH) > 1000:
        print("[=] jlpt.json da co san, bo qua.")
        return True
    import csv
    import io as _io
    levels = {}
    for n in range(1, 6):
        try:
            txt = fetch(JLPT_URL.format(n=n), timeout=60).decode("utf-8")
        except Exception as e:
            print("[!] JLPT N{}: khong tai duoc ({})".format(n, e))
            continue
        cnt = 0
        for row in csv.DictReader(_io.StringIO(txt)):
            for key in ((row.get("expression") or "").strip(),
                        (row.get("reading") or "").strip()):
                if key:
                    levels[key] = max(levels.get(key, 0), n)   # giu cap de nhat
            cnt += 1
        print("[+] JLPT N{}: {} tu".format(n, cnt))
    if not levels:
        return False
    with open(JLPT_PATH, "w", encoding="utf-8") as f:
        json.dump(levels, f, ensure_ascii=False)
    return True


ENGLISH_FILES = ("envi.tsv", "en_ipa.tsv", "cefr.json", "it_terms.tsv")


def check_english():
    """Du lieu tieng Anh duoc dong goi san (rut gon tu mot CSDL 179MB) nen
    khong tai lai o day - chi kiem tra con du khong."""
    missing = [n for n in ENGLISH_FILES
               if not os.path.exists(os.path.join(DATA_DIR, n))]
    if missing:
        print("[!] Thieu du lieu tieng Anh: {}".format(", ".join(missing)))
        print("    Giai nen lai LangScan.zip de lay lai thu muc data/")
        return False
    print("[=] Du lieu tieng Anh day du ({}).".format(", ".join(ENGLISH_FILES)))
    return True


def main():
    os.makedirs(DATA_DIR, exist_ok=True)
    vi_ok = download_cvdict()
    en_ok = download_cedict()
    download_hsk()
    print()
    download_kengdic()
    download_jlpt()
    check_english()
    print()
    if vi_ok or en_ok:
        print("XONG. Gio chay:  python langscan.py")
        if not vi_ok:
            print("(Chua co tu dien Trung-Viet - popup se chi hien nghia tieng Anh)")
    else:
        print("Khong tai duoc tu dien nao - app chua chay duoc. Xem huong dan o tren.")
    return 0 if (vi_ok or en_ok) else 1


if __name__ == "__main__":
    sys.exit(main())
