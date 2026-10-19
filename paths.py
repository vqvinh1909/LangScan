# -*- coding: utf-8 -*-
"""
paths.py - Thu muc cua app va thu muc data/, dung chung cho moi module.

Chay bang Python: thu muc chua file .py.
Chay bang LangScan.exe (dong goi PyInstaller): thu muc chua file .exe -
khong dung __file__ vi luc do no tro vao thu muc _internal cua PyInstaller.
Trinh cai dat cai vao %LOCALAPPDATA%\\Programs\\LangScan nen data/ ghi duoc
(cache, log, kich thuoc popup) ma khong can quyen admin.
"""

import os
import sys

FROZEN = bool(getattr(sys, "frozen", False))
APP_DIR = (os.path.dirname(os.path.abspath(sys.executable)) if FROZEN
           else os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(APP_DIR, "data")
