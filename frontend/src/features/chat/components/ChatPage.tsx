/**
 * Chat Page - main chat interface with two-column layout
 */
import { useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { MessageSquarePlus } from 'lucide-react';
import { useAppStore } from '@/stores/appStore';
import { ThreadList } from './ThreadList';
import { ChatWindow } from './ChatWindow';

export function ChatPage() {
  const { threadId } = useParams<{ threadId: string }>();
  const navigate = useNavigate();
  const { activeChatId, setActiveChatId } = useAppStore();

  // Sync URL param with store
  useEffect(() => {
    if (threadId && threadId !== activeChatId) {
      setActiveChatId(threadId);
    }
  }, [threadId, activeChatId, setActiveChatId]);

  const handleThreadSelect = (id: string) => {
    setActiveChatId(id);
    navigate(`/chat/${id}`);
  };

  return (
    <div className="flex h-full">
      {/* Left panel - Thread list */}
      <div className="w-64 flex-shrink-0">
        <ThreadList
          activeThreadId={activeChatId}
          onThreadSelect={handleThreadSelect}
        />
      </div>

      {/* Right panel - Chat window */}
      <div className="flex-1">
        {activeChatId ? (
          <ChatWindow threadId={activeChatId} />
        ) : (
          <EmptyState />
        )}
      </div>
    </div>
  );
}

function EmptyState() {
  return (
    <div className="flex flex-col items-center justify-center h-full text-center p-8">
      <MessageSquarePlus
        className="h-16 w-16 text-muted-foreground mb-4"
        aria-hidden="true"
      />
      <h2 className="text-xl font-semibold mb-2">Start a conversation</h2>
      <p className="text-sm text-muted-foreground max-w-md">
        Select a thread from the left or create a new chat to begin investigating
        incidents and asking questions about your infrastructure.
      </p>
    </div>
  );
}
