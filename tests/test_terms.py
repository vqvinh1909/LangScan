# -*- coding: utf-8 -*-
"""Bo thuat ngu chuyen nganh (data/terms/*.tsv)."""
import pytest

import langs


@pytest.mark.parametrize("text, lang, word, badge", [
    ("The balance sheet shows accounts receivable", langs.EN, "balance sheet", "Kinh tế"),
    ("患者因心肌梗死住院", langs.ZH, "心肌梗死", "Y khoa"),
    ("品質管理と予防保全", langs.JA, "品質管理", "Kỹ thuật"),
    ("생산 라인의 불량률", langs.KO, "생산 라인", "Kỹ thuật"),   # giu dau cach
])
def test_multiword_term_card(analyzer, text, lang, word, badge):
    if lang == langs.JA:
        try:
            analyzer.ja()
        except ImportError:
            pytest.skip("chua cai tu dien tieng Nhat")
    cards = analyzer.analyze(text, force_lang=lang)[1]
    card = next(c for c in cards if c.word == word)
    assert card.badge == badge


def test_term_card_has_equivalents(analyzer):
    cards = analyzer.analyze("balance sheet", force_lang=langs.EN)[1]
    assert "资产负债表" in cards[0].note and "貸借対照表" in cards[0].note


def test_single_word_term_keeps_normal_meaning(analyzer):
    # 服务器 trung voi the tu thuong: nghia chuyen nganh len dau, khong mat nghia khac
    card = analyzer.analyze("服务器", force_lang=langs.ZH)[1][0]
    assert card.vi[0].startswith("[IT] máy chủ")
    assert card.badge.startswith("HSK") or card.badge == "IT"   # co cap do thi giu cap do


def test_pieces_replaced_by_term(analyzer):
    words = [c.word for c in analyzer.analyze("资产负债表", force_lang=langs.ZH)[1]]
    assert words == ["资产负债表"]


@pytest.mark.parametrize("query, target, word", [
    ("nhồi máu cơ tim", langs.ZH, "心肌梗死"),
    ("nhoi mau co tim", langs.KO, "심근경색"),          # go khong dau
    ("bảng cân đối kế toán", langs.EN, "balance sheet"),
    ("dây chuyền sản xuất", langs.JA, "生産ライン"),
])
def test_terms_from_vietnamese(analyzer, query, target, word):
    assert analyzer.terms_from_vi(query, target)[0].word == word
