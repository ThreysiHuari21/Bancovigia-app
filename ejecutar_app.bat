@echo off
REM Abre el aplicativo BancoVigia en el navegador (Windows / Anaconda Prompt)
cd /d "%~dp0"
streamlit run app.py
pause
