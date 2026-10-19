# -*- coding: utf-8 -*-
"""
chandoan.py - Kiem tra xem cai gi thieu, cai gi hong.

Chay:  python chandoan.py     (hoac nhay dup chandoan.bat)
Roi gui ket qua cho Claude neu can giup.
"""

import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "data")


def line(title):
    print("\n" + "=" * 58)
    print("  " + title)
    print("=" * 58)


def check_python():
    line("1. Python")
    print("Phien ban :", sys.version.split()[0])
    print("Duong dan :", sys.executable)


def check_libs():
    line("2. Thu vien")
    need = [("keyboard", "phim tat", True), ("pyperclip", "doc clipboard", True),
            ("gtts", "phat am", False), ("pygame", "phat am", False),
            ("pystray", "icon khay", False), ("PIL", "icon khay", False),
            ("jieba", "tach tu tieng Trung", False),
            ("jamdict", "TU DIEN TIENG NHAT", False),
            ("janome", "tach tu tieng Nhat", False)]
    missing_ja = False
    for mod, what, required in need:
        try:
            __import__(mod)
            print("[OK] {:12} {}".format(mod, what))
        except ImportError:
            mark = "[THIEU - BAT BUOC]" if required else "[thieu]"
            print("{} {:12} {}".format(mark, mod, what))
            if mod in ("jamdict", "janome"):
                missing_ja = True
    if missing_ja:
        print("\n>> Tieng Nhat se KHONG tra duoc. Nhay dup: caidat_tiengnhat.bat")


def check_data():
    line("3. Du lieu tu dien")
    files = [("cvdict.u8", "Trung - Viet"), ("cedict.txt", "Trung - Anh"),
             ("hsk.json", "cap do HSK"), ("kengdic.tsv", "TIENG HAN"),
             ("jlpt.json", "cap do JLPT"), ("envi.tsv", "Anh - Viet"),
             ("en_ipa.tsv", "phien am IPA"), ("cefr.json", "cap do CEFR"),
             ("it_terms.tsv", "thuat ngu IT")]
    for name, what in files:
        path = os.path.join(DATA, name)
        if os.path.exists(path):
            print("[OK] {:14} {:14} {:>7} KB".format(
                name, what, os.path.getsize(path) // 1024))
        else:
            print("[THIEU] {:14} {}".format(name, what))
    local_db = os.path.join(DATA, "jamdict.db")
    if os.path.exists(local_db):
        print("[OK] {:14} {:14} {:>7} MB".format(
            "jamdict.db", "TU DIEN NHAT", os.path.getsize(local_db) // 1048576))
    ja = False
    try:
        sys.path.insert(0, BASE)
        import japanese
        ja = bool(japanese.Japanese().lookup("水").entries)
    except Exception as e:
        print("[THIEU] tu dien tieng Nhat:", str(e)[:60])
    if ja:
        print("[OK] tu dien tieng Nhat chay duoc")


def check_dicts():
    line("4. Thu tra tu that")
    sys.path.insert(0, BASE)
    import langs
    a = langs.Analyzer()
    for text, name in (("银行", "Trung"), ("食べる", "Nhat"),
                       ("은행", "Han"), ("firewall", "Anh")):
        try:
            lang, cards, err = a.analyze(text)
            if err:
                print("[X ] {:6} {}  -> {}".format(name, text, err))
            elif cards and cards[0].found:
                nghia = "; ".join(cards[0].vi or cards[0].en)[:45]
                print("[OK] {:6} {}  -> {}".format(name, text, nghia))
            else:
                print("[X ] {:6} {}  -> khong ra ket qua".format(name, text))
        except Exception as e:
            print("[X ] {:6} {}  -> {}: {}".format(name, text, type(e).__name__, e))


def check_ocr():
    line("5. OCR (chup man hinh roi doc chu - Ctrl+Alt+X)")
    sys.path.insert(0, BASE)
    try:
        import ocr
        print(ocr.status_text())
        if not ocr.available():
            print("\n>> Nhanh (Trung + Anh, ~1 phut): nhay dup caidat_ocr_nhanh.bat")
            print(">> Day du (them Nhat + Han): nhay dup caidat_ocr.bat")
    except Exception as e:
        print("[X] Khong kiem tra duoc OCR:", e)


def check_network():
    line("6. Dich online (can cho tieng Nhat/Han va dich ca cau)")
    sys.path.insert(0, BASE)
    import translate
    translate.selftest()


def main():
    print("CHAN DOAN LANGSCAN")
    check_python()
    check_libs()
    check_data()
    check_dicts()
    check_ocr()
    check_network()
    print("\nXong. Chup man hinh hoac copy toan bo phan tren gui lai neu can giup.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
