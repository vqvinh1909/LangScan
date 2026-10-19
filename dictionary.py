# -*- coding: utf-8 -*-
"""
dictionary.py - Nhan tu dien Trung-Viet (CVDICT) + Trung-Anh (CC-CEDICT),
                pinyin co dau thanh, cap do HSK, tach tu tieng Trung.

Dung doc lap duoc:  python dictionary.py 学习汉语很有意思
"""

import json
import os
import pickle
import re
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
CEDICT_PATH = os.path.join(DATA_DIR, "cedict.txt")     # Trung -> Anh
CVDICT_PATH = os.path.join(DATA_DIR, "cvdict.u8")      # Trung -> Viet
HSK_PATH = os.path.join(DATA_DIR, "hsk.json")

HANZI_RE = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]")

# ---------------------------------------------------------------- pinyin ----
_TONE_TABLE = {
    "a": "āáǎàa", "e": "ēéěèe", "i": "īíǐìi",
    "o": "ōóǒòo", "u": "ūúǔùu", "ü": "ǖǘǚǜü",
}

_CEDICT_LINE = re.compile(r"^(\S+)\s+(\S+)\s+\[([^\]]*)\]\s+/(.*)/\s*$")
_CLASSIFIER_PREFIX = ("CL:", "LT:")     # CL = CC-CEDICT, LT = luong tu (CVDICT)


def _syllable_to_marks(syl):
    """vd: 'xue2' -> 'xué', 'nu:3' -> 'nǚ', 'de5' -> 'de'."""
    m = re.match(r"^([A-Za-z:]+)([1-5])$", syl)
    if not m:
        return syl.replace("u:", "ü").replace("U:", "Ü")
    body, tone = m.group(1), int(m.group(2))
    body = body.replace("u:", "ü").replace("U:", "Ü")
    if tone == 5:
        return body
    low = body.lower()
    # Quy tac dat dau thanh
    if "a" in low:
        idx = low.index("a")
    elif "o" in low and "e" not in low:
        idx = low.index("o")
    elif "e" in low:
        idx = low.index("e")
    elif "iu" in low:
        idx = low.index("iu") + 1
    elif "ui" in low:
        idx = low.index("ui") + 1
    else:
        idx = -1
        for i, ch in enumerate(low):
            if ch in "aeiouü":
                idx = i
        if idx < 0:
            return body
    ch = low[idx]
    if ch not in _TONE_TABLE:
        return body
    marked = _TONE_TABLE[ch][tone - 1]
    if body[idx].isupper():
        marked = marked.upper()
    return body[:idx] + marked + body[idx + 1:]


def pinyin_pretty(numbered):
    """'xue2 xi2' -> 'xué xí'."""
    return " ".join(_syllable_to_marks(s) for s in numbered.split())


def tone_of(syllable_numbered):
    """Tra ve so thanh dieu 1-5 cua mot am tiet dang so."""
    m = re.match(r"^[A-Za-z:]+([1-5])$", syllable_numbered)
    return int(m.group(1)) if m else 5


# ------------------------------------------------------------- tu dien ------
_REF_RE = re.compile(r"([^\s|\[\]]+)\|([^\s|\[\]]+)\[([^\]]+)\]")
_REF_RE2 = re.compile(r"([\u4e00-\u9fff]+)\[([^\]]+)\]")
_WEAK_PREFIX = ("see ", "variant of", "old variant", "surname ", "abbr. for",
                "used in", "Japanese variant",
                "xem ", "dạng khác của", "biến thể", "họ ", "viết tắt")


def clean_sense(s):
    """Lam gon nghia: '嗎啡|吗啡[ma3 fei1]' -> '吗啡 (mǎfēi)'."""
    s = _REF_RE.sub(lambda m: "{} ({})".format(m.group(2), pinyin_pretty(m.group(3))), s)
    s = _REF_RE2.sub(lambda m: "{} ({})".format(m.group(1), pinyin_pretty(m.group(2))), s)
    return s.strip()


class Entry(object):
    __slots__ = ("simplified", "traditional", "pinyin_num", "pinyin",
                 "senses", "classifiers")

    def __init__(self, simp, trad, pin_num, senses):
        self.simplified = simp
        self.traditional = trad
        self.pinyin_num = pin_num
        self.pinyin = pinyin_pretty(pin_num)
        self.classifiers = [clean_sense(s[3:]) for s in senses
                            if s.startswith(_CLASSIFIER_PREFIX)]
        self.senses = [clean_sense(s) for s in senses
                       if not s.startswith(_CLASSIFIER_PREFIX)] \
            or [clean_sense(s) for s in senses]

    def tones(self):
        return [tone_of(s) for s in self.pinyin_num.split()]

    def weight(self):
        """Diem uu tien: nghia chinh dung truoc, 'see .../xem ...' xuong sau."""
        first = self.senses[0] if self.senses else ""
        score = 0
        if first.startswith(_WEAK_PREFIX):
            score += 10
        if self.pinyin_num and self.pinyin_num[0].isupper():
            score += 2          # thuong la ten rieng / dia danh
        return score

    def as_text(self):
        return "{}  [{}]  {}".format(self.simplified, self.pinyin, "; ".join(self.senses))


def _load_cedict_file(path):
    """Doc file dinh dang CC-CEDICT -> (index gian the, index phon the)."""
    by_simp, by_trad = {}, {}
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if not line or line[0] == "#":
                continue
            m = _CEDICT_LINE.match(line.rstrip("\n"))
            if not m:
                continue
            trad, simp, pin, defs = m.groups()
            senses = [d.strip() for d in defs.split("/") if d.strip()]
            if not senses:
                continue
            e = Entry(simp, trad, pin, senses)
            by_simp.setdefault(simp, []).append(e)
            if trad != simp:
                by_trad.setdefault(trad, []).append(e)
    return by_simp, by_trad


def _load_cached(path, cache_path):
    """Nap co cache pickle (lan khoi dong sau nhanh hon nhieu)."""
    try:
        if (os.path.exists(cache_path)
                and os.path.getmtime(cache_path) > os.path.getmtime(path)):
            with open(cache_path, "rb") as f:
                return pickle.load(f)
    except Exception:
        pass
    data = _load_cedict_file(path)
    try:
        with open(cache_path, "wb") as f:
            pickle.dump(data, f, protocol=4)
    except Exception:
        pass
    return data


class Dictionary(object):
    """Tra dong thoi 2 tu dien: Trung-Viet (chinh) va Trung-Anh (bo sung)."""

    def __init__(self, cvdict_path=CVDICT_PATH, cedict_path=CEDICT_PATH,
                 hsk_path=HSK_PATH):
        self.vi_simp, self.vi_trad = {}, {}
        self.en_simp, self.en_trad = {}, {}

        if os.path.exists(cvdict_path):
            self.vi_simp, self.vi_trad = _load_cached(
                cvdict_path, os.path.join(DATA_DIR, "cvdict.pickle"))
        if os.path.exists(cedict_path):
            self.en_simp, self.en_trad = _load_cached(
                cedict_path, os.path.join(DATA_DIR, "cedict.pickle"))

        if not self.vi_simp and not self.en_simp:
            raise FileNotFoundError(
                "Chua co tu dien nao trong {}\nHay chay truoc:  python setup_data.py"
                .format(DATA_DIR))

        self.hsk = {}
        self._load_hsk(hsk_path)

    # ---- so muc tu (de in ra luc khoi dong)
    @property
    def size_vi(self):
        return len(self.vi_simp)

    @property
    def size_en(self):
        return len(self.en_simp)

    def _load_hsk(self, path):
        if not os.path.exists(path):
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            return
        # Tu xuat hien o nhieu cap thi giu cap thap nhat
        for lvl in sorted(data.keys(), key=lambda x: int(x), reverse=True):
            for w in data[lvl]:
                self.hsk[w] = int(lvl)

    # ---- tra cuu
    def hsk_level(self, word):
        return self.hsk.get(word)

    def lookup(self, word, lang="vi"):
        """Danh sach Entry cho mot tu, da sap xep theo do 'chinh' cua nghia.

        Nhieu Entry = tu da am (vd 行 xíng / háng) -> popup se hien het.
        """
        if lang == "vi":
            hits = self.vi_simp.get(word) or self.vi_trad.get(word) or []
        else:
            hits = self.en_simp.get(word) or self.en_trad.get(word) or []
        return sorted(hits, key=lambda e: e.weight())

    def has(self, word):
        return (word in self.vi_simp or word in self.vi_trad
                or word in self.en_simp or word in self.en_trad)

    def lookup_deep(self, word):
        """Tra tu -> (tu_thuc_te, entries_viet, entries_anh).

        Neu ca cum khong co trong tu dien thi cat dan tu phai de tim tu dai nhat khop.
        """
        for end in range(len(word), 0, -1):
            key = word[:end]
            vi = self.lookup(key, "vi")
            en = self.lookup(key, "en")
            if vi or en:
                return key, vi, en
        return word, [], []


# ------------------------------------------------------------ tach tu -------
def _jieba_cut(text):
    try:
        import jieba
    except ImportError:
        return None
    return [t for t in jieba.cut(text) if t.strip()]


def segment(text, dictionary=None):
    """Tach chuoi tieng Trung thanh danh sach tu.

    Uu tien jieba; neu khong co jieba thi dung thuat toan 'khop dai nhat'
    dua tren chinh tu dien.
    """
    text = "".join(ch for ch in text if HANZI_RE.match(ch))
    if not text:
        return []
    toks = _jieba_cut(text)
    if toks is not None:
        return toks
    if dictionary is None:
        return list(text)
    out, i, n = [], 0, len(text)
    while i < n:
        for size in range(min(6, n - i), 0, -1):
            chunk = text[i:i + size]
            if size == 1 or dictionary.has(chunk):
                out.append(chunk)
                i += size
                break
    return out


def cards(text, dictionary, max_words=25):
    """Tra ca doan -> danh sach langs.Card cho popup ve."""
    import langs
    out = []
    for w in segment(text, dictionary)[:max_words]:
        key, vi, en = dictionary.lookup_deep(w)
        head = (vi or en)[0] if (vi or en) else None
        lvl = dictionary.hsk_level(key)
        note = ""
        if head is not None and head.classifiers:
            note = "luong tu: " + ", ".join(head.classifiers[:2])
        extra_vi, extra_en = [], []
        if vi:
            extra_vi = vi[0].senses[:5]
            if len(vi) > 1:
                extra_vi.append("(hoac doc [{}]: {})".format(
                    vi[1].pinyin, "; ".join(vi[1].senses[:3])))
        if en:
            extra_en = en[0].senses[:5]
        out.append(langs.Card(
            word=key,
            reading=head.pinyin if head else "",
            badge="HSK{}".format(lvl) if lvl else "ngoai HSK",
            vi=extra_vi, en=extra_en, note=note,
            speak=key, lang=langs.ZH,
            tones=head.tones() if head else []))
    return out


def clean_selection(raw, max_chars=120):
    """Lay phan tieng Trung tu doan van ban boi den."""
    if not raw:
        return ""
    kept = "".join(ch for ch in raw.strip() if HANZI_RE.match(ch))
    return kept[:max_chars]


# ----------------------------------------------------------------- CLI ------
def main(argv):
    text = " ".join(argv[1:]) or "学习汉语很有意思"
    d = Dictionary()
    print("Tu dien: {} muc Trung-Viet, {} muc Trung-Anh\n".format(d.size_vi, d.size_en))
    words = segment(clean_selection(text), d)
    print("Tach tu:", " / ".join(words), "\n")
    for w in words:
        key, vi, en = d.lookup_deep(w)
        lvl = d.hsk_level(key)
        tag = "HSK{}".format(lvl) if lvl else "ngoai HSK"
        pin = (vi or en)[0].pinyin if (vi or en) else "?"
        print("{}  [{}]  ({})".format(key, pin, tag))
        if vi:
            print("   VI: " + "; ".join(vi[0].senses[:5]))
        if en:
            print("   EN: " + "; ".join(en[0].senses[:5]))
        if not vi and not en:
            print("   -- khong co trong tu dien")
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
