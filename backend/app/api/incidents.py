"""Incident management API endpoints."""

from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import get_db
from app.db import crud
from app.connectors.servicenow.client import ServiceNowClient
from app.connectors.servicenow.config import AuthType, ServiceNowConfig
from app.connectors.servicenow.connector import ServiceNowConnector
from app.connectors.servicenow.models import IncidentFilter
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/incidents", tags=["incidents"])

# Global connector instance
_servicenow_connector: ServiceNowConnector = None


def get_servicenow_connector() -> ServiceNowConnector:
    """Get or create ServiceNow connector."""
    global _servicenow_connector
    if _servicenow_connector is None:
        _servicenow_connector = ServiceNowConnector(redis_client=None)
    return _servicenow_connector


@router.get("")
async def get_incidents(
    tenant_id: str = Query(...),
    refresh: bool = Query(False),
    db: AsyncSession = Depends(get_db)
):
    """Get incidents - from database or refresh from ServiceNow."""
    try:
        logger.info("fetching_incidents", tenant_id=tenant_id, refresh=refresh)
        
        integrations = await crud.get_integrations(db, tenant_id, "servicenow")
        
        if not integrations:
            logger.warning("no_servicenow_integration", tenant_id=tenant_id)
            return []
        
        integration = next((i for i in integrations if i.is_active), None)
        if not integration:
            logger.warning("no_active_servicenow_integration", tenant_id=tenant_id)
            return []
        
        if refresh:
            try:
                config_dict = crud.decrypt_integration_config(integration)
                
                sn_config = ServiceNowConfig(
                    instance=config_dict["instance"],
                    auth_type=AuthType.BASIC,
                    username=config_dict["username"],
                    password=config_dict["password"],
                )
                
                connector = get_servicenow_connector()
                try:
                    tenant_uuid = UUID(tenant_id)
                    connector.register_tenant(tenant_uuid, sn_config)
                    incidents = await connector.get_open_incidents(tenant_uuid)
                except ValueError:
                    logger.warning("invalid_uuid_using_direct_client", tenant_id=tenant_id)
                    client = ServiceNowClient(sn_config)
                    incident_filter = IncidentFilter(limit=50)
                    raw_incidents = await client.get_incidents(incident_filter)
                    await client.close()
                    
                    temp_connector = ServiceNowConnector(redis_client=None)
                    incidents = [temp_connector._normalize_incident(raw, UUID('00000000-0000-0000-0000-000000000000')) for raw in raw_incidents]
                
                for incident in incidents:
                    try:
                        incident_data = {
                            "sys_id": incident.sys_id,
                            "number": incident.number,
                            "short_description": incident.short_description,
                            "description": incident.description,
                            "priority": int(incident.priority.value) if hasattr(incident.priority, 'value') else int(incident.priority),
                            "state": incident.state.value if hasattr(incident.state, 'value') else incident.state,
                            "category": incident.category,
                            "subcategory": incident.subcategory,
                            "cmdb_ci": incident.cmdb_ci,
                            "assignment_group": incident.assignment_group,
                            "assigned_to": incident.assigned_to,
                            "opened_at": incident.opened_at,
                            "updated_at": incident.updated_at,
                            "resolved_at": incident.resolved_at,
                        }
                        
                        await crud.upsert_incident(
                            db=db,
                            tenant_id=tenant_id,
                            integration_id=integration.id,
                            incident_data=incident_data
                        )
                    except Exception as incident_error:
                        logger.error("failed_to_store_incident", incident_number=incident.number if hasattr(incident, 'number') else 'unknown', error=str(incident_error))
                        continue
                
                try:
                    await crud.update_integration(
                        db=db,
                        integration_id=integration.id,
                        is_active=True
                    )
                except Exception as update_error:
                    logger.warning("failed_to_update_last_sync", error=str(update_error))
                
                logger.info("incidents_refreshed", tenant_id=tenant_id, count=len(incidents))
                
            except Exception as e:
                logger.error("incident_refresh_error", tenant_id=tenant_id, error=str(e))
        
        db_incidents = await crud.get_incidents(db, tenant_id)
        
        incidents_dict = [
            {
                "sys_id": i.sys_id,
                "number": i.number,
                "short_description": i.short_description,
                "description": i.description,
                "priority": i.priority,
                "state": i.state,
                "opened_at": i.opened_at.isoformat() if i.opened_at else None,
                "updated_at": i.updated_at.isoformat() if i.updated_at else None,
                "assigned_to": i.assigned_to,
                "assignment_group": i.assignment_group,
                "cmdb_ci": i.cmdb_ci,
                "work_notes": [],
                "investigation_status": i.investigation_status,
                "investigation_id": i.investigation_id,
            }
            for i in db_incidents
        ]
        
        logger.info("incidents_returned", tenant_id=tenant_id, count=len(incidents_dict))
        
        return incidents_dict
        
    except Exception as e:
        logger.error("get_incidents_error", tenant_id=tenant_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to fetch incidents: {str(e)}")
