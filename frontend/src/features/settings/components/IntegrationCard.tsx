/**
 * Integration Card Component - Display individual integration card
 */
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

interface IntegrationCardProps {
  integration: {
    id: string;
    name: string;
    description: string;
    category: string;
    icon: string;
    iconColor: string;
    available?: boolean;
    status?: 'connected' | 'warning';
    statusLabel?: string;
  };
  viewMode: 'grid' | 'list';
  onClick: () => void;
}

export function IntegrationCard({ integration, viewMode, onClick }: IntegrationCardProps) {
  const isConnected = integration.status === 'connected';
  const isAvailable = integration.available !== false;

  if (viewMode === 'list') {
    return (
      <Card
        className={`flex items-center gap-4 p-4 transition-all ${
          isAvailable ? 'cursor-pointer hover:border-gray-400 hover:shadow-sm' : 'opacity-60'
        }`}
        onClick={onClick}
      >
        <div className={`flex h-12 w-12 items-center justify-center rounded-lg ${integration.iconColor} text-white text-xl font-bold flex-shrink-0`}>
          {integration.icon}
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <h3 className="font-semibold text-gray-900">{integration.name}</h3>
            {integration.statusLabel && (
              <Badge
                variant={integration.status === 'connected' ? 'default' : 'secondary'}
                className={
                  integration.status === 'connected'
                    ? 'bg-yellow-100 text-yellow-800 hover:bg-yellow-100'
                    : 'bg-gray-100 text-gray-700'
                }
              >
                {integration.statusLabel}
              </Badge>
            )}
          </div>
          <p className="mt-1 text-sm text-gray-500 line-clamp-1">{integration.description}</p>
        </div>
      </Card>
    );
  }

  return (
    <Card
      className={`group relative flex flex-col p-5 transition-all ${
        isAvailable ? 'cursor-pointer hover:border-gray-400 hover:shadow-md' : 'opacity-60'
      }`}
      onClick={onClick}
    >
      {/* Status Badge */}
      {integration.statusLabel && (
        <div className="absolute right-4 top-4">
          <Badge
            variant={integration.status === 'connected' ? 'default' : 'secondary'}
            className={
              integration.status === 'connected'
                ? 'bg-yellow-100 text-yellow-800 hover:bg-yellow-100'
                : 'bg-gray-100 text-gray-700'
            }
          >
            {integration.statusLabel}
          </Badge>
        </div>
      )}

      {/* Icon */}
      <div className={`mb-4 flex h-14 w-14 items-center justify-center rounded-xl ${integration.iconColor} text-white text-2xl font-bold`}>
        {integration.icon}
      </div>

      {/* Content */}
      <div className="flex-1">
        <h3 className="mb-2 font-semibold text-gray-900">{integration.name}</h3>
        <p className="text-sm text-gray-500 line-clamp-2">{integration.description}</p>
      </div>
    </Card>
  );
}
