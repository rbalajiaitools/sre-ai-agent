/**
 * Service Picker Modal - select service to attach
 */
import { useState } from 'react';
import { Search, Loader2 } from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { useServices } from '../hooks';

interface ServicePickerModalProps {
  open: boolean;
  onClose: () => void;
  onSelect: (serviceName: string) => void;
}

export function ServicePickerModal({
  open,
  onClose,
  onSelect,
}: ServicePickerModalProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const { data: services, isLoading } = useServices();

  const filteredServices = services?.filter((service) =>
    service.name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const handleSelect = (serviceName: string) => {
    onSelect(serviceName);
    onClose();
  };

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl max-h-[80vh] flex flex-col">
        <DialogHeader>
          <DialogTitle>Attach Service</DialogTitle>
        </DialogHeader>

        {/* Search */}
        <div className="relative">
          <Search
            className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground"
            aria-hidden="true"
          />
          <Input
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search services..."
            className="pl-9"
            aria-label="Search services"
          />
        </div>

        {/* Service list */}
        <div className="flex-1 overflow-y-auto border rounded-md">
          {isLoading ? (
            <div className="flex items-center justify-center h-32">
              <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" aria-label="Loading" />
            </div>
          ) : filteredServices && filteredServices.length > 0 ? (
            <div className="divide-y">
              {filteredServices.map((service) => (
                <button
                  key={service.id}
                  onClick={() => handleSelect(service.name)}
                  className="w-full text-left p-4 hover:bg-muted transition-colors"
                >
                  <p className="text-sm font-medium mb-1">{service.name}</p>
                  <div className="flex gap-2 text-xs text-muted-foreground">
                    <span>{service.type}</span>
                    <span>•</span>
                    <span>{service.provider}</span>
                  </div>
                </button>
              ))}
            </div>
          ) : (
            <div className="flex items-center justify-center h-32 text-sm text-muted-foreground">
              {searchQuery ? 'No services found' : 'No services available'}
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
