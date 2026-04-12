/**
 * Error Message - displays error with suggested action
 */
import { AlertTriangle } from 'lucide-react';
import { ChatMessage } from '../../types';
import { cn } from '@/lib/utils';
import { statusColors } from '@/lib/colors';

interface ErrorMessageProps {
  message: ChatMessage;
}

export function ErrorMessage({ message }: ErrorMessageProps) {
  const { error_message, suggested_action } = message.metadata as {
    error_message?: string;
    suggested_action?: string;
  };

  return (
    <div className={cn('rounded-lg border p-4', statusColors.error.bg, statusColors.error.border)}>
      <div className="flex items-start gap-3">
        <AlertTriangle
          className={cn('h-5 w-5 mt-0.5', statusColors.error.icon)}
          aria-hidden="true"
        />
        <div className="flex-1">
          <p className={cn('font-medium', statusColors.error.text)}>
            Error
          </p>
          <p className={cn('text-sm mt-1', statusColors.error.textMuted)}>
            {error_message || message.content}
          </p>
          {suggested_action && (
            <div className={cn('mt-3 pt-3 border-t', statusColors.error.border)}>
              <p className={cn('text-xs font-medium mb-1', statusColors.error.text)}>
                Suggested Action
              </p>
              <p className={cn('text-sm', statusColors.error.textMuted)}>
                {suggested_action}
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
