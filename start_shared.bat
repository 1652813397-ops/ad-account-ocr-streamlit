@echo off
setlocal

cd /d "%~dp0"

set "PYTHON_EXE=%~dp0.venv\Scripts\python.exe"
set "SYSTEM_PYTHON=C:\Users\Administrator\AppData\Local\Programs\Python\Python311\python.exe"
set "APP_AUTH_ENABLED=true"
set "APP_USERNAME=admin"
set "APP_ACCESS_CODE=962464"
set "FLAGS_use_mkldnn=0"

if not exist "%PYTHON_EXE%" (
    echo [1/3] Creating virtual environment...
    if exist "%SYSTEM_PYTHON%" (
        "%SYSTEM_PYTHON%" -m venv .venv
    ) else (
        echo Python 3.11 was not found.
        pause
        exit /b 1
    )
)

if not exist "%~dp0.venv\Scripts\streamlit.exe" (
    echo [2/3] Installing dependencies...
    "%PYTHON_EXE%" -m pip install --upgrade pip
    if errorlevel 1 goto :error
    "%PYTHON_EXE%" -m pip install -r requirements.txt
    if errorlevel 1 goto :error
)

echo [3/3] Starting shared web app...
echo.
echo Local access:   http://localhost:8501
echo LAN access:     http://YourComputerIP:8501
echo Username:       %APP_USERNAME%
echo Access code:    %APP_ACCESS_CODE%
echo.
"%PYTHON_EXE%" -m streamlit run app.py --server.address 0.0.0.0 --server.port 8501 --server.headless true
goto :eof

:error
echo.
echo Dependency installation failed. Please check the error messages above.
pause
exit /b 1
