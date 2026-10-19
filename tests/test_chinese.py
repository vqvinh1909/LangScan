# -*- coding: utf-8 -*-
import pytest

import dictionary
import langs


@pytest.mark.parametrize("numbered, pretty", [
    ("xue2 xi2", "xué xí"), ("nu:3", "nǚ"), ("de5", "de"),
    ("liu2", "liú"), ("gui4", "guì"), ("yin2 hang2", "yín háng"),
])
def test_pinyin_pretty(numbered, pretty):
    assert dictionary.pinyin_pretty(numbered) == pretty


def test_segment(zh):
    assert dictionary.segment("我在银行工作", zh) == ["我", "在", "银行", "工作"]


def test_lookup_vi_and_hsk(zh):
    entries = zh.lookup("银行", "vi")
    assert entries and "ngân hàng" in entries[0].senses[0]
    assert zh.hsk_level("银行") == 3


def test_reverse_vi_to_zh(analyzer):
    import reverse
    cards = reverse.Reverse(analyzer).search("ngân hàng")
    assert cards[0].word == "银行"


@pytest.mark.parametrize("text, lang", [
    ("你好吗", langs.ZH), ("日本語", langs.ZH),       # toan Kanji -> mac dinh Trung
    ("こんにちは", langs.JA), ("東京に行きます", langs.JA),
    ("안녕하세요", langs.KO), ("hello", langs.EN), ("", None),
])
def test_detect(text, lang):
    assert langs.detect(text) == lang


@pytest.mark.parametrize("text, words", [
    ("臺灣", ["臺灣"]),                      # jieba cat vun chu phon the
    ("你為什麼不來", ["你", "為什麼", "不來"]),
    ("我們學習漢語很有意思", ["我們", "學習", "漢語", "很", "有意思"]),
    ("我在银行工作", ["我", "在", "银行", "工作"]),   # gian the giu nguyen
])
def test_segment_traditional(zh, text, words):
    assert dictionary.segment(text, zh) == words


def test_lookup_traditional(analyzer):
    _lang, cards, _err = analyzer.analyze("我在銀行工作", force_lang=langs.ZH)
    assert "ngân hàng" in [c for c in cards if c.word == "銀行"][0].vi[0]


@pytest.fixture(scope="module")
def rev(analyzer):
    import reverse
    return reverse.Reverse(analyzer)


@pytest.mark.parametrize("query, words", [
    ("wo shi", ["我", "是"]),                # khong phai 卧室 (phong ngu)
    ("woshi", ["我", "是"]),
    ("wǒ shì", ["我", "是"]),
    ("wo3 shi4", ["我", "是"]),
    ("wo shi xuesheng", ["我", "是", "学生"]),
    ("wo zai yinhang gongzuo", ["我", "在", "银行", "工作"]),
    ("jintian tianqi hen hao", ["今天", "天气", "很", "好"]),
])
def test_pinyin_phrase(rev, query, words):
    assert [c.word for c in rev.pinyin_phrase(query)] == words


@pytest.mark.parametrize("query", ["ni hao", "yinhang", "zhongguo"])
def test_pinyin_single_word_is_not_a_phrase(rev, query):
    # Mot tu thi de search_pinyin lo, khong hien them dong "Cau pinyin"
    assert rev.pinyin_phrase(query) == []
