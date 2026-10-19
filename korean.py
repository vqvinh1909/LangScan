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

from paths import DATA_DIR
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


# ------------------------------------------------ phien am Latin -> Hangul --
# Go 'annyeonghaseyo' / 'eunhaeng' -> 안녕하세요 / 은행. Kho vi RR viet phu am
# cuoi noi sang am sau (한국어 = han-gu-geo), nen sinh nhieu cach doc roi de
# tu dien chon. Moi lua chon 'kem chuan' bi cong diem phat, thu re nhat truoc.
_R_VOWELS = {v: i for i, v in enumerate(_JUNG)}
# phu am dau: chuoi Latin -> [(chi so, diem phat)]; k/t/p/ch cung thu ㄱ/ㄷ/ㅂ/ㅈ
# vi nhieu sach dung kieu cu (kamsahamnida thay vi gamsahamnida)
_R_INITIAL = {"g": [(0, 0)], "kk": [(1, 0)], "n": [(2, 0)], "d": [(3, 0)],
              "tt": [(4, 0)], "r": [(5, 0)], "l": [(5, 1)], "m": [(6, 0)],
              "b": [(7, 0)], "pp": [(8, 0)], "s": [(9, 0)], "ss": [(10, 0)],
              "j": [(12, 0)], "jj": [(13, 0)], "ch": [(14, 0), (12, 1)],
              "k": [(15, 0), (0, 1)], "t": [(16, 0), (3, 1)], "p": [(17, 0), (7, 1)],
              "h": [(18, 0)]}
# phu am cuoi: chuoi Latin -> [chi so jong]
_R_FINAL = {"k": [1], "g": [1], "kk": [2], "n": [4], "t": [7, 19, 22, 23, 25],
            "d": [7], "l": [8], "r": [8], "m": [16], "p": [17], "b": [17],
            "s": [19], "ss": [20], "ng": [21], "j": [22], "ch": [23], "h": [27]}
# Dong hoa am mui: RR viet theo cach doc, phu am cuoi dung truoc n/m doi am
# (합니다 hamnida, 있는 inneun, 한국말 hangungmal) -> thu ca phu am goc
_R_FINAL_NASAL = {"m": [17], "ng": [1], "n": [20, 19, 7, 22, 23, 25]}
_R_MAX_PARSES = 400


def _romaja_parses(text):
    """Moi cach doc chuoi Latin thanh Hangul -> [(diem phat, chuoi Hangul)]."""
    text = re.sub(r"[^a-z]", "", text.lower())
    results = []

    def vowel_at(i):
        return [(v, i + len(v)) for v in _R_VOWELS if text.startswith(v, i)]

    def walk(i, out, cost):
        if len(results) >= _R_MAX_PARSES * 4 or cost > 6:
            return
        if i == len(text):
            if out:
                results.append((cost, "".join(out)))
            return
        inits = [(c, k, p) for c in _R_INITIAL if text.startswith(c, i)
                 for k, p in _R_INITIAL[c]] + [("", 11, 0)]
        for c, cho, p_init in inits:
            for v, j in vowel_at(i + len(c)):
                jung = _R_VOWELS[v]
                walk(j, out + [_syl(cho, jung)], cost + p_init)
                for f, idxs in _R_FINAL.items():
                    if not text.startswith(f, j):
                        continue
                    nxt = j + len(f)
                    # phu am cuoi dung truoc nguyen am = kieu noi am cua RR
                    # (한국어 hangugeo): duoc, nhung kem uu tien hon
                    linked = bool(vowel_at(nxt))
                    for n_idx, jong in enumerate(idxs):
                        walk(nxt, out + [_syl(cho, jung, jong)],
                             cost + p_init + (1 if linked else 0) + n_idx)
                    if f in _R_FINAL_NASAL and text.startswith(("n", "m"), nxt):
                        for jong in _R_FINAL_NASAL[f]:
                            walk(nxt, out + [_syl(cho, jung, jong)], cost + p_init + 1)

    walk(0, [], 0)
    results.sort(key=lambda r: (r[0], len(r[1])))
    seen, uniq = set(), []
    for cost, h in results:
        if h not in seen:
            seen.add(h)
            uniq.append((cost, h))
    return uniq[:_R_MAX_PARSES]


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

# Phan duoi con lai SAU khi da tach ra am tiet bi rut gon (갔|습니다, 예뻐|요).
# "" = ca tu la dang 아/어 tran (예뻐, 추워).
_TAILS = {"", "요", "서", "도", "야", "다", "니다", "니까", "습니다", "습니까",
          "어", "아", "어요", "아요", "어서", "아서", "는데", "지만", "고", "죠",
          "지요", "네요", "세요", "셔요", "으세요", "면", "으면", "으니까", "는",
          "은", "을", "거예요", "게요", "던"}

# Chi so jamo (theo bang Unicode Hangul)
_C_IEUNG, _C_RIEUL, _C_HIEUH = 11, 5, 18
_V_A, _V_AE, _V_EO, _V_YEO, _V_O, _V_WA, _V_WAE, _V_OE = 0, 1, 4, 6, 8, 9, 10, 11
_V_U, _V_WO, _V_EU, _V_I = 13, 14, 18, 20
_J_N, _J_D, _J_L, _J_B, _J_S, _J_SS, _J_H = 4, 7, 8, 17, 19, 20, 27
# ㅆ cua thi qua khu chi dinh vao am tiet dang 아/어 (갔 했 왔 마셨), con 있 la ㅆ goc
_PAST_VOWELS = (_V_A, _V_AE, _V_EO, _V_YEO, _V_WA, _V_WAE, _V_WO)


def _syl(cho, jung, jong=0):
    return chr(_HANGUL_START + cho * 588 + jung * 28 + jong)


def _stem_candidates(prefix):
    """Cac goc dong tu/tinh tu (chua co '다') co the sinh ra 'prefix'.

    Thao nguoc cac kieu rut gon va bat quy tac hay gap:
      갔 -> 가 (+았)        예뻐 -> 예쁘 (으 bi luoc)   추워 -> 춥 (ㅂ)
      들어 -> 들 / 듣 (ㄷ)   나아 -> 낫 (ㅅ)            불러 -> 부르 (르)
      그래 -> 그렇 (ㅎ)      마셔 -> 마시   봐 -> 보   줘 -> 주   돼 -> 되
      갑니다 -> 가 (ㅂ니다)  만드세요 -> 만들 (ㄹ bi luoc)
    Tra ve danh sach theo thu tu kha nang, tu dien se quyet dinh cai nao dung.
    """
    if not prefix or decompose(prefix[-1]) is None:
        return []
    head = prefix[:-1]
    cho, jung, jong = decompose(prefix[-1])
    out = [prefix]

    if jong == _J_SS and jung in _PAST_VOWELS:   # thi qua khu: bo ㅆ roi thao tiep
        out += _stem_candidates(head + _syl(cho, jung))
    elif jong in (_J_N, _J_L, _J_B):         # 간다, 갈 거예요, 갑니다
        out.append(head + _syl(cho, jung))
    elif jong == 0:
        out.append(head + _syl(cho, jung, _J_L))      # ㄹ bi luoc: 사세요 -> 살

    if jong == 0:
        prev = decompose(head[-1]) if head else None
        if cho == _C_IEUNG and jung in (_V_A, _V_EO) and head:
            if prev and prev[2] == 0:
                # Goc tan cung nguyen am thi 아/어 da bi rut gon (가+아 = 가),
                # nen 나아 de lai nguyen 아 gan nhu chac la bat quy tac ㅅ: 낫다
                out.append(head[:-1] + _syl(prev[0], prev[1], _J_S))
            if prev and prev[2] == _J_SS and prev[1] in _PAST_VOWELS:   # 왔어 -> 오
                out += _stem_candidates(head[:-1] + _syl(prev[0], prev[1]))
            out.append(head)                           # 먹어 -> 먹
            if prev and prev[2] == _J_L:               # ㄷ: 들어 -> 듣
                out.append(head[:-1] + _syl(prev[0], prev[1], _J_D))
        if cho == _C_IEUNG and jung in (_V_WA, _V_WO) and prev and prev[2] == 0:
            out.append(head[:-1] + _syl(prev[0], prev[1], _J_B))   # 추워 -> 춥
        if jung in (_V_A, _V_EO):
            # 으 bi luoc theo hai hoa nguyen am: truoc ㅏ/ㅗ thanh 아 (바쁘 -> 바빠),
            # con lai thanh 어 (예쁘 -> 예뻐, 쓰 -> 써). Nen 싸 khong the la 쓰다.
            bright = prev is not None and prev[1] in (_V_A, _V_O)
            if (jung == _V_A) == bright:
                eu = head + _syl(cho, _V_EU)
                if jung == _V_EO:
                    out.insert(0, eu)                  # 써 -> 쓰다 truoc 써다 (hiem)
                else:
                    out.append(eu)
            if cho == _C_RIEUL and prev and prev[2] == _J_L:   # 르: 불러 -> 부르
                out.append(head[:-1] + _syl(prev[0], prev[1]) + "르")
        elif jung == _V_YEO:
            out.append(head + _syl(cho, _V_I))         # 마셔 -> 마시
        elif jung == _V_WA:
            out.append(head + _syl(cho, _V_O))         # 봐 -> 보
        elif jung == _V_WO:
            out.append(head + _syl(cho, _V_U))         # 줘 -> 주, 배워 -> 배우
        elif jung == _V_WAE:
            out.append(head + _syl(cho, _V_OE))        # 돼 -> 되
        elif jung == _V_AE:
            if cho == _C_HIEUH:
                out.append(head + _syl(cho, _V_A))     # 해 -> 하
            out.append(head + _syl(cho, _V_EO, _J_H))  # ㅎ: 그래 -> 그렇
            out.append(head + _syl(cho, _V_A, _J_H))   # ㅎ: 빨개 -> 빨갛

    seen, uniq = set(), []
    for s in out:
        if s and s not in seen:
            seen.add(s)
            uniq.append(s)
    return uniq


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

    def lookup_deep(self, word, trim=True):
        """trim=False: khong dung cach cuoi 'cat dan tu phai' (doan mo)."""
        key, hits = self._lookup_deep(word, trim)
        # Muc chi la loi chi dan ('봐' -> 'see 보다', '그래다' -> 'see 그렇다'):
        # hien thang tu goc cho nguoi hoc
        if hits and all(g.startswith("see ") for g, _h in hits):
            target = hits[0][0][4:].strip()
            if target != key and self.lookup(target):
                return target, self.lookup(target)
        return key, hits

    def _lookup_deep(self, word, trim=True):
        """Thu nguyen tu -> bo tro tu -> ve dang '~다' -> cat dan tu phai."""
        if self.lookup(word):
            return word, self.lookup(word)

        # '요' de cuoi cung: 타요 / 좋아요 la dong tu, khong phai danh tu + 요
        for p in sorted(PARTICLES, key=len, reverse=True):
            if p != "요" and word.endswith(p) and len(word) > len(p):
                stem = word[:-len(p)]
                if self.lookup(stem):
                    return stem, self.lookup(stem)

        # Am tiet bi rut gon / bat quy tac (갔습니다, 예뻐요, 추워요, 불렀어요).
        # Chay truoc bang ENDINGS: 나았어요 khop '았어요' -> 나다 la sai, phai la 낫다
        for k in range(len(word), 0, -1):
            if word[k:] not in _TAILS:
                continue
            for stem in _stem_candidates(word[:k]):
                cand = stem + "다"
                if self.lookup(cand):
                    return cand, self.lookup(cand)

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

        if word.endswith("요") and len(word) > 1 and self.lookup(word[:-1]):
            return word[:-1], self.lookup(word[:-1])         # 학교요

        if not trim:
            return word, []
        for end in range(len(word) - 1, 1, -1):
            cand = word[:end]
            if self.lookup(cand):
                return cand, self.lookup(cand)
        return word, []

    def _strong_hit(self, hangul):
        """Tra duoc ma KHONG phai nho cat bot duoi tu (cach cuoi cua lookup_deep)."""
        return bool(self.lookup_deep(hangul, trim=False)[1])

    def from_romaja(self, text):
        """'annyeonghaseyo' -> '안녕하세요', 'jeoneun haksaeng' -> '저는 학생'.

        Moi tu (cach nhau boi dau cach) thu cac cach doc tu chuan RR nhat
        tro di, lay cach dau tien tra ra tu that. '' neu khong tu nao ra."""
        out, found = [], False
        for token in text.split():
            pick = None
            for _cost, hangul in _romaja_parses(token):
                if self._strong_hit(hangul):
                    pick = hangul
                    break
            if pick:
                found = True
                out.append(pick)
        return " ".join(out) if found else ""

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
