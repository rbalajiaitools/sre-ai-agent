/**
 * Incident Picker Modal - select incident to attach
 */
import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Search, RefreshCw, Loader2 } from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Incident, IncidentPriority } from '@/types';
import { getIncidents } from '@/api/incidents';
import { useTenant } from '@/stores/authStore';
import { cn } from '@/lib/utils';

interface IncidentPickerModalProps {
  open: boolean;
  onClose: () => void;
  onSelect: (incident: Incident) => void;
}

export function IncidentPickerModal({
  open,
  onClose,
  onSelect,
}: IncidentPickerModalProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const tenant = useTenant();

  const { data: incidents, isLoading, refetch, isRefetching } = useQuery({
    queryKey: ['incidents', tenant?.id],
    queryFn: () => getIncidents(tenant!.id),
    enabled: !!tenant && open,
  });

  const filteredIncidents = incidents?.filter(
    (incident) =>
      incident.number.toLowerCase().includes(searchQuery.toLowerCase()) ||
      incident.short_description
        .toLowerCase()
        .includes(searchQuery.toLowerCase())
  );

  const handleSelect = (incident: Incident) => {
    onSelect(incident);
    onClose();
  };

  const getPriorityColor = (priority: IncidentPriority) => {
    switch (priority) {
      case IncidentPriority.P1:
        return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200';
      case IncidentPriority.P2:
        return 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200';
      case IncidentPriority.P3:
        return 'bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-200';
      default:
        return 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200';
    }
  };

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl max-h-[80vh] flex flex-col">
        <DialogHeader>
          <DialogTitle>Attach Incident</DialogTitle>
        </DialogHeader>

        {/* Search and refresh */}
        <div className="flex gap-2">
          <div className="relative flex-1">
            <Search
              className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground"
              aria-hidden="true"
            />
            <Input
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search incidents..."
              className="pl-9"
              aria-label="Search incidents"
            />
          </div>
          <Button
            variant="outline"
            size="icon"
            onClick={() => refetch()}
            disabled={isRefetching}
            aria-label="Refresh incidents"
          >
            <RefreshCw
              className={cn('h-4 w-4', isRefetching && 'animate-spin')}
              aria-hidden="true"
            />
          </Button>
        </div>

        {/* Incident list */}
        <div className="flex-1 overflow-y-auto border rounded-md">
          {isLoading ? (
            <div className="flex items-center justify-center h-32">
              <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" aria-label="Loading" />
            </div>
          ) : filteredIncidents && filteredIncidents.length > 0 ? (
            <div className="divide-y">
              {filteredIncidents.map((incident) => (
                <button
                  key={incident.sys_id}
                  onClick={() => handleSelect(incident)}
                  className="w-full text-left p-4 hover:bg-muted transition-colors"
                >
                  <div className="flex items-start justify-between gap-2 mb-2">
                    <span className="font-mono text-sm font-medium">
                      {incident.number}
                    </span>
                    <span
                      className={cn(
                        'px-2 py-0.5 rounded text-xs font-medium',
                        getPriorityColor(incident.priority)
                      )}
                    >
                      P{incident.priority}
                    </span>
                  </div>
                  <p className="text-sm font-medium mb-1">
                    {incident.short_description}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    Opened {new Date(incident.opened_at).toLocaleDateString()}
                  </p>
                </button>
              ))}
            </div>
          ) : (
            <div className="flex items-center justify-center h-32 text-sm text-muted-foreground">
              {searchQuery ? 'No incidents found' : 'No open incidents'}
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
