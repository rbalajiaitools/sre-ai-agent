/**
 * Validation result display component
 */
import { CheckCircle2, XCircle, Loader2 } from 'lucide-react';
import type { ValidationResult } from '../types';

interface ValidationResultCardProps {
  result: ValidationResult | null;
  isLoading: boolean;
  error?: string;
}

export function ValidationResultCard({ result, isLoading, error }: ValidationResultCardProps) {
  if (isLoading) {
    return (
      <div className="flex items-center gap-3 rounded-lg border bg-muted/50 p-4">
        <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
        <span className="text-sm text-muted-foreground">Validating connection...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-lg border border-red-500/50 bg-red-500/10 p-4">
        <div className="flex items-start gap-3">
          <XCircle className="h-5 w-5 flex-shrink-0 text-red-500" />
          <div className="flex-1">
            <p className="font-medium text-red-500">Validation Failed</p>
            <p className="mt-1 text-sm text-red-500/90">{error}</p>
          </div>
        </div>
      </div>
    );
  }

  if (!result) {
    return null;
  }

  if (result.success) {
    return (
      <div className="rounded-lg border border-green-500/50 bg-green-500/10 p-4">
        <div className="flex items-start gap-3">
          <CheckCircle2 className="h-5 w-5 flex-shrink-0 text-green-500" />
          <div className="flex-1">
            <p className="font-medium text-green-500">Connection Successful</p>
            <ul className="mt-2 space-y-1">
              {result.checks.map((check, idx) => (
                <li key={idx} className="flex items-center gap-2 text-sm text-green-500/90">
                  <CheckCircle2 className="h-3 w-3" />
                  {check.name}
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>
    );
  }

  const failedCheck = result.checks.find((c) => !c.passed);

  return (
    <div className="rounded-lg border border-red-500/50 bg-red-500/10 p-4">
      <div className="flex items-start gap-3">
        <XCircle className="h-5 w-5 flex-shrink-0 text-red-500" />
        <div className="flex-1">
          <p className="font-medium text-red-500">Connection Failed</p>
          {result.error && (
            <p className="mt-1 text-sm text-red-500/90">{result.error}</p>
          )}
          <ul className="mt-2 space-y-1">
            {result.checks.map((check, idx) => (
              <li
                key={idx}
                className={`flex items-start gap-2 text-sm ${
                  check.passed ? 'text-green-500/90' : 'text-red-500/90'
                }`}
              >
                {check.passed ? (
                  <CheckCircle2 className="h-3 w-3 flex-shrink-0 mt-0.5" />
                ) : (
                  <XCircle className="h-3 w-3 flex-shrink-0 mt-0.5" />
                )}
                <div>
                  <div className="font-medium">{check.name}</div>
                  {!check.passed && check.message && (
                    <div className="mt-0.5 text-xs">{check.message}</div>
                  )}
                </div>
              </li>
            ))}
          </ul>
          {failedCheck && (
            <div className="mt-3 rounded bg-red-500/20 p-2 text-xs text-red-500">
              <strong>Action required:</strong> {failedCheck.message}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
