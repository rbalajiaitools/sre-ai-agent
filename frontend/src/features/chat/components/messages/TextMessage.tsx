/**
 * Text Message - plain text with markdown support
 */
import ReactMarkdown from 'react-markdown';
import { ChatMessage } from '../../types';

interface TextMessageProps {
  message: ChatMessage;
}

export function TextMessage({ message }: TextMessageProps) {
  return (
    <div className="prose prose-sm dark:prose-invert max-w-none">
      <ReactMarkdown>{message.content}</ReactMarkdown>
    </div>
  );
}
