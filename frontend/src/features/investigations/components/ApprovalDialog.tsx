/**
 * Approval Dialog - confirmation dialog for approving resolution
 */
import { useState } from 'react';
import { AlertTriangle, CheckCircle2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { cn } from '@/lib/utils';
import { statusColors } from '@/lib/colors';

interface ApprovalDialogProps {
  onApprove: (approverName: string) => void;
  onCancel: () => void;
  isPending: boolean;
  isError: boolean;
  defaultApproverName: string;
}

export function ApprovalDialog({
  onApprove,
  onCancel,
  isPending,
  isError,
  defaultApproverName,
}: ApprovalDialogProps) {
  const [approverName, setApproverName] = useState(defaultApproverName);

  const handleApprove = () => {
    if (!approverName.trim()) return;
    onApprove(approverName);
  };

  return (
    <div className="space-y-4">
      <div className={cn('p-4 rounded-md border', statusColors.warning.bg, statusColors.warning.border)}>
        <div className="flex items-start gap-3">
          <AlertTriangle className={cn('h-5 w-5 mt-0.5', statusColors.warning.icon)} aria-hidden="true" />
          <div className="flex-1">
            <p className={cn('font-medium text-sm mb-1', statusColors.warning.text)}>
              Confirm Approval
            </p>
            <p className={cn('text-sm', statusColors.warning.textMuted)}>
              This will post the resolution to ServiceNow and close the ticket. This action cannot be undone.
            </p>
          </div>
        </div>
      </div>

      <div>
        <Label htmlFor="approver-name">Approved By</Label>
        <Input
          id="approver-name"
          value={approverName}
          onChange={(e) => setApproverName(e.target.value)}
          placeholder="Enter your name"
          className="mt-1"
          aria-required="true"
        />
      </div>

      {isError && (
        <p className="text-sm text-destructive" role="alert">
          Failed to approve resolution. Please try again.
        </p>
      )}

      <div className="flex gap-2">
        <Button
          onClick={handleApprove}
          disabled={isPending || !approverName.trim()}
          className="flex-1"
        >
          {isPending ? 'Approving...' : 'Confirm Approval'}
        </Button>
        <Button
          onClick={onCancel}
          variant="outline"
          className="flex-1"
        >
          Cancel
        </Button>
      </div>
    </div>
  );
}
