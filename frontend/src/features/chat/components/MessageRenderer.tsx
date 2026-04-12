/**
 * Message Renderer - routes to correct message component based on type
 */
import { ChatMessage, MessageType } from '../types';
import { TextMessage } from './messages/TextMessage';
import { InvestigationStartMessage } from './messages/InvestigationStartMessage';
import { AgentProgressMessage } from './messages/AgentProgressMessage';
import { RCAResultMessage } from './messages/RCAResultMessage';
import { ResolutionMessage } from './messages/ResolutionMessage';
import { IncidentAttachedMessage } from './messages/IncidentAttachedMessage';
import { ServiceAttachedMessage } from './messages/ServiceAttachedMessage';
import { ErrorMessage } from './messages/ErrorMessage';

interface MessageRendererProps {
  message: ChatMessage;
}

export function MessageRenderer({ message }: MessageRendererProps) {
  const isUser = message.role === 'user';

  return (
    <div
      className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}
    >
      <div className={`max-w-[80%] ${isUser ? 'ml-auto' : 'mr-auto'}`}>
        {/* User messages */}
        {isUser && (
          <div className="rounded-lg bg-primary text-primary-foreground px-4 py-2">
            <p className="text-sm">{message.content}</p>
          </div>
        )}

        {/* Assistant/System messages */}
        {!isUser && (
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
      </div>
    </div>
  );
}
