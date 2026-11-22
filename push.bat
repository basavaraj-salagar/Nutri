@echo off
echo ========================================================
echo NutriTrack - Push to GitHub Repositories
echo ========================================================
cd /d "%~dp0"

echo.
echo [1/2] Pushing to origin (https://github.com/basavaraj-salagar/Nutri.git) ...
git push origin main

echo.
echo [2/2] Pushing to sathushetty7 (https://github.com/sathushetty7/NutriTrack.git) ...
git push sathushetty7 main 2>nul || echo Notice: sathushetty7 push requires collaborator access for this account.

echo.
echo ========================================================
echo [DONE] Push process finished!
echo ========================================================
pause
