# ASTRA AI System Test Script
Write-Host "ASTRA AI System Test" -ForegroundColor Cyan
Write-Host "===================" -ForegroundColor Cyan
Write-Host ""

$baseUrl = "http://localhost:8000/api/v1"

# Test 1: Health Checks
Write-Host "Test 1: Health Checks" -ForegroundColor Yellow
$services = @(
    @{Name="API Gateway"; Port=8000},
    @{Name="Auth Service"; Port=8009},
    @{Name="Alert Service"; Port=8001},
    @{Name="Investigation Engine"; Port=8002},
    @{Name="AI Engine"; Port=8003},
    @{Name="Knowledge Graph"; Port=8004},
    @{Name="Action Engine"; Port=8005},
    @{Name="Admin Service"; Port=8006},
    @{Name="Notification Service"; Port=8007},
    @{Name="Eval Service"; Port=8008},
    @{Name="Eraser Service"; Port=8010}
)

foreach ($service in $services) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:$($service.Port)/health" -Method GET -TimeoutSec 2
        if ($response.StatusCode -eq 200) {
            Write-Host "  ✓ $($service.Name) - OK" -ForegroundColor Green
        }
    } catch {
        Write-Host "  ✗ $($service.Name) - FAILED" -ForegroundColor Red
    }
}

Write-Host ""

# Test 2: Bootstrap (if not already done)
Write-Host "Test 2: Bootstrap System" -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/bootstrap" -Method POST -ContentType "application/json"
    Write-Host "  ✓ Bootstrap successful" -ForegroundColor Green
    Write-Host "    Tenant ID: $($response.tenant_id)" -ForegroundColor Gray
    Write-Host "    Admin Email: $($response.admin_email)" -ForegroundColor Gray
    $tenantId = $response.tenant_id
} catch {
    if ($_.Exception.Response.StatusCode -eq 400) {
        Write-Host "  ℹ System already bootstrapped" -ForegroundColor Cyan
        # Get tenant from users endpoint
        try {
            $users = Invoke-RestMethod -Uri "$baseUrl/users" -Method GET
            if ($users.Count -gt 0) {
                $tenantId = $users[0].tenant_id
                Write-Host "    Using existing tenant: $tenantId" -ForegroundColor Gray
            }
        } catch {
            Write-Host "  ✗ Could not get tenant ID" -ForegroundColor Red
        }
    } else {
        Write-Host "  ✗ Bootstrap failed: $($_.Exception.Message)" -ForegroundColor Red
    }
}

Write-Host ""

# Test 3: Login
Write-Host "Test 3: Authentication" -ForegroundColor Yellow
try {
    $loginBody = @{
        email = "admin@astra.ai"
        password = "admin123"
    } | ConvertTo-Json

    $loginResponse = Invoke-RestMethod -Uri "$baseUrl/auth/login" -Method POST -Body $loginBody -ContentType "application/json"
    $token = $loginResponse.access_token
    Write-Host "  ✓ Login successful" -ForegroundColor Green
    Write-Host "    Token: $($token.Substring(0, 20))..." -ForegroundColor Gray
} catch {
    Write-Host "  ✗ Login failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Test 4: Create Alert
Write-Host "Test 4: Create Alert" -ForegroundColor Yellow
try {
    $alertBody = @{
        tenant_id = $tenantId
        source = "test"
        title = "Test Alert - High CPU Usage"
        description = "CPU usage above 90% on production server"
        severity = "high"
        labels = @{}
        annotations = @{}
    } | ConvertTo-Json

    $headers = @{
        "Authorization" = "Bearer $token"
        "Content-Type" = "application/json"
    }

    $alert = Invoke-RestMethod -Uri "$baseUrl/alerts" -Method POST -Body $alertBody -Headers $headers
    Write-Host "  ✓ Alert created" -ForegroundColor Green
    Write-Host "    Alert ID: $($alert.id)" -ForegroundColor Gray
    Write-Host "    Severity: $($alert.severity)" -ForegroundColor Gray
} catch {
    Write-Host "  ✗ Alert creation failed: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""

# Test 5: Create Investigation
Write-Host "Test 5: Create Investigation" -ForegroundColor Yellow
try {
    $invBody = @{
        tenant_id = $tenantId
        title = "Test Investigation - Database Performance"
        description = "Investigating slow database queries"
    } | ConvertTo-Json

    $investigation = Invoke-RestMethod -Uri "$baseUrl/investigations" -Method POST -Body $invBody -Headers $headers
    Write-Host "  ✓ Investigation created" -ForegroundColor Green
    Write-Host "    Investigation ID: $($investigation.id)" -ForegroundColor Gray
    Write-Host "    Status: $($investigation.status)" -ForegroundColor Gray
    
    # Wait a bit for investigation to progress
    Write-Host "    Waiting for investigation to complete..." -ForegroundColor Gray
    Start-Sleep -Seconds 12
    
    # Check investigation status
    $invStatus = Invoke-RestMethod -Uri "$baseUrl/investigations/$($investigation.id)" -Method GET -Headers $headers
    Write-Host "    Final Status: $($invStatus.status)" -ForegroundColor Gray
    if ($invStatus.root_cause) {
        Write-Host "    Root Cause: $($invStatus.root_cause)" -ForegroundColor Gray
    }
} catch {
    Write-Host "  ✗ Investigation creation failed: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""

# Test 6: List Resources
Write-Host "Test 6: List Resources" -ForegroundColor Yellow
try {
    $alerts = Invoke-RestMethod -Uri "$baseUrl/alerts?tenant_id=$tenantId&limit=5" -Method GET -Headers $headers
    Write-Host "  ✓ Alerts: $($alerts.Count) found" -ForegroundColor Green
    
    $investigations = Invoke-RestMethod -Uri "$baseUrl/investigations?tenant_id=$tenantId&limit=5" -Method GET -Headers $headers
    Write-Host "  ✓ Investigations: $($investigations.Count) found" -ForegroundColor Green
    
    $incidents = Invoke-RestMethod -Uri "$baseUrl/incidents?tenant_id=$tenantId&limit=5" -Method GET -Headers $headers
    Write-Host "  ✓ Incidents: $($incidents.Count) found" -ForegroundColor Green
} catch {
    Write-Host "  ✗ Resource listing failed: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""
Write-Host "===================" -ForegroundColor Cyan
Write-Host "Test Complete!" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "1. Open http://localhost:3000 in your browser" -ForegroundColor White
Write-Host "2. Login with admin@astra.ai / admin123" -ForegroundColor White
Write-Host "3. Explore the dashboard and investigations" -ForegroundColor White
