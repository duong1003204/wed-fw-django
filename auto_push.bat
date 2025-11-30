@echo off
echo ==== AUTO GIT PUSH START ====
cd /d "C:\Users\duong\OneDrive\Desktop\DACNCNPM -COPY"
git add .
git commit -m "Auto update BY Phạm Đại Dương %date% %time%"
git push origin main
echo ==== DONE ====
pause
