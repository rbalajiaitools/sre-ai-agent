/**
 * Thread List - left panel with thread list
 */
import { useState } from 'react';
import { Plus, Search, Loader2, MessageSquare } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import { useChatThreads, useCreateThread } from '../hooks';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { cn } from '@/lib/utils';

interface ThreadListProps {
  activeThreadId: string | null;
  onThreadSelect: (threadId: string) => void;
}

export function ThreadList({ activeThreadId, onThreadSelect }: ThreadListProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const { data: threads, isLoading, isError } = useChatThreads();
  const createThreadMutation = useCreateThread();

  const filteredThreads = threads?.filter((thread) =>
    thread.title.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const handleNewChat = () => {
    createThreadMutation.mutate();
  };

  return (
    <div className="flex flex-col h-full border-r bg-muted/30">
      {/* Header */}
      <div className="p-4 border-b">
        <Button
          onClick={handleNewChat}
          disabled={createThreadMutation.isPending}
          className="w-full"
        >
          <Plus className="h-4 w-4 mr-2" aria-hidden="true" />
          New Chat
        </Button>
      </div>

      {/* Search */}
      <div className="p-4 border-b">
        <div className="relative">
          <Search
            className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground"
            aria-hidden="true"
          />
          <Input
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search threads..."
            className="pl-9"
            aria-label="Search threads"
          />
        </div>
      </div>

      {/* Thread list */}
      <div className="flex-1 overflow-y-auto">
        {isLoading ? (
          <div className="flex items-center justify-center h-32">
            <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" aria-label="Loading threads" />
          </div>
        ) : isError ? (
          <div className="p-4 text-center text-sm text-muted-foreground">
            Failed to load threads
          </div>
        ) : filteredThreads && filteredThreads.length > 0 ? (
          <div>
            {filteredThreads.map((thread) => (
              <button
                key={thread.id}
                onClick={() => onThreadSelect(thread.id)}
                className={cn(
                  'w-full text-left p-4 border-b hover:bg-muted/50 transition-colors',
                  activeThreadId === thread.id && 'bg-muted'
                )}
                aria-current={activeThreadId === thread.id ? 'page' : undefined}
              >
                <div className="flex items-start gap-3">
                  <MessageSquare
                    className="h-4 w-4 text-muted-foreground mt-1 flex-shrink-0"
                    aria-hidden="true"
                  />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium truncate mb-1">
                      {thread.title}
                    </p>
                    <div className="flex items-center gap-2 text-xs text-muted-foreground">
                      <span>
                        {formatDistanceToNow(new Date(thread.last_message_at), {
                          addSuffix: true,
                        })}
                      </span>
                      {thread.incident_number && (
                        <>
                          <span>•</span>
                          <span className="font-mono">
                            {thread.incident_number}
                          </span>
                        </>
                      )}
                    </div>
                  </div>
                </div>
              </button>
            ))}
          </div>
        ) : (
          <div className="p-4 text-center text-sm text-muted-foreground">
            {searchQuery ? 'No threads found' : 'No threads yet'}
          </div>
        )}
      </div>
    </div>
  );
}
