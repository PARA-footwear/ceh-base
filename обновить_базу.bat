@echo off
chcp 65001 > nul
python build_ceh_base.py
git add -A
git commit -m "Обновление базы"
git pull --rebase
git push
echo.
echo Готово! База обновлена.
pause