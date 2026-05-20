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
echo   Acesse: http://localhost:8080/
echo ==================================================
pause
