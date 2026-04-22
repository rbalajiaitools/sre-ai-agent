# Restart all ASTRA AI microservices after fixing metadata issue

Write-Host "Restarting CloudScore ASTRA AI Services..." -ForegroundColor Cyan
Write-Host ""

# Kill existing Python processes (services)
Write-Host "Stopping existing services..." -ForegroundColor Yellow
Get-Process python -ErrorAction SilentlyContinue | Where-Object {$_.Path -like "*astra-ai*"} | Stop-Process -Force
Start-Sleep -Seconds 2
Write-Host "Existing services stopped" -ForegroundColor Green
Write-Host ""

# Reinstall shared libraries
Write-Host "Reinstalling shared libraries..." -ForegroundColor Yellow
Set-Location shared-libs
pip install -e . -q
Set-Location ..
Write-Host "Shared libraries reinstalled" -ForegroundColor Green
Write-Host ""

# Array of services with their ports
$services = @(
    @{Name="API Gateway"; Port=8000; Path="services/api-gateway"},
    @{Name="Auth Service"; Port=8009; Path="services/auth-service"},
    @{Name="Alert Service"; Port=8001; Path="services/alert-service"},
    @{Name="Investigation Engine"; Port=8002; Path="services/investigation-engine"},
    @{Name="AI Engine"; Port=8003; Path="services/ai-engine"},
    @{Name="Knowledge Graph"; Port=8004; Path="services/knowledge-graph"},
    @{Name="Action Engine"; Port=8005; Path="services/action-engine"},
    @{Name="Admin Service"; Port=8006; Path="services/admin-service"},
    @{Name="Notification Service"; Port=8007; Path="services/notification-service"},
    @{Name="Eval Service"; Port=8008; Path="services/eval-service"},
    @{Name="Eraser Service"; Port=8010; Path="services/eraser-service"}
)

# Start each service
foreach ($service in $services) {
    Write-Host "Starting $($service.Name) on port $($service.Port)..." -ForegroundColor Yellow
    
    Set-Location $service.Path
    
    # Start service in background
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "python main.py" -WindowStyle Minimized
    
    Set-Location ../..
    Start-Sleep -Seconds 1
}

Write-Host ""
Write-Host "All services restarted!" -ForegroundColor Green
Write-Host ""
Write-Host "Service URLs:" -ForegroundColor Cyan
Write-Host "  API Gateway:          http://localhost:8000"
Write-Host "  Auth Service:         http://localhost:8009"
Write-Host "  Alert Service:        http://localhost:8001"
Write-Host "  Investigation Engine: http://localhost:8002"
Write-Host "  AI Engine:            http://localhost:8003"
Write-Host "  Knowledge Graph:      http://localhost:8004"
Write-Host "  Action Engine:        http://localhost:8005"
Write-Host "  Admin Service:        http://localhost:8006"
Write-Host "  Notification Service: http://localhost:8007"
Write-Host "  Eval Service:         http://localhost:8008"
Write-Host "  Eraser Service:       http://localhost:8010"
Write-Host ""
Write-Host "API Documentation:" -ForegroundColor Cyan
Write-Host "  http://localhost:8000/docs (via API Gateway)"
Write-Host ""
