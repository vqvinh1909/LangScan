@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ================================================
echo   Cai OCR nhanh (tieng Trung + tieng Anh)
echo   Tai khoang 36 MB, khong can quyen admin.
echo   Muon doc ca tieng Nhat/Han thi dung caidat_ocr.bat
echo ================================================
echo.
python -m pip install rapidocr-onnxruntime
echo.
echo === Kiem tra lai ===
python ocr.py
echo.
echo Xong. Thoat LangScan (Ctrl+Alt+Q) roi mo lai run_hidden.bat.
pause
