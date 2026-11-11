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


def test_ai_uses_glossary_caches_and_falls_through_services(tmp_path, monkeypatch):
    import translate as t
    monkeypatch.setattr(t, "AI_PREFS", str(tmp_path / "ai.json"))
    monkeypatch.setattr(t, "_db", t.sqlite3.connect(":memory:", check_same_thread=False))
    assert t.translate_ai("hello", "en") == ("", "")       # chua co khoa -> giu ban dich may
    (tmp_path / "ai.json").write_text('{"key": "k", "model": "gemini-x-flash-lite"}')   # dang cu
    assert t.ai_ready("gemini") and not t.ai_ready("groq")
    calls = []

    def gemini(path, key, body=None, timeout=0):
        calls.append(body["contents"][0]["parts"][0]["text"])
        return {"candidates": [{"content": {"parts": [{"text": "chỗ bám của cơ"}]}}]}
    monkeypatch.setattr(t, "_gemini_call", gemini)
    out = t.translate_ai("muscle insertion", "en", "vi", [("muscle insertion", "chỗ bám của cơ")])
    assert out == ("chỗ bám của cơ", "Gemini") and "- muscle insertion = chỗ bám của cơ" in calls[0]
    assert t.translate_ai("muscle insertion", "en") == out and len(calls) == 1   # cache

    def boom(*a, **k):
        raise RuntimeError("Gemini 429: het luot")
    monkeypatch.setattr(t, "_gemini_call", boom)
    assert t.translate_ai("another text", "en") == ("", "")   # Gemini loi, khong con nguon nao
    t.ai_set("groq", key="g", model="llama-x")
    monkeypatch.setattr(t, "_openai_call", lambda name, path, key, body=None, timeout=0: {
        "choices": [{"message": {"content": "bản " + name}}]})
    assert t.translate_ai("another text", "en") == ("bản groq", "Groq")   # het Gemini -> Groq
    t.ai_set("gemini", key="")
    assert not t.ai_ready("gemini") and t.ai_ready("groq")


def test_openrouter_only_picks_free_models(monkeypatch):
    import translate as t
    ids = ["openai/gpt-9", "google/gemma-4-31b-it:free", "google/gemma-4-26b-a4b-it:free",
           "cohere/north-mini-code:free", "liquid/lfm-3-1.7b:free"]
    monkeypatch.setattr(t, "_openai_call", lambda name, path, key, body=None, timeout=0: {
        "data": [{"id": i} for i in ids]})
    assert t.openai_pick_model("openrouter", "k") == "google/gemma-4-31b-it:free"


def test_bing_first_then_google_when_bing_fails(tmp_path, monkeypatch):
    import translate as t
    monkeypatch.setattr(t, "CACHE_PATH", str(tmp_path / "cache.db"))
    monkeypatch.setattr(t, "_db", None)
    monkeypatch.setattr(t, "_offline_until", [0.0])
    assert t.PROVIDERS[0] is t._bing
    assert t._bing("x" * (t.BING_MAX + 1), "en") == ""        # qua dai: nhuong nguon sau

    def bing_down(text, src, target="vi"):
        raise RuntimeError("Bing doi trang")
    monkeypatch.setattr(t, "PROVIDERS", (bing_down, lambda text, src, target="vi": "ban Google"))
    assert t.translate_detail("hello there", "en") == ("ban Google", "online")


def test_gemini_prefers_fast_lite_model(monkeypatch):
    import translate as t
    names = ["gemini-3.8-flash", "gemini-3.5-flash-lite", "gemini-3.1-flash-lite",
             "gemini-3.8-flash-lite-tts", "gemini-omni-1.2-flash", "gemini-3.9-flash-lite-preview"]
    monkeypatch.setattr(t, "_gemini_call", lambda path, key, body=None, timeout=0: {"models": [
        {"name": "models/" + n, "supportedGenerationMethods": ["generateContent"]} for n in names]})
    assert t.gemini_pick_model("k") == "gemini-3.5-flash-lite"
