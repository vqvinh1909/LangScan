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
echo   Bat OCR tieng Viet cua Windows cho LangScan
echo   (doc chu Viet co dau trong anh / Ctrl+Alt+X)
echo   Windows tai khoang vai MB, mat 1-3 phut.
echo ================================================
echo.
powershell -NoProfile -Command "Add-WindowsCapability -Online -Name 'Language.OCR~~~vi-VN~0.0.1.0' | Out-Null; if ($?) { 'Da bat OCR tieng Viet.' } else { 'That bai - kiem tra mang roi chay lai.' }"
echo.
echo Xong. Thoat LangScan (Ctrl+Alt+Q) roi mo lai.
pause
