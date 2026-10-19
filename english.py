# -*- coding: utf-8 -*-
"""
english.py - Tra tu tieng Anh: nghia tieng Viet offline + IPA + cap do CEFR.

Du lieu trong ./data:
  envi.tsv    - 118.000 tu Anh, nghia tieng Viet (nguon minhqnd/dictionary, CC BY-SA 4.0)
  en_ipa.tsv  - 163.000 phien am IPA
  cefr.json   - cap do A1-C2 (CEFR-J + Octanove)

Thu:  python english.py "I am studying network administration"
"""

import json
import os
import re
import sys

import langs

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
ENVI_PATH = os.path.join(DATA_DIR, "envi.tsv")
IPA_PATH = os.path.join(DATA_DIR, "en_ipa.tsv")
CEFR_PATH = os.path.join(DATA_DIR, "cefr.json")
IT_PATH = os.path.join(DATA_DIR, "it_terms.tsv")
MAX_PHRASE = 3          # cum thuat ngu dai nhat, vd "infrastructure as code"

WORD_RE = re.compile(r"[A-Za-z][A-Za-z'\-]*")

# Tu chuc nang - boi den ca cau thi bo qua cho do roi mat.
# (Boi den dung mot tu trong so nay thi van tra binh thuong.)
STOPWORDS = set("""
a an the this that these those i you he she it we they me him her us them my your his
its our their is am are was were be been being do does did done have has had having
of in on at to for from by with without into onto about as and or but if then than so
not no nor too very can could will would shall should may might must
""".split())

POS_VI = {
    "N": "danh tu", "V": "dong tu", "A": "tinh tu", "ADJ": "tinh tu",
    "ADV": "trang tu", "PRON": "dai tu", "PREP": "gioi tu", "CONJ": "lien tu",
    "INT": "than tu", "NUM": "so tu", "DET": "tu han dinh",
}


# Dong tu bat quy tac + so nhieu bat quy tac hay gap.
# Tu dien co san mot so dang nay, nhung khong day du - bang nay bit cho hong.
IRREGULAR = {}
for _base, _forms in {
    "be": "am is are was were been", "become": "became become",
    "begin": "began begun", "break": "broke broken", "bring": "brought",
    "build": "built", "buy": "bought", "catch": "caught", "choose": "chose chosen",
    "come": "came", "cost": "cost", "cut": "cut", "deal": "dealt", "do": "did done",
    "draw": "drew drawn", "drink": "drank drunk", "drive": "drove driven",
    "eat": "ate eaten", "fall": "fell fallen", "feed": "fed", "feel": "felt",
    "fight": "fought", "find": "found", "fly": "flew flown", "forget": "forgot forgotten",
    "get": "got gotten", "give": "gave given", "go": "went gone", "grow": "grew grown",
    "have": "has had", "hear": "heard", "hide": "hid hidden", "hit": "hit",
    "hold": "held", "keep": "kept", "know": "knew known", "lead": "led",
    "learn": "learnt", "leave": "left", "lend": "lent", "let": "let", "lose": "lost",
    "make": "made", "mean": "meant", "meet": "met", "pay": "paid", "put": "put",
    "read": "read", "ride": "rode ridden", "ring": "rang rung", "rise": "rose risen",
    "run": "ran", "say": "said", "see": "saw seen", "sell": "sold", "send": "sent",
    "set": "set", "shut": "shut", "sing": "sang sung", "sit": "sat", "sleep": "slept",
    "speak": "spoke spoken", "spend": "spent", "stand": "stood", "steal": "stole stolen",
    "take": "took taken", "teach": "taught", "tell": "told", "think": "thought",
    "throw": "threw thrown", "understand": "understood", "wear": "wore worn",
    "win": "won", "write": "wrote written",
    "child": "children", "man": "men", "woman": "women", "person": "people",
    "foot": "feet", "tooth": "teeth", "mouse": "mice", "goose": "geese",
    "datum": "data", "criterion": "criteria", "analysis": "analyses",
    "index": "indices indexes", "matrix": "matrices", "vertex": "vertices",
}.items():
    for _f in _forms.split():
        IRREGULAR.setdefault(_f, _base)


def _strip_suffix(word):
    """Sinh cac dang goc co the co: 'running' -> run, runn; 'studies' -> study..."""
    out = []
    w = word
    rules = [
        ("ies", "y"), ("ied", "y"), ("ier", "y"), ("iest", "y"),
        ("sses", "ss"), ("shes", "sh"), ("ches", "ch"), ("xes", "x"),
        ("ves", "f"), ("ves", "fe"),
        ("s", ""), ("es", ""), ("ed", ""), ("ed", "e"),
        ("ing", ""), ("ing", "e"), ("er", ""), ("er", "e"),
        ("est", ""), ("est", "e"), ("ly", ""),
    ]
    for suf, rep in rules:
        if w.endswith(suf) and len(w) - len(suf) >= 2:
            out.append(w[:-len(suf)] + rep)
    # phu am gap doi: running -> run, stopped -> stop
    for suf in ("ing", "ed", "er", "est"):
        if w.endswith(suf) and len(w) - len(suf) >= 3:
            stem = w[:-len(suf)]
            if len(stem) >= 3 and stem[-1] == stem[-2] and stem[-1] not in "aeiou":
                out.append(stem[:-1])
    return out


class English(object):
    def __init__(self):
        if not os.path.exists(ENVI_PATH):
            raise FileNotFoundError(
                "Chua co tu dien Anh-Viet: {}\nChay:  python setup_data.py".format(ENVI_PATH))
        self.index = {}
        with open(ENVI_PATH, "r", encoding="utf-8") as f:
            for line in f:
                parts = line.rstrip("\n").split("\t")
                if len(parts) < 3 or not parts[0]:
                    continue
                word, pos, defs = parts[0], parts[1], parts[2]
                example = parts[3] if len(parts) > 3 else ""
                self.index[word] = (pos, [d.strip() for d in defs.split("|") if d.strip()],
                                    example)
        self.ipa = {}
        if os.path.exists(IPA_PATH):
            with open(IPA_PATH, "r", encoding="utf-8") as f:
                for line in f:
                    w, _, i = line.rstrip("\n").partition("\t")
                    if w:
                        self.ipa[w] = i
        self.cefr = {}
        if os.path.exists(CEFR_PATH):
            try:
                with open(CEFR_PATH, "r", encoding="utf-8") as f:
                    self.cefr = json.load(f)
            except Exception:
                pass

        # Thuat ngu IT - uu tien hon tu dien thong thuong
        self.it = {}
        if os.path.exists(IT_PATH):
            with open(IT_PATH, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.rstrip("\n")
                    if not line or line.startswith("#"):
                        continue
                    parts = line.split("\t")
                    if len(parts) < 2 or not parts[0].strip():
                        continue
                    term = parts[0].strip().lower()
                    self.it[term] = (parts[1].strip(),
                                     parts[2].strip() if len(parts) > 2 else "")

    # ---- tra cuu
    def lookup(self, word):
        return self.index.get(word.lower())

    def lookup_deep(self, word):
        """Tra tu; khong thay thi thu cac dang goc (chia duoi, so nhieu)."""
        w = word.lower()
        hit = self.lookup(w)
        if hit:
            return w, hit
        base = IRREGULAR.get(w)
        if base:
            hit = self.lookup(base)
            if hit:
                return base, hit
        for cand in _strip_suffix(w):
            hit = self.lookup(cand)
            if hit:
                return cand, hit
        # Nguon du lieu co loi chinh ta -y -> -i (properti, qualiti)
        if w.endswith("y"):
            hit = self.lookup(w[:-1] + "i")
            if hit:
                return w, hit
        if w.endswith("ies"):
            hit = self.lookup(w[:-3] + "i")
            if hit:
                return w[:-3] + "y", hit
        if "-" in w:                       # tu ghep: thu bo gach noi
            for cand in (w.replace("-", " "), w.replace("-", "")):
                hit = self.lookup(cand)
                if hit:
                    return cand, hit
        return w, None

    def phonetic(self, word):
        i = self.ipa.get(word.lower(), "")
        if not i:
            return ""
        i = i.split(",")[0].strip()
        return i if i.startswith("/") else "/{}/".format(i.strip("/"))

    # Muc kieu "Dang phan tu hien tai cua study." -> tra tiep tu goc
    _XREF = re.compile(r"c[uủ]a\s+([A-Za-z][A-Za-z'\-]*)\s*\.?\s*$", re.I)

    def _follow_xref(self, key, hit):
        pos, defs, example = hit
        if not defs:
            return key, hit
        m = self._XREF.search(defs[0])
        if not m or len(defs) > 1:
            return key, hit
        base = m.group(1).lower()
        base_hit = self.lookup(base)
        if not base_hit:
            base, base_hit = self.lookup_deep(base)
        if not base_hit or base == key:
            return key, hit
        b_pos, b_defs, b_ex = base_hit
        return base, (b_pos or pos, b_defs, b_ex or example)

    def it_card(self, phrase):
        """The tu cho mot thuat ngu IT (uu tien hon nghia tu dien thong thuong)."""
        it = self.it.get(phrase.lower())
        if not it:
            return None
        meaning, extra = it
        vi = [meaning]
        # Kem theo nghia tu dien thong thuong neu co - de thay nghia goc cua tu
        key, hit = self.lookup_deep(phrase)
        if hit and hit[1]:
            vi.append("(nghia chung: {})".format("; ".join(hit[1][:2])))
        return langs.Card(
            word=phrase, reading=self.phonetic(phrase),
            badge="IT", vi=vi, note=extra, speak=phrase, lang=langs.EN)

    @staticmethod
    def looks_proper(token, first_in_text=False):
        """Ten rieng? CamelCase (OneDrive) hoac viet hoa giua cau (Dropbox)."""
        if not token[:1].isupper():
            return False
        if any(c.isupper() for c in token[1:]):     # OneDrive, GitHub, PowerShell
            return True
        return not first_in_text                    # viet hoa giua cau

    def card(self, token, first_in_text=False):
        it = self.it_card(token)
        if it is not None:
            return it
        key, hit = self.lookup_deep(token)
        if hit is not None:
            key, hit = self._follow_xref(key, hit)
        if hit is None:
            # Ten rieng thi khong dich - dich may se cho ra nghia vo nghia
            if self.looks_proper(token, first_in_text):
                return langs.Card(
                    word=token, reading=self.phonetic(token), badge="ten rieng",
                    vi=["tên riêng - giữ nguyên, không dịch"],
                    speak=token, lang=langs.EN)
            return langs.Card(word=token, reading=self.phonetic(token),
                              badge="", speak=token, lang=langs.EN)
        pos, defs, example = hit
        note_bits = []
        pos_vi = POS_VI.get((pos or "").upper()[:4]) or POS_VI.get((pos or "").upper()[:1])
        if pos_vi:
            note_bits.append(pos_vi)
        if example:
            note_bits.append("vd: " + example)
        lvl = self.cefr.get(key) or self.cefr.get(token.lower())

        # Tu goc khac voi tu boi den (studying -> study) thi noi ro
        shown = key if key == token.lower() else "{}  ({})".format(token, key)
        return langs.Card(
            word=shown, reading=self.phonetic(key) or self.phonetic(token),
            badge=lvl or "ngoai CEFR", vi=defs[:4],
            note="  ·  ".join(note_bits), speak=token, lang=langs.EN)

    def cards(self, text, max_words=25):
        tokens = WORD_RE.findall(text or "")
        if not tokens:
            return []
        single = len(tokens) == 1
        out, seen = [], set()

        # Buoc 1: bat cac cum thuat ngu nhieu tu truoc ("load balancer",
        # "high availability") roi danh dau cac tu da nam trong cum.
        used = [False] * len(tokens)
        for size in range(MAX_PHRASE, 1, -1):
            for i in range(len(tokens) - size + 1):
                if any(used[i:i + size]):
                    continue
                phrase = " ".join(tokens[i:i + size]).lower()
                c = self.it_card(phrase)
                if c is not None:
                    out.append(c)
                    for j in range(i, i + size):
                        used[j] = True
                    seen.add(phrase)

        for idx, t in enumerate(tokens):
            if used[idx]:
                continue
            low = t.lower()
            if not single and low in STOPWORDS and low not in self.it:
                continue
            if low in seen:
                continue
            seen.add(low)
            c = self.card(t, first_in_text=(idx == 0))
            # Tu khong co trong tu dien (thuat ngu IT moi nhu 'firewall', 'kubernetes')
            # van giu lai - popup se dich online roi cache lai.
            if c.found or single or len(t) >= 3:
                out.append(c)
            if len(out) >= max_words:
                break
        return out


# ----------------------------------------------------------------- CLI ------
def main(argv):
    text = " ".join(argv[1:]) or "I am studying network administration"
    en = English()
    print("Tu dien Anh-Viet: {} tu | IPA: {} | CEFR: {}\n".format(
        len(en.index), len(en.ipa), len(en.cefr)))
    for c in en.cards(text):
        print("{}  {}  ({})".format(c.word, c.reading, c.badge))
        if c.vi:
            print("   " + "; ".join(c.vi[:4]))
        if c.note:
            print("   " + c.note)
        if not c.vi:
            print("   -- khong co trong tu dien")
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
