Write-Host "Starting CloudScore Astra AI..." -ForegroundColor Cyan
Write-Host ""

# Start backend
Write-Host "Starting Backend Server..." -ForegroundColor Yellow
$backend = Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd backend; python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000" -PassThru

# Wait for backend to start
Start-Sleep -Seconds 3

# Start frontend
Write-Host "Starting Frontend Server..." -ForegroundColor Yellow
$frontend = Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd frontend; npm run dev" -PassThru

Write-Host ""
Write-Host "CloudScore Astra AI is running!" -ForegroundColor Green
Write-Host "Backend: http://localhost:8000" -ForegroundColor White
Write-Host "Frontend: http://localhost:5173" -ForegroundColor White
Write-Host ""
Write-Host "Press Ctrl+C to stop all servers..." -ForegroundColor Yellow

# Wait for Ctrl+C
try {
    while ($true) {
        Start-Sleep -Seconds 1
    }
} finally {
    Write-Host ""
    Write-Host "Stopping all servers..." -ForegroundColor Yellow
    Stop-Process -Id $backend.Id -Force -ErrorAction SilentlyContinue
    Stop-Process -Id $frontend.Id -Force -ErrorAction SilentlyContinue
    Write-Host "All servers stopped." -ForegroundColor Green
}
