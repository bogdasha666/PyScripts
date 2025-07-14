@echo off
REM Убедись, что pyinstaller установлен: pip install pyinstaller

setlocal

REM Список всех твоих скриптов (кроме Menu.py)
set SCRIPTS=KillSay.py KillSound.py AutoStop.py XCarry.py RGBCrosshair.py R8Double.py ChatSpammer.py RainbowHUD.py CustomBinds.py Scope.py AngleBind.py AntiAFK.py AutoAccept.py BombTimer.py Crosshair.py Keystrokes.py KnifeSwitch.py RecoilCrosshair.py Trigger.py Watermark.py GSI.py

REM Сначала компилируем Menu.py с ресурсами
echo ==========================
echo Компиляция Menu.py ...
pyinstaller --onefile --noconsole ^
  --add-data "Arial Greek Regular.ttf;." ^
  --add-data "gear.svg;." ^
  --add-data "c4.png;." ^
  Menu.py

REM Теперь компилируем все остальные скрипты
for %%F in (%SCRIPTS%) do (
    echo ==========================
    echo Компиляция %%F ...
    pyinstaller --onefile --noconsole "%%F"
)

echo.
echo Все exe-файлы будут лежать в папке dist
echo Готово!
pause 