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
