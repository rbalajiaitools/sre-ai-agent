/**
 * Text Message - plain text with markdown support and modern styling
 */
import ReactMarkdown from 'react-markdown';
import { ChatMessage } from '../../types';

interface TextMessageProps {
  message: ChatMessage;
}

export function TextMessage({ message }: TextMessageProps) {
  return (
    <div className="prose prose-sm dark:prose-invert max-w-none prose-p:leading-relaxed prose-pre:bg-muted prose-pre:border prose-pre:border-border prose-code:text-sm">
      <ReactMarkdown
        components={{
          // Custom styling for code blocks
          pre: ({ children }) => (
            <pre className="rounded-lg p-4 overflow-x-auto">{children}</pre>
          ),
          // Custom styling for inline code
          code: ({ children, className }) => {
            const isInline = !className;
            return isInline ? (
              <code className="px-1.5 py-0.5 rounded bg-muted text-foreground font-mono text-sm">
                {children}
              </code>
            ) : (
              <code className={className}>{children}</code>
            );
          },
        }}
      >
        {message.content}
      </ReactMarkdown>
    </div>
  );
}
