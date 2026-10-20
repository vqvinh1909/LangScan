@echo off
chcp 65001 >nul
cd /d "%~dp0"
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo Can quyen Administrator - dang xin quyen...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)
echo ================================================
echo   Bat OCR cua Windows cho Trung / Nhat / Han / Anh / Viet
echo   Windows se tai vai chuc MB cho moi thu tieng.
echo ================================================
echo.
for %%L in (zh-CN ja-JP ko-KR en-US vi-VN) do (
    echo --- %%L
    powershell -NoProfile -Command "Add-WindowsCapability -Online -Name 'Language.OCR~~~%%L~0.0.1.0' | Out-Null; if ($?) { 'da bat' } else { 'that bai' }"
)
echo.
echo === Kiem tra lai ===
python ocr.py
echo.
echo Xong. Thoat LangScan (Ctrl+Alt+Q) roi mo lai run_hidden.bat.
pause
