/**
 * Onboarding welcome step
 */
import { Shield, Zap, Brain } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface WelcomeStepProps {
  onNext: () => void;
}

export function WelcomeStep({ onNext }: WelcomeStepProps) {
  return (
    <div className="space-y-8 py-8 text-center">
      <div>
        <h1 className="text-3xl font-bold">Welcome to SRE AI Agent</h1>
        <p className="mt-3 text-lg text-muted-foreground">
          Connect your infrastructure and start investigating incidents with AI
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-3">
        <div className="rounded-lg border bg-card p-6 text-center">
          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-blue-500/10">
            <Brain className="h-6 w-6 text-blue-500" />
          </div>
          <h3 className="mt-4 font-semibold">AI-Powered RCA</h3>
          <p className="mt-2 text-sm text-muted-foreground">
            Automated root cause analysis using specialized AI agents
          </p>
        </div>

        <div className="rounded-lg border bg-card p-6 text-center">
          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-green-500/10">
            <Zap className="h-6 w-6 text-green-500" />
          </div>
          <h3 className="mt-4 font-semibold">Instant Resolution</h3>
          <p className="mt-2 text-sm text-muted-foreground">
            Get actionable fix recommendations in minutes, not hours
          </p>
        </div>

        <div className="rounded-lg border bg-card p-6 text-center">
          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-purple-500/10">
            <Shield className="h-6 w-6 text-purple-500" />
          </div>
          <h3 className="mt-4 font-semibold">Secure & Compliant</h3>
          <p className="mt-2 text-sm text-muted-foreground">
            Read-only access with enterprise-grade security
          </p>
        </div>
      </div>

      <div className="pt-4">
        <Button size="lg" onClick={onNext}>
          Get Started
        </Button>
      </div>
    </div>
  );
}
