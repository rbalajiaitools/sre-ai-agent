/**
 * Message Renderer - Professional chat interface with agent execution
 */
import { ChatMessage, MessageType } from '../types';
import { User, Bot } from 'lucide-react';
import { TextMessage } from './messages/TextMessage';
import { InvestigationStartMessage } from './messages/InvestigationStartMessage';
import { AgentProgressMessage } from './messages/AgentProgressMessage';
import { RCAResultMessage } from './messages/RCAResultMessage';
import { ResolutionMessage } from './messages/ResolutionMessage';
import { IncidentAttachedMessage } from './messages/IncidentAttachedMessage';
import { ServiceAttachedMessage } from './messages/ServiceAttachedMessage';
import { ErrorMessage } from './messages/ErrorMessage';
import { AgentExecutionMessage } from './messages/AgentExecutionMessage';
import { InvestigationResultMessage } from './messages/InvestigationResultMessage';

interface MessageRendererProps {
  message: ChatMessage;
}

export function MessageRenderer({ message }: MessageRendererProps) {
  const isUser = message.role === 'user';

  // Check if this is an agent execution or investigation result message
  const isAgentExecution = message.metadata?.type === 'agent_execution';
  const isInvestigationResult = message.metadata?.type === 'investigation_result';

  return (
    <div className="mb-8">
      <div className="flex gap-4 items-start">
        {/* Avatar */}
        <div className={`flex h-8 w-8 items-center justify-center rounded-lg flex-shrink-0 ${
          isUser 
            ? 'bg-gradient-to-br from-gray-100 to-gray-200 dark:from-gray-700 dark:to-gray-800' 
            : 'bg-gradient-to-br from-blue-500 to-indigo-600'
        }`}>
          {isUser ? (
            <User className="h-4 w-4 text-gray-600 dark:text-gray-300" />
          ) : (
            <Bot className="h-4 w-4 text-white" />
          )}
        </div>

        {/* Message content */}
        <div className="flex-1 space-y-2 min-w-0">
          {/* Role label */}
          <div className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">
            {isUser ? 'You' : 'Astra AI'}
          </div>

          {/* User messages */}
          {isUser && (
            <div className="prose prose-sm max-w-none dark:prose-invert">
              <p className="text-foreground leading-relaxed m-0">{message.content}</p>
            </div>
          )}

          {/* Assistant/System messages */}
          {!isUser && (
            <>
              {/* Special message types */}
              {isAgentExecution && <AgentExecutionMessage message={message} />}
              {isInvestigationResult && <InvestigationResultMessage message={message} />}
              
              {/* Standard message types */}
              {!isAgentExecution && !isInvestigationResult && (
                <>
                  {message.message_type === MessageType.TEXT && (
                    <TextMessage message={message} />
                  )}
                  {message.message_type === MessageType.INVESTIGATION_START && (
                    <InvestigationStartMessage message={message} />
                  )}
                  {message.message_type === MessageType.AGENT_PROGRESS && (
                    <AgentProgressMessage message={message} />
                  )}
                  {message.message_type === MessageType.RCA_RESULT && (
                    <RCAResultMessage message={message} />
                  )}
                  {message.message_type === MessageType.RESOLUTION && (
                    <ResolutionMessage message={message} />
                  )}
                  {message.message_type === MessageType.INCIDENT_ATTACHED && (
                    <IncidentAttachedMessage message={message} />
                  )}
                  {message.message_type === MessageType.SERVICE_ATTACHED && (
                    <ServiceAttachedMessage message={message} />
                  )}
                  {message.message_type === MessageType.ERROR && (
                    <ErrorMessage message={message} />
                  )}
                </>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
