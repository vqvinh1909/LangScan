# -*- coding: utf-8 -*-
"""
japanese.py - Tra tu tieng Nhat: JMdict (qua thu vien jamdict) + tach tu janome
              + chuyen kana sang romaji + cap do JLPT.

Cai dat:  pip install jamdict jamdict-data janome
Thu:      python japanese.py 私は毎日日本語を勉強しています
"""

import json
import os
import re
import sys

import langs

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
JLPT_PATH = os.path.join(DATA_DIR, "jlpt.json")
# Goi 'jamdict-data' cai bang pip hay hong tren Windows, nen caidat_tiengnhat.py
# tai thang file .db ve day. Co file nay thi dung, khong thi dung ban cua pip.
LOCAL_DB = os.path.join(DATA_DIR, "jamdict.db")

# Tro tu / tro dong tu - khong can tra nghia rieng
SKIP_POS = ("助詞", "助動詞", "記号", "フィラー")
# Thanh phan phu thuoc (いる trong ています, ~さん, ~たち...) - bo qua cho gon
SKIP_SUBPOS = ("非自立", "接尾", "接続助詞", "数")

# ------------------------------------------------------------- romaji -------
_ROMAJI = {
    "あ": "a", "い": "i", "う": "u", "え": "e", "お": "o",
    "か": "ka", "き": "ki", "く": "ku", "け": "ke", "こ": "ko",
    "が": "ga", "ぎ": "gi", "ぐ": "gu", "げ": "ge", "ご": "go",
    "さ": "sa", "し": "shi", "す": "su", "せ": "se", "そ": "so",
    "ざ": "za", "じ": "ji", "ず": "zu", "ぜ": "ze", "ぞ": "zo",
    "た": "ta", "ち": "chi", "つ": "tsu", "て": "te", "と": "to",
    "だ": "da", "ぢ": "ji", "づ": "zu", "で": "de", "ど": "do",
    "な": "na", "に": "ni", "ぬ": "nu", "ね": "ne", "の": "no",
    "は": "ha", "ひ": "hi", "ふ": "fu", "へ": "he", "ほ": "ho",
    "ば": "ba", "び": "bi", "ぶ": "bu", "べ": "be", "ぼ": "bo",
    "ぱ": "pa", "ぴ": "pi", "ぷ": "pu", "ぺ": "pe", "ぽ": "po",
    "ま": "ma", "み": "mi", "む": "mu", "め": "me", "も": "mo",
    "や": "ya", "ゆ": "yu", "よ": "yo",
    "ら": "ra", "り": "ri", "る": "ru", "れ": "re", "ろ": "ro",
    "わ": "wa", "を": "wo", "ん": "n",
    "ゃ": "ya", "ゅ": "yu", "ょ": "yo", "っ": "", "ー": "",
    "ぁ": "a", "ぃ": "i", "ぅ": "u", "ぇ": "e", "ぉ": "o",
}
_YOON = {"ゃ": "ya", "ゅ": "yu", "ょ": "yo"}


def kata_to_hira(s):
    return "".join(chr(ord(ch) - 0x60) if "ァ" <= ch <= "ヶ" else ch for ch in s)


def to_romaji(kana):
    """Chuyen kana sang romaji (kieu Hepburn, du dung de doc)."""
    s = kata_to_hira(kana or "")
    out, i = [], 0
    while i < len(s):
        ch = s[i]
        nxt = s[i + 1] if i + 1 < len(s) else ""
        if ch == "っ":                              # am ngat -> gap doi phu am sau
            nxt_r = _ROMAJI.get(nxt, "")
            if nxt_r:
                out.append(nxt_r[0])
            i += 1
            continue
        if nxt in _YOON and ch in _ROMAJI:          # am chap: きゃ -> kya
            base = _ROMAJI[ch]
            if base.endswith("i") and len(base) > 1:
                stem = base[:-1]
                if stem in ("sh", "ch", "j"):
                    out.append(stem + _YOON[nxt][1:])
                else:
                    out.append(stem + _YOON[nxt])
                i += 2
                continue
        if ch == "ー" and out:                       # keo dai nguyen am
            out.append(out[-1][-1] if out[-1] else "")
            i += 1
            continue
        out.append(_ROMAJI.get(ch, ch))
        i += 1
    return "".join(out)


# ------------------------------------------------------------ tu dien -------
_POS_VI = [
    ("noun", "danh tu"), ("verb", "dong tu"), ("adjective", "tinh tu"),
    ("adverb", "trang tu"), ("expression", "cum tu"), ("particle", "tro tu"),
    ("counter", "luong tu"), ("pronoun", "dai tu"), ("suffix", "hau to"),
    ("prefix", "tien to"), ("conjunction", "lien tu"), ("interjection", "than tu"),
]
_POS_RE = re.compile(r"\s*\(\((.*)\)\)\s*$", re.S)


def _split_sense(text):
    """'to eat ((Ichidan verb|transitive verb))' -> ('to eat', 'dong tu')."""
    m = _POS_RE.search(text)
    if not m:
        return text.strip(), ""
    body = text[:m.start()].strip()
    tags = m.group(1).lower()
    for en, vi in _POS_VI:
        if en in tags:
            return body, vi
    return body, ""


class Japanese(object):
    def __init__(self):
        try:
            from jamdict import Jamdict
        except ImportError:
            raise ImportError("chua cai tu dien tieng Nhat - nhay dup file"
                              " caidat_tiengnhat.bat")
        if os.path.exists(LOCAL_DB) and os.path.getsize(LOCAL_DB) > 10 * 1024 * 1024:
            self.jam = Jamdict(db_file=LOCAL_DB)
        else:
            self.jam = Jamdict()
        try:                              # kiem tra du lieu da co chua
            if not self.jam.lookup("水").entries:
                raise RuntimeError("tra thu khong ra ket qua")
        except Exception:
            raise ImportError("thieu du lieu tu dien tieng Nhat - nhay dup file"
                              " caidat_tiengnhat.bat")
        self.tokenizer = None
        try:
            from janome.tokenizer import Tokenizer
            self.tokenizer = Tokenizer()
        except ImportError:
            pass
        self.jlpt = {}
        if os.path.exists(JLPT_PATH):
            try:
                with open(JLPT_PATH, "r", encoding="utf-8") as f:
                    self.jlpt = json.load(f)
            except Exception:
                pass

    # ---- tach tu
    def tokens(self, text):
        """-> danh sach (surface, base_form, reading_kana, pos)."""
        if self.tokenizer is None:
            # Khong co janome: cat tho theo cum Kanji / cum kana
            parts = re.findall(r"[㐀-鿿]+|[ぁ-ゟ]+|[゠-ヿー]+", text)
            return [(p, p, "", "") for p in parts]
        out = []
        for t in self.tokenizer.tokenize(text):
            base = t.base_form if t.base_form and t.base_form != "*" else t.surface
            reading = t.reading if t.reading and t.reading != "*" else ""
            out.append((t.surface, base, reading, t.part_of_speech))
        return out

    def jlpt_level(self, *forms):
        best = 0
        for f in forms:
            if f:
                best = max(best, self.jlpt.get(f, 0))
        return best or None

    # ---- tra mot tu
    def lookup(self, word):
        try:
            return self.jam.lookup(word, strict_lookup=True)
        except Exception:
            return None

    def card(self, surface, base, reading, pos):
        res = self.lookup(base)
        word = base                      # dong tu chia duoi -> hien dang goc
        if res is None or not getattr(res, "entries", []):
            res = self.lookup(surface)
            word = surface
        entries = getattr(res, "entries", []) if res else []

        kana = ""
        senses_en, notes = [], []
        if entries:
            e = entries[0]
            kana = str(e.kana_forms[0]) if e.kana_forms else ""
            for s in e.senses[:4]:
                body, pos_vi = _split_sense(str(s))
                if pos_vi and not notes:
                    notes.append(pos_vi)
                senses_en.extend([g.strip() for g in body.split("/") if g.strip()])
        if not kana:
            kana = kata_to_hira(reading)

        romaji = to_romaji(kana)
        display_reading = "{} · {}".format(kana, romaji) if kana and kana != word else romaji
        lvl = self.jlpt_level(base, surface, kana)

        # Kanji trong tu: nghia tung chu, giup nho mat chu
        kanji_note = ""
        if res is not None and getattr(res, "chars", None):
            bits = []
            for c in res.chars[:3]:
                try:
                    meanings = [m for m in c.meanings(english_only=True) if m][:2]
                except TypeError:
                    meanings = [m for m in c.meanings() if m][:2]
                if meanings:
                    bits.append("{} = {}".format(c.literal, ", ".join(meanings)))
            kanji_note = " | ".join(bits)

        note = "; ".join([n for n in notes if n])
        if kanji_note:
            note = (note + "  ·  " if note else "") + kanji_note

        return langs.Card(
            word=word, reading=display_reading,
            badge="N{}".format(lvl) if lvl else "ngoai JLPT",
            en=senses_en[:5], note=note,
            speak=surface, lang=langs.JA)

    def search_english(self, word, limit=8):
        """Tim tu tieng Nhat theo nghia tieng Anh (JMdict tra nguoc duoc san).

        Dung cho duong 'Viet -> Anh -> Nhat', vi khong co tu dien Viet-Nhat.
        """
        try:
            res = self.jam.lookup(word)
        except Exception:
            return []
        out = []
        for e in getattr(res, "entries", [])[:limit]:
            kana = str(e.kana_forms[0]) if e.kana_forms else ""
            kanji = str(e.kanji_forms[0]) if e.kanji_forms else ""
            shown = kanji or kana
            if not shown:
                continue
            senses = []
            for s in e.senses[:3]:
                body, _pos = _split_sense(str(s))
                senses.extend([g.strip() for g in body.split("/") if g.strip()])
            lvl = self.jlpt_level(kanji, kana)
            romaji = to_romaji(kana)
            out.append(langs.Card(
                word=shown,
                reading="{} · {}".format(kana, romaji) if kana and kana != shown else romaji,
                badge="N{}".format(lvl) if lvl else "Nhật",
                en=senses[:4], speak=shown, lang=langs.JA))
        return out

    def cards(self, text, max_words=25):
        out, seen = [], set()
        for surface, base, reading, pos in self.tokens(text):
            fields = pos.split(",")
            if not surface.strip() or fields[0] in SKIP_POS:
                continue
            if len(fields) > 1 and fields[1] in SKIP_SUBPOS:
                continue
            if base in seen:                     # tu lap lai thi chi hien 1 lan
                continue
            seen.add(base)
            c = self.card(surface, base, reading, pos)
            if c.found or c.reading:
                out.append(c)
            if len(out) >= max_words:
                break
        return out


# ----------------------------------------------------------------- CLI ------
def main(argv):
    text = " ".join(argv[1:]) or "私は毎日日本語を勉強しています"
    ja = Japanese()
    print("janome:", "co" if ja.tokenizer else "KHONG (tach tu tho)")
    for c in ja.cards(langs.clean(text, langs.JA)):
        print("{}  [{}]  ({})".format(c.word, c.reading, c.badge))
        if c.en:
            print("   EN: " + "; ".join(c.en))
        if c.note:
            print("   " + c.note)
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
