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
