@echo off
title Iniciando App de Física Interativo
cd /d "C:\Users\DELL\Downloads\app_fisica_web"

echo Instalando dependências...
pip install -r requirements.txt

echo Iniciando o servidor Flask...
python app.py

pause
