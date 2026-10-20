# -*- coding: utf-8 -*-
"""Phien am ca cau (dong Latin duoi ban dich sang Trung / Nhat / Han)."""
import pytest

import langs


@pytest.mark.parametrize("text, want", [
    ("我去上学。", "wǒ qù shàngxué."),
    ("我在银行工作，也学习汉语。", "wǒ zài yínháng gōngzuò, yě xuéxí Hànyǔ."),
    ("你好吗？", "nǐhǎo ma?"),                 # 吗 thanh nhe, khong phai ma2
    ("我爱你", "wǒ ài nǐ"),                   # tach cum jieba thanh tu HSK
    ("今天天气很好", "jīntiān tiānqì hěn hǎo"),
    ("这是我的书", "zhè shì wǒ de shū"),
])
def test_pinyin(analyzer, text, want):
    assert analyzer.romanize_sentence(text, langs.ZH) == want


@pytest.mark.parametrize("text, want", [
    ("学校に行きます。", "gakkou ni ikimasu."),
    ("私は学生です。", "watashi wa gakusei desu."),
    ("日本語を勉強しています", "nihongo o benkyou shite imasu"),
    ("美味しいです", "oishii desu"),
    ("読んでいます", "yonde imasu"),
    ("ありがとうございます", "arigatou gozaimasu"),
])
def test_romaji(analyzer, text, want):
    try:
        analyzer.ja()
    except ImportError:
        pytest.skip("chua cai tu dien tieng Nhat")
    assert analyzer.romanize_sentence(text, langs.JA) == want


@pytest.mark.parametrize("text, want", [
    ("학교에 갑니다.", "hakgyoe gamnida."),   # dong hoa am mui: ㅂ+ㄴ -> m
    ("감사합니다!", "gamsahamnida!"),
    ("한국말", "hangungmal"), ("있는", "inneun"),
    ("한국어", "hangugeo"), ("은행", "eunhaeng"),
])
def test_korean(analyzer, text, want):
    assert analyzer.romanize_sentence(text, langs.KO) == want
