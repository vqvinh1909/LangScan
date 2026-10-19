# -*- coding: utf-8 -*-
import threading

import pytest

import japanese


@pytest.mark.parametrize("romaji, kana", [
    ("tabemashita", "たべました"), ("konnichiwa", "こんにちわ"), ("onna", "おんな"),
    ("kitte", "きって"), ("matcha", "まっちゃ"), ("shimbun", "しんぶん"),
    ("shinbun", "しんぶん"), ("kon'ya", "こんや"), ("tōkyō", "とうきょう"),
    ("si", "し"), ("tu", "つ"), ("sya", "しゃ"),
    ("watashi wa gakusei desu", "わたし は がくせい です"),   # tro tu wa -> は
    ("hon o yomu", "ほん を よむ"),
    ("hello", ""),                       # khong phai romaji -> khong doan bua
])
def test_from_romaji(romaji, kana):
    assert japanese.from_romaji(romaji) == kana


@pytest.fixture(scope="module")
def ja(analyzer):
    try:
        return analyzer.ja()
    except ImportError:
        pytest.skip("chua cai tu dien tieng Nhat (caidat_tiengnhat.bat)")


@pytest.mark.parametrize("romaji, word", [
    ("gakkou", "学校"), ("gakko", "学校"),          # bo truong am van ra
    ("tokyo", "東京"), ("osaka", "大阪"),
    ("dozo", "どうぞ"),                            # khong phai 銅像 (どうぞう)
    ("ryoko", "旅行"),                             # khong phai 良好 (りょうこう)
    ("kyo", "今日"),
    ("tabemashita", "食べる"), ("ikimasu", "行く"),   # dong tu chia duoi
    ("kami", "紙"),                                # dong am: lay tu co JLPT
    ("kore", "これ"),                              # tu thuong viet kana giu kana
    ("arigatou", "ありがとう"),
])
def test_romaji_cards(ja, romaji, word):
    assert ja.romaji_cards(romaji)[0].word == word


def test_romaji_sentence(ja):
    words = [c.word for c in ja.romaji_cards("watashi wa gakusei desu")]
    assert words[:2] == ["私", "学生"]


def test_lookup_from_worker_thread(ja):
    # SQLite khong dung chung ket noi giua cac luong; popup tra o luong nen
    out = []
    t = threading.Thread(target=lambda: out.extend(ja.romaji_cards("gakkou")))
    t.start()
    t.join()
    assert out and out[0].word == "学校"
