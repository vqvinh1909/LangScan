# -*- coding: utf-8 -*-
"""
ocr.py - Doc chu tu anh (chup man hinh, anh, PDF scan...).

Ba bo doc chu, thu lan luot:

1. RapidOCR (goi pip 'rapidocr-onnxruntime', ~36MB) - Trung + Anh, cai
   nhanh, khong can quyen admin. Nhay dup caidat_ocr_nhanh.bat.
2. OCR co san cua Windows - du ca Nhat + Han, nhung phai bat goi ngon ngu
   qua Windows Update (lau). Nhay dup caidat_ocr.bat.
3. Tesseract - neu may da co san.

Thu:  python ocr.py            (liet ke ngon ngu OCR co san)
      python ocr.py anh.png    (doc chu trong mot file anh)
"""

import sys

import langs

VI = "vi"               # chi dung cho OCR (doc anh co chu tieng Viet)

# Ma ngon ngu cua LangScan -> ma Windows dung
WIN_LANG = {langs.ZH: ["zh-Hans-CN", "zh-Hans", "zh-CN", "zh"],
            langs.JA: ["ja-JP", "ja"],
            langs.KO: ["ko-KR", "ko"],
            langs.EN: ["en-US", "en-GB", "en"]}
# Ma Tesseract
TESS_LANG = {langs.ZH: "chi_sim", langs.JA: "jpn", langs.KO: "kor", langs.EN: "eng"}
# RapidOCR chi co san mo hinh tieng Trung + tieng Anh (nhung hai thu do rat tot)
RAPID_LANGS = (langs.ZH, langs.EN)
_rapid = [None]          # giu mot ban dung chung, nap model mat vai giay


# ------------------------------------------------------ OCR cua Windows -----
def _winrt():
    """Nap cac module WinRT can thiet, tra ve None neu khong co."""
    # Goi winrt mang theo msvcp140.dll rieng (ban cu). Nap no truoc thi
    # onnxruntime (RapidOCR) loi "DLL initialization routine failed" -> mat
    # OCR Trung/Anh. Nen luon nap RapidOCR truoc.
    rapid_ready()
    try:
        from winrt.windows.media.ocr import OcrEngine
        from winrt.windows.globalization import Language
        from winrt.windows.graphics.imaging import SoftwareBitmap, BitmapPixelFormat
        from winrt.windows.storage.streams import DataWriter
        return OcrEngine, Language, SoftwareBitmap, BitmapPixelFormat, DataWriter
    except Exception:
        pass
    try:                                    # ten goi kieu cu
        from winsdk.windows.media.ocr import OcrEngine
        from winsdk.windows.globalization import Language
        from winsdk.windows.graphics.imaging import SoftwareBitmap, BitmapPixelFormat
        from winsdk.windows.storage.streams import DataWriter
        return OcrEngine, Language, SoftwareBitmap, BitmapPixelFormat, DataWriter
    except Exception:
        return None


def windows_languages():
    """Danh sach ma ngon ngu OCR ma Windows dang co."""
    mods = _winrt()
    if mods is None:
        return []
    OcrEngine = mods[0]
    try:
        return [str(l.language_tag) for l in OcrEngine.available_recognizer_languages]
    except Exception:
        return []


def windows_lang_for(lang):
    """Ma Windows phu hop cho tieng Trung/Nhat/Han/Anh, None neu chua cai."""
    have = [t.lower() for t in windows_languages()]
    for want in WIN_LANG.get(lang, []):
        for tag in have:
            if tag == want.lower() or tag.startswith(want.lower()):
                return windows_languages()[have.index(tag)]
    return None


def _windows_ocr(image, lang):
    import asyncio

    mods = _winrt()
    if mods is None:
        return ""
    OcrEngine, Language, SoftwareBitmap, BitmapPixelFormat, DataWriter = mods
    tag = windows_lang_for(lang)
    if not tag:
        return ""

    if image.mode != "RGBA":
        image = image.convert("RGBA")
    writer = DataWriter()
    writer.write_bytes(image.tobytes())
    bitmap = SoftwareBitmap.create_copy_from_buffer(
        writer.detach_buffer(), BitmapPixelFormat.RGBA8, image.width, image.height)
    engine = OcrEngine.try_create_from_language(Language(tag))
    if engine is None:
        return ""

    async def run():
        return await engine.recognize_async(bitmap)

    result = asyncio.run(run())
    # Tieng Trung/Nhat khong co khoang trang giua tu, nen noi lien cac o chu;
    # tieng Han/Anh thi giu khoang trang
    lines = []
    for line in result.lines:
        words = [w.text for w in line.words]
        lines.append(("" if lang in (langs.ZH, langs.JA) else " ").join(words))
    return "\n".join(lines).strip()


# ----------------------------------------------------------- RapidOCR ------
def rapid_ready():
    """Co goi rapidocr-onnxruntime khong? (cai bang pip, khong can quyen admin)"""
    try:
        import rapidocr_onnxruntime  # noqa: F401
        return True
    except ImportError:
        return False


def _rapid_engine():
    if _rapid[0] is None:
        from rapidocr_onnxruntime import RapidOCR
        _rapid[0] = RapidOCR()
    return _rapid[0]


def _rapid_lines(image):
    """Mot lan chay RapidOCR -> danh sach (x, y_giua, cao, rong, chu)."""
    import numpy
    result, _elapse = _rapid_engine()(numpy.array(image.convert("RGB")))
    items = []
    for row in result or []:
        if len(row) < 2:
            continue
        txt = str(row[1]).strip()
        if not txt:
            continue
        try:
            pts = row[0]
            xs = [p[0] for p in pts]
            ys = [p[1] for p in pts]
            items.append((min(xs), (min(ys) + max(ys)) / 2.0,
                          max(ys) - min(ys), max(xs) - min(xs), txt))
        except Exception:
            items.append((0, len(items) * 100.0, 50.0, 0, txt))
    return items


def _rapid_join(items):
    """Gop cac o chu nam cung mot hang (RapidOCR hay tach 'BRING ALL' / 'THE'
    thanh hai dong) roi sap theo hang, trai -> phai."""
    rows = []
    for it in sorted(items, key=lambda t: t[1]):
        for row in rows:
            ref = row[0]
            if abs(it[1] - ref[1]) <= 0.5 * max(it[2], ref[2]):
                row.append(it)
                break
        else:
            rows.append([it])
    lines = []
    for row in rows:
        row.sort(key=lambda t: t[0])
        # Cac o chu ke nhau/chong len nhau thuoc cung mot tu ('ENCLO' + 'LOSURE',
        # 'DISCIPLES H' + 'HERE!'): bo phan chu lap o giua roi noi lai.
        text, x_end, h = row[0][4], row[0][0] + row[0][3], row[0][2]
        for t in row[1:]:
            gap = t[0] - x_end
            joined = False
            if gap < -0.05 * max(h, t[2]):          # hai o chong len nhau that su
                low_a, low_b = text.lower(), t[4].lower()
                k = min(len(text), len(t[4]))
                while k > 0 and not low_a.endswith(low_b[:k]):
                    k -= 1
                if k > 0:
                    text = text[:-k] + t[4]
                    joined = True
            if not joined:
                text = text + " " + t[4]
            x_end = max(x_end, t[0] + t[3])
            h = max(h, t[2])
        lines.append(text)
    return lines


_VOCAB = {}
_FUNC2 = {"of", "to", "in", "on", "at", "by", "an", "as", "be", "do", "go", "he",
          "me", "my", "no", "so", "up", "us", "we", "or", "if", "is", "it", "am"}


def _vocab():
    """Tu thong dung -> do 'hiem' (A1 = 0 ... C2 = 0.5), tu cefr.json - nap luc can dung."""
    if "common" not in _VOCAB:
        import json
        import os
        from paths import DATA_DIR as base
        rank = {"A1": 0.0, "A2": 0.05, "B1": 0.1, "B2": 0.2, "C1": 0.3, "C2": 0.4}
        common = {}
        try:
            with open(os.path.join(base, "cefr.json"), encoding="utf-8") as f:
                for w, lvl in json.load(f).items():
                    if w.isalpha():
                        common[w.lower()] = rank.get(lvl, 0.3)
        except Exception:
            pass
        for w in _FUNC2 | {"a", "i"}:
            common[w] = 0.0
        _VOCAB["common"] = common
    return _VOCAB["common"]


def _full_vocab():
    if "full" not in _VOCAB:
        import os
        full = set()
        from paths import DATA_DIR
        path = os.path.join(DATA_DIR, "envi.tsv")
        try:
            with open(path, encoding="utf-8") as f:
                for line in f:
                    w = line.split("\t", 1)[0].strip().lower()
                    if w.isalpha():
                        full.add(w)
        except Exception:
            pass
        _VOCAB["full"] = full
    return _VOCAB["full"]


def _stem_of(w, vocab):
    """Tra ve tu goc neu w la dang chia (doctors, played, playing...) cua tu trong vocab."""
    for suf, minstem in (("s", 3), ("es", 3), ("ed", 4), ("d", 4), ("ing", 4),
                         ("ly", 4), ("er", 4), ("est", 4)):
        if w.endswith(suf) and len(w) - len(suf) >= minstem:
            stem = w[:-len(suf)]
            if stem in vocab:
                return stem
            if suf in ("ed", "ing", "er", "est") and stem + "e" in vocab:
                return stem + "e"
    return None


def _in_vocab(w, vocab):
    return w in vocab or _stem_of(w, vocab) is not None


def _segment(word):
    """Tach 'BEENALONG' -> ['BEEN','A','LONG'] bang tu thong dung; None neu khong tach duoc."""
    low = word.lower()
    n = len(low)
    common = _vocab()
    full = _full_vocab()
    best = [None] * (n + 1)          # best[i] = (chi phi, danh sach diem cat) cho low[:i]
    best[0] = (0.0, [])
    for i in range(1, n + 1):
        for j in range(max(0, i - 14), i):
            if best[j] is None:
                continue
            piece = low[j:i]
            if piece in common:
                extra = common[piece] + (0.6 if len(piece) <= 2 else 0.0)
            elif len(piece) >= 4 and _stem_of(piece, common) is not None:
                extra = common[_stem_of(piece, common)] + 0.2
            elif len(piece) >= 5 and _in_vocab(piece, full):
                extra = 1.5              # tu it gap hon: chi dung khi can
            else:
                continue
            cost = best[j][0] + 1 + extra
            if best[i] is None or cost < best[i][0]:
                best[i] = (cost, best[j][1] + [(j, i)])
    if best[n] is None or len(best[n][1]) > 8:
        return None
    return [word[a:b] for a, b in best[n][1]]


def _split_glued(text):
    """Tach cac tu bi OCR dinh lien ('IT'SBEENALONG' -> 'IT'S BEEN A LONG').

    Chi dung cho tu dai >= 8 chu ma KHONG co trong tu dien (ten rieng, tu
    that khong bi dong cham)."""
    import re

    def fix(m):
        tok = m.group(0)
        head = ""
        mm = re.match(r"^([A-Za-z]+'(?:s|t|re|ve|ll|d|m))([A-Za-z]{6,})$", tok, re.I)
        rest = tok
        if mm:
            head, rest = mm.group(1), mm.group(2)
        if not rest.isalpha() or len(rest) < 8:
            return tok
        low = rest.lower()
        if _in_vocab(low, _vocab()) or _in_vocab(low, _full_vocab()):
            return tok
        parts = _segment(rest)
        if not parts or len(parts) < 2:
            return tok
        return (head + " " if head else "") + " ".join(parts)

    return re.sub(r"[A-Za-z]+(?:'[A-Za-z]+)?", fix, text)


def _rapid_clean(text):
    """Sua loi OCR hay gap voi chu truyen tranh viet hoa: 'ALL1' -> 'ALL'."""
    import re
    text = _split_glued(text)
    text = re.sub(r"\b([A-Z]{2,})1\b", r"\1", text)
    return re.sub(r"(?<=[A-Z]) 1 (?=[A-Z])", " ", text)


def _rapid_ocr(image, lang):
    if lang not in RAPID_LANGS or not rapid_ready():
        return ""
    # RapidOCR doi khi bo sot ca mot dong tuy kich thuoc anh (cung noi dung,
    # cat rong hon mot chut lai doc thieu). Doc nhieu phien ban anh va chon
    # ban doc duoc nhieu chu nhat.
    variants = [image]
    try:
        from PIL import Image
        variants.append(image.resize((image.width * 2, image.height * 2),
                                     Image.LANCZOS))
    except Exception:
        pass
    best, best_n = "", 0
    for img in variants:
        try:
            lines = _rapid_join(_rapid_lines(img))
        except Exception:
            continue
        text = "\n".join(l for l in lines if l)
        n = sum(1 for ch in text if ch.isalnum())
        if n > best_n:
            best, best_n = text, n
    if not best:
        # Vung khoanh sat chu qua (vd. chi khoanh dung mot tu) thi bo do chu
        # tim khong ra gi: them vien trang roi doc lai.
        try:
            from PIL import ImageOps
            pad = max(40, image.height // 2)
            padded = ImageOps.expand(image.convert("RGB"), border=pad, fill="white")
            for img in (padded, padded.resize((padded.width * 2, padded.height * 2),
                                              Image.LANCZOS)):
                lines = _rapid_join(_rapid_lines(img))
                text = "\n".join(l for l in lines if l)
                n = sum(1 for ch in text if ch.isalnum())
                if n > best_n:
                    best, best_n = text, n
        except Exception:
            pass
    text = best
    if not text:
        return ""
    if lang == langs.ZH:
        text = text.replace(" ", "")
    else:
        text = _rapid_clean(text)
    return text.strip()


# ---------------------------------------------------------- Tesseract ------
def tesseract_languages():
    try:
        import pytesseract
        return list(pytesseract.get_languages(config=""))
    except Exception:
        return []


def _tesseract_ocr(image, lang):
    try:
        import pytesseract
    except ImportError:
        return ""
    code = TESS_LANG.get(lang, "eng")
    if code not in tesseract_languages():
        return ""
    try:
        text = pytesseract.image_to_string(image, lang=code)
    except Exception:
        return ""
    if lang in (langs.ZH, langs.JA):
        text = text.replace(" ", "")
    return text.strip()


# --------------------------------------------------------------- chung -----
def available():
    """-> danh sach ma ngon ngu LangScan doc duoc bang OCR."""
    out = []
    rapid = rapid_ready()
    for lang in (langs.ZH, langs.JA, langs.KO, langs.EN):
        if ((rapid and lang in RAPID_LANGS) or windows_lang_for(lang)
                or TESS_LANG[lang] in tesseract_languages()):
            out.append(lang)
    return out


def read(image, lang):
    """Doc chu trong anh theo mot thu tieng.

    Thu lan luot: RapidOCR (Trung/Anh, cai bang pip) -> OCR cua Windows
    (can bat goi ngon ngu) -> Tesseract (neu may co san).
    """
    text = _rapid_ocr(image, lang)
    if not text:
        text = _windows_ocr(image, lang)
    if not text:
        text = _tesseract_ocr(image, lang)
    return text


def read_auto(image, prefer=None):
    """Khong biet truoc la tieng gi: thu tung thu tieng roi chon ket qua tot nhat.

    'Tot nhat' = doc ra dung loai chu cua thu tieng do va duoc nhieu chu nhat.
    """
    langs_to_try = available()
    if not langs_to_try:
        return "", None
    if prefer and prefer in langs_to_try:       # nguoi dung da chon san ngon ngu
        text = read(image, prefer)
        if text:
            return text, prefer

    # RapidOCR doc mot lan la ra ca chu Han lan chu Latinh, khong can chay
    # hai lan cho hai thu tieng - do la phan ton thoi gian nhat.
    if rapid_ready():
        # Doc voi che do tieng Anh (giu nguyen khoang trang), quyet dinh
        # ngon ngu xong moi bo khoang trang neu la tieng Trung
        text = _rapid_ocr(image, langs.EN)
        if text:
            han, kana, hangul, latin = langs.count_scripts(text)
            if not (kana or hangul):
                if han >= max(1, latin // 3):
                    # Mo hinh RapidOCR chi biet chu Han: cau tieng Nhat bi roi
                    # mat kana (私は学生です -> 私学). Windows doc ra kana thi la Nhat.
                    ja = _windows_ocr(image, langs.JA) if windows_lang_for(langs.JA) else ""
                    if langs.count_scripts(ja)[1] >= 2:
                        return ja, langs.JA
                    return text.replace(" ", ""), langs.ZH
                vi = _read_vietnamese(image, text)
                if vi:
                    return vi, VI
                return text, langs.EN

    best, best_lang, best_score = "", None, 0
    for lang in langs_to_try:
        text = read(image, lang)
        if not text:
            continue
        han, kana, hangul, latin = langs.count_scripts(text)
        if lang == langs.ZH:
            score = han * 2 - hangul * 3 - kana
        elif lang == langs.JA:
            score = (han + kana * 2) - hangul * 3
        elif lang == langs.KO:
            score = hangul * 2 - han - kana
        else:
            score = latin - (han + kana + hangul) * 2
        if score > best_score:
            best, best_lang, best_score = text, lang, score
    if best_lang == langs.EN:
        vi = _read_vietnamese(image, best)
        if vi:
            return vi, VI
    return best, best_lang


# ------------------------------------------------ tieng Viet (Tesseract) ---
# RapidOCR chi biet chu Trung + Anh (mo hinh chu Latin cua no cung khong co
# ơ ư ă ạ...), OCR cua Windows khong ho tro tieng Viet -> dung Tesseract voi
# du lieu 'vie' (data/tessdata/vie.traineddata, ban tessdata_fast).
# Ban .exe goi kem mot ban Tesseract rut gon trong thu muc tesseract/.
def tesseract_exe():
    """Duong dan tesseract.exe: ban goi kem -> ban da cai -> PATH."""
    import os
    import shutil
    from paths import APP_DIR
    for path in (os.path.join(APP_DIR, "tesseract", "tesseract.exe"),
                 os.path.join(os.environ.get("ProgramFiles", r"C:\Program Files"),
                              "Tesseract-OCR", "tesseract.exe"),
                 os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs",
                              "Tesseract-OCR", "tesseract.exe")):
        if os.path.exists(path):
            return path
    return shutil.which("tesseract")


def _vie_tessdata():
    import os
    from paths import DATA_DIR
    d = os.path.join(DATA_DIR, "tessdata")
    return d if os.path.exists(os.path.join(d, "vie.traineddata")) else None


def vietnamese_ready():
    return bool(tesseract_exe() and _vie_tessdata())


def _tesseract_vi(image):
    """Doc anh bang Tesseract tieng Viet (chay tesseract.exe, khong can pytesseract)."""
    import os
    import subprocess
    import tempfile
    from PIL import Image, ImageOps
    exe, tessdata = tesseract_exe(), _vie_tessdata()
    if not (exe and tessdata):
        return ""
    g = ImageOps.grayscale(image)
    if sum(g.histogram()[:128]) > g.width * g.height / 2:   # chu sang tren nen toi
        g = ImageOps.invert(g)
    if g.width < 1500:                       # Tesseract can chu cao ~30px tro len
        g = g.resize((g.width * 2, g.height * 2), Image.LANCZOS)
    fd, path = tempfile.mkstemp(suffix=".png")
    os.close(fd)
    try:
        g.save(path)
        # Xuat TSV de co diem tin cay tung chu (file cau hinh 'tsv' khong co
        # trong thu muc tessdata rieng nen bat bang -c)
        r = subprocess.run([exe, path, "-", "-l", "vie", "--psm", "6",
                            "--tessdata-dir", tessdata, "-c", "tessedit_create_tsv=1"],
                           capture_output=True, timeout=20,
                           creationflags=0x08000000 if os.name == "nt" else 0)
        tsv = r.stdout.decode("utf-8", "replace")
    except Exception:
        return ""
    finally:
        try:
            os.remove(path)
        except OSError:
            pass
    return _clean_tsv(tsv)


def _clean_tsv(tsv):
    """Ghep chu tu ket qua TSV cua Tesseract, bo phan rac.

    Vung khoanh dinh mot dong chu bi cat ngang, vien, thanh cuon... thi
    Tesseract van 'doc' ra rac ("F «-c^Š» r1 2 hAiiFfc ^^") nhung diem tin
    cay rat thap (~10-40), con chu that ~85-97. Bo ca dong trung binh < 65,
    bo tu chi toan ky hieu, bo tu ngan (1-2 ky tu) diem < 80."""
    import re
    lines = {}
    for row in tsv.splitlines()[1:]:
        c = row.split("\t")
        if len(c) < 12 or not c[11].strip():
            continue
        try:
            conf = float(c[10])
        except ValueError:
            continue
        key = (int(c[2]), int(c[3]), int(c[4]))        # block, doan, dong
        lines.setdefault(key, []).append((conf, c[11].strip()))
    out = []
    for key in sorted(lines):
        words = lines[key]
        chars = sum(len(w) for _c, w in words)
        mean = sum(c * len(w) for c, w in words) / float(chars or 1)
        if mean < 65:
            continue                                   # ca dong la rac
        keep = [_split_glued_vi(w) for c, w in words
                if re.search(r"\w", w) and not (len(w) <= 2 and c < 80)]
        if keep:
            out.append(" ".join(keep))
    return "\n".join(out).strip()


def _split_glued_vi(word):
    """Tesseract hay lam dinh hai am tiet (truoc chu in dam, chu sat nhau):
    'từcó' -> 'từ có', 'gốithành' -> 'gối thành'. Chi tach khi ca tu KHONG
    phai mot am tiet tieng Viet ma tach duoc thanh 2-3 am tiet hop le."""
    import re
    import unicodedata
    m = re.match(r"^(\W*)(.*?)(\W*)$", word)
    head, core, tail = m.group(1), m.group(2), m.group(3)
    if len(core) < 4 or not core.isalpha():
        return word

    def plain(s):
        s = unicodedata.normalize("NFD", s.lower().replace("đ", "d"))
        return "".join(ch for ch in s if not unicodedata.combining(ch))

    def ok(s):
        return bool(langs.RE_VI_SYLLABLE.match(plain(s)))

    # chi lam voi chu co dau tieng Viet (khong dung vao tu tieng Anh, ten rieng)
    if ok(core) or not langs.RE_VI.search(core.lower()):
        return word

    def splits(s, n):
        """Moi cach cat s thanh dung n am tiet hop le."""
        if n == 1:
            return [[s]] if ok(s) else []
        out = []
        for i in range(1, len(s)):
            if ok(s[:i]):
                out += [[s[:i]] + r for r in splits(s[i:], n - 1)]
        return out

    parts = None
    for n in (2, 3):                     # it manh nhat truoc: 'gối thành', khong 'gố i thành'
        cands = splits(core, n)
        if cands:
            # chu hoa giua tu ('lạiGõ') la ranh gioi chac chan; khong co thi
            # uu tien manh sau bat dau bang phu am (am tiet that hiem bat dau 'i')
            cands.sort(key=lambda p: (not all(x[:1].isupper() == (k > 0 and x[:1].isupper())
                                              for k, x in enumerate(p)),
                                      sum(1 for x in p[1:] if plain(x)[:1] in "aeiouy")))
            parts = cands[0]
            break
    return head + " ".join(parts) + tail if parts else word


def _english_ratio(text):
    """Ti le tu tieng Anh pho bien trong chu RapidOCR doc ra (0..1)."""
    import re
    toks = [t.lower() for t in re.findall(r"[A-Za-z]+", text)]
    if not toks:
        return 0.0
    common = _vocab()
    hits = sum(1 for t in toks if t in common or _stem_of(t, common))
    return hits / float(len(toks))


def _read_vietnamese(image, rapid_text=""):
    """Anh chu Latin: doc lai bang Tesseract tieng Viet, tra ve chu neu that su
    la tieng Viet (co dau). '' neu khong co Tesseract hoac la tieng Anh."""
    if not vietnamese_ready():
        return ""
    if rapid_text and _english_ratio(rapid_text) > 0.6:
        return ""                    # tieng Anh ro rang: khoi ton ~1 giay
    text = _tesseract_vi(image)
    letters = sum(1 for ch in text if ch.isalpha())
    marks = len(langs.RE_VI.findall(text.lower()))
    # Tieng Viet ~1 chu co dau / 4 chu cai; tieng Anh doc bang 'vie' gan nhu 0
    return text if letters and marks >= max(1, letters // 25) else ""


def status_text():
    """Mo ta ngan gon tinh trang OCR, de in ra khi chan doan."""
    win = windows_languages()
    tess = tesseract_languages()
    bits = []
    if rapid_ready():
        bits.append("RapidOCR (pip): Trung, Anh")
    if win:
        bits.append("Windows OCR: " + ", ".join(win))
    if tess:
        bits.append("Tesseract: " + ", ".join(t for t in tess if t != "osd"))
    if not bits:
        return ("Chưa có bộ OCR nào.\n"
                "  - Nhanh nhất (Trung + Anh, ~1 phút): nháy đúp caidat_ocr_nhanh.bat\n"
                "  - Đầy đủ (thêm Nhật + Hàn, lâu hơn): nháy đúp caidat_ocr.bat")
    ready = [langs.LANG_NAME[l] for l in available()]
    if vietnamese_ready():
        ready.append("Việt")
    bits.append("Đọc được: " + (", ".join(ready) if ready else "chưa thứ tiếng nào"))
    if not vietnamese_ready():
        bits.append("Chưa đọc được chữ tiếng Việt trong ảnh: cần Tesseract + "
                    "data/tessdata/vie.traineddata (bản cài .exe có sẵn)")
    return "\n".join(bits)


def main(argv):
    print(status_text())
    if len(argv) > 1:
        from PIL import Image
        img = Image.open(argv[1])
        text, lang = read_auto(img)
        print("\nNgon ngu doan: {}\n{}".format(
            langs.LANG_NAME.get(lang, "?"), text or "(khong doc duoc chu nao)"))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
