@echo off
echo =======================================
echo   Flappy Shiba Inu  —  .exe Builder
echo =======================================
echo.

echo [1/3] Installing dependencies...
pip install pygame pyinstaller
if errorlevel 1 (
    echo ERROR: pip install failed. Make sure Python is installed and on your PATH.
    pause
    exit /b 1
)
echo.

echo [2/3] Building .exe (this may take a minute)...
pyinstaller --onefile --noconsole --name "FlappyShibaInu" main.py
if errorlevel 1 (
    echo ERROR: PyInstaller build failed.
    pause
    exit /b 1
)
echo.

echo [3/3] Setting up assets folder next to .exe...
if not exist "dist\assets" mkdir "dist\assets"
echo.

echo =======================================
echo   Build complete!
echo.
echo   Your game:   dist\FlappyShibaInu.exe
echo.
echo   To add your Shiba image:
echo     Copy shiba.png  into  dist\assets\shiba.png
echo     then run the .exe — it will show your image.
echo =======================================
echo.
pause
