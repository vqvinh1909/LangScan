# -*- coding: utf-8 -*-
"""
langs.py - Nhan dien ngon ngu tu doan van ban va dieu phoi sang dung tu dien.

Moi tu tra ra mot 'Card' - popup chi biet ve Card, khong quan tam ngon ngu nao.
"""

import re

ZH, JA, KO, EN = "zh", "ja", "ko", "en"

LANG_NAME = {ZH: "Trung", JA: "Nhật", KO: "Hàn", EN: "Anh"}
TTS_LANG = {ZH: "zh-CN", JA: "ja", KO: "ko", EN: "en", "vi": "vi"}

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

    # ---- lam sach cau truoc khi gui dich may
    def prepare_for_mt(self, text, lang):
        """Don cau truoc khi dich may - dich may dich do chu yeu vi cau hong:
          - noi chu bi gach noi khi xuong dong ('trans-\\nlation' -> 'translation')
          - noi dong bi ngat giua cau (PDF, OCR, tieu de)
          - bo khoang trang thua, khoang trang truoc dau cau; them dau cach sau
            dau cau bi dinh ('word.Next' -> 'word. Next')
          - chu IN HOA -> chu thuong (calm_caps)"""
        import ocr
        t = (text or "").replace("\r\n", "\n").replace("\r", "\n")
        cjk = bool(RE_HAN.search(t) or RE_KANA.search(t) or RE_HANGUL.search(t))
        if not cjk:
            # trans-\nlation -> translation; Self-\nService -> Self-Service
            t = re.sub(r"([^\W\d_])-[ \t]*\n[ \t]*([^\W\d_])",
                       lambda m: m.group(1) + ("" if m.group(2).islower() else "-")
                       + m.group(2), t)
        t = ocr.tidy_lines(t)
        t = re.sub(r"[ \t ]+", " ", t)
        if not cjk:
            t = re.sub(r" +([,.;:!?)\]])", r"\1", t)
            t = re.sub(r"([,;])(?=[^\W\d_])", r"\1 ", t)
            t = re.sub(r"(?<=[a-zà-ỹ])([.!?])(?=[A-ZÀ-Ỹ])", r"\1 ", t)
        t = "\n".join(l.strip() for l in t.split("\n")).strip()
        if lang in (EN, "vi") or not cjk:
            t = self.calm_caps(t)
        return t

    # ---- ep dich may dung thuat ngu
    @staticmethod
    def _meanings(vi):
        """'container - moi truong dong goi' / 'a; b (c)' -> ['container', 'a', 'b']."""
        out = []
        for part in re.split(r"[;/]", vi or ""):
            part = re.sub(r"\(.*?\)", "", part.split(" - ")[0]).strip(" .,:")
            if part:
                out.append(part)
        return out

    def _glossary_hits(self, text, lang, target):
        """Thuat ngu xuat hien trong cau -> [(chu trong cau, [cach dich dung])]."""
        hits = []
        try:
            for surface, e in self.terms().find(text, lang):
                if target == "vi":
                    good = self._meanings(e["vi"])
                elif target in ("en", "zh", "ja", "ko") and e[target]:
                    good = [f.strip() for f in e[target].split("/") if f.strip()]
                else:
                    good = []
                if good:
                    hits.append((surface, good, e["domain"]))
        except Exception:
            pass
        if lang == EN and target == "vi":        # bo IT cu chi co tieng Anh (offline...)
            try:
                it = self.en().it
                toks = [(m.group(0), m.start(), m.end())
                        for m in re.finditer(r"[A-Za-z][A-Za-z0-9'-]*", text)]
                taken = {s.lower() for s, _g, _d in hits}
                i = 0
                while i < len(toks):
                    for n in (3, 2, 1):
                        key = " ".join(t[0].lower() for t in toks[i:i + n])
                        if len(toks[i:i + n]) == n and key in it:
                            if key not in taken:
                                hits.append((text[toks[i][1]:toks[i + n - 1][2]],
                                             self._meanings(it[key][0]), "it"))
                            i += n
                            break
                    else:
                        i += 1
            except Exception:
                pass
        return hits

    def enforce_terms(self, text, lang, translated, target, translate_fn):
        """Ban dich may dich sai thuat ngu ('offline' -> 'ngoai tuyen') thi dich
        lai, thay thuat ngu do bang ma giu cho (ZQ0) roi dien nghia dung vao.
        Chi lam voi thuat ngu bi dich sai - cau van tu nhien nhat co the.
        translate_fn(text) -> ban dich. Tra ve ban dich (da sua hoac nhu cu)."""
        if not translated:
            return translated
        low = translated.lower()
        hits = self._glossary_hits(text, lang, target)

        def in_context(surface, domain):
            # Tu don tieng Anh nhieu nghia (capital: von / thu do, mold: khuon /
            # nam moc, stock: co phieu / hang ton): chi ep khi cau co them it nhat
            # mot thuat ngu khac cung nganh. 'the database is offline' -> ep;
            # 'Hanoi is the capital of Vietnam' -> giu ban dich may.
            if lang != EN or " " in surface.strip():
                return True
            return any(d == domain and s.lower() != surface.lower() for s, _g, d in hits)
        wrong = [(s, good) for s, good, d in hits
                 if in_context(s, d) and not any(g.lower() in low for g in good)]
        if not wrong:
            return translated
        masked = text
        fills = []
        for k, (surface, good) in enumerate(wrong):
            ph = "ZQ{}".format(k)
            pat = re.escape(surface)
            if lang == EN:
                pat = r"(?<![A-Za-z])" + pat + r"(?![A-Za-z])"
            masked, n = re.subn(pat, ph, masked, flags=re.I)
            if n:
                fills.append((ph, good[0]))
        if not fills:
            return translated
        out = translate_fn(masked)
        if not out or not all(ph in out for ph, _g in fills):
            return translated                  # ma giu cho bi mat: giu ban cu
        for ph, good in fills:
            if target == "vi" and good.split(" ")[0].lower() in ("không", "đang", "đã", "bị"):
                # 'is offline' -> 'la ZQ0' -> 'la khong ket noi mang': bo 'la' thua
                out = re.sub(r"\b[Ll]à\s+" + ph, ph, out)
            out = out.replace(ph, good)
        return out

    # ---- chu IN HOA truoc khi dich may
    def calm_caps(self, text):
        """'THE ENTERPRISE AI COMPASS: NAVIGATING...' -> 'The enterprise AI
        compass: navigating...'. Dich may coi chu in hoa nhu ten rieng / viet
        tat nen dich te ('COMPASS AI DOANH NGHIEP...'); ha ve chu thuong thi ra
        'La ban AI doanh nghiep...'. Giu viet tat (AI, NASA, TNHH): tu <= 4 chu
        khong phai tu tieng Anh pho bien."""
        letters = [c for c in text if c.isalpha() and not RE_HAN.match(c)
                   and not RE_KANA.match(c) and not RE_HANGUL.match(c)]
        if len(letters) < 6 or sum(c.isupper() for c in letters) < 0.8 * len(letters):
            return text
        try:
            common = self.en().cefr
        except Exception:
            common = {}

        vietnamese = bool(RE_VI.search(text.lower()))

        def word(m):
            w = m.group(0)
            low = w.lower()
            if len(w) > 4:
                return low
            if vietnamese:               # cau tieng Viet: am tiet Viet thi ha thuong
                if w in ("AI", "IT", "TV", "PC", "OK", "CEO", "USB", "GPS", "VIP"):
                    return w             # viet tat trung am tiet Viet (ai = nguoi nao)
                import unicodedata
                plain = "".join(c for c in unicodedata.normalize("NFD", low.replace("đ", "d"))
                                if not unicodedata.combining(c))
                return low if RE_VI_SYLLABLE.match(plain) else w   # TNHH, ABC giu
            return low if low in common else w                    # AI, NASA giu
        out = re.sub(r"[^\W\d_]+", word, text)
        # viet hoa dau cau
        return re.sub(r"(^|[.!?]\s+)([^\W\d_])", lambda m: m.group(1) + m.group(2).upper(), out)

    # ---- thuat ngu chuyen nganh (data/terms/*.tsv)
    def terms(self):
        if getattr(self, "_terms", None) is None:
            import terms
            self._terms = terms.Terms()
        return self._terms

    @staticmethod
    def _norm_word(w):
        """'studying  (study)' -> 'studying', 'Servers' -> 'servers'."""
        return re.sub(r"\s+", "", (w or "").split("  (")[0]).lower()

    def _apply_terms(self, text, lang, cards):
        """Gan nghia chuyen nganh vao the tu.

        - Thuat ngu trung dung mot the (order, 服务器): them '[Kinh te] ...' len
          dau nghia - KHONG che nghia thuong.
        - Thuat ngu nhieu tu / bi tach vun (balance sheet, 心肌梗死): mot the
          rieng co nhan nganh, thay cho cac manh le nam trong no.
        Ca hai deu kem tu tuong duong o cac thu tieng kia."""
        try:
            t = self.terms()
            found = t.find(text, lang)
        except Exception as e:
            print("[!] Loi doc thuat ngu:", e)
            return cards
        if not found:
            return cards
        import terms as terms_mod
        cards = list(cards)
        for surface, e in found:
            key = self._norm_word(surface)
            label = t.label(e)
            eq = t.equivalents(e, lang)
            note = "  ·  ".join(x for x in (eq, e["note"]) if x)
            same = next((c for c in cards if self._norm_word(c.word) in
                         (key, terms_mod._singular(key))), None)
            if same is not None:
                same.vi = ["[{}] {}".format(label, e["vi"])] + [
                    v for v in same.vi if v != e["vi"]]
                same.note = "  ·  ".join(x for x in (note, same.note) if x)
                if not same.badge or same.badge.startswith(("ngoài", "thuần", "gốc")):
                    same.badge = label       # khong co cap do -> hien nhan nganh
                continue
            shown = surface
            if lang != EN:
                # cach viet trong bo thuat ngu (생산 라인 co dau cach) thay cho chu
                # da bo dau cach de do (생산라인)
                forms = [f.strip() for f in e[lang].split("/")]
                shown = next((f for f in forms if re.sub(r"\s+", "", f) == surface), surface)
            reading = self._term_reading(shown, lang)
            card = Card(word=shown, reading=reading, badge=label, vi=[e["vi"]],
                        en=[e["en"]] if lang != EN and e["en"] else [], note=note,
                        speak=surface, lang=lang)
            inside = [i for i, c in enumerate(cards)
                      if self._norm_word(c.word) and self._norm_word(c.word) in key]
            pos = inside[0] if inside else 0
            cards = [c for i, c in enumerate(cards) if i not in inside]
            cards.insert(min(pos, len(cards)), card)
        return cards

    def _term_reading(self, word, lang):
        """Phien am cua thuat ngu: IPA tung tu ghep lai (tieng Anh) hoac pinyin /
        romaji / phien am Han."""
        try:
            if lang == EN:
                bits = [self.en().phonetic(w).strip("/") for w in word.split()]
                return "/{}/".format(" ".join(b for b in bits if b)) if any(bits) else ""
            return self.romanize_sentence(word, lang)
        except Exception:
            return ""

    def terms_from_vi(self, query, target):
        """Go tieng Viet -> thuat ngu chuyen nganh o ngon ngu dich (the tu)."""
        if target not in (ZH, JA, KO, EN):
            return []
        try:
            t = self.terms()
        except Exception:
            return []
        out = []
        for e in t.search_vi(query):
            word = e[target].split("/")[0].strip()
            if not word:
                continue
            reading = self._term_reading(word, target)
            note ="  ·  ".join(x for x in (t.equivalents(e, target), e["note"]) if x)
            out.append(Card(word=word, reading=reading, badge=t.label(e), vi=[e["vi"]],
                            note=note, speak=word, lang=target))
        return out

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

    # ---- phien am ca cau (dong chu Latin duoi ban dich sang Trung/Nhat/Han)
    _PUNCT = str.maketrans({"，": ", ", "。": ". ", "、": ", ", "？": "? ", "！": "! ",
                            "：": ": ", "；": "; ", "（": " (", "）": ") ", "「": '"',
                            "」": '"', "『": '"', "』": '"', "“": '"', "”": '"', "　": " "})

    def romanize_sentence(self, text, lang):
        """'我去上学' -> 'wǒ qù shàngxué', '学校に行きます' -> 'gakkou ni ikimasu',
        '학교에 갑니다' -> 'hakgyoe gamnida'. '' neu khong phai Trung/Nhat/Han."""
        text = (text or "").strip()
        if not text:
            return ""
        if lang == ZH:
            out = self._pinyin_sentence(text)
        elif lang == JA:
            out = self._romaji_sentence(text)
        elif lang == KO:
            import korean
            out = korean.romanize(text)
        else:
            return ""
        out = out.translate(self._PUNCT)
        out = re.sub(r"\s+([,.?!:;)])", r"\1", out)
        return re.sub(r"\s+", " ", out).strip()

    # Tro tu da am: trong cau gan nhu luon doc thanh nhe (吗 ma chu khong phai ma2)
    _NEUTRAL = {"吗": "ma", "呢": "ne", "吧": "ba", "了": "le", "的": "de", "得": "de",
                "着": "zhe", "过": "guo", "啊": "a", "们": "men", "么": "me", "嘛": "ma"}

    @staticmethod
    def _split_hsk(words, d):
        """jieba hay giu nguyen cum (我爱你, 今天天气) -> pinyin dinh lien kho doc.
        Cum khong phai tu HSK ma tach het duoc thanh tu HSK thi tach ra."""
        out = []
        for w in words:
            if len(w) < 3 or d.hsk_level(w):
                out.append(w)
                continue
            parts, i = [], 0
            while i < len(w):
                for size in range(min(4, len(w) - i), 0, -1):
                    piece = w[i:i + size]
                    if d.hsk_level(piece) or (size == 1 and Analyzer._NEUTRAL.get(piece)):
                        parts.append(piece)
                        i += size
                        break
                else:
                    parts = None
                    break
            out.extend(parts if parts and len(parts) > 1 else [w])
        return out

    def _pinyin_sentence(self, text):
        """Pinyin co dau thanh, viet lien theo tu (shàngxué) nhu sach giao khoa."""
        import dictionary
        d = self.zh()
        out = []
        for run in re.findall(r"[㐀-䶿一-鿿豈-﫿]+|[^㐀-䶿一-鿿豈-﫿]+", text):
            if not RE_HAN.match(run):
                out.append(run)
                continue
            for word in self._split_hsk(dictionary.segment(run, d), d):
                if word in self._NEUTRAL:
                    out.append(self._NEUTRAL[word])
                    continue
                entries = d.lookup(word, "vi") or d.lookup(word, "en")
                if entries:
                    out.append(entries[0].pinyin.replace(" ", ""))
                    continue
                syl = []                 # tu ghep la: ghep pinyin tung chu
                for ch in word:
                    e = d.lookup(ch, "vi") or d.lookup(ch, "en")
                    syl.append(e[0].pinyin if e else ch)
                out.append("".join(syl))
        return " ".join(out)

    def _romaji_sentence(self, text):
        """Romaji theo tu; duoi dong tu / tro dong tu dinh vao tu truoc (ikimasu)."""
        import japanese
        out, prev = [], ""
        for surface, _base, reading, pos in self.ja().tokens(text):
            fields = (pos or "").split(",")
            if fields[0] == "記号" or not (reading or japanese.RE_KANA_ONLY.match(surface)):
                out.append(surface)      # dau cau, chu Latin, so
                prev = ""
                continue
            kana = japanese.kata_to_hira(reading or surface)
            if fields[0] == "助詞" and surface in ("は", "へ", "を"):
                rom = {"は": "wa", "へ": "e", "を": "o"}[surface]
            else:
                rom = japanese.to_romaji(kana)
            # Dinh vao DONG TU / tinh tu dung truoc: 行き+ます -> ikimasu,
            # し+て -> shite. Sau danh tu thi tach: gakusei desu.
            glue = prev in ("動詞", "形容詞", "助動詞") and not (
                fields[0] == "助動詞" and surface[:1] == "で") and (     # です tach rieng
                fields[0] == "助動詞"
                or (fields[0] == "助詞" and len(fields) > 1 and fields[1] == "接続助詞"))
            if glue and out:
                out[-1] += rom
            else:
                out.append(rom)
            prev = fields[0]
        return " ".join(out)

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
            cards = None
            if lang == ZH:
                import dictionary
                cards = dictionary.cards(text, self.zh(), max_words)
            elif lang == JA:
                cards = self.ja().cards(text, max_words)
            elif lang == KO:
                cards = self.ko().cards(text, max_words)
            elif lang == EN:
                cards = self.en().cards(text, max_words)
            if cards is not None:
                return lang, self._apply_terms(text, lang, cards), ""
        except ImportError as e:
            return lang, [], "Tiếng {}: {}".format(LANG_NAME[lang], e)
        except FileNotFoundError as e:
            return lang, [], str(e)
        return lang, [], ""
