@echo off
setlocal

cd /d "%~dp0"

set "CLOUDFLARED_EXE=C:\Users\Administrator\AppData\Local\Microsoft\WinGet\Packages\Cloudflare.cloudflared_Microsoft.Winget.Source_8wekyb3d8bbwe\cloudflared.exe"

if not exist "%CLOUDFLARED_EXE%" (
    echo cloudflared was not found.
    echo Please install it first or run this project setup again.
    pause
    exit /b 1
)

echo Starting public tunnel for http://localhost:8501 ...
echo.
echo Keep this window open while your colleagues are using the site.
echo The public URL will appear below after Cloudflare creates it.
echo.

"%CLOUDFLARED_EXE%" tunnel --url http://localhost:8501 --no-autoupdate
