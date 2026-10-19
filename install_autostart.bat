@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo Bat che do khoi dong cung Windows (se hien cua so UAC - bam Yes)...
python autostart.py install
echo.
echo Tu lan dang nhap Windows sau, LangScan tu chay ngam.
echo Muon chay ngay bay gio thi nhay dup run_hidden.bat
pause
