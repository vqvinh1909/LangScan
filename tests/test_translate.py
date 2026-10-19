# -*- coding: utf-8 -*-
"""Chi kiem tra phan cache - khong goi mang."""
import pytest

import translate


@pytest.fixture
def tmp_cache(tmp_path, monkeypatch):
    monkeypatch.setattr(translate, "CACHE_PATH", str(tmp_path / "vi_cache.db"))
    monkeypatch.setattr(translate, "_db", None)
    yield
    if translate._db is not None:
        translate._db.close()


def test_cache_roundtrip(tmp_cache):
    assert translate.cached("食べる", "ja") is None
    translate.remember("食べる", "ja", "ăn")
    assert translate.cached("食べる", "ja") == "ăn"
    assert translate.translate("食べる", "ja", use_network=False) == "ăn"


def test_cache_is_per_target_language(tmp_cache):
    translate.remember("bank", "en", "ngân hàng", target="vi")
    assert translate.cached("bank", "en", target="zh") is None


def test_offline_miss_returns_empty(tmp_cache):
    assert translate.translate("chưa có", "vi", use_network=False, target="en") == ""


def test_same_language_is_noop(tmp_cache):
    assert translate.translate("hello", "en", target="en") == ""
