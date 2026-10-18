@echo off
rem Arranque con ventana, para ver los errores si algo falla.
rem El acceso directo del Escritorio arranca sin ventana; este es el de repuesto.
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" -m krv
) else (
    python -m krv
)
if errorlevel 1 (
    echo.
    echo La aplicacion ha terminado con un error. Revisa el mensaje de arriba
    echo y el fichero logs\krv.log
    pause
)
