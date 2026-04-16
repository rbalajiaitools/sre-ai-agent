/**
 * Chat Page - Two-section layout with resizable left panel
 */
import { useEffect, useState, useRef } from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import { Zap, Image as ImageIcon, Search, Send, Trash2, MoreVertical } from 'lucide-react';
import { useAppStore } from '@/stores/appStore';
import { useCreateThread, useChatThreads, useDeleteThread } from '../hooks';
import { useInvestigations } from '@/features/investigations/hooks';
import { ChatWindow } from './ChatWindow';
import { Button } from '@/components/ui/button';
import { formatDistanceToNow } from 'date-fns';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';

// Sample prompts for the empty state
const samplePrompts = [
  {
    title: 'Check the memory usage and execution duration patterns for the cloudscore-demo-payment-processor Lambda function',
    category: 'Connected Integrations: AWS'
  },
  {
    title: 'What code changes or feature improvements were made to Lambda functions in the past week?',
    category: 'Connected Integrations: AWS'
  },
  {
    title: 'List all running EC2 instances across all regions with their health status',
    category: 'Connected Integrations: AWS'
  },
  {
    title: 'Show me all failed deployments in the last 24 hours and their root causes',
    category: 'Connected Integrations: AWS'
  },
  {
    title: 'Show me error logs for the cloudscore-demo-payment-processor Lambda function in the past 3 days',
    category: 'Connected Integrations: AWS'
  }
];

export function ChatPage() {
  const { threadId } = useParams<{ threadId: string }>();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { activeChatId, setActiveChatId } = useAppStore();
  const createThreadMutation = useCreateThread();
  const threadsQuery = useChatThreads();
  const investigationsQuery = useInvestigations();
  const deleteThreadMutation = useDeleteThread();
  const [inputValue, setInputValue] = useState('');
  const [activeTab, setActiveTab] = useState<'investigations' | 'chats'>('investigations');
  
  // Resizable left panel
  const [leftWidth, setLeftWidth] = useState(400); // Default 400px
  const isResizing = useRef(false);
  const MIN_WIDTH = 300;
  const MAX_WIDTH = 600;

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
    } else if (!threadId && activeChatId) {
      // Clear active chat if no threadId in URL
      setActiveChatId(null);
    }
  }, [threadId, activeChatId, setActiveChatId]);

  const handleNewChat = () => {
    createThreadMutation.mutate(undefined);
  };

  const handlePromptClick = (prompt: string) => {
    // Create new thread and navigate, user can then send the message
    createThreadMutation.mutate(undefined);
  };

  const handleSend = () => {
    if (!inputValue.trim()) return;
    
    // Create new thread and navigate, user can then send the message
    createThreadMutation.mutate(undefined);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  // Handle mouse move for resizing
  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!isResizing.current) return;
      
      const newWidth = e.clientX - 240; // Subtract sidebar width
      if (newWidth >= MIN_WIDTH && newWidth <= MAX_WIDTH) {
        setLeftWidth(newWidth);
      }
    };

    const handleMouseUp = () => {
      isResizing.current = false;
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
    };

    if (isResizing.current) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
    }

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };
  }, []);

  const handleMouseDown = () => {
    isResizing.current = true;
    document.body.style.cursor = 'col-resize';
    document.body.style.userSelect = 'none';
  };

  const handleDeleteThread = (threadId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (window.confirm('Are you sure you want to delete this chat?')) {
      deleteThreadMutation.mutate(threadId);
      // If deleting active chat, clear it
      if (activeChatId === threadId) {
        setActiveChatId(null);
        navigate('/chat');
      }
    }
  };

  const handleThreadClick = (threadId: string) => {
    setActiveChatId(threadId);
    navigate(`/chat/${threadId}`);
  };

  const handleInvestigationClick = (investigationId: string) => {
    navigate(`/investigations/${investigationId}`);
  };

  // Get real data
  const chatThreads = threadsQuery.data || [];
  const investigations = investigationsQuery.data?.items || [];

  return (
    <div className="flex h-full bg-background">
      {/* Left Section - Resizable */}
      <div 
        className="flex-shrink-0 border-r bg-white overflow-hidden flex flex-col"
        style={{ width: `${leftWidth}px` }}
      >
        {/* Recent Section */}
        <div className="flex-1 flex flex-col overflow-hidden p-6">
          <h2 className="text-xl font-semibold mb-4">Recent</h2>
          
          {/* Tabs */}
          <div className="flex items-center gap-6 mb-4 border-b">
            <button
              onClick={() => setActiveTab('investigations')}
              className={`pb-2 text-sm font-medium transition-colors relative ${
                activeTab === 'investigations'
                  ? 'text-foreground'
                  : 'text-muted-foreground hover:text-foreground'
              }`}
            >
              Investigations
              {activeTab === 'investigations' && (
                <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-primary" />
              )}
            </button>
            <button
              onClick={() => setActiveTab('chats')}
              className={`pb-2 text-sm font-medium transition-colors relative ${
                activeTab === 'chats'
                  ? 'text-foreground'
                  : 'text-muted-foreground hover:text-foreground'
              }`}
            >
              Chats
              {activeTab === 'chats' && (
                <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-primary" />
              )}
            </button>
          </div>

          {/* Filters */}
          <div className="flex items-center gap-3 mb-4">
            <select className="px-3 py-1.5 border border-border rounded-md text-sm bg-white">
              <option>All teams</option>
            </select>
            <select className="px-3 py-1.5 border border-border rounded-md text-sm bg-white">
              <option>Recent</option>
            </select>
          </div>

          {/* Activity list - scrollable */}
          <div className="flex-1 overflow-y-auto space-y-2">
            {activeTab === 'investigations' ? (
              investigations.length === 0 ? (
                <div className="text-center py-8 text-sm text-muted-foreground">
                  No investigations yet
                </div>
              ) : (
                investigations.map((investigation) => (
                  <button
                    key={investigation.id}
                    onClick={() => handleInvestigationClick(investigation.id)}
                    className="w-full flex items-center gap-3 p-3 border border-border rounded-lg hover:bg-muted/50 transition-colors text-left"
                  >
                    <div className="flex h-8 w-8 items-center justify-center rounded-full bg-muted flex-shrink-0">
                      <span className="text-xs font-medium">I</span>
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium truncate">
                        {investigation.incident_number}
                        {investigation.service_name && ` - ${investigation.service_name}`}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        Investigations • {formatDistanceToNow(new Date(investigation.started_at), { addSuffix: true })}
                      </p>
                    </div>
                  </button>
                ))
              )
            ) : (
              chatThreads.length === 0 ? (
                <div className="text-center py-8 text-sm text-muted-foreground">
                  No chats yet
                </div>
              ) : (
                chatThreads.map((thread) => (
                  <div
                    key={thread.id}
                    className="w-full flex items-center gap-3 p-3 border border-border rounded-lg hover:bg-muted/50 transition-colors group"
                  >
                    <button
                      onClick={() => handleThreadClick(thread.id)}
                      className="flex items-center gap-3 flex-1 min-w-0 text-left"
                    >
                      <div className="flex h-8 w-8 items-center justify-center rounded-full bg-muted flex-shrink-0">
                        <span className="text-xs font-medium">C</span>
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium truncate">{thread.title}</p>
                        <p className="text-xs text-muted-foreground">
                          Chats • {formatDistanceToNow(new Date(thread.last_message_at || thread.created_at), { addSuffix: true })}
                        </p>
                      </div>
                    </button>
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <button className="p-1 hover:bg-muted rounded opacity-0 group-hover:opacity-100 transition-opacity">
                          <MoreVertical className="h-4 w-4 text-muted-foreground" />
                        </button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuItem
                          onClick={(e) => handleDeleteThread(thread.id, e as any)}
                          className="text-red-600"
                        >
                          <Trash2 className="h-4 w-4 mr-2" />
                          Delete
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </div>
                ))
              )
            )}
          </div>
        </div>
      </div>

      {/* Resize handle */}
      <div
        className="w-1 bg-border hover:bg-primary/50 cursor-col-resize transition-colors flex-shrink-0"
        onMouseDown={handleMouseDown}
      />

      {/* Right Section - Main content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {activeChatId ? (
          <ChatWindow threadId={activeChatId} />
        ) : (
          <div className="flex-1 flex flex-col items-center justify-start pt-16 px-4 max-w-4xl mx-auto w-full overflow-y-auto">
            {/* Header with icon */}
            <div className="flex items-center justify-center mb-6">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-primary">
                <Zap className="h-6 w-6 text-white" />
              </div>
            </div>

            {/* Main heading */}
            <h1 className="text-3xl font-semibold mb-8 text-center">
              What can I help you investigate today?
            </h1>

            {/* Input area */}
            <div className="w-full mb-6">
              <div className="relative">
                <textarea
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="Ask a question or describe a problem in your system. Use @ to mention services or dashboards."
                  className="w-full min-h-[120px] p-4 pr-32 border border-border rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-primary bg-white text-sm"
                />
                <div className="absolute bottom-3 left-3 flex items-center gap-2">
                  <button className="p-2 hover:bg-muted rounded-md transition-colors">
                    <ImageIcon className="h-4 w-4 text-muted-foreground" />
                  </button>
                  <button className="p-2 hover:bg-muted rounded-md transition-colors flex items-center">
                    <Search className="h-4 w-4 text-muted-foreground" />
                    <span className="ml-1 text-xs text-muted-foreground">Deep Investigation</span>
                  </button>
                </div>
                <button
                  onClick={handleSend}
                  disabled={!inputValue.trim() || createThreadMutation.isPending}
                  className="absolute bottom-3 right-3 px-4 py-2 bg-primary text-white rounded-md hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors text-sm font-medium"
                >
                  {createThreadMutation.isPending ? 'Starting...' : 'Send'}
                </button>
              </div>
              
              {/* Connected integrations */}
              <div className="mt-3 flex items-center justify-between text-xs text-muted-foreground">
                <div className="flex items-center gap-2">
                  <span>Connected Integrations:</span>
                  <span className="px-2 py-1 bg-muted rounded">AWS</span>
                </div>
                <span>💎 3 of 20 daily limit used</span>
              </div>
            </div>

            {/* Sample prompts */}
            <div className="w-full grid grid-cols-2 gap-3 mb-8">
              {samplePrompts.map((prompt, index) => (
                <button
                  key={index}
                  onClick={() => handlePromptClick(prompt.title)}
                  className="p-4 text-left border border-border rounded-lg hover:bg-muted/50 transition-colors"
                >
                  <p className="text-sm mb-2">{prompt.title}</p>
                  <p className="text-xs text-muted-foreground">{prompt.category}</p>
                </button>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
