@echo off
echo ====================================================
echo  Syncing and Pushing Operations Dashboard to GitHub
echo ====================================================
git add -A
git commit -m "update: sync operational data and dashboard updates"
git push origin main
echo.
echo Sync Complete! Your Streamlit Cloud deployment will auto-refresh.
pause
