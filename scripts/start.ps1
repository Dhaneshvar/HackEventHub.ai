<#
.SYNOPSIS
    Starts the Opportunity Agent on Windows.
#>

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$ProjectDir = Split-Path -Parent $ScriptDir
Set-Location $ProjectDir

Write-Host "=== Starting Opportunity Agent ===" -ForegroundColor Cyan

# 1. Check .env
if (-not (Test-Path ".env")) {
    Write-Host "Creating .env from .env.example..." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
}

# 2. Check virtual environment
$PythonExe = Join-Path $ProjectDir ".venv\Scripts\python.exe"
$UvicornExe = Join-Path $ProjectDir ".venv\Scripts\uvicorn.exe"
$AlembicExe = Join-Path $ProjectDir ".venv\Scripts\alembic.exe"

if (-not (Test-Path $PythonExe)) {
    Write-Host "Virtual environment not found. Creating with uv..." -ForegroundColor Yellow
    if (Get-Command uv -ErrorAction SilentlyContinue) {
        uv venv --python 3.11
        uv pip install -e ".[dev]"
    } else {
        python -m venv .venv
        & $PythonExe -m pip install -e ".[dev]"
    }
}

# 3. Ensure data folder exists
if (-not (Test-Path "data")) {
    New-Item -ItemType Directory -Path "data" | Out-Null
}

# 4. Run database migrations
Write-Host "Applying database migrations..." -ForegroundColor Green
& $AlembicExe upgrade head

# 5. Check frontend build
if (Test-Path "frontend\package.json" -and -not (Test-Path "frontend\dist")) {
    Write-Host "Building frontend assets..." -ForegroundColor Yellow
    Push-Location "frontend"
    if (Get-Command npm -ErrorAction SilentlyContinue) {
        npm install
        npm run build
    }
    Pop-Location
}

# 6. Start the server
Write-Host "Starting FastAPI server on http://127.0.0.1:8000 ..." -ForegroundColor Cyan
& $UvicornExe app.main:app --host 127.0.0.1 --port 8000 --reload
