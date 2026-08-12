@echo off
title CashFlow Dashboard
color 1F
cls

echo.
echo  ==========================================
echo   CashFlow Dashboard
echo   Iniciando o sistema...
echo  ==========================================
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo  [ERRO] Python nao encontrado.
    pause
    exit /b
)

cd /d "%~dp0"

if not exist ".env" (
    echo  [AVISO] Arquivo .env nao encontrado.
    echo  Copie .env.example para .env e preencha suas credenciais.
    echo.
    pause
    exit /b
)

echo  [OK] Iniciando backend Flask na porta 5000...
echo  [OK] Abra o frontend/index.html com Live Server no VS Code.
echo.
echo  Pressione CTRL+C para encerrar.
echo  ==========================================
echo.

python backend/app.py
pause
