/**
 * Incident Work Notes - collapsible work notes section
 */
import { useState } from 'react';
import { ChevronDown, ChevronRight } from 'lucide-react';

interface IncidentWorkNotesProps {
  workNotes: string[];
}

export function IncidentWorkNotes({ workNotes }: IncidentWorkNotesProps) {
  const [expanded, setExpanded] = useState(false);

  if (workNotes.length === 0) {
    return null;
  }

  const visibleNotes = expanded ? workNotes : workNotes.slice(0, 3);

  return (
    <div>
      <button
        onClick={() => setExpanded(!expanded)}
        className="flex items-center gap-2 text-sm font-medium text-muted-foreground hover:text-foreground transition-colors mb-3"
        aria-expanded={expanded}
        aria-label={expanded ? 'Collapse work notes' : 'Expand work notes'}
      >
        {expanded ? (
          <ChevronDown className="h-4 w-4" aria-hidden="true" />
        ) : (
          <ChevronRight className="h-4 w-4" aria-hidden="true" />
        )}
        Work Notes ({workNotes.length})
      </button>
      {(expanded || workNotes.length <= 3) && (
        <div className="space-y-2">
          {visibleNotes.map((note, index) => (
            <div
              key={index}
              className="p-3 rounded-md bg-muted text-sm leading-relaxed"
            >
              {note}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
