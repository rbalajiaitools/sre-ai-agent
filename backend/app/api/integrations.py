"""Integration management API endpoints (ServiceNow, AWS, etc.)."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import get_db
from app.db import crud
from app.connectors.servicenow.client import ServiceNowClient
from app.connectors.servicenow.config import AuthType, ServiceNowConfig
from app.connectors.servicenow.models import IncidentFilter
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/settings", tags=["integrations"])


class IntegrationResponse(BaseModel):
    id: str
    name: str
    type: str
    is_active: bool
    created_at: str
    updated_at: str
    last_sync_at: str | None = None


class ServiceNowTestRequest(BaseModel):
    instance_url: str
    username: str
    password: str


class ServiceNowSaveRequest(BaseModel):
    tenant_id: str
    name: str
    instance_url: str
    username: str
    password: str


class CloudProviderTestRequest(BaseModel):
    provider: str
    credentials: dict


class CloudProviderSaveRequest(BaseModel):
    tenant_id: str
    name: str
    provider: str
    credentials: dict


class UpdateIntegrationRequest(BaseModel):
    name: str | None = None
    config: dict | None = None
    is_active: bool | None = None


@router.post("/servicenow/test")
async def test_servicenow(request: ServiceNowTestRequest):
    """Test ServiceNow connection with real API call."""
    try:
        instance_url = request.instance_url.strip()
        if not instance_url.startswith("https://"):
            return {"success": False, "message": "Instance URL must start with https://"}
        
        instance = instance_url.replace("https://", "").replace(".service-now.com", "").split("/")[0]
        
        logger.info("testing_servicenow_connection", instance=instance, username=request.username)
        
        config = ServiceNowConfig(
            instance=instance,
            auth_type=AuthType.BASIC,
            username=request.username,
            password=request.password,
        )
        
        client = ServiceNowClient(config)
        
        try:
            incident_filter = IncidentFilter(limit=1)
            incidents = await client.get_incidents(incident_filter)
            await client.close()
            
            logger.info("servicenow_connection_successful", instance=instance, incidents_count=len(incidents))
            
            return {
                "success": True,
                "message": f"Connection successful! Found {len(incidents)} incident(s) in your instance."
            }
            
        except Exception as e:
            await client.close()
            logger.error("servicenow_connection_failed", instance=instance, error=str(e))
            
            error_msg = str(e)
            if "401" in error_msg or "Unauthorized" in error_msg:
                return {"success": False, "message": "Authentication failed. Please check your username and password."}
            elif "404" in error_msg or "Not Found" in error_msg:
                return {"success": False, "message": "Instance not found. Please check your instance URL."}
            elif "timeout" in error_msg.lower():
                return {"success": False, "message": "Connection timeout. Please check your instance URL and network connection."}
            else:
                return {"success": False, "message": f"Connection failed: {error_msg}"}
                
    except Exception as e:
        logger.error("servicenow_test_error", error=str(e), error_type=type(e).__name__)
        return {"success": False, "message": f"Error: {str(e)}"}


@router.post("/servicenow")
async def save_servicenow(request: ServiceNowSaveRequest, db: AsyncSession = Depends(get_db)):
    """Save ServiceNow configuration to database."""
    try:
        instance_url = request.instance_url.strip()
        instance = instance_url.replace("https://", "").replace(".service-now.com", "").split("/")[0]
        
        logger.info("saving_servicenow_config", tenant_id=request.tenant_id, instance=instance)
        
        config = {
            "instance": instance,
            "instance_url": instance_url,
            "username": request.username,
            "password": request.password,
            "auth_type": "basic",
        }
        
        integration = await crud.create_integration(
            db=db,
            tenant_id=request.tenant_id,
            name=request.name,
            integration_type="servicenow",
            config=config
        )
        
        logger.info("servicenow_config_saved", tenant_id=request.tenant_id, integration_id=integration.id)
        
        return {
            "success": True,
            "message": "ServiceNow configuration saved successfully",
            "integration_id": integration.id
        }
        
    except Exception as e:
        logger.error("servicenow_save_error", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to save configuration: {str(e)}")


@router.post("/cloud-providers/test")
async def test_cloud_provider(request: CloudProviderTestRequest):
    """Test cloud provider connection with real API call."""
    try:
        if request.provider == "aws":
            import boto3
            from botocore.exceptions import ClientError, NoCredentialsError
            
            access_key = request.credentials.get("access_key_id")
            secret_key = request.credentials.get("secret_access_key")
            region = request.credentials.get("region", "us-east-1")
            
            if not all([access_key, secret_key]):
                return {"success": False, "message": "Missing AWS credentials (access key or secret key)"}
            
            logger.info("testing_aws_connection", region=region)
            
            try:
                sts = boto3.client(
                    'sts',
                    aws_access_key_id=access_key,
                    aws_secret_access_key=secret_key,
                    region_name=region
                )
                
                identity = sts.get_caller_identity()
                account_id = identity['Account']
                
                logger.info("aws_connection_successful", account_id=account_id)
                
                return {"success": True, "message": f"AWS connection successful! Account ID: {account_id}"}
                
            except NoCredentialsError:
                return {"success": False, "message": "Invalid AWS credentials"}
            except ClientError as e:
                error_code = e.response.get('Error', {}).get('Code', 'Unknown')
                error_msg = e.response.get('Error', {}).get('Message', str(e))
                
                logger.error("aws_connection_failed", error_code=error_code, error_msg=error_msg)
                
                if error_code == 'InvalidClientTokenId':
                    return {"success": False, "message": "Invalid AWS access key ID"}
                elif error_code == 'SignatureDoesNotMatch':
                    return {"success": False, "message": "Invalid AWS secret access key"}
                else:
                    return {"success": False, "message": f"AWS connection failed: {error_msg}"}
            except Exception as e:
                logger.error("aws_test_error", error=str(e))
                return {"success": False, "message": f"Connection failed: {str(e)}"}
        else:
            return {"success": False, "message": f"Provider {request.provider} not supported yet"}
            
    except Exception as e:
        logger.error("cloud_provider_test_error", error=str(e))
        return {"success": False, "message": f"Error: {str(e)}"}


@router.post("/cloud-providers")
async def save_cloud_provider(request: CloudProviderSaveRequest, db: AsyncSession = Depends(get_db)):
    """Save cloud provider configuration to database."""
    try:
        logger.info("saving_cloud_provider_config", tenant_id=request.tenant_id, provider=request.provider)
        
        integration = await crud.create_integration(
            db=db,
            tenant_id=request.tenant_id,
            name=request.name,
            integration_type=request.provider,
            config=request.credentials
        )
        
        logger.info("cloud_provider_config_saved", tenant_id=request.tenant_id, integration_id=integration.id)
        
        return {
            "success": True,
            "message": f"{request.provider.upper()} configuration saved successfully",
            "integration_id": integration.id
        }
        
    except Exception as e:
        logger.error("cloud_provider_save_error", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to save configuration: {str(e)}")


@router.get("/integrations", response_model=List[IntegrationResponse])
async def get_integrations(
    tenant_id: str = Query(...),
    type: str = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Get all integrations for tenant."""
    try:
        integrations = await crud.get_integrations(db, tenant_id, type)
        
        return [
            IntegrationResponse(
                id=i.id,
                name=i.name,
                type=i.type,
                is_active=i.is_active,
                created_at=i.created_at.isoformat(),
                updated_at=i.updated_at.isoformat(),
                last_sync_at=i.last_sync_at.isoformat() if i.last_sync_at else None
            )
            for i in integrations
        ]
    except Exception as e:
        logger.error("get_integrations_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/integrations/{integration_id}")
async def get_integration(integration_id: str, db: AsyncSession = Depends(get_db)):
    """Get integration by ID with decrypted config."""
    try:
        integration = await crud.get_integration(db, integration_id)
        
        if not integration:
            raise HTTPException(status_code=404, detail="Integration not found")
        
        config = crud.decrypt_integration_config(integration)
        safe_config = {k: v for k, v in config.items() if k not in ["password", "secret_key", "secret_access_key"]}
        
        return {
            "id": integration.id,
            "name": integration.name,
            "type": integration.type,
            "config": safe_config,
            "is_active": integration.is_active,
            "created_at": integration.created_at.isoformat(),
            "updated_at": integration.updated_at.isoformat(),
            "last_sync_at": integration.last_sync_at.isoformat() if integration.last_sync_at else None
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_integration_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/integrations/{integration_id}")
async def update_integration(
    integration_id: str,
    request: UpdateIntegrationRequest,
    db: AsyncSession = Depends(get_db)
):
    """Update integration."""
    try:
        integration = await crud.update_integration(
            db=db,
            integration_id=integration_id,
            name=request.name,
            config=request.config,
            is_active=request.is_active
        )
        
        if not integration:
            raise HTTPException(status_code=404, detail="Integration not found")
        
        return {"success": True, "message": "Integration updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("update_integration_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/integrations/{integration_id}")
async def delete_integration(integration_id: str, db: AsyncSession = Depends(get_db)):
    """Delete integration."""
    try:
        deleted = await crud.delete_integration(db, integration_id)
        
        if not deleted:
            raise HTTPException(status_code=404, detail="Integration not found")
        
        return {"success": True, "message": "Integration deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("delete_integration_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
