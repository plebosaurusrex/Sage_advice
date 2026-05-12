@echo off
:: Change to the folder where this .bat lives — fixes the System32 cwd issue
cd /d "%~dp0"

echo ============================================
echo   Buddha Mountain Screensaver - Builder
echo ============================================
echo.

:: ── Find Python ───────────────────────────────────────────────────────────────
set PYTHON=%LOCALAPPDATA%\Python\pythoncore-3.14-64\python.exe

if not exist "%PYTHON%" (
    for %%P in (
        "%LOCALAPPDATA%\Programs\Python\Python314\python.exe"
        "%LOCALAPPDATA%\Programs\Python\Python313\python.exe"
        "%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
        "%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
        "%LOCALAPPDATA%\Programs\Python\Python310\python.exe"
        "C:\Python314\python.exe"
        "C:\Python313\python.exe"
        "C:\Python312\python.exe"
        "C:\Python311\python.exe"
        "C:\Python310\python.exe"
    ) do (
        if exist %%P ( set PYTHON=%%P & goto :found )
    )
    echo ERROR: Could not find python.exe
    echo Install Python from https://python.org and try again.
    pause
    exit /b 1
)

:found
echo Found Python: %PYTHON%
"%PYTHON%" --version
echo.

:: ── Check buddha.html is present ─────────────────────────────────────────────
if not exist "buddha.html" (
    echo ERROR: buddha.html not found in this folder.
    echo Make sure buddha.html is in the same folder as this .bat file.
    pause
    exit /b 1
)
echo Found: buddha.html
echo.

:: ── Step 1: Install dependencies ─────────────────────────────────────────────
echo [1/4] Installing dependencies...
"%PYTHON%" -m pip install PyQt6 PyQt6-WebEngine pyinstaller --quiet
if errorlevel 1 (
    echo ERROR: pip install failed. Check your internet connection.
    pause
    exit /b 1
)
echo       Done.
echo.

:: ── Step 2: Build with PyInstaller ───────────────────────────────────────────
echo [2/4] Building with PyInstaller (this takes a minute)...
"%PYTHON%" -m PyInstaller ^
    --onefile ^
    --noconsole ^
    --name buddhamountain ^
    --add-data "buddha.html;." ^
    --hidden-import PyQt6.QtWebEngineWidgets ^
    --hidden-import PyQt6.QtWebEngineCore ^
    --collect-all PyQt6 ^
    buddha_screensaver.py

if errorlevel 1 (
    echo.
    echo ERROR: PyInstaller build failed. See output above.
    pause
    exit /b 1
)
echo       Done.
echo.

:: ── Step 3: Rename .exe to .scr ──────────────────────────────────────────────
echo [3/4] Renaming .exe to .scr...
copy /Y dist\buddhamountain.exe dist\buddhamountain.scr >nul
if errorlevel 1 (
    echo ERROR: Could not rename. Check dist\ folder exists.
    pause
    exit /b 1
)
echo       Done.
echo.

:: ── Step 4: Copy to System32 ─────────────────────────────────────────────────
echo [4/4] Copying to System32...
copy /Y dist\buddhamountain.scr %SystemRoot%\System32\buddhamountain.scr >nul
if errorlevel 1 (
    echo.
    echo NOTE: Could not copy to System32 automatically.
    echo       This usually means you need to run as Administrator.
    echo.
    echo       Manually copy this file:
    echo         %~dp0dist\buddhamountain.scr
    echo       To:
    echo         C:\Windows\System32\buddhamountain.scr
    echo.
    echo       Right-click the .scr ^> Copy ^> paste into C:\Windows\System32
    echo       Then right-click it there ^> Install
) else (
    echo       Installed to System32!
    echo.
    echo       Right-click buddhamountain.scr in System32 and choose Install,
    echo       or go to Settings ^> Personalization ^> Lock Screen ^> Screen Saver
    echo       and select "buddhamountain" from the dropdown.
)

echo.
echo ============================================
echo   Build complete!
echo   File: %~dp0dist\buddhamountain.scr
echo ============================================
echo.
pause
