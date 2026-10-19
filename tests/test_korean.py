# -*- coding: utf-8 -*-
import pytest

import korean


@pytest.mark.parametrize("word, base", [
    # quy tac, khong rut gon
    ("먹었어요", "먹다"), ("먹고", "먹다"), ("먹지만", "먹다"), ("알아요", "알다"),
    ("좋아요", "좋다"), ("있어요", "있다"), ("있습니다", "있다"), ("없어요", "없다"),
    ("재미있어요", "재미있다"),
    # 하다
    ("일해요", "일하다"), ("공부합니다", "공부하다"), ("공부했어요", "공부하다"),
    # nguyen am bi rut gon
    ("갔습니다", "가다"), ("갑니다", "가다"), ("마셨어요", "마시다"), ("봤어요", "보다"),
    ("왔어요", "오다"), ("줘요", "주다"), ("배웠어요", "배우다"), ("돼요", "되다"),
    ("되어요", "되다"), ("타요", "타다"), ("싸요", "싸다"), ("서요", "서다"),
    ("만나요", "만나다"), ("비싸요", "비싸다"),
    # 으 bi luoc (theo hai hoa nguyen am)
    ("예뻐요", "예쁘다"), ("예뻤어요", "예쁘다"), ("바빠요", "바쁘다"), ("나빠요", "나쁘다"),
    ("아파요", "아프다"), ("기뻐요", "기쁘다"), ("써요", "쓰다"), ("썼어요", "쓰다"),
    ("커요", "크다"),
    # bat quy tac ㅂ / ㅅ / 르 / ㅎ / ㄹ
    ("추워요", "춥다"), ("어려워요", "어렵다"), ("도와요", "돕다"), ("나았어요", "낫다"),
    ("불렀어요", "부르다"), ("몰라요", "모르다"), ("그래요", "그렇다"), ("봐요", "보다"), ("보내요", "보내다"), ("빨개요", "빨갛다"),
    ("만드세요", "만들다"),
    # danh tu + tro tu
    ("은행에서", "은행"), ("저는", "저"), ("한국어를", "한국어"), ("친구와", "친구"),
    ("학교요", "학교"), ("학교", "학교"),
])
def test_lookup_deep(ko, word, base):
    assert ko.lookup_deep(word)[0] == base


def test_stem_candidates_non_hangul():
    assert korean._stem_candidates("") == []
    assert korean._stem_candidates("abc") == []


def test_romanize():
    assert korean.romanize("한국어") == "hangugeo"
    assert korean.romanize("은행") == "eunhaeng"


def test_hanja_meaning(ko):
    card = ko.card("은행")
    assert "銀行" in card.note
    assert "ngân hàng" in card.note


@pytest.mark.parametrize("romaja, hangul", [
    ("eunhaeng", "은행"), ("annyeonghaseyo", "안녕하세요"), ("hangugeo", "한국어"),
    ("meogeosseoyo", "먹었어요"), ("saranghae", "사랑해"),
    ("gamsahamnida", "감사합니다"),          # 합니다 doc thanh hamnida
    ("kamsahamnida", "감사합니다"),          # kieu cu: k thay vi g
    ("hangungmal", "한국말"),
    ("mannaseo bangapseumnida", "만나서 반갑습니다"),
    ("test", ""),
])
def test_from_romaja(ko, romaja, hangul):
    assert ko.from_romaja(romaja) == hangul


def test_romanized_analyze(analyzer):
    import langs
    _lang, cards, _err = analyzer.analyze("eunhaeng", force_lang=langs.KO)
    assert [c.word for c in cards] == ["은행"]
