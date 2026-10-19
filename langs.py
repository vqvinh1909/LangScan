# -*- coding: utf-8 -*-
"""
langs.py - Nhan dien ngon ngu tu doan van ban va dieu phoi sang dung tu dien.

Moi tu tra ra mot 'Card' - popup chi biet ve Card, khong quan tam ngon ngu nao.
"""

import re

ZH, JA, KO, EN = "zh", "ja", "ko", "en"

LANG_NAME = {ZH: "Trung", JA: "Nhat", KO: "Han", EN: "Anh"}
TTS_LANG = {ZH: "zh-CN", JA: "ja", KO: "ko", EN: "en"}

# Viet bang ma Unicode chu khong dung ky tu truc tiep - vai chu Han tu va chu
# tuong thich trong nhin giong het nhau nhung ma khac nhau, de viet nham dai.
RE_HAN = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]")   # Han tu / Kanji
RE_KANA = re.compile(r"[\u3040-\u30ff\u31f0-\u31ff\uff66-\uff9f]")  # Hiragana+Katakana
RE_HANGUL = re.compile(r"[\uac00-\ud7a3\u1100-\u11ff\u3130-\u318f]")  # Hangul
RE_LATIN = re.compile(r"[A-Za-z]")                                   # chu Latinh


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
            return lang, [], "Tieng {}: {}".format(LANG_NAME[lang], e)
        except FileNotFoundError as e:
            return lang, [], str(e)
        return lang, [], ""
