@echo off
:: ============================================================
:: run_docker.bat — Inicia o sistema via Docker e abre o navegador
:: Squad FISC — Fiscal Finance
:: ============================================================

title Fiscal Finance — Docker

echo.
echo  ============================================================
echo   Fiscal Finance — Squad FISC
echo   Iniciando ambiente via Docker...
echo  ============================================================
echo.

if not exist ".env" (
    echo  [0/4] Arquivo .env nao encontrado. Criando copia a partir do .env.example...
    copy .env.example .env >nul
)

:: REMOVE CONTAINERS ANTIGOS PARA EVITAR CONFLITOS DE NOME
echo  [1/4] Removendo containers e redes anteriores...
docker rm -f container-fisc >nul 2>&1
docker compose down >nul 2>&1

echo  [2/4] Iniciando o container (isso pode demorar na primeira vez)...
docker compose up --build -d
if %errorlevel% neq 0 (
    echo.
    echo  [ERRO] Falha ao iniciar o Docker.
    echo         Verifique se o Docker Desktop esta aberto e rodando.
    pause
    exit /b 1
)

echo.
echo  [3/4] Aguardando aplicacao iniciar...
timeout /t 5 /nobreak >nul

echo.
echo  [4/4] Abrindo frontend no navegador (porta 8080)...
start "" "http://localhost:8080"

echo.
echo  ============================================================
echo   Sistema iniciado com sucesso no Docker!
echo.
echo   Frontend : http://localhost:8080
echo   Swagger  : http://localhost:8080/docs
echo.
echo   Login padrao: admin@fiscal.com / admin123
echo.
echo   Para parar o sistema, rode no terminal:
echo   docker compose down
echo  ============================================================
echo.

pause
