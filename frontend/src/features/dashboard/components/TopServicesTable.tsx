/**
 * Top services table component
 */
import { useNavigate } from 'react-router-dom';
import { LoadingSpinner } from '@/components/shared/LoadingSpinner';
import { useTopServices } from '../hooks';

export function TopServicesTable() {
  const navigate = useNavigate();
  const servicesQuery = useTopServices(10);

  if (servicesQuery.isLoading) {
    return <LoadingSpinner size="sm" />;
  }

  if (servicesQuery.isError) {
    return (
      <div className="p-4 text-center">
        <p className="text-sm text-red-500">Failed to load services</p>
      </div>
    );
  }

  const services = servicesQuery.data || [];

  return (
    <div className="space-y-4">
      <h3 className="font-semibold">Top Recurring Services</h3>

      {services.length === 0 ? (
        <p className="py-8 text-center text-sm text-muted-foreground">No data available</p>
      ) : (
        <div className="overflow-auto">
          <table className="w-full">
            <thead className="border-b">
              <tr>
                <th className="p-2 text-left text-xs font-medium text-muted-foreground">Service</th>
                <th className="p-2 text-left text-xs font-medium text-muted-foreground">Incidents</th>
                <th className="p-2 text-left text-xs font-medium text-muted-foreground">Avg Resolution</th>
                <th className="p-2 text-left text-xs font-medium text-muted-foreground">Last Incident</th>
              </tr>
            </thead>
            <tbody>
              {services.map((service) => (
                <tr
                  key={service.service_name}
                  onClick={() => navigate(`/topology?tab=map&service=${encodeURIComponent(service.service_name)}`)}
                  className="cursor-pointer border-b transition-colors hover:bg-muted/50"
                  role="button"
                  tabIndex={0}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                      e.preventDefault();
                      navigate(`/topology?tab=map&service=${encodeURIComponent(service.service_name)}`);
                    }
                  }}
                  aria-label={`View ${service.service_name} in topology`}
                >
                  <td className="p-2 text-sm font-medium">{service.service_name}</td>
                  <td className="p-2 text-sm">{service.incident_count}</td>
                  <td className="p-2 text-sm">{service.avg_resolution_hours.toFixed(1)}h</td>
                  <td className="p-2 text-sm text-muted-foreground">
                    {new Date(service.last_incident_at).toLocaleDateString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
