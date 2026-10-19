@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo === Buoc 1/4: thu vien chinh ===
python -m pip install -r requirements.txt
echo.
echo === Buoc 2/4: tieng Nhat (~75MB, tai mot lan - co the bo qua) ===
set /p JA="Cai tu dien tieng Nhat? (y/n): "
rem Khong dung "pip install jamdict-data": goi do loi WinError 32 tren Windows
if /i "%JA%"=="y" (
    python caidat_tiengnhat.py
) else (
    echo Bo qua. Sau nay nhay dup caidat_tiengnhat.bat
)
echo.
echo (tuy chon) jieba - tach tu tieng Trung chinh xac hon, bo qua neu loi:
python -m pip install jieba
echo.
echo === Buoc 3/4: kiem tra tu dien ===
python setup_data.py
echo.
echo === Buoc 4/4: khoi dong cung Windows ===
set /p AUTO="Bat che do tu chay khi mo may? (y/n): "
if /i "%AUTO%"=="y" (
    python autostart.py install
) else (
    echo Bo qua. Sau nay muon bat thi chay install_autostart.bat
)
echo.
echo XONG. Nhay dup run_hidden.bat de chay ngam, hoac run.bat de xem console.
pause
