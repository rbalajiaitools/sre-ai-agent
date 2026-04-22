# ASTRA AI - Startup Verification Script
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "ASTRA AI - Startup Verification" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if services are running
Write-Host "Checking Backend Services..." -ForegroundColor Yellow
Write-Host "----------------------------------------" -ForegroundColor Gray

$services = @(
    @{Name="API Gateway"; Port=8000; Path="/health"},
    @{Name="Alert Service"; Port=8001; Path="/health"},
    @{Name="Investigation Engine"; Port=8002; Path="/health"},
    @{Name="AI Engine"; Port=8003; Path="/health"},
    @{Name="Knowledge Graph"; Port=8004; Path="/health"},
    @{Name="Action Engine"; Port=8005; Path="/health"},
    @{Name="Admin Service"; Port=8006; Path="/health"},
    @{Name="Notification Service"; Port=8007; Path="/health"},
    @{Name="Eval Service"; Port=8008; Path="/health"},
    @{Name="Auth Service"; Port=8009; Path="/health"},
    @{Name="Eraser Service"; Port=8010; Path="/health"}
)

$allHealthy = $true
$healthyCount = 0

foreach ($service in $services) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:$($service.Port)$($service.Path)" -Method GET -TimeoutSec 2 -UseBasicParsing
        if ($response.StatusCode -eq 200) {
            Write-Host "  [OK] $($service.Name) (Port $($service.Port))" -ForegroundColor Green
            $healthyCount++
        }
    }
    catch {
        Write-Host "  [FAIL] $($service.Name) (Port $($service.Port)) - Not responding" -ForegroundColor Red
        $allHealthy = $false
    }
}

Write-Host ""
Write-Host "Backend Status: $healthyCount/11 services healthy" -ForegroundColor $(if ($healthyCount -eq 11) { "Green" } else { "Yellow" })
Write-Host ""

# Check frontend
Write-Host "Checking Frontend..." -ForegroundColor Yellow
Write-Host "----------------------------------------" -ForegroundColor Gray

try {
    $frontendResponse = Invoke-WebRequest -Uri "http://localhost:3000" -Method GET -TimeoutSec 2 -UseBasicParsing
    if ($frontendResponse.StatusCode -eq 200) {
        Write-Host "  [OK] Frontend (Port 3000)" -ForegroundColor Green
    }
}
catch {
    Write-Host "  [FAIL] Frontend (Port 3000) - Not responding" -ForegroundColor Red
    Write-Host "  Run: .\start-frontend.ps1" -ForegroundColor Gray
    $allHealthy = $false
}

Write-Host ""

# Summary
Write-Host "========================================" -ForegroundColor Cyan
if ($allHealthy -and $healthyCount -eq 11) {
    Write-Host "All Systems Operational!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next Steps:" -ForegroundColor Yellow
    Write-Host "  1. Open http://localhost:3000" -ForegroundColor White
    Write-Host "  2. Login with admin@astra.ai / admin123" -ForegroundColor White
    Write-Host "  3. Run demo: .\demo-e2e.ps1" -ForegroundColor White
}
else {
    Write-Host "Some Services Not Running" -ForegroundColor Red
    Write-Host ""
    Write-Host "To start services:" -ForegroundColor Yellow
    if ($healthyCount -lt 11) {
        Write-Host "  Backend: .\start-all-services.ps1" -ForegroundColor White
    }
    Write-Host "  Frontend: .\start-frontend.ps1" -ForegroundColor White
}
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
