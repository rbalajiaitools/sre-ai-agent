/**
 * Incident Metadata - metadata grid display
 */
import { ServiceNowIncident } from '../types';

interface IncidentMetadataProps {
  incident: ServiceNowIncident;
}

export function IncidentMetadata({ incident }: IncidentMetadataProps) {
  return (
    <div>
      <h4 className="text-sm font-medium text-muted-foreground mb-3">
        Details
      </h4>
      <div className="grid grid-cols-2 gap-4 text-sm">
        <div>
          <p className="text-muted-foreground mb-1">CI Name</p>
          <p className="font-medium">{incident.cmdb_ci || 'N/A'}</p>
        </div>
        <div>
          <p className="text-muted-foreground mb-1">Assignment Group</p>
          <p className="font-medium">{incident.assignment_group || 'N/A'}</p>
        </div>
        <div>
          <p className="text-muted-foreground mb-1">Category</p>
          <p className="font-medium">{incident.category || 'N/A'}</p>
        </div>
        <div>
          <p className="text-muted-foreground mb-1">Subcategory</p>
          <p className="font-medium">{incident.subcategory || 'N/A'}</p>
        </div>
        <div>
          <p className="text-muted-foreground mb-1">Assigned To</p>
          <p className="font-medium">{incident.assigned_to || 'Unassigned'}</p>
        </div>
        <div>
          <p className="text-muted-foreground mb-1">Updated At</p>
          <p className="font-medium">
            {new Date(incident.updated_at).toLocaleString()}
          </p>
        </div>
      </div>
    </div>
  );
}
