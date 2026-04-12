/**
 * Resolution Panel - fix steps with approval flow
 */
import { useState } from 'react';
import { CheckCircle2, Copy, AlertTriangle, Download, ChevronDown, ChevronRight } from 'lucide-react';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { ResolutionOutput } from '../types';
import { Button } from '@/components/ui/button';
import { ApprovalDialog } from './ApprovalDialog';
import { useApproveResolution, useExportPostMortem } from '../hooks';
import { useUser } from '@/stores/authStore';
import { cn } from '@/lib/utils';
import { statusColors } from '@/lib/colors';

interface ResolutionPanelProps {
  resolution: ResolutionOutput;
  investigationId: string;
  approvedBy: string | null;
  approvedAt: string | null;
}

export function ResolutionPanel({
  resolution,
  investigationId,
  approvedBy,
  approvedAt,
}: ResolutionPanelProps) {
  const user = useUser();
  const [showConfirmDialog, setShowConfirmDialog] = useState(false);
  const [copiedIndex, setCopiedIndex] = useState<number | null>(null);
  const [workNoteExpanded, setWorkNoteExpanded] = useState(false);

  const approveMutation = useApproveResolution(investigationId);
  const exportMutation = useExportPostMortem(investigationId);

  const handleCopyCommand = async (command: string, index: number) => {
    await navigator.clipboard.writeText(command);
    setCopiedIndex(index);
    setTimeout(() => setCopiedIndex(null), 2000);
  };

  const handleApprove = (approverName: string) => {
    approveMutation.mutate(approverName);
    setShowConfirmDialog(false);
  };

  const handleExport = () => {
    exportMutation.mutate();
  };

  const isApproved = !!approvedBy;

  return (
    <div className="space-y-6">
      {/* Recommended Fix */}
      <div className="p-6 rounded-lg border bg-card">
        <h3 className="text-lg font-semibold mb-3">Recommended Fix</h3>
        <p className="text-sm leading-relaxed">{resolution.recommended_fix}</p>
      </div>

      {/* Fix Steps */}
      <div className="p-6 rounded-lg border bg-card">
        <h3 className="text-lg font-semibold mb-4">Steps to Resolve</h3>
        <ol className="space-y-3 list-decimal list-inside">
          {resolution.fix_steps.map((step, index) => (
            <li key={index} className="text-sm leading-relaxed">
              {step}
            </li>
          ))}
        </ol>
      </div>

      {/* Commands */}
      {resolution.commands.length > 0 && (
        <div className="p-6 rounded-lg border bg-card">
          <h3 className="text-lg font-semibold mb-4">Commands</h3>
          <div className="space-y-3">
            {resolution.commands.map((command, index) => (
              <div key={index} className="relative group">
                <SyntaxHighlighter
                  language="bash"
                  style={vscDarkPlus}
                  customStyle={{
                    margin: 0,
                    borderRadius: '0.5rem',
                    fontSize: '0.875rem',
                  }}
                >
                  {command}
                </SyntaxHighlighter>
                <button
                  onClick={() => handleCopyCommand(command, index)}
                  className="absolute top-2 right-2 p-2 rounded bg-background/80 opacity-0 group-hover:opacity-100 transition-opacity"
                  aria-label="Copy command"
                >
                  {copiedIndex === index ? (
                    <CheckCircle2 className={cn('h-4 w-4', statusColors.success.icon)} aria-hidden="true" />
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
        <div className={cn('p-4 rounded-lg border', statusColors.warning.bg, statusColors.warning.border)}>
          <div className="flex items-start gap-3">
            <AlertTriangle className={cn('h-5 w-5 mt-0.5', statusColors.warning.icon)} aria-hidden="true" />
            <div>
              <p className={cn('font-medium text-sm mb-1', statusColors.warning.text)}>
                Estimated Impact
              </p>
              <p className={cn('text-sm', statusColors.warning.textMuted)}>
                {resolution.estimated_impact}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* ServiceNow Work Note Preview */}
      <div className="p-6 rounded-lg border bg-card">
        <button
          onClick={() => setWorkNoteExpanded(!workNoteExpanded)}
          className="flex items-center gap-2 text-lg font-semibold mb-3 hover:text-primary transition-colors"
          aria-expanded={workNoteExpanded}
        >
          {workNoteExpanded ? (
            <ChevronDown className="h-5 w-5" aria-hidden="true" />
          ) : (
            <ChevronRight className="h-5 w-5" aria-hidden="true" />
          )}
          ServiceNow Work Note Preview
        </button>
        {workNoteExpanded && (
          <div className="p-4 rounded-md bg-muted font-mono text-xs whitespace-pre-wrap">
            {resolution.snow_work_note}
          </div>
        )}
      </div>

      {/* Approval Section */}
      {resolution.requires_human_approval && !isApproved && (
        <div className="p-6 rounded-lg border bg-card">
          <h3 className="text-lg font-semibold mb-4">Approval Required</h3>
          {!showConfirmDialog ? (
            <Button onClick={() => setShowConfirmDialog(true)} className="w-full" size="lg">
              Approve and Close ServiceNow Ticket
            </Button>
          ) : (
            <ApprovalDialog
              onApprove={handleApprove}
              onCancel={() => setShowConfirmDialog(false)}
              isPending={approveMutation.isPending}
              isError={approveMutation.isError}
              defaultApproverName={user?.name || ''}
            />
          )}
        </div>
      )}

      {/* Approved State */}
      {isApproved && (
        <div className={cn('p-4 rounded-lg border', statusColors.success.bg, statusColors.success.border)}>
          <div className="flex items-center gap-3">
            <CheckCircle2 className={cn('h-5 w-5', statusColors.success.icon)} aria-hidden="true" />
            <div className="flex-1">
              <p className={cn('font-medium', statusColors.success.text)}>
                Ticket Closed
              </p>
              <p className={cn('text-sm mt-1', statusColors.success.textMuted)}>
                Approved by {approvedBy} on {approvedAt && new Date(approvedAt).toLocaleString()}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Export Post-Mortem */}
      {exportMutation.isError && (
        <p className="text-sm text-destructive" role="alert">
          Failed to export post-mortem. Please try again.
        </p>
      )}
      <Button
        onClick={handleExport}
        disabled={exportMutation.isPending}
        variant="outline"
        className="w-full"
      >
        <Download className="h-4 w-4 mr-2" aria-hidden="true" />
        {exportMutation.isPending ? 'Exporting...' : 'Export Post-Mortem PDF'}
      </Button>
    </div>
  );
}
