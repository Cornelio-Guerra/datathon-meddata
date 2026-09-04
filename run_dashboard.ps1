$ErrorActionPreference = "Stop"

Set-Location -LiteralPath $PSScriptRoot

if (-not (Test-Path -LiteralPath ".\.venv\Scripts\python.exe")) {
    throw "No se encontró el entorno virtual .venv. Ejecuta primero la preparación del entorno."
}

Write-Host "Iniciando MedData Decision Dashboard..." -ForegroundColor Cyan
Write-Host "Abre http://127.0.0.1:8000 en tu navegador." -ForegroundColor Yellow
& ".\.venv\Scripts\python.exe" ".\dashboard\app.py"
