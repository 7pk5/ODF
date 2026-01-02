@echo off
TITLE ODF Installer and Launcher
CLS

ECHO ========================================================
ECHO    Offline Document Finder (ODF) - Setup & Run
ECHO ========================================================
ECHO.

:: 1. Check for Python
python --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    ECHO [ERROR] Python is not installed or not in PATH.
    ECHO Please install Python 3.10+ from python.org and try again.
    PAUSE
    EXIT /B
)

:: 2. Check/Create Virtual Environment
IF NOT EXIST "odf_dist_env" (
    ECHO [INFO] Creating virtual environment 'odf_dist_env'...
    python -m venv odf_dist_env
) ELSE (
    ECHO [INFO] Virtual environment found.
)

:: 3. Activate Environment
CALL odf_dist_env\Scripts\activate.bat

:: 4. Install Dependencies
ECHO.
ECHO [INFO] Checking and installing dependencies...
ECHO (This may take a while for the first time - downloading AI models and Torch)
ECHO.
pip install -r requirements.txt
IF %ERRORLEVEL% NEQ 0 (
    ECHO [ERROR] Failed to install dependencies. Check your internet connection.
    PAUSE
    EXIT /B
)

:: 5. Run Application
ECHO.
ECHO [INFO] Launching ODF...
python main.py

PAUSE
