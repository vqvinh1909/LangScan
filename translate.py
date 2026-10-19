# -*- coding: utf-8 -*-
"""
translate.py - Dich nghia sang tieng Viet cho tieng Nhat / tieng Han.

Tieng Trung da co tu dien Trung-Viet offline (CVDICT) nen khong can dung day.
Nhat va Han khong co tu dien Viet offline chat luong, nen:
  - Nghia tieng Anh lay offline (JMdict / kengdic) -> hien ngay lap tuc
  - Dong tieng Viet dich online, LUU CACHE vao SQLite -> tu tra roi thi
    lan sau hien ngay, khong can mang nua.

Thu:  python translate.py 食べる ja vi
"""

import json
import os
import sqlite3
import sys
import threading
import urllib.parse
import urllib.request

from paths import DATA_DIR
CACHE_PATH = os.path.join(DATA_DIR, "vi_cache.db")
TIMEOUT = 8
HEADERS = {"User-Agent": "Mozilla/5.0 (LangScan)"}

_lock = threading.Lock()


# ---------------------------------------------------------------- cache -----
def _conn():
    os.makedirs(DATA_DIR, exist_ok=True)
    c = sqlite3.connect(CACHE_PATH, check_same_thread=False)
    c.execute("CREATE TABLE IF NOT EXISTS vi "
              "(src TEXT, lang TEXT, vi TEXT, PRIMARY KEY (src, lang))")
    # Bang moi: dich duoc sang bat ky thu tieng nao, khong chi tieng Viet
    c.execute("CREATE TABLE IF NOT EXISTS tr "
              "(src TEXT, sl TEXT, tl TEXT, out TEXT, PRIMARY KEY (src, sl, tl))")
    return c


_db = None


def _db_get():
    global _db
    if _db is None:
        _db = _conn()
    return _db


def cached(text, lang, target="vi"):
    try:
        with _lock:
            row = _db_get().execute(
                "SELECT out FROM tr WHERE src=? AND sl=? AND tl=?",
                (text, lang, target)).fetchone()
        return row[0] if row else None
    except Exception:
        return None


def remember(text, lang, out, target="vi"):
    try:
        with _lock:
            db = _db_get()
            db.execute("INSERT OR REPLACE INTO tr VALUES (?,?,?,?)",
                       (text, lang, target, out))
            db.commit()
    except Exception:
        pass


# -------------------------------------------------------------- nha cung ----
def _google(text, src, target="vi"):
    url = ("https://translate.googleapis.com/translate_a/single"
           "?client=gtx&sl={}&tl={}&dt=t&q={}".format(
               src, target, urllib.parse.quote(text)))
    req = urllib.request.Request(url, headers=HEADERS)
    data = json.loads(urllib.request.urlopen(req, timeout=TIMEOUT).read().decode("utf-8"))
    return "".join(part[0] for part in data[0] if part and part[0]).strip()


def _mymemory(text, src, target="vi"):
    url = ("https://api.mymemory.translated.net/get?q={}&langpair={}"
           .format(urllib.parse.quote(text),
                   urllib.parse.quote("{}|{}".format(src, target))))
    req = urllib.request.Request(url, headers=HEADERS)
    data = json.loads(urllib.request.urlopen(req, timeout=TIMEOUT).read().decode("utf-8"))
    out = (data.get("responseData") or {}).get("translatedText") or ""
    if out.upper().startswith("NO QUERY") or "MYMEMORY WARNING" in out.upper():
        return ""
    return out.strip()


def _google_dict(text, src, target="vi"):
    """Diem cuoi thu hai cua Google - doi khi mang chan cai kia ma khong chan cai nay."""
    url = ("https://clients5.google.com/translate_a/t"
           "?client=dict-chrome-ex&sl={}&tl={}&q={}".format(
               src, target, urllib.parse.quote(text)))
    req = urllib.request.Request(url, headers=HEADERS)
    data = json.loads(urllib.request.urlopen(req, timeout=TIMEOUT).read().decode("utf-8"))
    if isinstance(data, list) and data:
        first = data[0]
        if isinstance(first, str):
            return first.strip()
        if isinstance(first, list) and first:
            return str(first[0]).strip()
    return ""


def _lingva(text, src, target="vi"):
    """Lingva - may chu cong cong lam trung gian goi Google."""
    for host in ("lingva.ml", "lingva.lunar.icu", "translate.plausibility.cloud"):
        url = "https://{}/api/v1/{}/{}/{}".format(
            host, src, target, urllib.parse.quote(text))
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            data = json.loads(
                urllib.request.urlopen(req, timeout=TIMEOUT).read().decode("utf-8"))
            out = (data.get("translation") or "").strip()
            if out:
                return out
        except Exception:
            continue
    return ""


PROVIDERS = (_google, _google_dict, _mymemory, _lingva)


def translate(text, lang="ja", use_network=True, target="vi"):
    """Dich sang 'target' (mac dinh tieng Viet). '' = that bai / khong co mang."""
    text = (text or "").strip()
    if not text or lang == target:
        return ""
    hit = cached(text, lang, target)
    if hit is not None:
        return hit
    if not use_network:
        return ""
    for provider in PROVIDERS:
        try:
            out = provider(text, lang, target)
        except Exception:
            continue                       # nha cung cap loi -> thu cai tiep theo
        if not out:
            continue
        # Ket qua trung het voi dau vao van la ket qua that (ten rieng,
        # thuat ngu giu nguyen) - truoc day bi coi nham la that bai.
        remember(text, lang, out, target)
        return out
    return ""


def translate_async(text, lang, callback, target="vi"):
    """Dich o luong rieng roi goi callback. Popup dung de khong bi treo."""
    def work():
        try:
            callback(translate(text, lang, target=target))
        except Exception:
            callback("")
    t = threading.Thread(target=work, daemon=True)
    t.start()
    return t


def selftest():
    """Thu tung nguon dich mot - de biet mang chan cai nao."""
    samples = [("ja", "食べる"), ("ko", "은행"), ("en", "firewall"),
               ("zh", "我每天在银行工作")]
    print("Kiem tra tung nguon dich (moi nguon thu 4 tu):\n")
    ok_any = False
    for provider in PROVIDERS:
        name = provider.__name__.strip("_")
        results, errors = [], []
        for lang, word in samples:
            try:
                out = provider(word, lang, "vi")
                if out:
                    results.append("{} -> {}".format(word, out))
                else:
                    errors.append("{}: rong".format(word))
            except Exception as e:
                errors.append("{}: {}".format(word, type(e).__name__))
        if results:
            ok_any = True
            print("[OK] {}".format(name))
            for r in results:
                print("       " + r)
        else:
            print("[X ] {}  ({})".format(name, "; ".join(errors[:2])))
        print()
    print("=" * 58)
    if ok_any:
        print("Co it nhat mot nguon dich chay duoc -> app dich duoc.")
    else:
        print("KHONG nguon nao chay. Mang cua ban dang chan cac dich vu dich.")
        print("Tra tu Trung/Anh van chay binh thuong (offline).")
    return 0 if ok_any else 1


def main(argv):
    if len(argv) > 1 and argv[1] in ("test", "selftest", "kiemtra"):
        return selftest()
    text = argv[1] if len(argv) > 1 else "食べる"
    lang = argv[2] if len(argv) > 2 else "ja"
    target = argv[3] if len(argv) > 3 else "vi"
    print("cache:", cached(text, lang, target))
    print("dich :", translate(text, lang, target=target)
          or "(that bai - kiem tra mang)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
