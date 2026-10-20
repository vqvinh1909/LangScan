# -*- coding: utf-8 -*-
"""Chup lai vung cu: nho vung khoanh qua cac lan mo app."""
import langscan


def test_snip_box_remembered(tmp_path, monkeypatch):
    monkeypatch.setattr(langscan, "SNIP_PREFS", str(tmp_path / "snip.json"))
    sn = langscan.Snipper(None, lambda t, e: None)
    assert sn.last_box is None                 # chua khoanh lan nao
    sn._save_box((10, 20, 300, 80))
    again = langscan.Snipper(None, lambda t, e: None)   # nhu mo lai app
    assert again.last_box == (10, 20, 300, 80)


def test_snip_box_bad_file(tmp_path, monkeypatch):
    p = tmp_path / "snip.json"
    p.write_text("hong", encoding="utf-8")
    monkeypatch.setattr(langscan, "SNIP_PREFS", str(p))
    assert langscan.Snipper(None, lambda t, e: None).last_box is None
