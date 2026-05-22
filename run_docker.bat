@echo off
echo ==================================================
echo   Iniciando Fiscal-Finance via Docker Compose
echo ==================================================
echo.

echo Parando containers antigos, se existirem...
docker-compose down

echo.
echo Construindo imagens e subindo containers...
docker-compose up -d --build

echo.
echo ==================================================
echo   Containers rodando!
echo   Abrindo navegador em http://localhost:8080/
echo ==================================================
echo.

start http://localhost:8080/

pause
