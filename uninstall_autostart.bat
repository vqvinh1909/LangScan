@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo Tat che do khoi dong cung Windows (se hien cua so UAC - bam Yes)...
python autostart.py uninstall
pause
