# -*- coding: utf-8 -*-
"""Nhan dien tieng Viet go khong dau / chu OCR mat dau."""
import pytest


@pytest.mark.parametrize("text, want", [
    # chac la tieng Viet
    ("toi di hoc", "vi"), ("ngan hang", "vi"), ("may chu", "vi"), ("cam on", "vi"),
    ("tuong lua", "vi"), ("nguoi", "vi"), ("khong", "vi"), ("an com chua", "vi"),
    ("thu tu nen lam tiep", "vi"),
    # chu OCR mat dau, lan tu dinh lien / tu Anh
    ("Dong goithanh file exe cai dat Buoc nay quyet dinh nguoi khac co dung duoc", "vi"),
    # doc duoc ca kieu Viet lan pinyin -> hien ca hai
    ("xin chao", "maybe"), ("ni hao", "maybe"), ("chao ban", "maybe"),
    # khong phai tieng Viet
    ("wo shi", None), ("wo ai ni", None),                      # pinyin (w khong co trong tieng Viet)
    ("the man can do it", None), ("hang on", None), ("can do", None),   # tieng Anh
    ("bank", None), ("ban", None), ("deploy", None), ("hello world", None),
    ("tabemashita", None), ("annyeonghaseyo", None),           # romaji / phien am Han
    ("ngân hàng", None),                                       # co dau: nhan o cho khac
    ("Jeff currently lives in Kelowna Canada where he is producing videos", None),
])
def test_vietnamese_plain(analyzer, text, want):
    assert analyzer.vietnamese_plain(text) == want
