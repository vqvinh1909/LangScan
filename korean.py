# -*- coding: utf-8 -*-
"""
korean.py - Tra tu tieng Han: tu dien kengdic (Han -> Anh) + phien am Latin
            (Romanization sua doi) + am Han-Viet cua phan hanja.

Du lieu: data/kengdic.tsv  (~133.000 muc, giay phep MPL 2.0 / LGPL)
Thu:     python korean.py 저는 매일 한국어를 공부합니다
"""

import os
import re
import sys

import langs

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
KENGDIC_PATH = os.path.join(DATA_DIR, "kengdic.tsv")

# ------------------------------------------------------- phien am Latin -----
# Romanization sua doi (Revised Romanization of Korean)
_CHO = ["g", "kk", "n", "d", "tt", "r", "m", "b", "pp", "s", "ss", "",
        "j", "jj", "ch", "k", "t", "p", "h"]
_JUNG = ["a", "ae", "ya", "yae", "eo", "e", "yeo", "ye", "o", "wa", "wae",
         "oe", "yo", "u", "wo", "we", "wi", "yu", "eu", "ui", "i"]
# Phu am cuoi: dang dung mot minh / dang khi noi sang chu sau bat dau bang nguyen am
_JONG = ["", "k", "kk", "k", "n", "n", "n", "t", "l", "k", "m", "l", "l",
         "l", "p", "l", "m", "p", "p", "t", "t", "ng", "t", "t", "k", "t",
         "p", "t"]
_JONG_LINK = ["", "g", "kk", "ks", "n", "nj", "nh", "d", "r", "lg", "lm", "lb",
              "ls", "lt", "lp", "lh", "m", "b", "bs", "s", "ss", "ng", "j",
              "ch", "k", "t", "p", "h"]

_HANGUL_START = 0xAC00
_HANGUL_END = 0xD7A3


def decompose(ch):
    """Tach mot chu Hangul -> (phu am dau, nguyen am, phu am cuoi) dang chi so."""
    code = ord(ch)
    if not (_HANGUL_START <= code <= _HANGUL_END):
        return None
    off = code - _HANGUL_START
    return off // 588, (off % 588) // 28, off % 28


def romanize(text):
    """'한국어' -> 'hangugeo' (Romanization sua doi, gan dung).

    Diem quan trong: phu am cuoi dung truoc chu bat dau bang nguyen am (ㅇ)
    thi doc noi sang - 한국어 la 'hangug-eo' chu khong phai 'hanguk-eo'.
    """
    syls = [(ch, decompose(ch)) for ch in text]
    out = []
    for i, (ch, parts) in enumerate(syls):
        if parts is None:
            out.append(ch)
            continue
        cho, jung, jong = parts
        out.append(_CHO[cho] + _JUNG[jung])
        if not jong:
            continue
        nxt = syls[i + 1][1] if i + 1 < len(syls) else None
        # Chu sau bat dau bang ㅇ (chi so 11) = khong co phu am dau -> noi am
        out.append(_JONG_LINK[jong] if (nxt and nxt[0] == 11) else _JONG[jong])
    return "".join(out)


# --------------------------------------------------- tach tu / bo duoi ------
# Tro tu hay gap - cat bo de tim tu goc
PARTICLES = ["으로부터", "에게서", "한테서", "이라고", "라고", "에서", "에게", "한테",
             "께서", "부터", "까지", "처럼", "보다", "마다", "밖에", "이나", "나마",
             "으로", "로", "은", "는", "이", "가", "을", "를", "의", "에", "도",
             "만", "와", "과", "랑", "이랑", "요"]
# Duoi dong tu / tinh tu hay gap - thay bang '다' de ve dang tu dien
ENDINGS = ["았습니다", "었습니다", "겠습니다", "합니다", "습니다", "ㅂ니다",
           "았어요", "었어요", "이에요", "예요", "했어요", "해요", "아요", "어요",
           "여요", "았다", "었다", "는다", "ㄴ다", "지만", "는데", "으면", "면",
           "아서", "어서", "해서", "지요", "네요", "세요", "죠", "고"]
# Duoi bat dau bang 해/했/하 -> tu goc gan nhu chac chan la '~하다'
_HADA_HINT = ("해", "했", "하", "합")


class Korean(object):
    def __init__(self, hanviet=None, path=KENGDIC_PATH):
        """hanviet: mot dictionary.Dictionary (tieng Trung) de tra am Han-Viet
        cua phan hanja - co thi tot, khong co van chay binh thuong."""
        if not os.path.exists(path):
            raise FileNotFoundError(
                "Chua co tu dien tieng Han: {}\nChay:  python setup_data.py".format(path))
        self.index = {}
        self._load(path)
        self.hanviet = hanviet

    def _load(self, path):
        with open(path, "r", encoding="utf-8") as f:
            first = True
            for line in f:
                if first:                      # bo dong tieu de
                    first = False
                    continue
                parts = line.rstrip("\n").split("\t")
                if len(parts) < 4:
                    continue
                surface, hanja, gloss = parts[1].strip(), parts[2].strip(), parts[3].strip()
                if not surface or not gloss:
                    continue
                self.index.setdefault(surface, []).append((gloss, hanja))

    # ---- tra cuu
    def lookup(self, word):
        return self.index.get(word, [])

    def lookup_deep(self, word):
        """Thu nguyen tu -> bo tro tu -> ve dang '~다' -> cat dan tu phai."""
        if self.lookup(word):
            return word, self.lookup(word)

        for p in sorted(PARTICLES, key=len, reverse=True):
            if word.endswith(p) and len(word) > len(p):
                stem = word[:-len(p)]
                if self.lookup(stem):
                    return stem, self.lookup(stem)

        for e in sorted(ENDINGS, key=len, reverse=True):
            if word.endswith(e) and len(word) > len(e):
                stem = word[:-len(e)]
                if e.startswith(_HADA_HINT):
                    cands = (stem + "하다", stem + "다", stem)
                else:
                    cands = (stem + "다", stem + "하다", stem)
                for cand in cands:
                    if self.lookup(cand):
                        return cand, self.lookup(cand)

        for end in range(len(word) - 1, 1, -1):
            cand = word[:end]
            if self.lookup(cand):
                return cand, self.lookup(cand)
        return word, []

    def han_viet(self, hanja):
        """Nghia tieng Viet cua phan Han tu, lay tu tu dien Trung-Viet.

        Luu y: day la NGHIA cua Han tu, khong phai am Han-Viet.
        Vd 每日 -> 'hang ngay' (am Han-Viet la 'moi nhat').
        """
        hanja = "".join(ch for ch in (hanja or "") if langs.RE_HAN.match(ch))
        if not hanja or self.hanviet is None:
            return ""
        entries = self.hanviet.lookup(hanja, "vi")
        if entries:
            return entries[0].senses[0]
        bits = []
        for ch in hanja:
            e = self.hanviet.lookup(ch, "vi")
            if e:
                bits.append(e[0].senses[0].split(";")[0])
        return " ".join(bits)

    def _build_english_index(self):
        """Nghia tieng Anh -> tu tieng Han (de di duong Viet -> Anh -> Han)."""
        if getattr(self, "_by_en", None) is not None:
            return self._by_en
        idx = {}
        for surface, entries in self.index.items():
            for gloss, hanja in entries:
                for part in re.split(r"[;,/]", gloss):
                    key = part.strip().lower().strip(".")
                    key = re.sub(r"^(to|a|an|the)\s+", "", key)
                    if 1 < len(key) <= 40:
                        idx.setdefault(key, []).append((surface, hanja, gloss))
        self._by_en = idx
        return idx

    def search_hanja(self, hanja, limit=6):
        """Tim tu tieng Han theo Han tu - vd 銀行 -> 은행.

        Rat manh voi tu Han-Viet: 'ngân hàng' -> 银行 (Trung) -> 은행 (Han).
        """
        if getattr(self, "_by_hanja", None) is None:
            idx = {}
            for surface, entries in self.index.items():
                for gloss, hj in entries:
                    hj = "".join(ch for ch in (hj or "") if langs.RE_HAN.match(ch))
                    if hj:
                        idx.setdefault(hj, []).append((surface, gloss))
            self._by_hanja = idx
        out, seen = [], set()
        for surface, gloss in self._by_hanja.get(hanja, [])[:limit * 2]:
            if surface in seen:
                continue
            seen.add(surface)
            hv = self.han_viet(hanja)
            out.append(langs.Card(
                word=surface, reading=romanize(surface), badge="Hàn",
                en=[gloss.strip()],
                note="Han tu {}{}".format(hanja, "  =  {}".format(hv) if hv else ""),
                speak=surface, lang=langs.KO))
            if len(out) >= limit:
                break
        return out

    def search_english(self, word, limit=8):
        """Tim tu tieng Han theo nghia tieng Anh."""
        idx = self._build_english_index()
        key = word.strip().lower()
        key = re.sub(r"^(to|a|an|the)\s+", "", key)
        hits = idx.get(key, [])
        out, seen = [], set()
        for surface, hanja, gloss in hits:
            if surface in seen:
                continue
            seen.add(surface)
            note = ""
            hanja = "".join(ch for ch in (hanja or "") if langs.RE_HAN.match(ch))
            if hanja:
                hv = self.han_viet(hanja)
                note = "Han tu {}{}".format(hanja, "  =  {}".format(hv) if hv else "")
            out.append(langs.Card(
                word=surface, reading=romanize(surface),
                badge="Hàn", en=[gloss.strip()], note=note,
                speak=surface, lang=langs.KO))
            if len(out) >= limit:
                break
        return out

    def card(self, token):
        key, hits = self.lookup_deep(token)
        glosses, hanja = [], ""
        for g, h in hits[:4]:
            g = g.strip()
            if g and g not in glosses:
                glosses.append(g)
            if h and not hanja:
                hanja = h

        note = ""
        if hanja:
            hanja = "".join(ch for ch in hanja if langs.RE_HAN.match(ch))
        if hanja:
            hv = self.han_viet(hanja)
            note = "Han tu {}{}".format(hanja, "  =  {}".format(hv) if hv else "")

        return langs.Card(
            word=key, reading=romanize(key),
            badge="Hanja" if hanja else "thuan Han",
            en=glosses[:5], note=note, speak=key, lang=langs.KO)

    def cards(self, text, max_words=25):
        out, seen = [], set()
        for token in re.split(r"\s+", text):
            token = token.strip()
            if not token:
                continue
            c = self.card(token)
            if c.word in seen:
                continue
            seen.add(c.word)
            out.append(c)
            if len(out) >= max_words:
                break
        return out


# ----------------------------------------------------------------- CLI ------
def main(argv):
    text = " ".join(argv[1:]) or "저는 매일 한국어를 공부합니다"
    try:
        import dictionary
        hv = dictionary.Dictionary()
    except Exception:
        hv = None
    ko = Korean(hanviet=hv)
    print("Tu dien tieng Han: {} muc\n".format(len(ko.index)))
    for c in ko.cards(langs.clean(text, langs.KO)):
        print("{}  [{}]".format(c.word, c.reading))
        if c.en:
            print("   EN: " + "; ".join(c.en))
        if c.note:
            print("   " + c.note)
        if not c.en:
            print("   -- khong co trong tu dien")
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
