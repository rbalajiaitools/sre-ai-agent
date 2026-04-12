/**
 * Main onboarding wizard page
 */
import { useState } from 'react';
import { Check } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { OnboardingStep } from '../types';
import { WelcomeStep } from '../steps/WelcomeStep';
import { ConnectProviderStep } from '../steps/ConnectProviderStep';
import { ConnectServiceNowStep } from '../steps/ConnectServiceNowStep';
import { ValidateStep } from '../steps/ValidateStep';
import { DiscoverStep } from '../steps/DiscoverStep';
import { CompleteStep } from '../steps/CompleteStep';
import type { ConfiguredProvider, ServiceNowConfig, DiscoveryResult } from '../types';

const STEPS = [
  { key: OnboardingStep.WELCOME, label: 'Welcome' },
  { key: OnboardingStep.CONNECT_PROVIDER, label: 'Connect Provider' },
  { key: OnboardingStep.CONNECT_SERVICENOW, label: 'ServiceNow' },
  { key: OnboardingStep.VALIDATE, label: 'Validate' },
  { key: OnboardingStep.DISCOVER, label: 'Discover' },
  { key: OnboardingStep.COMPLETE, label: 'Complete' },
];

export function OnboardingPage() {
  const [currentStep, setCurrentStep] = useState(OnboardingStep.WELCOME);
  const [providers, setProviders] = useState<ConfiguredProvider[]>([]);
  const [serviceNowConfig, setServiceNowConfig] = useState<ServiceNowConfig | null>(null);
  const [discoveryResult, setDiscoveryResult] = useState<DiscoveryResult | null>(null);

  const currentStepIndex = STEPS.findIndex((s) => s.key === currentStep);

  const handleNext = () => {
    const nextIndex = currentStepIndex + 1;
    if (nextIndex < STEPS.length) {
      setCurrentStep(STEPS[nextIndex].key);
    }
  };

  const handleBack = () => {
    const prevIndex = currentStepIndex - 1;
    if (prevIndex >= 0) {
      setCurrentStep(STEPS[prevIndex].key);
    }
  };

  const handleProviderAdded = (provider: ConfiguredProvider) => {
    setProviders([...providers, provider]);
  };

  const handleServiceNowValidated = (config: ServiceNowConfig) => {
    setServiceNowConfig(config);
    handleNext();
  };

  const handleServiceNowSkip = () => {
    handleNext();
  };

  const handleValidateAll = () => {
    handleNext();
  };

  const handleFixProvider = (providerId: string) => {
    setCurrentStep(OnboardingStep.CONNECT_PROVIDER);
  };

  const handleDiscoveryComplete = (result: DiscoveryResult) => {
    setDiscoveryResult(result);
    setTimeout(() => handleNext(), 2000);
  };

  const canContinue = () => {
    switch (currentStep) {
      case OnboardingStep.WELCOME:
        return true;
      case OnboardingStep.CONNECT_PROVIDER:
        return providers.length > 0;
      case OnboardingStep.CONNECT_SERVICENOW:
        return false;
      case OnboardingStep.VALIDATE:
        return providers.every((p) => p.validated);
      case OnboardingStep.DISCOVER:
        return false;
      case OnboardingStep.COMPLETE:
        return false;
      default:
        return false;
    }
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <div className="border-b bg-card">
        <div className="mx-auto max-w-5xl px-6 py-4">
          <h1 className="text-xl font-bold">SRE AI Agent</h1>
        </div>
      </div>

      {/* Progress Stepper */}
      <div className="border-b bg-card">
        <div className="mx-auto max-w-5xl px-6 py-6">
          <nav aria-label="Onboarding progress">
            <ol className="flex items-center justify-between">
              {STEPS.map((step, index) => {
                const isActive = index === currentStepIndex;
                const isComplete = index < currentStepIndex;

                return (
                  <li key={step.key} className="flex flex-1 items-center">
                    <div className="flex items-center gap-3">
                      <div
                        className={`flex h-8 w-8 items-center justify-center rounded-full border-2 text-sm font-medium transition-colors ${
                          isComplete
                            ? 'border-primary bg-primary text-primary-foreground'
                            : isActive
                            ? 'border-primary bg-background text-primary'
                            : 'border-muted bg-background text-muted-foreground'
                        }`}
                        aria-current={isActive ? 'step' : undefined}
                      >
                        {isComplete ? <Check className="h-4 w-4" /> : index + 1}
                      </div>
                      <span
                        className={`hidden text-sm md:inline ${
                          isActive ? 'font-medium' : 'text-muted-foreground'
                        }`}
                      >
                        {step.label}
                      </span>
                    </div>
                    {index < STEPS.length - 1 && (
                      <div
                        className={`mx-2 h-0.5 flex-1 ${
                          isComplete ? 'bg-primary' : 'bg-muted'
                        }`}
                        aria-hidden="true"
                      />
                    )}
                  </li>
                );
              })}
            </ol>
          </nav>
        </div>
      </div>

      {/* Content */}
      <div className="mx-auto max-w-2xl px-6 py-8">
        <div className="rounded-lg border bg-card p-8">
          {currentStep === OnboardingStep.WELCOME && (
            <WelcomeStep onNext={handleNext} />
          )}

          {currentStep === OnboardingStep.CONNECT_PROVIDER && (
            <ConnectProviderStep
              providers={providers}
              onProviderAdded={handleProviderAdded}
            />
          )}

          {currentStep === OnboardingStep.CONNECT_SERVICENOW && (
            <ConnectServiceNowStep
              onValidated={handleServiceNowValidated}
              onSkip={handleServiceNowSkip}
            />
          )}

          {currentStep === OnboardingStep.VALIDATE && (
            <ValidateStep
              providers={providers}
              serviceNowConfigured={!!serviceNowConfig}
              onValidateAll={handleValidateAll}
              onFixProvider={handleFixProvider}
              isValidating={false}
            />
          )}

          {currentStep === OnboardingStep.DISCOVER && (
            <DiscoverStep onComplete={handleDiscoveryComplete} />
          )}

          {currentStep === OnboardingStep.COMPLETE && (
            <CompleteStep
              providers={providers}
              discoveryResult={discoveryResult}
            />
          )}
        </div>

        {/* Navigation */}
        {currentStep !== OnboardingStep.WELCOME &&
          currentStep !== OnboardingStep.CONNECT_SERVICENOW &&
          currentStep !== OnboardingStep.DISCOVER &&
          currentStep !== OnboardingStep.COMPLETE && (
            <div className="mt-6 flex justify-between">
              <Button variant="outline" onClick={handleBack}>
                Back
              </Button>
              <Button onClick={handleNext} disabled={!canContinue()}>
                Continue
              </Button>
            </div>
          )}
      </div>
    </div>
  );
}
