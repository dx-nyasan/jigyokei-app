# scripts/run_app.ps1
# Automates the clean launch of the Jigyokei Hybrid System
# Usage: .\scripts\run_app.ps1

$ErrorActionPreference = "Stop"

Write-Host "🚀 Initializing Jigyokei Local Dev Environment..." -ForegroundColor Cyan

# 1. Determine Project Root
try {
    $ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
    # Assuming script is in /scripts/, parent is ProjectRoot
    $ProjectRoot = (Get-Item $ScriptDir).Parent.FullName
} catch {
    # Fallback if run directly or weird context
    $ProjectRoot = Get-Location
}

Write-Host "📂 Project Root detected: $ProjectRoot" -ForegroundColor Gray

# 2. Cleanup Stale Processes
Write-Host "🧹 Cleaning up stale Python/Streamlit processes..." -ForegroundColor Yellow
try {
    Stop-Process -Name "python" -Force -ErrorAction SilentlyContinue
    Write-Host "   ✅ Stale processes terminated." -ForegroundColor Green
} catch {
    Write-Host "   ℹ️ No stale processes found." -ForegroundColor Gray
}

# 3. Environment Check
$SecretsFile = Join-Path $ProjectRoot ".streamlit\secrets.toml"
if (-not (Test-Path $SecretsFile)) {
    Write-Warning "⚠️  .streamlit/secrets.toml NOT FOUND."
    Write-Host "   Please ensure setup prompt has been run."
    # Optional: Could auto-create here, but safer to warn for now as we just fixed it manually.
} else {
    Write-Host "✅ Secrets file found." -ForegroundColor Green
}

# 4. Launch Application
Write-Host "🌟 Launching Streamlit App..." -ForegroundColor Cyan
Set-Location $ProjectRoot

# Launch in current console so we see logs
streamlit run src/frontend/app_hybrid.py
