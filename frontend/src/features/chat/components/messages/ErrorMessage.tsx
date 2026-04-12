/**
 * Error Message - displays error with suggested action
 */
import { AlertTriangle } from 'lucide-react';
import { ChatMessage } from '../../types';

interface ErrorMessageProps {
  message: ChatMessage;
}

export function ErrorMessage({ message }: ErrorMessageProps) {
  const { error_message, suggested_action } = message.metadata as {
    error_message?: string;
    suggested_action?: string;
  };

  return (
    <div className="rounded-lg border border-red-200 dark:border-red-800 bg-red-50 dark:bg-red-950/30 p-4">
      <div className="flex items-start gap-3">
        <AlertTriangle
          className="h-5 w-5 text-red-600 dark:text-red-400 mt-0.5"
          aria-hidden="true"
        />
        <div className="flex-1">
          <p className="font-medium text-red-900 dark:text-red-100">
            Error
          </p>
          <p className="text-sm text-red-800 dark:text-red-200 mt-1">
            {error_message || message.content}
          </p>
          {suggested_action && (
            <div className="mt-3 pt-3 border-t border-red-200 dark:border-red-800">
              <p className="text-xs font-medium text-red-900 dark:text-red-100 mb-1">
                Suggested Action
              </p>
              <p className="text-sm text-red-800 dark:text-red-200">
                {suggested_action}
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
