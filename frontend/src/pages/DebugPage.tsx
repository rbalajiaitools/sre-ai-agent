/**
 * Debug page to check auth state and API connectivity
 */
import { useAuth } from '@/stores/authStore';
import { useIncidents } from '@/features/incidents/hooks';

export function DebugPage() {
  const auth = useAuth();
  const { data: incidents, isLoading, isError, error } = useIncidents();

  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold mb-4">Debug Information</h1>
      
      <div className="space-y-4">
        <div className="border p-4 rounded">
          <h2 className="font-semibold mb-2">Auth State</h2>
          <pre className="text-sm bg-gray-100 p-2 rounded overflow-auto">
            {JSON.stringify(auth, null, 2)}
          </pre>
        </div>

        <div className="border p-4 rounded">
          <h2 className="font-semibold mb-2">Incidents Query</h2>
          <p>Loading: {isLoading ? 'Yes' : 'No'}</p>
          <p>Error: {isError ? 'Yes' : 'No'}</p>
          {error && (
            <pre className="text-sm bg-red-100 p-2 rounded overflow-auto mt-2">
              {JSON.stringify(error, null, 2)}
            </pre>
          )}
          <p>Incidents count: {incidents?.length || 0}</p>
          {incidents && incidents.length > 0 && (
            <pre className="text-sm bg-gray-100 p-2 rounded overflow-auto mt-2 max-h-96">
              {JSON.stringify(incidents.slice(0, 3), null, 2)}
            </pre>
          )}
        </div>

        <div className="border p-4 rounded">
          <h2 className="font-semibold mb-2">LocalStorage</h2>
          <pre className="text-sm bg-gray-100 p-2 rounded overflow-auto">
            {localStorage.getItem('auth-storage')}
          </pre>
        </div>
      </div>
    </div>
  );
}
