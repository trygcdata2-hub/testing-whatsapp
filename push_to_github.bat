@echo off
echo ====================================================
echo  Syncing and Pushing Operations Dashboard to GitHub
echo ====================================================
set GIT_CMD="C:\Users\DA-05\AppData\Local\Programs\Git\cmd\git.exe"
%GIT_CMD% add -A
%GIT_CMD% commit -m "update: sync operational data and dashboard updates"
%GIT_CMD% push origin main
echo.
echo Sync Complete! Your Streamlit Cloud deployment will auto-refresh.
pause
