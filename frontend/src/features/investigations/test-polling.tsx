/**
 * Test component to verify polling is working
 * Add this temporarily to InvestigationDetailPage to debug
 */
import { useEffect, useState } from 'react';

export function PollingDebug({ investigationId }: { investigationId: string }) {
  const [pollCount, setPollCount] = useState(0);
  const [lastData, setLastData] = useState<any>(null);

  useEffect(() => {
    const interval = setInterval(async () => {
      try {
        const response = await fetch(`http://localhost:8000/api/v1/investigations/${investigationId}`);
        const data = await response.json();
        setPollCount(prev => prev + 1);
        setLastData(data);
        console.log(`[POLL #${pollCount + 1}]`, {
          status: data.status,
          agent_count: data.agent_results?.length || 0,
          timestamp: new Date().toISOString()
        });
      } catch (error) {
        console.error('Poll error:', error);
      }
    }, 2000);

    return () => clearInterval(interval);
  }, [investigationId, pollCount]);

  return (
    <div style={{
      position: 'fixed',
      bottom: 10,
      right: 10,
      background: 'black',
      color: 'lime',
      padding: '10px',
      fontFamily: 'monospace',
      fontSize: '12px',
      zIndex: 9999,
      maxWidth: '300px'
    }}>
      <div>Poll Count: {pollCount}</div>
      <div>Status: {lastData?.status || 'N/A'}</div>
      <div>Agents: {lastData?.agent_results?.length || 0}</div>
      <div>Last Update: {new Date().toLocaleTimeString()}</div>
    </div>
  );
}
