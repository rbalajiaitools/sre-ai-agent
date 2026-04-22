# ASTRA AI - End-to-End Demo Script
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "ASTRA AI - End-to-End Demo" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$baseUrl = "http://localhost:8000/api/v1"
$token = ""
$tenantId = ""

# Step 1: Bootstrap System
Write-Host "Step 1: Bootstrap System" -ForegroundColor Yellow
Write-Host "----------------------------------------" -ForegroundColor Gray
try {
    $bootstrap = Invoke-RestMethod -Uri "$baseUrl/bootstrap" -Method POST -ContentType "application/json"
    Write-Host "[OK] System bootstrapped" -ForegroundColor Green
    Write-Host "  Tenant ID: $($bootstrap.tenant_id)" -ForegroundColor Gray
    Write-Host "  Admin: $($bootstrap.admin_email)" -ForegroundColor Gray
    $tenantId = $bootstrap.tenant_id
}
catch {
    if ($_.Exception.Response.StatusCode -eq 400) {
        Write-Host "[INFO] System already bootstrapped" -ForegroundColor Cyan
        # Get tenant from users
        $users = Invoke-RestMethod -Uri "$baseUrl/users" -Method GET
        if ($users.Count -gt 0) {
            $tenantId = $users[0].tenant_id
            Write-Host "  Using tenant: $tenantId" -ForegroundColor Gray
        }
    }
}
Write-Host ""

# Step 2: Login
Write-Host "Step 2: Authenticate" -ForegroundColor Yellow
Write-Host "----------------------------------------" -ForegroundColor Gray
$loginBody = @{
    email = "admin@astra.ai"
    password = "admin123"
} | ConvertTo-Json

$login = Invoke-RestMethod -Uri "$baseUrl/auth/login" -Method POST -Body $loginBody -ContentType "application/json"
$token = $login.access_token
$headers = @{
    "Authorization" = "Bearer $token"
    "Content-Type" = "application/json"
}
Write-Host "[OK] Logged in as $($login.email)" -ForegroundColor Green
Write-Host ""

# Step 3: Register Services
Write-Host "Step 3: Register Services in Knowledge Graph" -ForegroundColor Yellow
Write-Host "----------------------------------------" -ForegroundColor Gray
$services = @(
    @{name="user-service"; type="api"; description="User management API"},
    @{name="auth-service"; type="api"; description="Authentication service"},
    @{name="payment-service"; type="api"; description="Payment processing"},
    @{name="database"; type="database"; description="PostgreSQL database"}
)

$serviceIds = @{}
foreach ($svc in $services) {
    $body = @{
        tenant_id = $tenantId
        name = $svc.name
        service_type = $svc.type
        description = $svc.description
        metadata = @{}
    } | ConvertTo-Json

    $result = Invoke-RestMethod -Uri "$baseUrl/services" -Method POST -Body $body -Headers $headers
    $serviceIds[$svc.name] = $result.id
    Write-Host "  [OK] Registered: $($svc.name)" -ForegroundColor Green
}
Write-Host ""

# Step 4: Create Dependencies
Write-Host "Step 4: Create Service Dependencies" -ForegroundColor Yellow
Write-Host "----------------------------------------" -ForegroundColor Gray
$dependencies = @(
    @{from="user-service"; to="auth-service"; type="sync"},
    @{from="user-service"; to="database"; type="sync"},
    @{from="payment-service"; to="database"; type="sync"}
)

foreach ($dep in $dependencies) {
    $body = @{
        tenant_id = $tenantId
        from_service_id = $serviceIds[$dep.from]
        to_service_id = $serviceIds[$dep.to]
        dependency_type = $dep.type
    } | ConvertTo-Json

    Invoke-RestMethod -Uri "$baseUrl/dependencies" -Method POST -Body $body -Headers $headers | Out-Null
    Write-Host "  [OK] $($dep.from) -> $($dep.to)" -ForegroundColor Green
}
Write-Host ""

# Step 5: Create Connector
Write-Host "Step 5: Configure AWS Connector" -ForegroundColor Yellow
Write-Host "----------------------------------------" -ForegroundColor Gray
$connectorBody = @{
    tenant_id = $tenantId
    name = "AWS Production"
    connector_type = "aws"
    config = @{
        region = "us-east-1"
        access_key_id = "DEMO_KEY"
        secret_access_key = "DEMO_SECRET"
    }
} | ConvertTo-Json

$connector = Invoke-RestMethod -Uri "$baseUrl/connectors" -Method POST -Body $connectorBody -Headers $headers
Write-Host "[OK] Connector created: $($connector.name)" -ForegroundColor Green
Write-Host ""

# Step 6: Create Policy
Write-Host "Step 6: Create Approval Policy" -ForegroundColor Yellow
Write-Host "----------------------------------------" -ForegroundColor Gray
$policyBody = @{
    tenant_id = $tenantId
    name = "Production Changes Require Approval"
    policy_type = "approval"
    rules = @{
        environment = "production"
        requires_approval = $true
        approvers = @("admin@astra.ai")
    }
} | ConvertTo-Json

$policy = Invoke-RestMethod -Uri "$baseUrl/policies" -Method POST -Body $policyBody -Headers $headers
Write-Host "[OK] Policy created: $($policy.name)" -ForegroundColor Green
Write-Host ""

# Step 7: Create Alert
Write-Host "Step 7: Ingest Critical Alert" -ForegroundColor Yellow
Write-Host "----------------------------------------" -ForegroundColor Gray
$alertBody = @{
    tenant_id = $tenantId
    source = "cloudwatch"
    title = "High CPU Usage on user-service"
    description = "CPU usage exceeded 90% for 5 minutes"
    severity = "critical"
    labels = @{
        service = "user-service"
        environment = "production"
    }
    annotations = @{
        runbook = "https://runbooks.example.com/high-cpu"
    }
} | ConvertTo-Json

$alert = Invoke-RestMethod -Uri "$baseUrl/alerts" -Method POST -Body $alertBody -Headers $headers
Write-Host "[OK] Alert created: $($alert.title)" -ForegroundColor Green
Write-Host "  Severity: $($alert.severity)" -ForegroundColor Gray
Write-Host "  Alert ID: $($alert.id)" -ForegroundColor Gray
Write-Host ""

# Step 8: Create Investigation
Write-Host "Step 8: Start AI Investigation" -ForegroundColor Yellow
Write-Host "----------------------------------------" -ForegroundColor Gray
$invBody = @{
    tenant_id = $tenantId
    title = "Investigate High CPU on user-service"
    description = "Automated investigation triggered by critical alert"
} | ConvertTo-Json

$investigation = Invoke-RestMethod -Uri "$baseUrl/investigations" -Method POST -Body $invBody -Headers $headers
Write-Host "[OK] Investigation started: $($investigation.id)" -ForegroundColor Green
Write-Host "  Status: $($investigation.status)" -ForegroundColor Gray
Write-Host ""

# Step 9: Wait for Investigation
Write-Host "Step 9: Monitor Investigation Progress" -ForegroundColor Yellow
Write-Host "----------------------------------------" -ForegroundColor Gray
Write-Host "  Waiting for investigation to complete..." -ForegroundColor Gray
Start-Sleep -Seconds 12

$invResult = Invoke-RestMethod -Uri "$baseUrl/investigations/$($investigation.id)" -Method GET -Headers $headers
Write-Host "[OK] Investigation completed" -ForegroundColor Green
Write-Host "  Status: $($invResult.status)" -ForegroundColor Gray
if ($invResult.root_cause) {
    Write-Host "  Root Cause: $($invResult.root_cause)" -ForegroundColor Gray
}
if ($invResult.confidence_level) {
    Write-Host "  Confidence: $($invResult.confidence_level)" -ForegroundColor Gray
}
Write-Host ""

# Step 10: Get Hypotheses
Write-Host "Step 10: Review Hypotheses" -ForegroundColor Yellow
Write-Host "----------------------------------------" -ForegroundColor Gray
$hypotheses = Invoke-RestMethod -Uri "$baseUrl/investigations/$($investigation.id)/hypotheses" -Method GET -Headers $headers
Write-Host "[OK] Found $($hypotheses.Count) hypotheses" -ForegroundColor Green
foreach ($hyp in $hypotheses) {
    Write-Host "  - $($hyp.hypothesis)" -ForegroundColor Gray
    if ($hyp.is_validated) {
        Write-Host "    [VALIDATED]" -ForegroundColor Green
    }
}
Write-Host ""

# Step 11: Get Evidence
Write-Host "Step 11: Review Evidence" -ForegroundColor Yellow
Write-Host "----------------------------------------" -ForegroundColor Gray
$evidence = Invoke-RestMethod -Uri "$baseUrl/investigations/$($investigation.id)/evidence" -Method GET -Headers $headers
Write-Host "[OK] Found $($evidence.Count) evidence items" -ForegroundColor Green
foreach ($ev in $evidence) {
    Write-Host "  - [$($ev.source)] $($ev.content)" -ForegroundColor Gray
}
Write-Host ""

# Step 12: Suggest Actions
Write-Host "Step 12: Get Remediation Suggestions" -ForegroundColor Yellow
Write-Host "----------------------------------------" -ForegroundColor Gray
$suggestions = Invoke-RestMethod -Uri "$baseUrl/actions/suggest?investigation_id=$($investigation.id)" -Method POST -Headers $headers
Write-Host "[OK] Found $($suggestions.suggestions.Count) suggested actions" -ForegroundColor Green
foreach ($sug in $suggestions.suggestions) {
    Write-Host "  - $($sug.title) (confidence: $($sug.confidence))" -ForegroundColor Gray
}
Write-Host ""

# Step 13: Create Action
Write-Host "Step 13: Create Remediation Action" -ForegroundColor Yellow
Write-Host "----------------------------------------" -ForegroundColor Gray
$actionBody = @{
    investigation_id = $investigation.id
    action_type = "restart_service"
    title = "Restart user-service"
    description = "Restart to clear memory leak"
    config = @{
        service = "user-service"
        environment = "production"
    }
    requires_approval = $true
} | ConvertTo-Json

$action = Invoke-RestMethod -Uri "$baseUrl/actions" -Method POST -Body $actionBody -Headers $headers
Write-Host "[OK] Action created: $($action.title)" -ForegroundColor Green
Write-Host "  Status: $($action.status)" -ForegroundColor Gray
Write-Host ""

# Step 14: Approve Action
Write-Host "Step 14: Approve Action" -ForegroundColor Yellow
Write-Host "----------------------------------------" -ForegroundColor Gray
$approvalBody = @{
    approved_by = "admin@astra.ai"
    approved = $true
} | ConvertTo-Json

Invoke-RestMethod -Uri "$baseUrl/actions/$($action.id)/approve" -Method POST -Body $approvalBody -Headers $headers | Out-Null
Write-Host "[OK] Action approved" -ForegroundColor Green
Write-Host ""

# Step 15: Execute Action
Write-Host "Step 15: Execute Action" -ForegroundColor Yellow
Write-Host "----------------------------------------" -ForegroundColor Gray
$execution = Invoke-RestMethod -Uri "$baseUrl/actions/$($action.id)/execute" -Method POST -Headers $headers
Write-Host "[OK] Action executed" -ForegroundColor Green
Write-Host "  Execution ID: $($execution.execution_id)" -ForegroundColor Gray
Write-Host ""

# Step 16: Query Health Dashboard
Write-Host "Step 16: Check Service Health" -ForegroundColor Yellow
Write-Host "----------------------------------------" -ForegroundColor Gray
$health = Invoke-RestMethod -Uri "$baseUrl/graph/health-dashboard?tenant_id=$tenantId" -Method GET -Headers $headers
Write-Host "[OK] Overall Health: $([math]::Round($health.overall_health * 100))%" -ForegroundColor Green
foreach ($svc in $health.services) {
    $color = if ($svc.status -eq "healthy") { "Green" } elseif ($svc.status -eq "degraded") { "Yellow" } else { "Red" }
    Write-Host "  - $($svc.name): $($svc.status) ($([math]::Round($svc.health_score * 100))%)" -ForegroundColor $color
}
Write-Host ""

# Step 17: AI Chat Query
Write-Host "Step 17: AI Dependency Query" -ForegroundColor Yellow
Write-Host "----------------------------------------" -ForegroundColor Gray
$chatBody = @{
    tenant_id = $tenantId
    query = "What services depend on the database?"
} | ConvertTo-Json

$chatResponse = Invoke-RestMethod -Uri "$baseUrl/ai/dependency-query" -Method POST -Body $chatBody -Headers $headers
Write-Host "[OK] Query: $($chatResponse.query)" -ForegroundColor Green
Write-Host "  Answer: $($chatResponse.answer)" -ForegroundColor Gray
Write-Host ""

# Summary
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Demo Complete!" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Summary:" -ForegroundColor Yellow
Write-Host "  - Services registered: $($services.Count)" -ForegroundColor White
Write-Host "  - Dependencies created: $($dependencies.Count)" -ForegroundColor White
Write-Host "  - Connectors configured: 1" -ForegroundColor White
Write-Host "  - Policies created: 1" -ForegroundColor White
Write-Host "  - Alerts ingested: 1" -ForegroundColor White
Write-Host "  - Investigations completed: 1" -ForegroundColor White
Write-Host "  - Actions executed: 1" -ForegroundColor White
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "  1. Open http://localhost:3000 in your browser" -ForegroundColor White
Write-Host "  2. Login with admin@astra.ai / admin123" -ForegroundColor White
Write-Host "  3. Explore the dashboard and features" -ForegroundColor White
Write-Host "  4. Try the AI chat interface" -ForegroundColor White
Write-Host "  5. View service health dashboard" -ForegroundColor White
Write-Host ""
