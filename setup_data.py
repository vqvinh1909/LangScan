# -*- coding: utf-8 -*-
"""
setup_data.py - Kiem tra du lieu tu dien trong data/ con du khong.

Tu dien da nam san trong ma nguon (va trong file cai dat) nen khong can tai them.
(Tu dien tieng Nhat JMdict nam trong goi pip 'jamdict-data'.)

Chay:  python setup_data.py
"""

import os
import sys

from paths import DATA_DIR

FILES = ("cvdict.u8", "cedict.txt", "hsk.json", "kengdic.tsv", "jlpt.json",
         "envi.tsv", "en_ipa.tsv", "cefr.json", "it_terms.tsv")


def main():
    missing = [n for n in FILES if not os.path.exists(os.path.join(DATA_DIR, n))]
    if missing:
        print("[!] Thieu du lieu: {}".format(", ".join(missing)))
        print("    Tai lai ma nguon LangScan de lay lai thu muc data/")
        return 1
    print("[=] Du lieu tu dien day du. Gio chay:  python langscan.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
