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


PROVIDERS = (_google, _google_dict, _mymemory)


CHUNK = 1500         # doan dai hon: chia theo cau, dich tung phan roi ghep lai


def _split_long(paragraph, size=CHUNK):
    """Chia mot doan thanh cac phan <= size ky tu, cat o ranh gioi cau."""
    import re
    sentences = re.split(r"(?<=[.!?。！？])\s*", paragraph)
    parts, cur = [], ""
    for s in sentences:
        if not s:
            continue
        while len(s) > size:                 # mot cau qua dai: cat o dau phay / cach
            cut = max(s.rfind(", ", 0, size), s.rfind(" ", 0, size), s.rfind("，", 0, size))
            cut = cut + 1 if cut > size // 2 else size
            parts.append((cur + " " + s[:cut]).strip() if cur else s[:cut].strip())
            cur, s = "", s[cut:].strip()
        if cur and len(cur) + 1 + len(s) > size:
            parts.append(cur)
            cur = s
        else:
            cur = (cur + " " + s).strip() if cur else s
    if cur:
        parts.append(cur)
    return parts


def _translate_long(text, lang, target):
    """Doan dai (trang tai lieu chup ve): dich tung phan theo cau, giu xuong doan.
    Dia chi dich mien phi gioi han do dai va dich doan qua dai kem hon."""
    cjk = lang in ("zh", "ja", "ko")
    out_paras = []
    for para in text.split("\n"):
        para = para.strip()
        if not para:
            continue
        outs = []
        for part in _split_long(para):
            o, engine = translate_detail(part, lang, target=target)
            if not o or engine == "offline":
                # mot phan hong / mat mang giua chung: bao that bai, khong ghep
                # do va khong luu cache - nguoi goi se dich offline ca doan
                return ""
            outs.append(o)
        out_paras.append(("" if (target in ("zh", "ja") and not cjk) else " ").join(outs))
    out = "\n".join(out_paras)
    if out:
        remember(text, lang, out, target)
    return out


# Mat mang: nho 30 giay de khong cho het thoi gian cho cua tung nguon (moi
# nguon 8 giay) moi lan dich - di thang sang bo dich offline.
OFFLINE_HOLD = 30
_offline_until = [0.0]


def _is_network_error(e):
    """Loi do mat mang / khong toi duoc may chu (khac loi HTTP cua may chu)."""
    import socket
    import urllib.error
    if isinstance(e, urllib.error.HTTPError):
        return False
    return isinstance(e, (urllib.error.URLError, socket.timeout, TimeoutError,
                          ConnectionError, OSError))


def _offline(text, lang, target):
    """Bo dich offline (offline_mt.py) - '' neu chua tai mo hinh."""
    try:
        import offline_mt
        return offline_mt.translate(text, lang, target)
    except Exception as e:
        print("[!] Khong dich offline duoc:", e)
        return ""


def translate_detail(text, lang="ja", use_network=True, target="vi"):
    """-> (ban dich, nguon): nguon la 'cache' / 'online' / 'offline' / ''."""
    import time
    text = (text or "").strip()
    if not text or lang == target:
        return "", ""
    hit = cached(text, lang, target)
    if hit is not None:
        return hit, "cache"
    if not use_network:
        return "", ""
    if time.time() >= _offline_until[0]:
        if len(text) > CHUNK:
            out = _translate_long(text, lang, target)
            if out:
                return out, "online"
        else:
            for provider in PROVIDERS:
                try:
                    out = provider(text, lang, target)
                except Exception as e:
                    if provider is _google and _is_network_error(e):
                        # khong toi duoc ca Google -> coi nhu mat mang
                        _offline_until[0] = time.time() + OFFLINE_HOLD
                        print("[*] Mat mang - dung bo dich offline trong {}s".format(
                            OFFLINE_HOLD))
                        break
                    continue                   # nha cung cap loi -> thu cai tiep theo
                if not out:
                    continue
                # Ket qua trung het voi dau vao van la ket qua that (ten rieng,
                # thuat ngu giu nguyen) - truoc day bi coi nham la that bai.
                remember(text, lang, out, target)
                return out, "online"
    # Khong co mang / moi nguon deu loi: dich offline. KHONG luu cache de co
    # mang lai thi lan sau dung ban Google.
    out = _offline(text, lang, target)
    return (out, "offline") if out else ("", "")


def translate(text, lang="ja", use_network=True, target="vi"):
    """Dich sang 'target' (mac dinh tieng Viet). '' = that bai."""
    return translate_detail(text, lang, use_network, target)[0]


def translate_async(text, lang, callback, target="vi", detail=False):
    """Dich o luong rieng roi goi callback(ban_dich) - hoac callback(ban_dich,
    nguon) neu detail=True. Popup dung de khong bi treo."""
    def work():
        try:
            out, engine = translate_detail(text, lang, target=target)
        except Exception:
            out, engine = "", ""
        try:
            callback(out, engine) if detail else callback(out)
        except Exception:
            pass
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
