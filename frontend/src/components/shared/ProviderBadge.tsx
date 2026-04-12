/**
 * Provider badge component
 */
import { Cloud, Server } from 'lucide-react';
import { ProviderType } from '@/types';

interface ProviderBadgeProps {
  provider: ProviderType;
}

const providerIcons = {
  [ProviderType.AWS]: Cloud,
  [ProviderType.AZURE]: Cloud,
  [ProviderType.GCP]: Cloud,
  [ProviderType.ON_PREM]: Server,
  [ProviderType.CUSTOM]: Server,
};

export function ProviderBadge({ provider }: ProviderBadgeProps) {
  const Icon = providerIcons[provider];

  return (
    <span className="inline-flex items-center gap-1 rounded bg-primary/10 px-2 py-0.5 text-xs font-medium text-primary">
      <Icon className="h-3 w-3" aria-hidden="true" />
      {provider.toUpperCase()}
    </span>
  );
}
