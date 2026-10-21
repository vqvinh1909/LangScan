# -*- coding: utf-8 -*-
"""Mat mang thi dich ca cau bang bo dich offline (offline_mt.py)."""
import urllib.error

import pytest

import offline_mt
import translate

ready = offline_mt.runtime_ready() and offline_mt.has_pair("en", "vi")
need_models = pytest.mark.skipif(not ready, reason="chua tai mo hinh offline")


@need_models
def test_offline_en_vi():
    out = offline_mt.translate("I work at a bank.", "en", "vi")
    assert "ngân hàng" in out and "▁" not in out


@need_models
@pytest.mark.skipif(not offline_mt.has_pair("zh", "en"), reason="chua co zh->en")
def test_offline_pivot_zh_vi():
    assert "ngân hàng" in offline_mt.translate("我在银行工作。", "zh", "vi")


@pytest.fixture
def no_network(monkeypatch, tmp_path):
    def down(text, src, target="vi"):
        raise urllib.error.URLError("no network")
    monkeypatch.setattr(translate, "PROVIDERS", (down, down, down, down))
    monkeypatch.setattr(translate, "_google", down)
    monkeypatch.setattr(translate, "_offline_until", [0.0])
    monkeypatch.setattr(translate, "CACHE_PATH", str(tmp_path / "cache.db"))
    monkeypatch.setattr(translate, "_db", None)


@need_models
def test_fallback_when_offline_and_not_cached(no_network):
    out, engine = translate.translate_detail("The warehouse is full.", "en", target="vi")
    assert engine == "offline" and out
    assert translate.cached("The warehouse is full.", "en", "vi") is None   # khong luu cache


def test_cache_still_wins_offline(no_network):
    translate.remember("hello world", "en", "xin chào thế giới", "vi")
    assert translate.translate_detail("hello world", "en", target="vi") == (
        "xin chào thế giới", "cache")


def test_can_translate_needs_pivot_models(monkeypatch):
    monkeypatch.setattr(offline_mt, "runtime_ready", lambda: True)
    have = {("en", "vi"), ("zh", "en")}
    monkeypatch.setattr(offline_mt, "has_pair", lambda s, t: (s, t) in have)
    assert offline_mt.can_translate("zh", "vi")          # zh -> en -> vi
    assert not offline_mt.can_translate("ja", "vi")      # thieu ja -> en
