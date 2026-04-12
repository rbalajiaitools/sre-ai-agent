/**
 * Loading spinner component
 */
import { Loader2 } from 'lucide-react';

interface LoadingSpinnerProps {
  size?: 'sm' | 'md';
}

export function LoadingSpinner({ size = 'md' }: LoadingSpinnerProps) {
  const sizeClass = size === 'sm' ? 'h-4 w-4' : 'h-8 w-8';

  return (
    <div className="flex items-center justify-center p-8">
      <Loader2 className={`${sizeClass} animate-spin text-muted-foreground`} aria-label="Loading" />
    </div>
  );
}
