# -*- coding: utf-8 -*-
"""
terms.py - Bo thuat ngu chuyen nganh (IT, Kinh te, Y khoa, Ky thuat).

Moi nganh mot file data/terms/<nganh>.tsv, moi dong mot khai niem:
    Anh <TAB> Trung <TAB> Nhat <TAB> Han <TAB> Viet <TAB> ghi chu
Cot nao de trong cung duoc. Dong bat dau bang # la chu thich.
Them nganh moi: tao file .tsv moi trong data/terms (ten file = ten nganh).

Thu:  python terms.py 资产负债表
"""

import os
import re
import sys

from paths import DATA_DIR

TERMS_DIR = os.path.join(DATA_DIR, "terms")
COLS = ("en", "zh", "ja", "ko", "vi", "note")
# Ten nganh hien tren the tu (ten file -> nhan)
DOMAIN_LABEL = {"it": "IT", "kinhte": "Kinh tế", "ykhoa": "Y khoa",
                "kythuat": "Kỹ thuật", "theduc": "Thể thao", "phapluat": "Pháp luật",
                "xaydung": "Xây dựng", "marketing": "Marketing", "logistics": "Logistics",
                "giaoduc": "Giáo dục", "moitruong": "Môi trường"}
LANG_LABEL = {"en": "Anh", "zh": "Trung", "ja": "Nhật", "ko": "Hàn"}


def _strip_tone(text):
    import unicodedata
    text = (text or "").lower().replace("đ", "d")
    text = unicodedata.normalize("NFD", text)
    return "".join(ch for ch in text if not unicodedata.combining(ch))


class Terms(object):
    def __init__(self, folder=TERMS_DIR):
        self.entries = []                      # moi muc: dict theo COLS + 'domain'
        self.index = {l: {} for l in ("en", "zh", "ja", "ko")}
        self.maxlen = {l: 1 for l in self.index}
        if os.path.isdir(folder):
            for name in sorted(os.listdir(folder)):
                if name.lower().endswith(".tsv"):
                    self._load(os.path.join(folder, name), name[:-4].lower())

    def _load(self, path, domain):
        with open(path, encoding="utf-8") as f:
            for line in f:
                if not line.strip() or line.lstrip().startswith("#"):
                    continue
                parts = [p.strip() for p in line.rstrip("\n").split("\t")]
                parts += [""] * (len(COLS) - len(parts))
                e = dict(zip(COLS, parts))
                if not e["vi"]:
                    continue
                e["domain"] = domain
                self.entries.append(e)
                for lang in self.index:
                    for form in e[lang].split("/"):      # nhieu cach viet: 'a/b'
                        key = self._key(form.strip(), lang)
                        if key:
                            self.index[lang].setdefault(key, []).append(e)
                            n = len(key.split()) if lang == "en" else len(key)
                            self.maxlen[lang] = max(self.maxlen[lang], n)

    @staticmethod
    def _key(text, lang):
        if lang == "en":
            return " ".join(re.findall(r"[a-z0-9]+(?:[-'][a-z0-9]+)*", text.lower()))
        return re.sub(r"\s+", "", text)

    def __len__(self):
        return len(self.entries)

    # ---- tim thuat ngu trong mot doan chu
    def find(self, text, lang):
        """-> [(chu xuat hien trong doan, muc)], dai nhat truoc, khong chong nhau."""
        idx = self.index.get(lang)
        if not idx or not text:
            return []
        found = []
        if lang == "en":
            spans = [(m.group(0), m.start(), m.end())
                     for m in re.finditer(r"[A-Za-z0-9]+(?:[-'][A-Za-z0-9]+)*", text)]
            i = 0
            while i < len(spans):
                for n in range(min(self.maxlen["en"], len(spans) - i), 0, -1):
                    key = " ".join(s[0].lower() for s in spans[i:i + n])
                    hit = idx.get(key) or (n == 1 and idx.get(_singular(key)))
                    if hit:
                        found.append((text[spans[i][1]:spans[i + n - 1][2]], hit[0]))
                        i += n
                        break
                else:
                    i += 1
            return found
        s = re.sub(r"\s+", "", text)
        i = 0
        while i < len(s):
            for n in range(min(self.maxlen[lang], len(s) - i), 0, -1):
                hit = idx.get(s[i:i + n])
                # Chu don le (肺, 胃, 간) de lan voi nghia thuong -> chi khop tu 2 chu
                if hit and (n >= 2 or len(s) == 1):
                    found.append((s[i:i + n], hit[0]))
                    i += n
                    break
            else:
                i += 1
        return found

    # ---- tra nguoc tu tieng Viet
    def search_vi(self, query, limit=6):
        """'bảng cân đối kế toán' / 'bang can doi ke toan' -> cac muc khop."""
        q = _strip_tone(query).strip()
        if len(q) < 2:
            return []
        exact, part = [], []
        for e in self.entries:
            for meaning in re.split(r"[;/(]", e["vi"]):
                m = _strip_tone(meaning).strip(" )")
                if m == q:
                    exact.append(e)
                    break
                if re.search(r"(?<![a-z])" + re.escape(q) + r"(?![a-z])", m):
                    part.append(e)
                    break
        return (exact + [e for e in part if e not in exact])[:limit]

    @staticmethod
    def label(e):
        return DOMAIN_LABEL.get(e["domain"], e["domain"].title())

    @staticmethod
    def equivalents(e, skip):
        """'Anh: balance sheet · Nhật: 貸借対照表 · Hàn: 대차대조표' (bo ngon ngu 'skip')."""
        bits = ["{}: {}".format(LANG_LABEL[l], e[l]) for l in ("en", "zh", "ja", "ko")
                if l != skip and e[l]]
        return "  ·  ".join(bits)


def _singular(word):
    """'servers' -> 'server', 'batteries' -> 'battery' (de khop so nhieu)."""
    if word.endswith("ies") and len(word) > 4:
        return word[:-3] + "y"
    if word.endswith("s") and not word.endswith("ss") and len(word) > 3:
        return word[:-1]
    return word


def main(argv):
    t = Terms()
    print("{} thuat ngu trong {}".format(len(t), TERMS_DIR))
    text = " ".join(argv[1:]) or "balance sheet"
    for lang in ("en", "zh", "ja", "ko"):
        for surface, e in t.find(text, lang):
            print("[{}] {} -> {}  ({})".format(Terms.label(e), surface, e["vi"],
                                              Terms.equivalents(e, lang)))
    for e in t.search_vi(text):
        print("[{}] {} <- {}".format(Terms.label(e), Terms.equivalents(e, ""), e["vi"]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
