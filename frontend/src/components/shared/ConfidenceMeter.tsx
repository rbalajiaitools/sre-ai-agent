/**
 * Confidence meter component
 */
interface ConfidenceMeterProps {
  confidence: number; // 0-1
}

export function ConfidenceMeter({ confidence }: ConfidenceMeterProps) {
  const percentage = Math.round(confidence * 100);
  
  const getColor = () => {
    if (percentage >= 80) return 'bg-green-500';
    if (percentage >= 60) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  const getLabel = () => {
    if (percentage >= 80) return 'High confidence';
    if (percentage >= 60) return 'Medium confidence';
    return 'Low confidence';
  };

  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between text-xs">
        <span className="text-muted-foreground">{getLabel()}</span>
        <span className="font-medium">{percentage}%</span>
      </div>
      <div className="h-2 w-full overflow-hidden rounded-full bg-muted">
        <div
          className={`h-full transition-all ${getColor()}`}
          style={{ width: `${percentage}%` }}
          role="progressbar"
          aria-valuenow={percentage}
          aria-valuemin={0}
          aria-valuemax={100}
          aria-label={`Confidence: ${percentage}%`}
        />
      </div>
    </div>
  );
}
