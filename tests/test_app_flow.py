# -*- coding: utf-8 -*-
"""Luong chinh cua app, khong can giao dien: lay chu boi den, phim tat, chon chu de dich."""
import os
import queue
import sys
import types

import pytest

import langs
import langscan


# ---- chon chu de dich
def route(analyzer, text, force=None, src="auto"):
    return langscan.route_text(analyzer, text, force, src)


def test_phrase_keeps_digits_and_punctuation(analyzer):
    raw = "我有3个苹果，你有5个。"
    _lang, _cards, _err, text, phrase, _vi, _plain = route(analyzer, raw)
    assert "3" not in text                     # tra tu dien: van loc
    assert phrase == raw                       # dem dich: giu nguyen


def test_phrase_not_truncated(analyzer):
    raw = "The quick brown fox jumps over the lazy dog. " * 20
    assert route(analyzer, raw)[4] == raw.strip()
    han = "我在银行工作。" * 50
    assert route(analyzer, han)[4] == han


def test_phrase_from_typed_romaji(analyzer):
    assert route(analyzer, "tabemashita", force=langs.JA)[4] == "たべました"


def test_romanize_accepts_raw_sentence(analyzer):
    out = analyzer.romanize_sentence("我有3个苹果，你呢？", langs.ZH)
    assert "3" in out and "wǒ" in out


def test_vietnamese_routes_to_phrase(analyzer):
    r = route(analyzer, "tôi đi học")
    assert r[0] is None and r[5] is True and r[4] == "tôi đi học"


@pytest.mark.parametrize("text,want", [("CIRCADIAN", False), ("wo shi", True), ("我是", False)])
def test_wants_phonetic(analyzer, text, want):
    lang, cards = route(analyzer, text)[:2]
    assert langscan.wants_phonetic(text, False, "auto", lang, cards)[0] is want


def test_long_latin_forced_korean_does_not_crash(analyzer):
    analyzer.analyze("a" * 5000, force_lang=langs.KO)


# ---- lay chu boi den
@pytest.fixture
def fake_clip(monkeypatch):
    log = {"seq": [5], "restored": None, "text": "chu moi"}
    monkeypatch.setitem(sys.modules, "keyboard", types.SimpleNamespace(
        release=lambda k: None, send=lambda k: log["on_send"]()))
    monkeypatch.setitem(sys.modules, "pyperclip", types.SimpleNamespace(
        paste=lambda: log["text"]))
    monkeypatch.setattr(langscan, "_clip_seq", lambda: log["seq"][0])
    monkeypatch.setattr(langscan, "_clip_save", lambda: [(8, b"anh")])
    monkeypatch.setattr(langscan, "_clip_restore", lambda s: log.update(restored=s))
    monkeypatch.setattr(langscan.time, "sleep", lambda s: None)
    return log


def test_grab_returns_text_and_restores_everything(fake_clip):
    fake_clip["on_send"] = lambda: fake_clip["seq"].__setitem__(0, 6)
    assert langscan.grab_selection() == "chu moi"
    assert fake_clip["restored"] == [(8, b"anh")]


def test_grab_nothing_selected_leaves_clipboard_alone(fake_clip):
    fake_clip["on_send"] = lambda: None
    assert langscan.grab_selection() == ""
    assert fake_clip["restored"] is None


# ---- phim tat
def test_ghost_hotkey_ignored_and_stale_state_cleared(monkeypatch):
    import threading
    pressed = {1: "ctrl", 2: "d"}
    monkeypatch.setitem(sys.modules, "keyboard", types.SimpleNamespace(
        _pressed_events=pressed, _pressed_events_lock=threading.Lock()))
    monkeypatch.setattr(langscan, "_key_pressed", lambda k: k == "alt")
    called = []
    langscan._run_if_held("ctrl+alt+d", lambda: called.append(1))
    assert not called and not pressed


def test_real_hotkey_runs(monkeypatch):
    monkeypatch.setattr(langscan, "_key_pressed", lambda k: True)
    called = []
    langscan._run_if_held("ctrl+alt+d", lambda: called.append(1))
    assert called == [1]


@pytest.mark.parametrize("hotkey", ["ctrl+alt+d", "ctrl+alt+x", "ctrl+alt+q"])
def test_key_pressed_accepts_every_part_of_a_hotkey(hotkey):
    for key in hotkey.split("+"):                # goi Windows that, khong gia lap
        assert langscan._key_pressed(key) in (True, False)


def test_double_ctrl():
    tap = langscan.DoubleTap(None, gap=0.4)
    assert not tap.feed("ctrl", False, 1.0)
    assert tap.feed("left ctrl", False, 1.2)
    assert not tap.feed("ctrl", False, 1.3)      # lan bam da dung het


def test_double_ctrl_too_slow_or_with_other_key():
    tap = langscan.DoubleTap(None, gap=0.4)
    tap.feed("ctrl", False, 1.0)
    assert not tap.feed("ctrl", False, 2.0)      # cach qua xa
    tap.feed("c", True, 2.1)                     # Ctrl+C
    assert not tap.feed("ctrl", False, 2.2)
    assert not tap.feed("ctrl", False, 2.3)      # lan truoc khong tinh


# ---- vong lap xu ly yeu cau
def test_pump_survives_error_and_handles_next():
    shown = []

    def show(text, force):
        if text == "hong":
            raise RecursionError("x")
        shown.append(text)
    after = []
    app = types.SimpleNamespace(
        q=queue.Queue(), popup=types.SimpleNamespace(show=show),
        root=types.SimpleNamespace(after=lambda ms, fn: after.append(fn)), pump=None)
    app.q.put(("hong", None))
    app.q.put(("tot", None))
    langscan.App.pump(app)
    assert shown == ["tot"] and len(after) == 1


# ---- am thanh
def fake_gtts(monkeypatch, fail):
    class GTTS(object):
        def __init__(self, text, lang):
            pass

        def save(self, path):
            with open(path, "wb") as f:           # nhu gTTS that: tao file truoc
                if fail:
                    raise OSError("mat mang")
                f.write(b"mp3")
    monkeypatch.setitem(sys.modules, "gtts", types.SimpleNamespace(gTTS=GTTS))


def test_failed_tts_leaves_nothing_then_works(tmp_path, monkeypatch):
    path = str(tmp_path / "a.mp3")
    fake_gtts(monkeypatch, fail=True)
    with pytest.raises(OSError):
        langscan._save_tts("x", "vi", path)
    assert os.listdir(str(tmp_path)) == []
    fake_gtts(monkeypatch, fail=False)
    langscan._save_tts("x", "vi", path)
    assert open(path, "rb").read() == b"mp3"


def test_empty_mp3_from_old_version_is_refetched(tmp_path, monkeypatch):
    path = tmp_path / "a.mp3"
    path.write_bytes(b"")
    fake_gtts(monkeypatch, fail=False)
    langscan._save_tts("x", "vi", str(path))
    assert path.read_bytes() == b"mp3"


# ---- vi tri popup
def test_popup_stays_on_second_monitor():
    right = (1920, 0, 3840, 1040)
    assert langscan._fit_popup(3000, 100, 500, 300, right) == (3012, 116)
    assert langscan._fit_popup(3800, 100, 500, 300, right)[0] == 3330
    left = (-1920, 0, 0, 1040)
    assert langscan._fit_popup(-1000, 100, 500, 300, left)[0] == -988


def test_box_maps_per_monitor_scale():
    # Man chinh 125% (1536 -> 1920), man trai 100%
    logical = [(0, 0, 1536, 864), (-1920, -124, 0, 956)]
    physical = [(0, 0, 1920, 1080), (-1920, -155, 0, 925)]
    assert langscan._map_box((100, 100, 200, 200), logical, physical, 1.25) == (125, 125, 250, 250)
    assert langscan._map_box((-1000, 100, -900, 200), logical, physical, 1.25) == (-1000, 69, -900, 169)


def test_snip_covers_only_monitor_under_cursor():
    rects = [(0, 0, 1536, 864), (-1920, -124, 0, 956)]
    assert langscan._snip_geometry(100, 100, rects, "x") == "1536x864+0+0"
    assert langscan._snip_geometry(-5, 0, rects, "x") == "1920x1080+-1920+-124"
    assert langscan._snip_geometry(9999, 0, rects, "x") == "x"


def test_box_outside_monitors_falls_back_to_scale():
    assert langscan._map_box((10, 10, 20, 20), [], [], 2.0) == (20, 20, 40, 40)


def test_popup_flips_above_cursor_near_bottom():
    assert langscan._fit_popup(100, 1000, 500, 300, (0, 0, 1920, 1040))[1] == 684
