@echo off
title Fiscal Finance — Docker Setup
echo ==================================================
echo   Iniciando Fiscal-Finance via Docker Compose
echo ==================================================
echo.

:: 1. Detectar comando docker compose ou docker-compose
set "DOCKER_CMD=docker compose"
docker compose version >nul 2>&1
if %errorlevel% neq 0 (
    set "DOCKER_CMD=docker-compose"
    docker-compose version >nul 2>&1
    if %errorlevel% neq 0 (
        echo [ERRO] Docker nao encontrado! 
        echo        Certifique-se de que o Docker Desktop esta instalado e rodando.
        pause
        exit /b 1
    )
)

:: 2. Verificar e criar a rede externa core-engine-main_erp-network
echo Verificando rede de integracao 'core-engine-main_erp-network'...
docker network inspect core-engine-main_erp-network >nul 2>&1
if %errorlevel% neq 0 (
    echo Rede nao encontrada. Criando a rede externa para integracao inter-squads...
    docker network create core-engine-main_erp-network
) else (
    echo Rede externa de integracao ja existe.
)
echo.

:: 3. Verificar e auto-criar o arquivo .env a partir do .env.example
if not exist .env (
    if exist .env.example (
        echo Arquivo .env nao encontrado na raiz.
        echo Copiando variaveis padrao de .env.example automaticamente...
        copy .env.example .env >nul
        echo Arquivo .env criado com sucesso!
        echo.
    ) else (
        echo [AVISO] Arquivo .env nao encontrado e .env.example nao esta presente!
        echo.
    )
)

:: 4. Limpar eventuais conflitos de nomes de containers no Docker
echo Removendo conflitos de containers antigos (se houver)...
docker rm -f container-fisc-backend >nul 2>&1
docker rm -f container-fisc-frontend >nul 2>&1
echo.

:: 5. Parar containers antigos e rodar os novos
echo Parando containers antigos do projeto atual, se existirem...
%DOCKER_CMD% down

echo.
echo Construindo imagens e subindo containers...
%DOCKER_CMD% up -d --build

echo.
echo ==================================================
echo   Containers rodando com sucesso!
echo   Acesse o sistema local em: http://localhost:8080/
echo ==================================================
pause
