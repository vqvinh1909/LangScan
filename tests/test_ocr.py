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


def test_clean_tsv_drops_garbage_line():
    head = "level\tpage_num\tblock_num\tpar_num\tline_num\tword_num\tleft\ttop\twidth\theight\tconf\ttext"
    rows = [(1, 96.9, "Việc"), (1, 96.5, "còn"), (1, 96.4, "lại."), (1, 72.4, "|"), (1, 76.5, "À"),
            (2, 27.9, "i"), (2, 23.8, "^¬~“,"), (2, 92.0, "H"), (2, 16.1, "“x"), (2, 34.5, "vy")]
    tsv = "\n".join([head] + ["5\t1\t1\t1\t{}\t{}\t0\t0\t9\t9\t{}\t{}".format(ln, i, c, w)
                              for i, (ln, c, w) in enumerate(rows)])
    assert ocr._clean_tsv(tsv) == "Việc còn lại."


@pytest.mark.parametrize("word, want", [
    ("từcó", "từ có"), ("gốithành", "gối thành"), ("lạiGõ", "lại Gõ"),
    ("thuậtngữ", "thuật ngữ"), ("từcó,", "từ có,"),
    ("người", "người"), ("tiếng", "tiếng"),            # chu dung thi giu nguyen
    ("Windows", "Windows"), ("LangScan", "LangScan"),  # khong dung vao chu Anh
])
def test_split_glued_vietnamese(word, want):
    assert ocr._split_glued_vi(word) == want


@pytest.mark.parametrize("tess, rapid, want", [
    # Tesseract doc nham l->1 trong chu kieu code: lay ban RapidOCR
    ("Khởi động lại app Ctr1+A1t+Q rồi", "Khoi dong lai app ( Ctrl+Alt+Q roi",
     "Khởi động lại app Ctrl+Alt+Q rồi"),
    ("bấm C0py và F5", "bam Copy va F5", "bấm Copy và F5"),
    # khong co dau hieu doc nham: giu Tesseract (RapidOCR lam mat dau cham)
    ("cài qua TiWorker.exe và", "cai qua TiWorkerexe va", "cài qua TiWorker.exe và"),
    ("rồi run_hidden.", "roi run hidden.ba", "rồi run_hidden."),
    # chu so that (Windows 11) giu nguyen; xuong dong giu nguyen
    ("mở Windows 11\ncũng đã xong", "mo Windows 11\ncung da xong", "mở Windows 11\ncũng đã xong"),
])
def test_merge_latin(tess, rapid, want):
    assert ocr._merge_latin(tess, rapid) == want
