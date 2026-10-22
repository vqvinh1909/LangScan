# -*- coding: utf-8 -*-
"""Don chu truoc khi dich: noi dong OCR bi ngat, ha chu IN HOA."""
import pytest

import ocr


@pytest.mark.parametrize("raw, want", [
    ("THE\nENTERPRISE\nAI COMPASS:\nNAVIGATING\nTALENT,\nGOVERNANCE\nAND ETHICS",
     "THE ENTERPRISE AI COMPASS: NAVIGATING TALENT, GOVERNANCE AND ETHICS"),
    ("Thứ tự nên làm tiếp\n1. Đóng gói.\n2. Sổ từ.",            # danh so: giu xuong dong
     "Thứ tự nên làm tiếp\n1. Đóng gói.\n2. Sổ từ."),
    ("Câu một kết thúc.\nCâu hai", "Câu một kết thúc.\nCâu hai"),
    ("我在银行\n工作。", "我在银行工作。"),                       # chu Han noi lien
    ("- mục một\n- mục hai", "- mục một\n- mục hai"),
])
def test_tidy_lines(raw, want):
    assert ocr.tidy_lines(raw) == want


@pytest.mark.parametrize("raw, want", [
    ("THE ENTERPRISE AI COMPASS: NAVIGATING TALENT, GOVERNANCE AND ETHICS",
     "The enterprise AI compass: navigating talent, governance and ethics"),
    ("NASA LAUNCHES NEW ROCKET. IT IS BIG.", "NASA launches new rocket. It is big."),
    ("CÔNG TY TNHH ABC THÔNG BÁO TUYỂN DỤNG", "Công ty TNHH ABC thông báo tuyển dụng"),
    ("ĐÃ SỬA: ỨNG DỤNG AI MỚI", "Đã sửa: ứng dụng AI mới"),
    ("Normal Sentence With Some Caps", "Normal Sentence With Some Caps"),   # khong in hoa: giu
    ("我在银行工作", "我在银行工作"),
])
def test_calm_caps(analyzer, raw, want):
    assert analyzer.calm_caps(raw) == want


@pytest.mark.parametrize("raw, want", [
    ("Machine trans-\nlation works best when the\ninput text is clean.",
     "Machine translation works best when the input text is clean."),
    ("Self-\nService portal", "Self-Service portal"),
    ("a test ,with bad spacing .And glued.Next one", "a test, with bad spacing. And glued. Next one"),
    ("Use e.g. the file run_hidden.bat or v1.0.0 , ok?", "Use e.g. the file run_hidden.bat or v1.0.0, ok?"),
    ("我在银行\n工作，也学习汉语。", "我在银行工作，也学习汉语。"),
])
def test_prepare_for_mt(analyzer, raw, want):
    assert analyzer.prepare_for_mt(raw, "en" if "我" not in raw else "zh") == want


def test_enforce_terms_fixes_wrong_term(analyzer):
    src = "The database is offline."
    calls = []

    def fake(text):                      # gia lap dich may: giu ma giu cho ZQ0
        calls.append(text)
        return "Cơ sở dữ liệu đang ZQ0."
    out = analyzer.enforce_terms(src, "en", "Cơ sở dữ liệu đang ngoại tuyến.", "vi", fake)
    assert out == "Cơ sở dữ liệu đang không kết nối mạng."
    assert calls == ["The database is ZQ0."]


def test_enforce_terms_keeps_good_translation(analyzer):
    out = analyzer.enforce_terms("The firewall blocks traffic.", "en",
                                 "Tường lửa chặn lưu lượng.", "vi",
                                 lambda t: pytest.fail("khong duoc dich lai"))
    assert out == "Tường lửa chặn lưu lượng."


def test_enforce_terms_lost_placeholder_keeps_original(analyzer):
    out = analyzer.enforce_terms("The database is offline.", "en", "ngoại tuyến", "vi",
                                 lambda t: "mất mã giữ chỗ")
    assert out == "ngoại tuyến"


def test_split_long():
    import translate
    para = "The server is running. " * 100
    parts = translate._split_long(para.strip())
    assert len(parts) > 1 and all(len(p) <= translate.CHUNK for p in parts)
    assert " ".join(parts) == para.strip()


@pytest.mark.parametrize("src, mt", [
    ("Hanoi is the capital of Vietnam.", "Hà Nội là thủ đô của Việt Nam."),
    ("There is mold on the bread.", "Có nấm mốc trên bánh mì."),
    ("The shop is out of stock.", "Cửa hàng đã hết hàng."),
])
def test_enforce_terms_needs_domain_context(analyzer, src, mt):
    # tu don nhieu nghia, cau khong co thuat ngu nganh nao khac: khong ep
    assert analyzer.enforce_terms(src, "en", mt, "vi",
                                  lambda t: pytest.fail("khong duoc dich lai")) == mt


def test_enforce_terms_drops_extra_la(analyzer):
    out = analyzer.enforce_terms("The server is offline.", "en", "Máy chủ đang ngoại tuyến.",
                                 "vi", lambda t: "Máy chủ là ZQ0.")
    assert out == "Máy chủ không kết nối mạng."


def test_enforce_terms_close_translation_is_kept(analyzer):
    # Google dich 'circadian rhythm' -> 'nhip sinh hoc' (3/5 chu nghia chuan): dat,
    # chi ep 'suprachiasmatic nucleus' bi dich sai thanh 'Nhan sieu am'
    seen = []

    def fake(text):
        seen.append(text)
        return "ZQ0 kiểm soát nhịp sinh học và giải phóng melatonin."
    out = analyzer.enforce_terms(
        "The suprachiasmatic nucleus controls the circadian rhythm and melatonin release.",
        "en", "Nhân siêu âm kiểm soát nhịp sinh học và giải phóng melatonin.", "vi", fake)
    assert out == "Nhân trên giao thoa thị giác kiểm soát nhịp sinh học và giải phóng melatonin."
    assert "circadian rhythm" in seen[0]                  # khong bi thay bang ma giu cho
