# -*- coding: utf-8 -*-
"""
langs.py - Nhan dien ngon ngu tu doan van ban va dieu phoi sang dung tu dien.

Moi tu tra ra mot 'Card' - popup chi biet ve Card, khong quan tam ngon ngu nao.
"""

import re

ZH, JA, KO, EN = "zh", "ja", "ko", "en"

LANG_NAME = {ZH: "Trung", JA: "Nhật", KO: "Hàn", EN: "Anh"}
TTS_LANG = {ZH: "zh-CN", JA: "ja", KO: "ko", EN: "en"}

# Viet bang ma Unicode chu khong dung ky tu truc tiep - vai chu Han tu va chu
# tuong thich trong nhin giong het nhau nhung ma khac nhau, de viet nham dai.
RE_HAN = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]")   # Han tu / Kanji
RE_KANA = re.compile(r"[\u3040-\u30ff\u31f0-\u31ff\uff66-\uff9f]")  # Hiragana+Katakana
RE_HANGUL = re.compile(r"[\uac00-\ud7a3\u1100-\u11ff\u3130-\u318f]")  # Hangul
RE_LATIN = re.compile(r"[A-Za-z]")                                   # chu Latinh
# Nguyen am co dau / chu d cua tieng Viet (dang NFC, chu thuong)
RE_VI = re.compile("[\u00e0\u00e1\u1ea1\u1ea3\u00e3\u00e2\u1ea7\u1ea5\u1ead\u1ea9\u1eab"
                    "\u0103\u1eb1\u1eaf\u1eb7\u1eb3\u1eb5\u00e8\u00e9\u1eb9\u1ebb\u1ebd"
                    "\u00ea\u1ec1\u1ebf\u1ec7\u1ec3\u1ec5\u00ec\u00ed\u1ecb\u1ec9\u0129"
                    "\u00f2\u00f3\u1ecd\u1ecf\u00f5\u00f4\u1ed3\u1ed1\u1ed9\u1ed5\u1ed7"
                    "\u01a1\u1edd\u1edb\u1ee3\u1edf\u1ee1\u00f9\u00fa\u1ee5\u1ee7\u0169"
                    "\u01b0\u1eeb\u1ee9\u1ef1\u1eed\u1eef\u1ef3\u00fd\u1ef5\u1ef7\u1ef9"
                    "\u0111]")


# Mot am tiet tieng Viet da bo dau (dau thanh, mu, rau, d -> d):
# phu am dau (co the khong co) + van + phu am cuoi (co the khong co)
RE_VI_SYLLABLE = re.compile(
    r"^(ngh|ng|nh|ch|gh|gi|kh|ph|qu|th|tr|[bcdghklmnprstvx])?"
    r"(uye|uya|uoi|uou|ieu|yeu|oai|oay|oeo|uay|uai|uoi|uoi|ia|ie|iu|ua|ue|ui|uo|uy|"
    r"ai|ao|au|ay|eo|eu|oa|oe|oi|ya|ye|[aeiouy])"
    r"(ng|nh|ch|[cmnpt])?$")
# Dau hieu CHI tieng Viet co (pinyin khong co): phu am cuoi c/t/p/m/ch/nh,
# phu am dau ph/th/tr/kh/nh/ng/gh/v, van oi/ay/uoi/ieu...
RE_VI_ONLY = re.compile(r"^(ngh|ng|nh|gh|kh|ph|th|tr|v)|(ch|nh|[ctpm])$|oi|ay|uoi|uou")


def vietnamese_plain_tokens(text):
    """Cac tu Latin trong chuoi, chu thuong ('' neu co ky tu la)."""
    toks = re.findall(r"[A-Za-z]+", text or "")
    rest = re.sub(r"[A-Za-z\s\d.,;:!?\"'()\-]+", "", text or "")
    return [] if rest else [t.lower() for t in toks]


class Card(object):
    """Mot the tu de popup ve ra."""

    __slots__ = ("word", "reading", "badge", "vi", "en", "note",
                 "speak", "lang", "tones")

    def __init__(self, word, reading="", badge="", vi=None, en=None,
                 note="", speak=None, lang=ZH, tones=None):
        self.word = word
        self.reading = reading          # pinyin / kana + romaji / romaja
        self.badge = badge              # HSK3 / N5 / ...
        self.vi = vi or []              # nghia tieng Viet
        self.en = en or []              # nghia tieng Anh
        self.note = note                # ghi chu them (luong tu, Han tu, Han-Viet...)
        self.speak = speak if speak is not None else word
        self.lang = lang
        self.tones = tones or []        # thanh dieu (chi tieng Trung)

    @property
    def found(self):
        return bool(self.vi or self.en)


def count_scripts(text):
    return (len(RE_HAN.findall(text)),
            len(RE_KANA.findall(text)),
            len(RE_HANGUL.findall(text)),
            len(RE_LATIN.findall(text)))


def detect(text):
    """Doan ngon ngu tu loai chu viet.

    - Co Hangul            -> tieng Han
    - Co kana              -> tieng Nhat
    - Chi co Han tu        -> tieng Trung (Kanji thuan rat kho phan biet,
                              nen co phim tat rieng de ep tra tieng Nhat)
    - Chi co chu Latinh    -> tieng Anh
    """
    han, kana, hangul, latin = count_scripts(text)
    if hangul:
        return KO
    if kana:
        return JA
    if han:
        return ZH
    if latin:
        return EN
    return None


def clean(text, lang, max_chars=120):
    """Giu lai phan chu thuoc ngon ngu do; tieng Han/Anh giu ca khoang trang."""
    if not text:
        return ""
    text = text.strip()
    if lang == EN:
        return re.sub(r"\s+", " ", text)[:max_chars * 2]
    if lang == KO:
        keep = [ch for ch in text
                if RE_HANGUL.match(ch) or RE_HAN.match(ch) or ch.isspace()]
        return re.sub(r"\s+", " ", "".join(keep)).strip()[:max_chars]
    if lang == JA:
        keep = [ch for ch in text
                if RE_HAN.match(ch) or RE_KANA.match(ch) or ch == "ー"]
        return "".join(keep)[:max_chars]
    return "".join(ch for ch in text if RE_HAN.match(ch))[:max_chars]


class Analyzer(object):
    """Nap tu dien theo kieu 'dung den dau nap den do' cho nhe bo nho."""

    def __init__(self):
        self._zh = None
        self._ja = None
        self._ko = None
        self._en = None

    # ---- tung ngon ngu
    def zh(self):
        if self._zh is None:
            import dictionary
            self._zh = dictionary.Dictionary()
        return self._zh

    def ja(self):
        if self._ja is None:
            import japanese
            self._ja = japanese.Japanese()
        return self._ja

    def ko(self):
        if self._ko is None:
            import korean
            # Muon tra nghia Han tu trong tu Han-Han thi can tu dien Trung-Viet
            try:
                hv = self.zh()
            except Exception:
                hv = None
            self._ko = korean.Korean(hanviet=hv)
        return self._ko

    def en(self):
        if self._en is None:
            import english
            self._en = english.English()
        return self._en

    # ---- tieng Viet go khong dau ('toi di hoc', 'ngan hang', chu OCR mat dau)
    def _pinyin_syllables(self):
        if getattr(self, "_py_syl", None) is None:
            syl = set()
            try:
                d = self.zh()
                for src in (d.en_simp, d.vi_simp):
                    for word, entries in src.items():
                        if len(word) == 1:
                            for e in entries:
                                s = re.sub(r"[^a-z]", "", e.pinyin_num.lower())
                                if s:
                                    syl.add(s)
            except Exception:
                pass
            self._py_syl = syl
        return self._py_syl

    def _is_pinyin(self, token):
        """'ni', 'hao', 'xuesheng' (ghep nhieu am tiet) deu la pinyin."""
        syl = self._pinyin_syllables()
        ok = [True] + [False] * len(token)
        for i in range(len(token)):
            if ok[i]:
                for j in range(i + 1, min(len(token), i + 6) + 1):
                    if token[i:j] in syl:
                        ok[j] = True
        return ok[len(token)]

    def vietnamese_plain(self, text):
        """Chu Latin nay co phai tieng Viet go khong dau khong?

        'vi'    : chac la tieng Viet ('toi di hoc', 'thu tu nen lam tiep')
        'maybe' : doc duoc ca tieng Viet lan pinyin ('xin chao', 'ni hao')
        None    : khong phai (tieng Anh, romaji, chu co dau...)
        """
        if RE_VI.search((text or "").lower()):
            return None                  # co dau thi da nhan ra o cho khac
        toks = vietnamese_plain_tokens(text)
        if not toks or len(toks) > 40:
            return None
        valid = [t for t in toks if RE_VI_SYLLABLE.match(t)]
        # Cau ngan: moi tu phai la am tiet Viet ('watashi', 'bank' -> khong).
        # Doan dai (chu OCR) duoc phep lan vai tu dinh lien / tu Anh ('file exe').
        if len(valid) < (len(toks) if len(toks) < 5 else 0.75 * len(toks)):
            return None
        try:
            common = self.en().cefr
        except Exception:
            common = {}
        english = sum(1 for t in toks if t in common)
        if english * 2 > len(toks):
            return None                  # 'the man can do it': tieng Anh
        toks = valid
        if len(toks) == 1:
            t = toks[0]
            try:
                in_en = bool(self.en().lookup(t))
            except Exception:
                in_en = False
            if in_en or len(t) < 3 or self._is_pinyin(t):
                return None              # 'ban', 'hao', 'an': qua mo ho
            return "vi"                  # 'nguoi', 'khong', 'nuoc'
        if any(RE_VI_ONLY.search(t) or not self._is_pinyin(t) for t in toks):
            return "vi"
        return "maybe"

    def romanized_text(self, text, lang):
        """'tabemashita' -> 'たべました', 'annyeong' -> '안녕' ('' neu khong doc duoc)."""
        if lang == JA:
            import japanese
            return japanese.from_romaji(text)
        if lang == KO:
            return self.ko().from_romaja(text)
        return ""

    def romanized(self, text, lang, max_words=25):
        """Doc chu Latin nhu romaji (Nhat) / phien am RR (Han) -> danh sach Card."""
        if lang == JA:
            return self.ja().romaji_cards(text, max_words)
        if lang == KO:
            hangul = self.ko().from_romaja(text)
            return self.ko().cards(hangul, max_words) if hangul else []
        return []

    # ---- tra cuu
    def analyze(self, raw_text, force_lang=None, max_words=25):
        """-> (ma_ngon_ngu, danh sach Card, thong bao loi neu co)."""
        lang = force_lang or detect(raw_text or "")
        if lang is None:
            return None, [], ""
        text = clean(raw_text, lang)
        try:
            if not text and lang in (JA, KO) and RE_LATIN.search(raw_text or ""):
                # Chon nguon Nhat/Han ma go chu Latin = go phien am
                # ('tabemashita' -> 食べる, 'annyeonghaseyo' -> 안녕하세요)
                return lang, self.romanized(raw_text, lang, max_words), ""
            if not text:
                return lang, [], ""
            if lang == ZH:
                import dictionary
                return lang, dictionary.cards(text, self.zh(), max_words), ""
            if lang == JA:
                return lang, self.ja().cards(text, max_words), ""
            if lang == KO:
                return lang, self.ko().cards(text, max_words), ""
            if lang == EN:
                return lang, self.en().cards(text, max_words), ""
        except ImportError as e:
            return lang, [], "Tiếng {}: {}".format(LANG_NAME[lang], e)
        except FileNotFoundError as e:
            return lang, [], str(e)
        return lang, [], ""
