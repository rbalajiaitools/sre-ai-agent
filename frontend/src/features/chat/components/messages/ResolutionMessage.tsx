/**
 * Resolution Message - fix steps with approval flow
 */
import { useState } from 'react';
import { CheckCircle2, Copy, AlertTriangle } from 'lucide-react';
import { ChatMessage, Resolution } from '../../types';
import { Button } from '@/components/ui/button';
import { useApproveResolution } from '../../hooks';
import { useUser } from '@/stores/authStore';
import { cn } from '@/lib/utils';

interface ResolutionMessageProps {
  message: ChatMessage;
}

export function ResolutionMessage({ message }: ResolutionMessageProps) {
  const resolution = message.metadata as unknown as Resolution;
  const user = useUser();
  const [showConfirmDialog, setShowConfirmDialog] = useState(false);
  const [copiedIndex, setCopiedIndex] = useState<number | null>(null);

  const investigationId = (message.metadata as { investigation_id?: string })
    .investigation_id;

  const approveMutation = useApproveResolution(investigationId || '');

  const handleCopyCommand = async (command: string, index: number) => {
    await navigator.clipboard.writeText(command);
    setCopiedIndex(index);
    setTimeout(() => setCopiedIndex(null), 2000);
  };

  const handleApprove = () => {
    if (!user) return;
    approveMutation.mutate(user.email);
    setShowConfirmDialog(false);
  };

  return (
    <div className="rounded-lg border bg-card p-6 shadow-sm">
      {/* Header */}
      <div className="flex items-start gap-3 mb-4">
        <CheckCircle2
          className="h-6 w-6 text-green-600 dark:text-green-400 mt-0.5"
          aria-hidden="true"
        />
        <div>
          <h3 className="text-lg font-semibold">Recommended Fix</h3>
          <p className="text-sm text-muted-foreground mt-1">
            {new Date(message.created_at).toLocaleString()}
          </p>
        </div>
      </div>

      {/* Fix Steps */}
      <div className="mb-6">
        <h4 className="text-sm font-medium text-muted-foreground mb-3">
          Steps to Resolve
        </h4>
        <ol className="space-y-3 list-decimal list-inside">
          {resolution.fix_steps.map((step, index) => (
            <li key={index} className="text-sm leading-relaxed">
              {step}
            </li>
          ))}
        </ol>
      </div>

      {/* Commands */}
      {resolution.commands && resolution.commands.length > 0 && (
        <div className="mb-6">
          <h4 className="text-sm font-medium text-muted-foreground mb-3">
            Commands
          </h4>
          <div className="space-y-2">
            {resolution.commands.map((command, index) => (
              <div
                key={index}
                className="relative group rounded-md bg-muted p-3 font-mono text-sm"
              >
                <pre className="overflow-x-auto">{command}</pre>
                <button
                  onClick={() => handleCopyCommand(command, index)}
                  className="absolute top-2 right-2 p-1.5 rounded bg-background/80 opacity-0 group-hover:opacity-100 transition-opacity"
                  aria-label="Copy command"
                >
                  {copiedIndex === index ? (
                    <CheckCircle2 className="h-4 w-4 text-green-600" aria-hidden="true" />
                  ) : (
                    <Copy className="h-4 w-4" aria-hidden="true" />
                  )}
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Estimated Impact */}
      {resolution.estimated_impact && (
        <div className="mb-6">
          <h4 className="text-sm font-medium text-muted-foreground mb-2">
            Estimated Impact
          </h4>
          <p className="text-sm">{resolution.estimated_impact}</p>
        </div>
      )}

      {/* Approval Section */}
      {resolution.requires_human_approval && !resolution.approved && (
        <div className="border-t pt-4">
          {!showConfirmDialog ? (
            <Button
              onClick={() => setShowConfirmDialog(true)}
              className="w-full"
              size="lg"
            >
              Approve and Close Ticket
            </Button>
          ) : (
            <div className="space-y-3">
              <div className="flex items-start gap-2 p-3 rounded-md bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-800">
                <AlertTriangle
                  className="h-5 w-5 text-amber-600 dark:text-amber-400 mt-0.5"
                  aria-hidden="true"
                />
                <div className="flex-1 text-sm">
                  <p className="font-medium text-amber-900 dark:text-amber-100">
                    Confirm Approval
                  </p>
                  <p className="text-amber-800 dark:text-amber-200 mt-1">
                    This will post the resolution to ServiceNow and close the
                    ticket. This action cannot be undone.
                  </p>
                </div>
              </div>
              <div className="flex gap-2">
                <Button
                  onClick={handleApprove}
                  disabled={approveMutation.isPending}
                  className="flex-1"
                >
                  {approveMutation.isPending ? 'Approving...' : 'Confirm'}
                </Button>
                <Button
                  onClick={() => setShowConfirmDialog(false)}
                  variant="outline"
                  className="flex-1"
                >
                  Cancel
                </Button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Approved State */}
      {resolution.approved && (
        <div className="border-t pt-4">
          <div className="flex items-center gap-2 p-3 rounded-md bg-green-50 dark:bg-green-950/30 border border-green-200 dark:border-green-800">
            <CheckCircle2
              className="h-5 w-5 text-green-600 dark:text-green-400"
              aria-hidden="true"
            />
            <div className="flex-1">
              <p className="font-medium text-green-900 dark:text-green-100">
                Ticket Closed
              </p>
              <p className="text-sm text-green-800 dark:text-green-200 mt-1">
                Approved by {resolution.approved_by} on{' '}
                {resolution.approved_at &&
                  new Date(resolution.approved_at).toLocaleString()}
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
