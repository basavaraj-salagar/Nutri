@echo off
echo ========================================================
echo NutriTrack - Push to GitHub Repositories
echo ========================================================
cd /d "%~dp0"

echo.
echo [1/2] Pushing to https://github.com/basavaraj-salagar/nutritrack ...
git push origin main

echo.
echo [2/2] Pushing to https://github.com/sathushetty7/NutriTrack ...
git push sathushetty7 main

echo.
echo ========================================================
echo [DONE] Push process finished!
echo If prompted for credentials for either account, please
echo complete the sign-in in the browser window.
echo ========================================================
pause
