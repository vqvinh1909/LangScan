# -*- coding: utf-8 -*-
"""
reverse.py - Tra nguoc: go tieng Viet -> tim tu tieng Trung / Anh / Nhat / Han.

Khong can them du lieu gi: quet thang nghia tieng Viet co san trong
CVDICT (Trung-Viet) va envi.tsv (Anh-Viet), roi xep theo do khop.

Bo dau tieng Viet khi so sanh, nen go "ngan hang" cung ra "ngân hàng".

Nhat va Han khong co tu dien Viet nen di duong vong (search_foreign):
  tieng Viet -> Han tu cua tu tieng Trung -> tu tieng Nhat/Han cung Han tu
  tieng Viet -> tu tieng Anh -> tu tieng Nhat/Han cung nghia

Thu:  python reverse.py "ngân hàng"
"""

import os
import pickle
import re
import sys
import unicodedata

import langs

MAX_PER_LANG = 12
from paths import DATA_DIR
CACHE_ZH = os.path.join(DATA_DIR, "reverse_zh.pickle")
CACHE_EN = os.path.join(DATA_DIR, "reverse_en.pickle")
CACHE_PY = os.path.join(DATA_DIR, "reverse_pinyin.pickle")
MAX_SENSE_LEN = 140


def strip_tone(text):
    """'Ngân Hàng' -> 'ngan hang' (bo dau, ha chu thuong)."""
    text = (text or "").lower().replace("đ", "d").replace("Đ", "d")
    text = unicodedata.normalize("NFD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", text).strip()


# --------------------------------------------------------------- pinyin -----
# Nguyen am co dau thanh -> nguyen am tran, de go "yínháng" cung khop "yinhang"
_PY_MARKS = {}
for _plain, _marked in (("a", "āáǎà"), ("e", "ēéěè"), ("i", "īíǐì"),
                        ("o", "ōóǒò"), ("u", "ūúǔù"), ("v", "ǖǘǚǜü")):
    for _ch in _marked:
        _PY_MARKS[_ch] = _plain


def flat_pinyin(text):
    """'yín háng' / 'yin2 hang2' / 'Yín Háng' -> 'yinhang'."""
    out = []
    for ch in (text or "").lower():
        ch = _PY_MARKS.get(ch, ch)
        if ch.isalpha():
            out.append(ch)
        elif ch == ":":          # kieu 'nu:3' trong CC-CEDICT
            continue
    return "".join(out)


def _score(needle, hay):
    """0 = khop het, cang lon cang xa. None = khong khop.

    Chi nhan khi khop tron tu. Truoc day co nhan ca chuoi nam giua tu,
    nen go 'hello' lai ra 'Phellodendron' (p-HELLO-dendron) - vo nghia.
    """
    if hay == needle:
        return 0
    if hay.startswith(needle + " ") or hay.startswith(needle + ","):
        return 1
    if re.search(r"(?<![0-9A-Za-z])" + re.escape(needle) + r"(?![0-9A-Za-z])", hay):
        return 2
    return None


class Reverse(object):
    """Chi so tra nguoc, dung den dau dung den do (nap lan dau hoi cham)."""

    def __init__(self, analyzer):
        self.analyzer = analyzer
        self.last_exact_vi = False   # lan tim vua roi co nghia trung y ca dau khong
        self._zh = None          # [(tu, pinyin, nghia_goc, nghia_da_bo_dau)]
        self._en = None
        self._py = None          # {pinyin_khong_dau: [(tu, pinyin, nghia)]}

    # ---- dung chi so (co cache ra dia, lan sau nap trong ~1 giay)
    @staticmethod
    def _load_cache(path, source_path):
        try:
            if (os.path.exists(path) and os.path.exists(source_path)
                    and os.path.getmtime(path) > os.path.getmtime(source_path)):
                with open(path, "rb") as f:
                    return pickle.load(f)
        except Exception:
            pass
        return None

    @staticmethod
    def _save_cache(path, rows):
        try:
            with open(path, "wb") as f:
                pickle.dump(rows, f, protocol=4)
        except Exception:
            pass

    def _build_zh(self):
        if self._zh is not None:
            return self._zh
        import dictionary
        rows = self._load_cache(CACHE_ZH, dictionary.CVDICT_PATH)
        if rows is None:
            rows = []
            d = self.analyzer.zh()
            for word, entries in d.vi_simp.items():
                for e in entries:
                    for sense in e.senses[:6]:
                        if len(sense) <= MAX_SENSE_LEN:
                            rows.append((word, e.pinyin, sense, strip_tone(sense)))
            self._save_cache(CACHE_ZH, rows)
        self._zh = rows
        return rows

    def _build_en(self):
        if self._en is not None:
            return self._en
        import english
        rows = self._load_cache(CACHE_EN, english.ENVI_PATH)
        if rows is None:
            rows = []
            e = self.analyzer.en()
            for word, (pos, defs, ex) in e.index.items():
                for sense in defs[:8]:
                    if len(sense) <= MAX_SENSE_LEN:
                        rows.append((word, "", sense, strip_tone(sense)))
            for term, (meaning, note) in e.it.items():
                rows.append((term, "IT", meaning, strip_tone(meaning)))
            self._save_cache(CACHE_EN, rows)
        self._en = rows
        return rows

    def _build_py(self):
        """Chi so pinyin -> tu tieng Trung."""
        if self._py is not None:
            return self._py
        import dictionary
        idx = self._load_cache(CACHE_PY, dictionary.CVDICT_PATH)
        if idx is None:
            idx = {}
            d = self.analyzer.zh()
            for source in (d.vi_simp, d.en_simp):
                for word, entries in source.items():
                    for e in entries:
                        key = flat_pinyin(e.pinyin_num)
                        if not key or len(key) > 24:
                            continue
                        bucket = idx.setdefault(key, [])
                        if not any(b[0] == word for b in bucket):
                            bucket.append((word, e.pinyin, e.senses[0][:120]))
            self._save_cache(CACHE_PY, idx)
        self._py = idx
        return idx

    def is_exact_pinyin(self, query):
        """Ca chuoi go vao dung bang pinyin cua mot tu that?"""
        key = flat_pinyin(query)
        return len(key) >= 2 and key in self._build_py()

    def search_pinyin(self, query, limit=MAX_PER_LANG):
        """Go pinyin (yinhang / yin2hang2 / yín háng) -> tu tieng Trung."""
        key = flat_pinyin(query)
        if len(key) < 2:
            return []
        idx = self._build_py()
        d = self.analyzer.zh()

        found = []
        for word, pinyin, sense in idx.get(key, []):
            found.append((0, word, pinyin))
        if len(found) < limit:                    # chua du thi lay them kieu go dở
            for k, bucket in idx.items():
                if k.startswith(key) and k != key:
                    for word, pinyin, sense in bucket:
                        found.append((1, word, pinyin))
                    if len(found) > limit * 6:
                        break

        found.sort(key=lambda f: (f[0], d.hsk_level(f[1]) or 9, len(f[1])))
        cards, seen = [], set()
        for _rank, word, pinyin in found:
            if word in seen:
                continue
            seen.add(word)
            vi = d.lookup(word, "vi")
            en = d.lookup(word, "en")
            lvl = d.hsk_level(word)
            cards.append(langs.Card(
                word=word, reading=pinyin,
                badge="HSK{}".format(lvl) if lvl else "Trung",
                vi=vi[0].senses[:4] if vi else [],
                en=en[0].senses[:3] if en else [],
                speak=word, lang=langs.ZH,
                tones=vi[0].tones() if vi else (en[0].tones() if en else [])))
            if len(cards) >= limit:
                break
        return cards

    def _word_cost(self):
        """Ham 'chi phi' cua mot tu khi tach cau: tu cang thong dung cang re.

        Co jieba thi dung tan suat that (-log xac suat, kieu Viterbi);
        khong co thi dua vao cap HSK."""
        if getattr(self, "_cost_fn", None) is not None:
            return self._cost_fn
        import math
        d = self.analyzer.zh()
        try:
            import jieba
            jieba.dt.check_initialized()
            freq, total = jieba.dt.FREQ, float(jieba.dt.total)

            def cost(word):
                return -math.log((freq.get(word, 0) + 1) / total)
        except Exception:
            def cost(word):
                return float(d.hsk_level(word) or 7) + 0.5
        self._cost_fn = cost
        return cost

    def pinyin_phrase(self, query):
        """Tach ca cau pinyin thanh tung tu: 'wo shi xuesheng' -> 我 是 学生.

        search_pinyin coi ca chuoi la MOT tu nen 'wo shi' ra 卧室 (phong ngu).
        Day chon cach tach ma tong do thong dung cao nhat. Go cach thi chi
        cat o cho cach; go lien ('woshi') thi cat o bat ky dau.
        Tra ve [] neu chi ra mot tu (luc do search_pinyin da du).
        """
        tokens = [flat_pinyin(t) for t in (query or "").split()]
        tokens = [t for t in tokens if t]
        flat = "".join(tokens)
        if len(flat) < 2 or len(flat) > 60:
            return []
        if len(tokens) > 1:                      # chi cat o ranh gioi nguoi dung go
            cuts, pos = {0}, 0
            for t in tokens:
                pos += len(t)
                cuts.add(pos)
        else:
            cuts = set(range(len(flat) + 1))
        idx = self._build_py()
        cost = self._word_cost()
        n = len(flat)
        best = [None] * (n + 1)                  # best[i] = (chi phi, [tu]) cho flat[:i]
        best[0] = (0.0, [])
        for i in range(n):
            if best[i] is None or i not in cuts:
                continue
            for j in range(i + 1, min(n, i + 24) + 1):
                if j not in cuts:
                    continue
                # chi tu toan chu Han: tu dien co ca 'T恤', 'T' ... -> 'melatonin'
                # bi cat ra '么 拉 T 哦 您'
                bucket = [b for b in idx.get(flat[i:j]) or []
                          if all("㐀" <= ch <= "鿿" or "豈" <= ch <= "﫿"
                                 for ch in b[0])]
                if not bucket:
                    continue
                word = min((b[0] for b in bucket), key=cost)
                c = best[i][0] + cost(word)
                if best[j] is None or c < best[j][0]:
                    best[j] = (c, best[i][1] + [word])
        if best[n] is None or len(best[n][1]) < 2:
            return []
        d = self.analyzer.zh()
        cards = []
        for word in best[n][1]:
            vi = d.lookup(word, "vi")
            en = d.lookup(word, "en")
            e = (vi or en)[0]
            lvl = d.hsk_level(word)
            cards.append(langs.Card(
                word=word, reading=e.pinyin,
                badge="HSK{}".format(lvl) if lvl else "Trung",
                vi=vi[0].senses[:4] if vi else [],
                en=en[0].senses[:3] if en else [],
                speak=word, lang=langs.ZH, tones=e.tones()))
        return cards

    # ---- tra cuu
    def _search_rows(self, rows, needle, limit, raw=""):
        hits = []
        raw = (raw or "").strip().lower()
        short = len(needle) <= 4 and bool(raw)
        for word, extra, sense, flat in rows:
            if needle not in flat:      # loc nhanh truoc khi cham vao regex
                continue
            low = sense.lower()
            # Tu qua ngan ma bo dau thi mo ho ('ăn' -> 'an' dinh du thu), nen
            # bat buoc co dung cum co dau. Loc truoc regex cho nhanh.
            if short and raw not in low:
                continue
            s = _score(needle, flat)
            if s is None:
                continue
            # 'chào' phai dung tren 'cháo': trung ca dau thi uu tien hon
            exact_tone = 0 if low.strip() == raw else 1
            hits.append((s, exact_tone, len(sense), word, extra, sense))
        hits.sort(key=lambda h: (h[0], h[1], h[2]))
        self.last_exact_vi = any(h[1] == 0 for h in hits)
        out, seen = [], set()
        for s, _tone, _len, word, extra, sense in hits:
            if word in seen:
                continue
            seen.add(word)
            out.append((word, extra, sense, 0 if s == 0 else 1, _tone, len(sense)))
            if len(out) >= 300:        # giu rong rai, viec xep hang de ben duoi lo
                break
        return out

    def search(self, query, limit=MAX_PER_LANG, only=None):
        """-> danh sach Card. only='zh' hoac 'en' de chi tim mot ben."""
        needle = strip_tone(query)
        self.last_exact_vi = False
        if len(needle) < 2:
            return []

        cards = []
        exact_any = False
        try:
            zh = (self._search_rows(self._build_zh(), needle, limit, query)
                  if only in (None, "zh") else [])
            exact_any = exact_any or self.last_exact_vi
        except Exception:
            zh = []
        # Xep lai: tu pho bien (co trong HSK, cap thap) len truoc
        d0 = self.analyzer.zh() if zh else None
        # Chu don le khong co trong HSK thuong la chu hiem (匑, 喏) -> day xuong
        def _zh_rank(row):
            lvl = d0.hsk_level(row[0])
            rare = 0 if lvl else (1 if len(row[0]) > 1 else 2)
            return (row[3], row[4], rare, lvl or 9, row[5], len(row[0]))

        zh.sort(key=_zh_rank)
        for word, pinyin, sense, _s, _t, _l in zh[:limit]:
            d = self.analyzer.zh()
            lvl = d.hsk_level(word)
            en_entries = d.lookup(word, "en")
            cards.append(langs.Card(
                word=word, reading=pinyin,
                badge="HSK{}".format(lvl) if lvl else "Trung",
                vi=[sense], en=en_entries[0].senses[:3] if en_entries else [],
                speak=word, lang=langs.ZH,
                tones=d.lookup(word, "vi")[0].tones() if d.lookup(word, "vi") else []))

        try:
            en = (self._search_rows(self._build_en(), needle, limit, query)
                  if only in (None, "en") else [])
            exact_any = exact_any or self.last_exact_vi
        except Exception:
            en = []
        e0 = self.analyzer.en() if en else None
        _cefr_rank = {"A1": 1, "A2": 2, "B1": 3, "B2": 4, "C1": 5, "C2": 6}

        def _en_rank(row):
            word = row[0]
            # Tu don gian (bank) tren tu ghep (land-bank, savings-bank)
            compound = 1 if (" " in word or "-" in word) else 0
            level = (0 if row[1] == "IT"
                     else _cefr_rank.get(e0.cefr.get(word, ""), 8))
            return (row[3], row[4], compound, level, row[5], len(word))

        en.sort(key=_en_rank)
        for word, extra, sense, _s, _t, _l in en[:limit]:
            e = self.analyzer.en()
            lvl = e.cefr.get(word)
            cards.append(langs.Card(
                word=word, reading=e.phonetic(word),
                badge="IT" if extra == "IT" else (lvl or "Anh"),
                vi=[sense], speak=word, lang=langs.EN))
        self.last_exact_vi = exact_any
        return cards


    # ---------------------------------------- Viet -> Nhat / Han (qua tieng Anh)
    def search_foreign(self, query, target, limit=MAX_PER_LANG):
        """Khong co tu dien Viet-Nhat / Viet-Han, nen di duong vong:

        tieng Viet -> tieng Anh (tu dien Anh-Viet) -> tieng Nhat/Han (JMdict,
        kengdic deu co nghia tieng Anh). Tu nao nhieu nghia tieng Anh cung tro
        toi thi xep len truoc - do la tin hieu no dung nghia.
        """
        needle = strip_tone(query)
        if len(needle) < 2:
            return [], []
        # Chon tu tieng Anh lam cau noi. Tin hieu manh nhat: ve trai cua nghia
        # dung y bang tu can tim - 'computer = Máy tính, máy vi tính...' thi
        # 'computer' chac chan hon 'brain = Máy tính điện tử.'
        rows = self._search_rows(self._build_en(), needle, limit * 2, query)
        e0 = self.analyzer.en()
        _cefr = {"A1": 1, "A2": 2, "B1": 3, "B2": 4, "C1": 5, "C2": 6}

        def seed_rank(row):
            word, extra, sense = row[0], row[1], row[2]
            head = strip_tone(re.split(r"[,;.]", sense)[0])
            exact_head = 0 if head == needle else 1
            level = 0 if extra == "IT" else _cefr.get(e0.cefr.get(word, ""), 8)
            compound = 1 if (" " in word or "-" in word) else 0
            return (exact_head, compound, level, len(word))

        seeds = []
        for row in sorted(rows, key=seed_rank):
            w = row[0]
            if " " in w or "-" in w or w in seeds:
                continue
            seeds.append(w)
            if len(seeds) >= 3:
                break
        if not seeds:
            return [], []

        try:
            engine = self.analyzer.ja() if target == langs.JA else self.analyzer.ko()
        except Exception as e:
            raise e

        # Tu Han-Viet: 'ngân hàng' -> 银行 (Trung) -> 銀行 (Han tu) -> 은행 / 銀行.
        # Neu Han tu cua ket qua Nhat/Han trung voi tu tieng Trung tim duoc thi
        # gan nhu chac chan la dung tu.
        han_forms = set()
        try:
            d = self.analyzer.zh()
            for card in self.search(query, limit=6, only=langs.ZH):
                for e in d.lookup(card.word, "vi") + d.lookup(card.word, "en"):
                    han_forms.add(e.simplified)
                    han_forms.add(e.traditional)
        except Exception:
            pass

        found = {}
        order = []

        # Duong tot nhat cho tu Han-Viet: dung thang Han tu cua tu tieng Trung.
        # 'ngân hàng' -> 银行/銀行 -> 銀行 (Nhat) / 은행 (Han).
        for hz in list(han_forms)[:6]:
            try:
                if target == langs.JA:
                    hits = engine.search_english(hz, limit=3) or []
                    # Uu tien muc co dung mat chu do (銀行 -> 銀行)
                    hits = [c for c in hits if c.word == hz] or hits
                else:
                    hits = engine.search_hanja(hz, limit=3)
            except Exception:
                hits = []
            for card in hits:
                if card.word not in found:
                    found[card.word] = [3, card, hz, -1]   # -1 = uu tien cao nhat
                    order.append(card.word)

        for seed_idx, seed in enumerate(seeds):
            for card in engine.search_english(seed, limit=8):
                key = card.word
                if key not in found:
                    found[key] = [0, card, seed, seed_idx]
                    order.append(key)
                found[key][0] += 1              # nhieu tu tieng Anh cung tro toi

        def rank(key):
            count, card, seed, seed_idx = found[key]
            # Han tu trung voi tu tieng Trung cung nghia -> chac chan dung
            han = "".join(ch for ch in (card.word + " " + (card.note or ""))
                          if langs.RE_HAN.match(ch))
            same_han = 0 if (han and han in han_forms) else 1
            badge = card.badge or ""
            lvl = 9
            if badge.startswith("N") and badge[1:].isdigit():
                lvl = 6 - int(badge[1:])        # N5 pho thong nhat -> len truoc
            # Nghia tieng Anh cang ngan thi cang la nghia chinh, khong phai
            # muc phu kieu 'a place where one studies; a den'
            gloss = len(card.en[0]) if card.en else 99
            return (same_han, seed_idx, -count, lvl, len(card.word), gloss,
                    order.index(key))

        cards = []
        for key in sorted(found, key=rank)[:limit]:
            count, card, seed, _idx = found[key]
            bridge = "qua tiếng Anh: {}".format(seed)
            card.note = (card.note + "  ·  " + bridge) if card.note else bridge
            cards.append(card)
        return cards, seeds


def main(argv):
    query = " ".join(argv[1:]) or "ngân hàng"
    import time
    a = langs.Analyzer()
    r = Reverse(a)
    t0 = time.time()
    cards = r.search_pinyin(query) or r.search(query)
    print("'{}' -> {} ket qua trong {:.2f}s\n".format(query, len(cards), time.time() - t0))
    for c in cards:
        print("{:12} {:12} [{}]  {}".format(
            c.word, c.reading[:12], c.badge, "; ".join(c.vi)[:60]))
    t0 = time.time()
    r.search(query)
    print("\n(lan tra thu hai: {:.2f}s)".format(time.time() - t0))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
