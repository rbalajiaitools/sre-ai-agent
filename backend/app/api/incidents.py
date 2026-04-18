"""Incident management API endpoints."""

from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.db.base import get_db
from app.db import crud
from app.connectors.servicenow.client import ServiceNowClient
from app.connectors.servicenow.config import AuthType, ServiceNowConfig
from app.connectors.servicenow.connector import ServiceNowConnector
from app.connectors.servicenow.models import IncidentFilter
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/incidents", tags=["incidents"])


class BulkDeleteRequest(BaseModel):
    """Request model for bulk delete."""
    incident_ids: List[str]

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
                    
                    # Get filter settings from config
                    from app.core.config import get_settings
                    settings = get_settings()
                    filter_mode = settings.servicenow_incident_filter_mode.lower()
                    
                    # Build incident filter based on mode
                    if filter_mode == "numbers" and settings.servicenow_incident_filter_numbers:
                        # Filter by specific incident numbers
                        incident_numbers = [n.strip() for n in settings.servicenow_incident_filter_numbers.split(",")]
                        incident_filter = IncidentFilter(
                            limit=50,
                            incident_numbers=incident_numbers
                        )
                        logger.info("using_incident_numbers_filter", numbers=incident_numbers)
                    elif filter_mode == "date":
                        # Filter by date (default)
                        from datetime import datetime, timezone
                        try:
                            filter_date_str = settings.servicenow_incident_filter_date
                            filter_date = datetime.strptime(filter_date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
                        except Exception:
                            # Fallback to default date
                            filter_date = datetime(2026, 4, 1, tzinfo=timezone.utc)
                        
                        incident_filter = IncidentFilter(
                            limit=50,
                            updated_after=filter_date
                        )
                        logger.info("using_date_filter", date=filter_date.isoformat())
                    else:
                        # No filter - get all incidents
                        incident_filter = IncidentFilter(limit=50)
                        logger.info("using_no_filter")
                    
                    raw_incidents = await client.get_incidents(incident_filter)
                    await client.close()
                    
                    temp_connector = ServiceNowConnector(redis_client=None)
                    incidents = [temp_connector._normalize_incident(raw, UUID('00000000-0000-0000-0000-000000000000')) for raw in raw_incidents]
                
                # Get list of sys_ids that exist in ServiceNow
                servicenow_sys_ids = {incident.sys_id for incident in incidents}
                
                # Get existing incidents from DB
                existing_incidents = await crud.get_incidents(db, tenant_id)
                existing_sys_ids = {inc.sys_id for inc in existing_incidents}
                
                # Delete incidents from DB that no longer exist in ServiceNow
                # (these were deleted from ServiceNow)
                deleted_sys_ids = existing_sys_ids - servicenow_sys_ids
                for sys_id in deleted_sys_ids:
                    incident_to_delete = await crud.get_incident_by_sys_id(db, sys_id, tenant_id)
                    if incident_to_delete:
                        await crud.delete_incident(db, incident_to_delete.id)
                        logger.info("deleted_incident_not_in_servicenow", sys_id=sys_id)
                
                # Upsert incidents from ServiceNow
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



@router.delete("/{incident_id}")
async def delete_incident(
    incident_id: str,
    tenant_id: str = Query(...),
    db: AsyncSession = Depends(get_db)
):
    """Delete a single incident from both ServiceNow and local DB."""
    try:
        logger.info("deleting_incident", incident_id=incident_id, tenant_id=tenant_id)
        
        # Get incident by sys_id (incident_id is actually sys_id from frontend)
        incident = await crud.get_incident_by_sys_id(db, incident_id, tenant_id)
        if not incident:
            raise HTTPException(status_code=404, detail="Incident not found")
        
        # Try to delete from ServiceNow first
        servicenow_deleted = False
        try:
            integrations = await crud.get_integrations(db, tenant_id, "servicenow")
            integration = next((i for i in integrations if i.is_active), None)
            
            if integration:
                config_dict = crud.decrypt_integration_config(integration)
                sn_config = ServiceNowConfig(
                    instance=config_dict["instance"],
                    auth_type=AuthType.BASIC,
                    username=config_dict["username"],
                    password=config_dict["password"],
                )
                
                client = ServiceNowClient(sn_config)
                await client.delete_incident(incident.sys_id)
                await client.close()
                servicenow_deleted = True
                logger.info("incident_deleted_from_servicenow", incident_id=incident_id)
        except Exception as sn_error:
            logger.warning("failed_to_delete_from_servicenow", incident_id=incident_id, error=str(sn_error))
        
        # Delete from local DB using database ID
        await crud.delete_incident(db, incident.id)
        
        logger.info("incident_deleted", incident_id=incident_id, servicenow_deleted=servicenow_deleted)
        return {
            "success": True, 
            "message": "Incident deleted successfully" if servicenow_deleted else "Incident deleted from local DB only (ServiceNow deletion failed)",
            "servicenow_deleted": servicenow_deleted
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("delete_incident_error", incident_id=incident_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to delete incident: {str(e)}")


@router.post("/bulk-delete")
async def bulk_delete_incidents(
    request: BulkDeleteRequest,
    tenant_id: str = Query(...),
    db: AsyncSession = Depends(get_db)
):
    """Delete multiple incidents in bulk from both ServiceNow and local DB."""
    try:
        logger.info("bulk_deleting_incidents", count=len(request.incident_ids), tenant_id=tenant_id)
        
        # Get ServiceNow client once for all deletions
        sn_client = None
        try:
            integrations = await crud.get_integrations(db, tenant_id, "servicenow")
            integration = next((i for i in integrations if i.is_active), None)
            
            if integration:
                config_dict = crud.decrypt_integration_config(integration)
                sn_config = ServiceNowConfig(
                    instance=config_dict["instance"],
                    auth_type=AuthType.BASIC,
                    username=config_dict["username"],
                    password=config_dict["password"],
                )
                sn_client = ServiceNowClient(sn_config)
        except Exception as sn_error:
            logger.warning("failed_to_initialize_servicenow_client", error=str(sn_error))
        
        deleted_count = 0
        failed_count = 0
        servicenow_deleted_count = 0
        
        for incident_sys_id in request.incident_ids:
            try:
                # Get incident by sys_id (incident_ids are actually sys_ids from frontend)
                incident = await crud.get_incident_by_sys_id(db, incident_sys_id, tenant_id)
                if not incident:
                    failed_count += 1
                    logger.warning("incident_not_found_for_delete", incident_id=incident_sys_id)
                    continue
                
                # Try to delete from ServiceNow
                if sn_client:
                    try:
                        await sn_client.delete_incident(incident.sys_id)
                        servicenow_deleted_count += 1
                    except Exception as sn_error:
                        logger.warning("failed_to_delete_from_servicenow", incident_id=incident_sys_id, error=str(sn_error))
                
                # Delete from local DB using database ID
                await crud.delete_incident(db, incident.id)
                deleted_count += 1
                
            except Exception as e:
                failed_count += 1
                logger.error("failed_to_delete_incident", incident_id=incident_sys_id, error=str(e))
        
        # Close ServiceNow client
        if sn_client:
            try:
                await sn_client.close()
            except Exception:
                pass
        
        logger.info("bulk_delete_complete", deleted=deleted_count, failed=failed_count, servicenow_deleted=servicenow_deleted_count)
        
        return {
            "success": True,
            "deleted_count": deleted_count,
            "failed_count": failed_count,
            "servicenow_deleted_count": servicenow_deleted_count,
            "message": f"Deleted {deleted_count} incident(s) from local DB ({servicenow_deleted_count} from ServiceNow), {failed_count} failed"
        }
        
    except Exception as e:
        logger.error("bulk_delete_error", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to bulk delete incidents: {str(e)}")
