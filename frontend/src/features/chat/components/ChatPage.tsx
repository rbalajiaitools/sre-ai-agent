/**
 * Chat Page - Clean design without duplicate sidebar
 */
import { useEffect, useState, useRef } from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import { Sparkles, Plus, MessageSquare, Clock, Trash2, MoreVertical, GripVertical } from 'lucide-react';
import { useAppStore } from '@/stores/appStore';
import { useCreateThread, useChatThreads, useDeleteThread } from '../hooks';
import { ChatWindow } from './ChatWindow';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { formatDistanceToNow } from 'date-fns';

export function ChatPage() {
  const { threadId } = useParams<{ threadId: string }>();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { activeChatId, setActiveChatId } = useAppStore();
  const createThreadMutation = useCreateThread();
  const threadsQuery = useChatThreads();
  const deleteThreadMutation = useDeleteThread();
  const [deletingThreadId, setDeletingThreadId] = useState<string | null>(null);
  
  // Resizable sidebar
  const [sidebarWidth, setSidebarWidth] = useState(256); // Default 256px
  const [isResizing, setIsResizing] = useState(false);
  const sidebarRef = useRef<HTMLDivElement>(null);

  // Handle service context from URL (Topology → Chat flow)
  useEffect(() => {
    const serviceName = searchParams.get('service');
    if (serviceName && !threadId) {
      // Create thread with service context
      createThreadMutation.mutate({
        service_name: serviceName,
      });
    }
  }, [searchParams, threadId]);

  // Sync URL param with store
  useEffect(() => {
    if (threadId && threadId !== activeChatId) {
      setActiveChatId(threadId);
    }
  }, [threadId, activeChatId, setActiveChatId]);

  // Handle resize
  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!isResizing) return;
      
      const newWidth = e.clientX;
      if (newWidth >= 200 && newWidth <= 500) {
        setSidebarWidth(newWidth);
      }
    };

    const handleMouseUp = () => {
      setIsResizing(false);
    };

    if (isResizing) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
    }

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isResizing]);

  const handleNewChat = () => {
    createThreadMutation.mutate({});
  };

  const handleThreadClick = (id: string) => {
    setActiveChatId(id);
    navigate(`/chat/${id}`);
  };

  const handleDeleteThread = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    
    if (!confirm('Are you sure you want to delete this conversation?')) {
      return;
    }

    setDeletingThreadId(id);
    
    try {
      await deleteThreadMutation.mutateAsync(id);
      
      // If we deleted the active thread, navigate to chat home
      if (id === activeChatId) {
        setActiveChatId(null);
        navigate('/chat');
      }
    } catch (error) {
      console.error('Failed to delete thread:', error);
      alert('Failed to delete thread. Please try again.');
    } finally {
      setDeletingThreadId(null);
    }
  };

  const handleDeleteAllThreads = async () => {
    if (!threadsQuery.data || threadsQuery.data.length === 0) {
      return;
    }

    if (!confirm(`Are you sure you want to delete all ${threadsQuery.data.length} conversations? This cannot be undone.`)) {
      return;
    }

    try {
      // Delete all threads
      for (const thread of threadsQuery.data) {
        await deleteThreadMutation.mutateAsync(thread.id);
      }
      
      // Navigate to chat home
      setActiveChatId(null);
      navigate('/chat');
    } catch (error) {
      console.error('Failed to delete threads:', error);
      alert('Failed to delete some threads. Please try again.');
    }
  };

  return (
    <div className="flex h-full bg-background">
      {/* Thread list sidebar - resizable */}
      <div 
        ref={sidebarRef}
        className="border-r bg-card flex flex-col relative"
        style={{ width: `${sidebarWidth}px`, minWidth: '200px', maxWidth: '500px' }}
      >
        <div className="p-4 border-b space-y-2">
          <Button onClick={handleNewChat} className="w-full gap-2" disabled={createThreadMutation.isPending}>
            <Plus className="h-4 w-4" />
            New Chat
          </Button>
          {threadsQuery.data && threadsQuery.data.length > 0 && (
            <Button 
              onClick={handleDeleteAllThreads} 
              variant="outline" 
              className="w-full gap-2 text-red-600 hover:text-red-700 hover:bg-red-50"
              disabled={deleteThreadMutation.isPending}
            >
              <Trash2 className="h-4 w-4" />
              Delete All ({threadsQuery.data.length})
            </Button>
          )}
        </div>

        <ScrollArea className="flex-1">
          <div className="p-2 space-y-1">
            {threadsQuery.isLoading && (
              <div className="p-4 text-center text-sm text-muted-foreground">
                Loading threads...
              </div>
            )}

            {threadsQuery.data && threadsQuery.data.length === 0 && (
              <div className="p-4 text-center text-sm text-muted-foreground">
                No conversations yet
              </div>
            )}

            {threadsQuery.data?.map((thread) => (
              <div
                key={thread.id}
                className={`group relative rounded-lg transition-colors hover:bg-muted/50 ${
                  activeChatId === thread.id ? 'bg-muted' : ''
                }`}
              >
                <button
                  onClick={() => handleThreadClick(thread.id)}
                  className="w-full text-left p-3 pr-10"
                  disabled={deletingThreadId === thread.id}
                >
                  <div className="flex items-start gap-2">
                    <MessageSquare className="h-4 w-4 mt-0.5 flex-shrink-0 text-muted-foreground" />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium truncate">
                        {thread.title || 'New Conversation'}
                      </p>
                      {thread.context?.service_name && (
                        <p className="text-xs text-muted-foreground truncate">
                          Service: {thread.context.service_name}
                        </p>
                      )}
                      {thread.context?.incident && (
                        <p className="text-xs text-muted-foreground truncate">
                          Incident: {thread.context.incident.incident_number}
                        </p>
                      )}
                      <div className="flex items-center gap-1 mt-1 text-xs text-muted-foreground">
                        <Clock className="h-3 w-3" />
                        <span>
                          {formatDistanceToNow(new Date(thread.created_at), { addSuffix: true })}
                        </span>
                      </div>
                    </div>
                  </div>
                </button>

                {/* Delete button */}
                <div className="absolute right-2 top-2 opacity-0 group-hover:opacity-100 transition-opacity">
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-7 w-7 p-0"
                        onClick={(e) => e.stopPropagation()}
                      >
                        <MoreVertical className="h-4 w-4" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                      <DropdownMenuItem
                        className="text-red-600 focus:text-red-600"
                        onClick={(e) => handleDeleteThread(thread.id, e)}
                        disabled={deletingThreadId === thread.id}
                      >
                        <Trash2 className="mr-2 h-4 w-4" />
                        {deletingThreadId === thread.id ? 'Deleting...' : 'Delete'}
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </div>
              </div>
            ))}
          </div>
        </ScrollArea>

        {/* Resize handle */}
        <div
          className="absolute right-0 top-0 bottom-0 w-1 cursor-col-resize hover:bg-primary/50 transition-colors group"
          onMouseDown={() => setIsResizing(true)}
        >
          <div className="absolute right-0 top-1/2 -translate-y-1/2 -translate-x-1/2 opacity-0 group-hover:opacity-100 transition-opacity">
            <GripVertical className="h-4 w-4 text-muted-foreground" />
          </div>
        </div>
      </div>

      {/* Chat window - full width */}
      <div className="flex-1 flex flex-col bg-white">
        {activeChatId ? (
          <ChatWindow threadId={activeChatId} />
        ) : (
          <EmptyState onNewChat={handleNewChat} />
        )}
      </div>
    </div>
  );
}

function EmptyState({ onNewChat }: { onNewChat: () => void }) {
  return (
    <div className="flex flex-col items-center justify-center h-full text-center p-8 max-w-2xl mx-auto">
      <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-primary mb-6">
        <Sparkles className="h-8 w-8 text-gray-900" />
      </div>
      <h2 className="text-2xl font-semibold mb-3">Welcome to Astra AI</h2>
      <p className="text-muted-foreground mb-8 max-w-md leading-relaxed">
        Your intelligent SRE assistant. Investigate incidents, analyze infrastructure, 
        and get AI-powered insights about your cloud environment.
      </p>
      <Button onClick={onNewChat} size="lg" className="gap-2">
        <Plus className="h-5 w-5" />
        Start New Chat
      </Button>
    </div>
  );
}
