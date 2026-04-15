/**
 * Investigation Result Message - Professional results display like resolve.ai
 */
import { useState } from 'react';
import { ChevronDown, ChevronRight, AlertTriangle, CheckCircle, Info, Lightbulb } from 'lucide-react';
import { ChatMessage } from '../../types';
import { cn } from '@/lib/utils';

interface InvestigationResultMessageProps {
  message: ChatMessage;
}

interface ResultSection {
  id: string;
  title: string;
  icon: 'warning' | 'success' | 'info' | 'lightbulb';
  content: string;
  items?: string[];
  expanded?: boolean;
}

export function InvestigationResultMessage({ message }: InvestigationResultMessageProps) {
  const [expandedSections, setExpandedSections] = useState<Set<string>>(
    new Set(['what-happened', 'root-cause'])
  );

  // Parse sections from message content or metadata
  const sections: ResultSection[] = message.metadata?.sections || [
    {
      id: 'what-happened',
      title: 'What Happened',
      icon: 'info',
      content: 'AWS Account Summary request failed with an incident investigation. The user asked for all running AWS services.',
      items: [
        '1 EC2 instance (payment-service-app, t3.medium) - running in us-east-1a',
        '1 RDS PostgreSQL (payment-service-db, v16.3.micro) - available in us-east-1b',
      ],
    },
    {
      id: 'root-cause',
      title: 'Root Cause',
      icon: 'warning',
      content: 'The CloudWatch Logs search returned zero results which are available log groups for the time range Wed April 8 9:00pm to Wed April 8 9:30pm in the last hour.',
      items: [
        'No log activity: The response may have generated any logs during this time period',
        'Different log group name: Logs may exist under a different name than expected',
        'Logs already expired: Logs may have been deleted or retention period expired',
      ],
    },
    {
      id: 'what-we-know',
      title: 'What We Know from the AWS Inventory',
      icon: 'success',
      content: 'During the earlier AWS service scan, I found a CloudWatch Log Stream in your account:',
      items: [
        '/aws/lambda/analytics-main-logGroup',
        '/aws/lambda/analytics-data-logGroup',
        '/aws/lambda/analytics-data-processor',
      ],
    },
    {
      id: 'next-steps',
      title: 'Next Steps',
      icon: 'lightbulb',
      content: 'Would you like me to:',
      items: [
        'Check if the instance has logging configured by inspecting its configuration',
        'Query logs from a broader time range (e.g., last 24 hours or last 7 days)?',
        'Help you set up CloudWatch Logs agent on the payment service instance if it was configured',
      ],
    },
  ];

  const toggleSection = (id: string) => {
    const newExpanded = new Set(expandedSections);
    if (newExpanded.has(id)) {
      newExpanded.delete(id);
    } else {
      newExpanded.add(id);
    }
    setExpandedSections(newExpanded);
  };

  const getIcon = (icon: ResultSection['icon']) => {
    switch (icon) {
      case 'warning':
        return <AlertTriangle className="h-5 w-5 text-amber-500" />;
      case 'success':
        return <CheckCircle className="h-5 w-5 text-green-500" />;
      case 'info':
        return <Info className="h-5 w-5 text-gray-500" />;
      case 'lightbulb':
        return <Lightbulb className="h-5 w-5 text-lime-500" />;
    }
  };

  return (
    <div className="space-y-3">
      {sections.map((section) => {
        const isExpanded = expandedSections.has(section.id);

        return (
          <div
            key={section.id}
            className="rounded-lg border bg-card card-shadow overflow-hidden"
          >
            <button
              onClick={() => toggleSection(section.id)}
              className="w-full px-4 py-3 text-left hover:bg-accent/50 transition-colors"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  {getIcon(section.icon)}
                  <h3 className="font-semibold text-sm">{section.title}</h3>
                </div>
                {isExpanded ? (
                  <ChevronDown className="h-4 w-4 text-muted-foreground" />
                ) : (
                  <ChevronRight className="h-4 w-4 text-muted-foreground" />
                )}
              </div>
            </button>

            {isExpanded && (
              <div className="px-4 pb-4 space-y-3 animate-expand">
                <p className="text-sm leading-relaxed text-foreground/90">
                  {section.content}
                </p>

                {section.items && section.items.length > 0 && (
                  <ul className="space-y-2">
                    {section.items.map((item, idx) => (
                      <li
                        key={idx}
                        className="text-sm flex items-start gap-2 text-foreground/80"
                      >
                        <span className="text-primary mt-1 font-bold">•</span>
                        <span>{item}</span>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
