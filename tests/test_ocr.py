# -*- coding: utf-8 -*-
"""OCR: chu Viet doc bang Tesseract, chu Anh / Trung khong bi anh huong."""
import pytest

import ocr

pytestmark = pytest.mark.skipif(not ocr.available(), reason="may chua co bo OCR nao")


def render(text, font, size=40):
    from PIL import Image, ImageDraw, ImageFont
    img = Image.new("RGB", (900, 80), "white")
    ImageDraw.Draw(img).text((10, 12), text, fill="black",
                             font=ImageFont.truetype("C:/Windows/Fonts/" + font, size))
    return img


@pytest.mark.skipif(not ocr.vietnamese_ready(), reason="chua co Tesseract + vie")
@pytest.mark.parametrize("text", ["Đã sửa:", "Cài xong thì thoát và mở lại"])
def test_vietnamese(text):
    got, lang = ocr.read_auto(render(text, "segoeui.ttf"))
    assert lang == ocr.VI
    assert got.strip() == text


def test_english_stays_english():
    got, lang = ocr.read_auto(render("Jeff currently lives in Canada", "segoeui.ttf"))
    assert lang == "en" and "currently" in got
