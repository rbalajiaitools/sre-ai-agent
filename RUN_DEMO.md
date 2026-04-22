# Running the End-to-End Demo

## Prerequisites

Make sure all backend services are running before running the demo.

## Step-by-Step Instructions

### 1. Start Backend Services

Open a PowerShell terminal and run:

```powershell
cd astra-ai
.\start-all-services.ps1
```

Wait for all 11 services to show "Application startup complete" messages.

### 2. Run the Demo Script

Open a NEW PowerShell terminal and run:

```powershell
cd astra-ai
.\demo-e2e.ps1
```

The demo will:
- Bootstrap the system (or use existing setup)
- Authenticate
- Register 4 services
- Create 3 dependencies
- Configure AWS connector
- Create approval policy
- Ingest critical alert
- Start AI investigation
- Review hypotheses and evidence
- Suggest and execute remediation actions
- Query service health
- Test AI chat

### 3. View Results in Frontend

Open your browser to http://localhost:3000

Login with:
- Email: `admin@astra.ai`
- Password: `admin123`

Explore:
- Overview dashboard
- Investigations page
- Services page
- Service health dashboard
- AI chat interface

## Troubleshooting

### "Invalid credentials" error
- Make sure you ran the bootstrap endpoint first
- Or the system is already bootstrapped and you can login

### "Not Found" errors
- Services are not running
- Start services with `.\start-all-services.ps1`
- Wait for all services to be ready

### "Method Not Allowed" errors
- Check that the correct HTTP method is being used
- Verify the API endpoint exists

## Expected Output

When successful, you should see:
- [OK] messages for each step
- Service registrations
- Investigation completion
- Action execution
- Health dashboard results
- AI chat responses

## Next Steps

After the demo completes:
1. Open the frontend at http://localhost:3000
2. Explore the registered services
3. View the completed investigation
4. Try creating your own investigation
5. Use the AI chat interface
6. View service health dashboard
