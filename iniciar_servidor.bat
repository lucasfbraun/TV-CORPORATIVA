@echo off
:: ============================================================
:: TV Corporativa - Iniciar Servidor Central
:: Grupo Flexivel
:: ============================================================
:: Execute este arquivo no PC que sera o SERVIDOR das TVs.
:: ============================================================
title TV Corporativa - Servidor
cd /d "%~dp0"

echo.
echo  ============================================================
echo   TV CORPORATIVA - GRUPO FLEXIVEL
echo  ============================================================
echo.

:: Verifica Python
python --version >nul 2>&1
if errorlevel 1 (
  echo  ERRO: Python nao encontrado. Instale em https://python.org
  echo  Marque a opcao "Add Python to PATH" durante a instalacao.
  pause
  exit /b 1
)

:: Instala/atualiza dependencias
echo  [1/2] Verificando dependencias...
python -m pip install -q -r requirements.txt

:: Descobre o IP da maquina para facilitar a configuracao das TVs
echo.
echo  [2/2] Iniciando servidor...
echo.
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4"') do (
  for /f "tokens=* delims= " %%b in ("%%a") do set IP=%%b
)
echo  ============================================================
echo   Servidor iniciando!
echo.
echo   Neste PC:     http://localhost:8080/admin
echo   Nas TVs use:  http://%IP%:8080/tela/principal
echo  ============================================================
echo.
echo   Primeiro login:  usuario = admin   senha = flexivel
echo   (troque a senha apos entrar)
echo.
echo   Feche esta janela para parar o servidor.
echo  ============================================================
echo.

python backend\server.py
pause
