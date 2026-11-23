@echo off
chcp 65001 > nul
python build_ceh_base.py
git add .
git commit -m "Обновление фото"
git push
echo Готово! База обновлена.
pause