@echo off
:: ============================================================
:: TV Corporativa – Script de Instalação Automática
:: Grupo Flexível
:: ============================================================
:: Este script configura uma TV automaticamente:
::   1. Cria atalho do Chrome em modo kiosk
::   2. Configura inicialização automática com o Windows
::   3. Cria tarefas de ligar/desligar no horário certo
::   4. Configura a tela para não desligar
:: ============================================================
:: USO: Execute como Administrador em cada PC/player das TVs
:: ============================================================

setlocal EnableDelayedExpansion
title TV Corporativa - Instalacao Automatica
color 0B

echo.
echo  ============================================================
echo   TV CORPORATIVA – GRUPO FLEXIVEL
echo   Script de Instalacao Automatica
echo  ============================================================
echo.

:: ── Solicitar IP do servidor ──────────────────────────────────
set /p SERVER_IP="  Digite o IP do servidor (ex: 192.168.1.10): "
set /p TV_NUM="  Numero desta TV (ex: 01, 02 ... 20): "
set /p TV_SLUG="  Slug/identificador da tela (ex: recepcao, padrao=principal): "
if "!TV_SLUG!"==""   set TV_SLUG=principal
set /p LIGAR_HORA="  Horario de LIGAR a TV (ex: 07:30, padrao=07:30): "
set /p DESLIGAR_HORA="  Horario de DESLIGAR a TV (ex: 18:00, padrao=18:00): "

if "!LIGAR_HORA!"==""     set LIGAR_HORA=07:30
if "!DESLIGAR_HORA!"=""   set DESLIGAR_HORA=18:00

set TV_URL=http://!SERVER_IP!:8080/tela/!TV_SLUG!
set TASK_NAME=TV_Corporativa_%TV_NUM%
set STARTUP_DIR=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup

echo.
echo  Configurando TV !TV_NUM! → !TV_URL!
echo.

:: ── 1. Criar atalho kiosk na Inicialização ───────────────────
echo  [1/5] Criando atalho de inicializacao automatica...

set CHROME_PATH=
for %%p in (
  "%ProgramFiles%\Google\Chrome\Application\chrome.exe"
  "%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"
  "%LocalAppData%\Google\Chrome\Application\chrome.exe"
) do (
  if exist %%p set CHROME_PATH=%%~p
)

if "!CHROME_PATH!"=="" (
  echo  AVISO: Chrome nao encontrado. Usando Microsoft Edge.
  set CHROME_PATH=%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe
)

:: Criar VBScript para gerar o atalho
set VBS=%TEMP%\cria_atalho_tv.vbs
(
  echo Set oWS = WScript.CreateObject^("WScript.Shell"^)
  echo sLinkFile = "!STARTUP_DIR!\TV Corporativa !TV_NUM!.lnk"
  echo Set oLink = oWS.CreateShortcut^(sLinkFile^)
  echo oLink.TargetPath = "!CHROME_PATH!"
  echo oLink.Arguments = "--kiosk ""!TV_URL!"" --no-first-run --disable-infobars --disable-session-crashed-bubble --autoplay-policy=no-user-gesture-required --disable-features=TranslateUI"
  echo oLink.WorkingDirectory = "%USERPROFILE%"
  echo oLink.WindowStyle = 1
  echo oLink.Description = "TV Corporativa Grupo Flexivel"
  echo oLink.Save
) > "!VBS!"
cscript //nologo "!VBS!"
del "!VBS!" 2>nul
echo     OK: Atalho criado em Inicializacao do Windows

:: ── 2. Configurar tela sempre ligada ─────────────────────────
echo  [2/5] Desativando protecao de tela e suspensao...
powercfg /change standby-timeout-ac 0
powercfg /change monitor-timeout-ac 0
powercfg /change hibernate-timeout-ac 0
powercfg /x -standby-timeout-ac 0 2>nul
echo     OK: Tela configurada para nao desligar

:: ── 3. Tarefa agendada: DESLIGAR no horario certo ────────────
echo  [3/5] Criando tarefa de desligamento (!DESLIGAR_HORA! Seg-Sex)...
schtasks /delete /tn "TV_Fechar_%TV_NUM%" /f 2>nul
schtasks /create ^
  /tn "TV_Fechar_%TV_NUM%" ^
  /tr "taskkill /f /im chrome.exe /im msedge.exe" ^
  /sc weekly /d MON,TUE,WED,THU,FRI ^
  /st !DESLIGAR_HORA! ^
  /ru SYSTEM /rl HIGHEST /f >nul
echo     OK: Tarefa de fechamento criada (!DESLIGAR_HORA!)

:: ── 4. Tarefa agendada: ABRIR a TV no horario certo ──────────
echo  [4/5] Criando tarefa de abertura (!LIGAR_HORA! Seg-Sex)...
schtasks /delete /tn "TV_Abrir_%TV_NUM%" /f 2>nul
schtasks /create ^
  /tn "TV_Abrir_%TV_NUM%" ^
  /tr "\"!CHROME_PATH!\" --kiosk \"!TV_URL!\" --no-first-run --disable-infobars --autoplay-policy=no-user-gesture-required" ^
  /sc weekly /d MON,TUE,WED,THU,FRI ^
  /st !LIGAR_HORA! ^
  /ru "%USERNAME%" /rl HIGHEST /f >nul
echo     OK: Tarefa de abertura criada (!LIGAR_HORA!)

:: ── 5. Registrar no log ───────────────────────────────────────
echo  [5/5] Registrando instalacao...
set LOG_FILE=%~dp0log_instalacao.txt
echo [%date% %time%] TV !TV_NUM! configurada. IP Servidor: !SERVER_IP!. Ligar: !LIGAR_HORA! Desligar: !DESLIGAR_HORA! >> "!LOG_FILE!"
echo     OK: Log salvo em log_instalacao.txt

:: ── Resumo ────────────────────────────────────────────────────
echo.
echo  ============================================================
echo   INSTALACAO CONCLUIDA COM SUCESSO!
echo  ============================================================
echo   TV numero   : !TV_NUM!
echo   URL da TV   : !TV_URL!
echo   Ligar       : !LIGAR_HORA! (Seg a Sex)
echo   Desligar    : !DESLIGAR_HORA! (Seg a Sex)
echo  ============================================================
echo.
echo   Proximos passos:
echo   1. Reinicie o computador para testar o autostart
echo   2. Verifique se a TV abre em tela cheia automaticamente
echo   3. Abra docs/protocolo_testes.html para registrar os resultados
echo.
pause
endloca