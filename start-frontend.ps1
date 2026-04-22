# Start ASTRA AI Frontend
Write-Host "Starting ASTRA AI Frontend..." -ForegroundColor Green

# Check if node_modules exists
if (-not (Test-Path "frontend/node_modules")) {
    Write-Host "Installing dependencies..." -ForegroundColor Yellow
    Set-Location frontend
    npm install
    Set-Location ..
}

# Start frontend
Write-Host "Starting Next.js development server on http://localhost:3000" -ForegroundColor Cyan
Set-Location frontend
npm run dev
