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
    # 'tr2': bang 'tr' cu chua ban dich Google truoc khi doi sang Bing - bo qua
    c.execute("CREATE TABLE IF NOT EXISTS tr2 "
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
                "SELECT out FROM tr2 WHERE src=? AND sl=? AND tl=?",
                (text, lang, target)).fetchone()
        return row[0] if row else None
    except Exception:
        return None


def remember(text, lang, out, target="vi"):
    try:
        with _lock:
            db = _db_get()
            db.execute("INSERT OR REPLACE INTO tr2 VALUES (?,?,?,?)",
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


# Bing ban web (khong can khoa): dich theo ngu canh tot hon dia chi mien phi cua
# Google ('muscle insertion' -> 'diem bam co' thay vi 'chen co'). Trang
# bing.com/translator cap mot ma dung tam; lay mot lan roi dung lai.
BING_PAGE = "https://www.bing.com/translator"
BING_LANG = {"zh": "zh-Hans", "auto": "auto-detect"}
BING_MAX = 1000          # dai hon thi Bing tu choi -> de nguon sau lo
BING_HOLD = 1800         # giay dung lai ma truoc khi lay ma moi
_bing_state = {}


def _bing_session():
    import http.cookiejar
    import re
    import time
    if _bing_state and time.time() < _bing_state["until"]:
        return _bing_state
    opener = urllib.request.build_opener(
        urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
    # Bing chi cap ma cho trinh duyet that
    opener.addheaders = [("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36")]
    page = opener.open(BING_PAGE, timeout=TIMEOUT).read().decode("utf-8", "replace")
    ig = re.search(r'IG:"([A-F0-9]+)"', page)
    iid = re.search(r'data-iid="(translator\.\d+)"', page)
    abuse = re.search(r'params_AbusePreventionHelper\s*=\s*\[(\d+),"([^"]+)"', page)
    if not (ig and abuse):
        raise RuntimeError("Bing doi trang, khong lay duoc ma")
    _bing_state.update(
        opener=opener, key=abuse.group(1), token=abuse.group(2), until=time.time() + BING_HOLD,
        url="https://www.bing.com/ttranslatev3?isVertical=1&IG={}&IID={}".format(
            ig.group(1), iid.group(1) if iid else "translator.5028"))
    return _bing_state


def _bing(text, src, target="vi"):
    if len(text) > BING_MAX:
        return ""
    st = _bing_session()
    body = urllib.parse.urlencode({
        "fromLang": BING_LANG.get(src, src), "to": BING_LANG.get(target, target),
        "text": text, "token": st["token"], "key": st["key"]}).encode("utf-8")
    try:
        data = json.loads(st["opener"].open(st["url"], body, timeout=TIMEOUT)
                          .read().decode("utf-8"))
        return data[0]["translations"][0]["text"].strip()
    except Exception:
        _bing_state.clear()          # ma het han / bi chan: lan sau lay ma moi
        raise


PROVIDERS = (_bing, _google, _google_dict, _mymemory)


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


# ---------------------------------------------------------- dich bang AI ----
# Dich may mien phi (Bing / Google) doi khi hieu sai ngu canh. Nguoi dung nhap
# khoa rieng (deu co goi mien phi) thi cau duoc dich lai bang mo hinh ngon ngu,
# thu lan luot: Gemini -> Groq -> OpenRouter. Khong co khoa / het luot / loi
# -> thu nguon sau, het thi giu ban dich may.
GEMINI_API = "https://generativelanguage.googleapis.com/v1beta"
OPENAI_API = {"groq": "https://api.groq.com/openai/v1",
              "openrouter": "https://openrouter.ai/api/v1"}
AI_SERVICES = ("gemini", "groq", "openrouter")          # thu theo thu tu nay
AI_LABEL = {"gemini": "Gemini", "groq": "Groq", "openrouter": "OpenRouter"}
AI_KEY_URL = {"gemini": "aistudio.google.com/apikey", "groq": "console.groq.com/keys",
              "openrouter": "openrouter.ai/keys"}
AI_TIMEOUT = 20
# shortcut: khoa luu dang chu thuong trong data/ (nhu moi tuy chinh khac), doi
# sang DPAPI neu may dung chung nhieu nguoi
AI_PREFS = os.path.join(DATA_DIR, "gemini.json")
LANG_NAMES = {"vi": "Vietnamese", "en": "English", "zh": "Simplified Chinese",
              "ja": "Japanese", "ko": "Korean"}
_AVOID = ("image", "tts", "audio", "live", "embedding", "vision", "thinking", "exp", "omni",
          "whisper", "guard", "code")


def _ai_prefs():
    """-> {ten dich vu: {"key": ..., "model": ...}}"""
    try:
        with open(AI_PREFS, encoding="utf-8") as f:
            d = json.load(f)
    except Exception:
        return {}
    if "key" in d:                      # dang cu: chi co Gemini, khoa nam ngoai cung
        d = {"gemini": {"key": d["key"], "model": d.get("model")}}
    return d


def ai_set(name, key=None, model=None):
    """Luu khoa / ten mo hinh cua mot dich vu. key='' -> tat dich vu do (xoa khoa)."""
    d = _ai_prefs()
    if key is not None:
        if key.strip():
            d[name] = {"key": key.strip()}
        else:
            d.pop(name, None)
    if model is not None and name in d:
        d[name]["model"] = model
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(AI_PREFS, "w", encoding="utf-8") as f:
        json.dump(d, f)


def ai_ready(name=None):
    """Da nhap khoa cho dich vu 'name' chua (None: bat ky dich vu nao)."""
    d = _ai_prefs()
    return bool(d.get(name, {}).get("key")) if name else any(v.get("key") for v in d.values())


def _ai_http(url, headers, body=None, timeout=TIMEOUT, who="AI"):
    """GET (body None) / POST JSON. Loi HTTP -> RuntimeError('<who> <ma>: <thong bao>')."""
    import urllib.error
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, headers=dict(
        {"Content-Type": "application/json", "User-Agent": HEADERS["User-Agent"]}, **headers))
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        try:
            err = json.loads(e.read().decode("utf-8"))["error"]
            msg = err["message"] if isinstance(err, dict) else str(err)
        except Exception:
            msg = str(e)
        raise RuntimeError("{} {}: {}".format(who, e.code, msg))


def _gemini_call(path, key, body=None, timeout=TIMEOUT):
    # Khoa nam trong header, khong trong URL (de khong lot vao log)
    return _ai_http(GEMINI_API + path, {"x-goog-api-key": key}, body, timeout, "Gemini")


def _openai_call(name, path, key, body=None, timeout=TIMEOUT):
    return _ai_http(OPENAI_API[name] + path, {"Authorization": "Bearer " + key}, body,
                    timeout, AI_LABEL[name])


def _version(name):
    import re
    m = re.search(r"(\d+(?:\.\d+)?)", name)
    return float(m.group(1)) if m else 0.0


def gemini_pick_model(key):
    """Chon mo hinh 'flash-lite' moi nhat ma khoa nay dung duoc (ten mo hinh doi
    theo thoi gian nen khong ghi cung). Ban 'flash' thuong co buoc suy nghi:
    10-15 giay moi cau, qua cham cho popup; ban lite 1-2 giay."""
    names = []
    for m in _gemini_call("/models?pageSize=200", key).get("models", []):
        name = m.get("name", "").split("/")[-1]
        if ("generateContent" in m.get("supportedGenerationMethods", [])
                and "flash" in name and not any(a in name for a in _AVOID)):
            names.append(name)
    if not names:
        raise RuntimeError("khóa này không có mô hình Gemini 'flash' nào")
    # ban lite truoc, roi moi nhat truoc; ban 'preview' sau cung
    names.sort(key=lambda n: ("lite" not in n, "preview" in n, -_version(n), len(n)))
    return names[0]


# Mo hinh dich tieng Viet kha tren Groq / OpenRouter, tot nhat truoc. Ten doi
# theo thoi gian: khong khop cai nao thi lay mo hinh dau tien trong danh sach.
_OPENAI_PREFER = ("gemma", "gpt-oss-120b", "llama-3.3-70b", "kimi", "qwen", "llama")


def openai_pick_model(name, key):
    ids = [m.get("id", "") for m in _openai_call(name, "/models", key).get("data", [])]
    if name == "openrouter":            # chi dung mo hinh mien phi
        ids = [i for i in ids if i.endswith(":free")]
    ids = [i for i in ids if not any(a in i.lower() for a in _AVOID)]
    for want in _OPENAI_PREFER:
        hit = sorted((i for i in ids if want in i.lower()), key=lambda i: -_version(i))
        if hit:
            return hit[0]
    if not ids:
        raise RuntimeError("khóa này không có mô hình nào dùng được")
    return ids[0]


def _ai_pick_model(name, key):
    return gemini_pick_model(key) if name == "gemini" else openai_pick_model(name, key)


def _ai_prompt(src, target, glossary=()):
    prompt = ("Translate the following text from {src} to {tgt}. Write natural, "
              "fluent {tgt} as a native speaker would, keeping the meaning and tone. "
              "Keep code, keyboard shortcuts, file names, URLs and product names "
              "unchanged. Output ONLY the translation, with no explanation and no "
              "quotes.").format(src=LANG_NAMES.get(src, src),
                                tgt=LANG_NAMES.get(target, target))
    if glossary:
        prompt += ("\nUse these glossary translations where the term has that "
                   "meaning in context:\n" + "\n".join(
                       "- {} = {}".format(a, b) for a, b in glossary))
    return prompt


def _ai_translate(name, text, src, target, key, model, glossary=()):
    prompt = _ai_prompt(src, target, glossary) + "\n\n" + text
    if name == "gemini":
        body = {"contents": [{"role": "user", "parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": 0.2}}
        data = _gemini_call("/models/{}:generateContent".format(model), key, body, AI_TIMEOUT)
        parts = (((data.get("candidates") or [{}])[0].get("content") or {}).get("parts") or [])
        return "".join(p.get("text", "") for p in parts).strip()
    body = {"model": model, "temperature": 0.2,
            "messages": [{"role": "user", "content": prompt}]}
    data = _openai_call(name, "/chat/completions", key, body, AI_TIMEOUT)
    return ((data.get("choices") or [{}])[0].get("message", {}).get("content") or "").strip()


def ai_check(name, key):
    """Kiem tra khoa (luc nguoi dung nhap). -> (True, ten mo hinh) / (False, loi)."""
    try:
        model = _ai_pick_model(name, key)
        out = _ai_translate(name, "Hello", "en", "vi", key, model)
        return (True, model) if out else (False, "{} không trả về bản dịch".format(AI_LABEL[name]))
    except Exception as e:
        return False, str(e)


def translate_ai(text, lang, target="vi", glossary=()):
    """Dich bang mo hinh ngon ngu, thu lan luot cac dich vu da nhap khoa.
    glossary: [(thuat ngu, nghia dung)]. -> (ban dich, ten dich vu), hoac
    ('', '') de nguoi goi giu ban dich may."""
    text = (text or "").strip()
    prefs = _ai_prefs()
    if not text or lang == target or not any(v.get("key") for v in prefs.values()):
        return "", ""
    hit = _cached_ai(text, lang, target)
    if hit:
        return hit
    for name in AI_SERVICES:
        key = prefs.get(name, {}).get("key")
        if not key:
            continue
        saved = prefs[name].get("model")
        try:
            model = saved or _ai_pick_model(name, key)
            try:
                out = _ai_translate(name, text, lang, target, key, model, glossary)
            except RuntimeError as e:
                if " 404:" not in str(e):
                    raise
                model = _ai_pick_model(name, key)    # mo hinh cu bi go -> chon lai
                out = _ai_translate(name, text, lang, target, key, model, glossary)
            if model != saved:
                ai_set(name, model=model)
        except Exception as e:
            print("[!] {} loi, thu nguon sau:".format(AI_LABEL[name]), e)
            continue
        if out:
            _remember_ai(text, lang, target, out, AI_LABEL[name])
            return out, AI_LABEL[name]
    return "", ""


_AI_TABLE = ("CREATE TABLE IF NOT EXISTS ai2 (src TEXT, sl TEXT, tl TEXT, out TEXT, "
             "who TEXT, PRIMARY KEY (src, sl, tl))")


def _cached_ai(text, lang, target):
    try:
        with _lock:
            db = _db_get()
            db.execute(_AI_TABLE)
            row = db.execute("SELECT out, who FROM ai2 WHERE src=? AND sl=? AND tl=?",
                             (text, lang, target)).fetchone()
        return tuple(row) if row else None
    except Exception:
        return None


def _remember_ai(text, lang, target, out, who):
    try:
        with _lock:
            db = _db_get()
            db.execute(_AI_TABLE)
            db.execute("INSERT OR REPLACE INTO ai2 VALUES (?,?,?,?,?)",
                       (text, lang, target, out, who))
            db.commit()
    except Exception:
        pass


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
