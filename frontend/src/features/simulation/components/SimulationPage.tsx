/**
 * Simulation Page - Trigger load/errors on services
 */
import { useState } from 'react';
import { Play, Square, Zap, AlertTriangle, Clock, Activity } from 'lucide-react';
import { useTenant } from '@/stores/authStore';
import { useServices, useSimulationRuns, useTriggerSimulation, useStopSimulation } from '../hooks';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import type { Service } from '../types';

export function SimulationPage() {
  const tenant = useTenant();
  const { data: services, isLoading: servicesLoading } = useServices();
  const { data: runs } = useSimulationRuns();
  const triggerMutation = useTriggerSimulation();
  const stopMutation = useStopSimulation();

  const [selectedService, setSelectedService] = useState<Service | null>(null);
  const [scenarioType, setScenarioType] = useState<'load' | 'error' | 'latency' | 'crash'>('load');
  const [severity, setSeverity] = useState<'low' | 'medium' | 'high' | 'critical'>('medium');
  const [duration, setDuration] = useState(60);

  const handleTrigger = () => {
    if (!selectedService || !tenant?.id) return;

    triggerMutation.mutate({
      tenant_id: tenant.id,
      service_id: selectedService.id,
      scenario_type: scenarioType,
      severity,
      duration_seconds: duration,
    });
  };

  const handleStop = (simulationId: string) => {
    stopMutation.mutate(simulationId);
  };

  const runningSimulations = runs?.filter(r => r.status === 'running') || [];

  if (servicesLoading) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="flex flex-col items-center gap-3">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
          <p className="text-sm text-muted-foreground">Loading services...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col bg-background">
      {/* Header */}
      <div className="bg-white border-b border-border px-8 py-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-semibold text-foreground">Simulation</h1>
            <p className="text-sm text-muted-foreground mt-1">
              Trigger load, errors, and failures on services to test incident response
            </p>
          </div>
          {runningSimulations.length > 0 && (
            <div className="flex items-center gap-2 px-4 py-2 bg-amber-50 border border-amber-200 rounded-lg">
              <Activity className="h-4 w-4 text-amber-600 animate-pulse" />
              <span className="text-sm font-medium text-amber-700">
                {runningSimulations.length} simulation{runningSimulations.length > 1 ? 's' : ''} running
              </span>
            </div>
          )}
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-auto p-8">
        <div className="max-w-[1600px] space-y-6">
          {/* Service Selection */}
          <div className="bg-white rounded-xl border border-border p-6">
            <h2 className="text-lg font-semibold mb-4">Select Service</h2>
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {services?.map((service) => (
                <button
                  key={service.id}
                  onClick={() => setSelectedService(service)}
                  className={cn(
                    'p-4 rounded-lg border-2 text-left transition-all hover:shadow-md',
                    selectedService?.id === service.id
                      ? 'border-primary bg-primary/5'
                      : 'border-border hover:border-primary/50'
                  )}
                >
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="font-semibold text-foreground">{service.name}</h3>
                    <span
                      className={cn(
                        'text-xs font-medium px-2 py-1 rounded-full',
                        service.status === 'healthy' && 'bg-green-100 text-green-700',
                        service.status === 'degraded' && 'bg-yellow-100 text-yellow-700',
                        service.status === 'down' && 'bg-red-100 text-red-700'
                      )}
                    >
                      {service.status}
                    </span>
                  </div>
                  <div className="flex items-center gap-4 text-sm text-muted-foreground">
                    <span>Load: {service.current_load}%</span>
                    <span>Errors: {service.error_rate}%</span>
                  </div>
                </button>
              ))}
            </div>
          </div>

          {/* Scenario Configuration */}
          {selectedService && (
            <div className="bg-white rounded-xl border border-border p-6">
              <h2 className="text-lg font-semibold mb-4">Configure Scenario</h2>
              
              <div className="space-y-6">
                {/* Scenario Type */}
                <div>
                  <label className="block text-sm font-medium mb-3">Scenario Type</label>
                  <div className="grid gap-3 md:grid-cols-4">
                    {[
                      { type: 'load' as const, icon: Zap, label: 'High Load', desc: 'CPU/Memory spike' },
                      { type: 'error' as const, icon: AlertTriangle, label: 'Error Rate', desc: '5xx errors' },
                      { type: 'latency' as const, icon: Clock, label: 'High Latency', desc: 'Slow responses' },
                      { type: 'crash' as const, icon: Square, label: 'Service Crash', desc: 'Complete failure' },
                    ].map(({ type, icon: Icon, label, desc }) => (
                      <button
                        key={type}
                        onClick={() => setScenarioType(type)}
                        className={cn(
                          'p-4 rounded-lg border-2 text-left transition-all',
                          scenarioType === type
                            ? 'border-primary bg-primary/5'
                            : 'border-border hover:border-primary/50'
                        )}
                      >
                        <Icon className={cn('h-5 w-5 mb-2', scenarioType === type ? 'text-primary' : 'text-muted-foreground')} />
                        <div className="font-medium text-sm">{label}</div>
                        <div className="text-xs text-muted-foreground mt-1">{desc}</div>
                      </button>
                    ))}
                  </div>
                </div>

                {/* Severity */}
                <div>
                  <label className="block text-sm font-medium mb-3">Severity</label>
                  <div className="grid gap-3 md:grid-cols-4">
                    {[
                      { level: 'low' as const, label: 'Low', color: 'bg-gray-100 text-gray-700 border-gray-300' },
                      { level: 'medium' as const, label: 'Medium', color: 'bg-yellow-100 text-yellow-700 border-yellow-300' },
                      { level: 'high' as const, label: 'High', color: 'bg-orange-100 text-orange-700 border-orange-300' },
                      { level: 'critical' as const, label: 'Critical', color: 'bg-red-100 text-red-700 border-red-300' },
                    ].map(({ level, label, color }) => (
                      <button
                        key={level}
                        onClick={() => setSeverity(level)}
                        className={cn(
                          'p-3 rounded-lg border-2 font-medium text-sm transition-all',
                          severity === level
                            ? color
                            : 'border-border hover:border-primary/50'
                        )}
                      >
                        {label}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Duration */}
                <div>
                  <label className="block text-sm font-medium mb-3">Duration (seconds)</label>
                  <div className="flex items-center gap-4">
                    <input
                      type="range"
                      min="30"
                      max="300"
                      step="30"
                      value={duration}
                      onChange={(e) => setDuration(Number(e.target.value))}
                      className="flex-1"
                    />
                    <span className="text-sm font-medium w-16 text-right">{duration}s</span>
                  </div>
                  <div className="flex justify-between text-xs text-muted-foreground mt-2">
                    <span>30s</span>
                    <span>5 minutes</span>
                  </div>
                </div>

                {/* Trigger Button */}
                <div className="flex items-center gap-4 pt-4 border-t">
                  <Button
                    onClick={handleTrigger}
                    disabled={triggerMutation.isPending}
                    size="lg"
                    className="gap-2"
                  >
                    <Play className="h-4 w-4" />
                    {triggerMutation.isPending ? 'Starting...' : 'Start Simulation'}
                  </Button>
                  {triggerMutation.isSuccess && (
                    <div className="text-sm text-green-600 font-medium">
                      ✓ Simulation started successfully
                    </div>
                  )}
                  {triggerMutation.isError && (
                    <div className="text-sm text-red-600 font-medium">
                      ✗ Failed to start simulation
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* Active Simulations */}
          {runs && runs.length > 0 && (
            <div className="bg-white rounded-xl border border-border p-6">
              <h2 className="text-lg font-semibold mb-4">Simulation History</h2>
              <div className="space-y-3">
                {runs.map((run) => (
                  <div
                    key={run.id}
                    className="flex items-center justify-between p-4 rounded-lg border border-border hover:bg-gray-50 transition-colors"
                  >
                    <div className="flex items-center gap-4">
                      <div
                        className={cn(
                          'flex h-10 w-10 items-center justify-center rounded-lg',
                          run.status === 'running' && 'bg-amber-100',
                          run.status === 'completed' && 'bg-green-100',
                          run.status === 'failed' && 'bg-red-100'
                        )}
                      >
                        {run.status === 'running' && <Activity className="h-5 w-5 text-amber-600 animate-pulse" />}
                        {run.status === 'completed' && <Play className="h-5 w-5 text-green-600" />}
                        {run.status === 'failed' && <AlertTriangle className="h-5 w-5 text-red-600" />}
                      </div>
                      <div>
                        <div className="font-medium text-sm">
                          {services?.find(s => s.id === run.service_id)?.name || run.service_id}
                        </div>
                        <div className="text-xs text-muted-foreground mt-1">
                          Started: {new Date(run.started_at).toLocaleString()}
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-6">
                      <div className="text-right">
                        <div className="text-sm font-medium">{run.metrics.requests_sent} requests</div>
                        <div className="text-xs text-muted-foreground">{run.metrics.errors_generated} errors</div>
                      </div>
                      {run.status === 'running' && (
                        <Button
                          onClick={() => handleStop(run.id)}
                          variant="outline"
                          size="sm"
                          className="gap-2"
                        >
                          <Square className="h-3 w-3" />
                          Stop
                        </Button>
                      )}
                      {run.incident_created && (
                        <span className="text-xs font-medium px-2 py-1 bg-red-100 text-red-700 rounded">
                          Incident: {run.incident_created}
                        </span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
