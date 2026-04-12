/**
 * Custom React Flow node for services
 */
import { memo } from 'react';
import { Handle, Position } from 'reactflow';
import { Cloud, Server, AlertCircle } from 'lucide-react';
import { ProviderType } from '@/types';
import type { ServiceNode } from '../types';

interface ServiceFlowNodeProps {
  data: ServiceNode;
  selected: boolean;
}

const providerIcons = {
  [ProviderType.AWS]: Cloud,
  [ProviderType.AZURE]: Cloud,
  [ProviderType.GCP]: Cloud,
  [ProviderType.ON_PREM]: Server,
  [ProviderType.CUSTOM]: Server,
};

const statusColors = {
  healthy: 'border-green-500 bg-green-500/10',
  degraded: 'border-yellow-500 bg-yellow-500/10',
  down: 'border-red-500 bg-red-500/10',
  unknown: 'border-gray-500 bg-gray-500/10',
};

const statusRingColors = {
  healthy: 'ring-green-500',
  degraded: 'ring-yellow-500',
  down: 'ring-red-500',
  unknown: 'ring-gray-500',
};

export const ServiceFlowNode = memo(({ data, selected }: ServiceFlowNodeProps) => {
  const Icon = providerIcons[data.provider] || Server;
  const statusColor = statusColors[data.status];
  const ringColor = statusRingColors[data.status];

  return (
    <div
      className={`rounded-lg border-2 bg-card p-4 shadow-md transition-all ${
        selected ? `ring-2 ${ringColor}` : ''
      }`}
      style={{ minWidth: 200 }}
    >
      <Handle type="target" position={Position.Top} className="!bg-primary" />

      <div className="space-y-2">
        {/* Service name */}
        <div className="font-semibold">{data.name}</div>

        {/* Provider badge */}
        <div className="flex items-center gap-2">
          <div className={`flex items-center gap-1 rounded px-2 py-0.5 text-xs ${statusColor}`}>
            <Icon className="h-3 w-3" aria-hidden="true" />
            <span>{data.provider.toUpperCase()}</span>
          </div>
          <span className="text-xs text-muted-foreground">{data.region}</span>
        </div>

        {/* Status and metrics */}
        <div className="flex items-center justify-between text-xs">
          <div className="flex items-center gap-1">
            <div
              className={`h-2 w-2 rounded-full ${
                data.status === 'healthy'
                  ? 'bg-green-500'
                  : data.status === 'degraded'
                  ? 'bg-yellow-500'
                  : data.status === 'down'
                  ? 'bg-red-500'
                  : 'bg-gray-500'
              }`}
              aria-hidden="true"
            />
            <span className="capitalize text-muted-foreground">{data.status}</span>
          </div>
          <span className="text-muted-foreground">{data.resource_count} resources</span>
        </div>

        {/* Incident badge */}
        {data.incident_count > 0 && (
          <div className="flex items-center gap-1 rounded bg-red-500/10 px-2 py-1 text-xs text-red-500">
            <AlertCircle className="h-3 w-3" aria-hidden="true" />
            <span>{data.incident_count} incident{data.incident_count > 1 ? 's' : ''}</span>
          </div>
        )}
      </div>

      <Handle type="source" position={Position.Bottom} className="!bg-primary" />
    </div>
  );
});

ServiceFlowNode.displayName = 'ServiceFlowNode';
