/**
 * Service map view with React Flow
 */
import { useCallback, useMemo, useState } from 'react';
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  MarkerType,
  type Node,
  type Edge,
} from 'reactflow';
import dagre from '@dagrejs/dagre';
import { Loader2 } from 'lucide-react';
import { ServiceFlowNode } from './ServiceFlowNode';
import { useTopologyGraph } from '../hooks';
import type { ServiceNode, ServiceEdge, ServiceStatus } from '../types';
import { ProviderType } from '@/types';
import 'reactflow/dist/style.css';

interface ServiceMapViewProps {
  onServiceClick: (serviceName: string) => void;
  providerFilter: ProviderType[];
  statusFilter: ServiceStatus[];
}

const nodeTypes = {
  service: ServiceFlowNode,
};

const edgeStyles: Record<string, { strokeDasharray: string; animated: boolean }> = {
  DEPENDS_ON: { strokeDasharray: '0', animated: false },
  CALLS: { strokeDasharray: '5,5', animated: true },
  READS_FROM: { strokeDasharray: '2,2', animated: false },
  WRITES_TO: { strokeDasharray: '2,2', animated: false },
  CONTAINS: { strokeDasharray: '0', animated: false },
  HOSTS: { strokeDasharray: '0', animated: false },
  ROUTES_TO: { strokeDasharray: '5,5', animated: false },
  INVOKES: { strokeDasharray: '5,5', animated: true },
};

// Dagre layout configuration
const getLayoutedElements = (nodes: Node[], edges: Edge[]) => {
  const dagreGraph = new dagre.graphlib.Graph();
  dagreGraph.setDefaultEdgeLabel(() => ({}));
  dagreGraph.setGraph({ rankdir: 'TB', ranksep: 100, nodesep: 80 });

  nodes.forEach((node) => {
    dagreGraph.setNode(node.id, { width: 200, height: 120 });
  });

  edges.forEach((edge) => {
    dagreGraph.setEdge(edge.source, edge.target);
  });

  dagre.layout(dagreGraph);

  const layoutedNodes = nodes.map((node) => {
    const nodeWithPosition = dagreGraph.node(node.id);
    return {
      ...node,
      position: {
        x: nodeWithPosition.x - 100,
        y: nodeWithPosition.y - 60,
      },
    };
  });

  return { nodes: layoutedNodes, edges };
};

export function ServiceMapView({
  onServiceClick,
  providerFilter,
  statusFilter,
}: ServiceMapViewProps) {
  const topologyQuery = useTopologyGraph();
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);

  // Convert topology data to React Flow format
  const { flowNodes, flowEdges } = useMemo(() => {
    if (!topologyQuery.data) return { flowNodes: [], flowEdges: [] };

    // Filter nodes
    let filteredNodes = topologyQuery.data.nodes;

    if (providerFilter.length > 0) {
      filteredNodes = filteredNodes.filter((n) => providerFilter.includes(n.provider));
    }

    if (statusFilter.length > 0) {
      filteredNodes = filteredNodes.filter((n) => statusFilter.includes(n.status));
    }

    const filteredNodeIds = new Set(filteredNodes.map((n) => n.id));

    // Convert to React Flow nodes
    const flowNodes: Node[] = filteredNodes.map((node: ServiceNode) => ({
      id: node.id,
      type: 'service',
      data: node,
      position: { x: 0, y: 0 }, // Will be set by dagre
    }));

    // Filter edges to only include those between visible nodes
    const filteredEdges = topologyQuery.data.edges.filter(
      (e: ServiceEdge) => filteredNodeIds.has(e.source) && filteredNodeIds.has(e.target)
    );

    // Convert to React Flow edges
    const flowEdges: Edge[] = filteredEdges.map((edge: ServiceEdge) => {
      const edgeStyle = edgeStyles[edge.relationship] || { strokeDasharray: '0', animated: false };
      
      return {
        id: edge.id,
        source: edge.source,
        target: edge.target,
        type: 'smoothstep',
        animated: edgeStyle.animated,
        style: {
          strokeDasharray: edgeStyle.strokeDasharray,
          stroke: 'hsl(var(--muted-foreground))',
        },
        markerEnd: {
          type: MarkerType.ArrowClosed,
          color: 'hsl(var(--muted-foreground))',
        },
        label: edge.relationship.replace(/_/g, ' '),
        labelStyle: { fontSize: 10, fill: 'hsl(var(--muted-foreground))' },
      };
    });

    return { flowNodes, flowEdges };
  }, [topologyQuery.data, providerFilter, statusFilter]);

  // Apply dagre layout when nodes/edges change
  useMemo(() => {
    if (flowNodes.length > 0) {
      const { nodes: layoutedNodes, edges: layoutedEdges } = getLayoutedElements(
        flowNodes,
        flowEdges
      );
      setNodes(layoutedNodes);
      setEdges(layoutedEdges);
    }
  }, [flowNodes, flowEdges, setNodes, setEdges]);

  const onNodeClick = useCallback(
    (_event: React.MouseEvent, node: Node) => {
      onServiceClick(node.data.name);
    },
    [onServiceClick]
  );

  if (topologyQuery.isLoading) {
    return (
      <div className="flex h-full items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (topologyQuery.isError) {
    const errorMessage = topologyQuery.error?.message || '';
    const isNoIntegration = errorMessage.includes('No AWS integration') || errorMessage.includes('No active AWS integration');
    
    return (
      <div className="flex h-full items-center justify-center">
        <div className="text-center space-y-4">
          <p className="text-sm text-muted-foreground">
            {isNoIntegration ? 'No AWS integration configured' : `Failed to load topology: ${errorMessage}`}
          </p>
          {isNoIntegration && (
            <div>
              <p className="text-xs text-muted-foreground mb-3">
                Configure AWS credentials to discover your infrastructure
              </p>
              <a
                href="/settings"
                className="inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 bg-primary text-primary-foreground hover:bg-primary/90 h-10 px-4 py-2"
              >
                Go to Settings
              </a>
            </div>
          )}
        </div>
      </div>
    );
  }

  if (!topologyQuery.data || topologyQuery.data.nodes.length === 0) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="text-center">
          <p className="text-muted-foreground">No services discovered yet.</p>
          <p className="mt-1 text-sm text-muted-foreground">
            Connect a provider to start mapping your infrastructure.
          </p>
        </div>
      </div>
    );
  }

  if (nodes.length === 0) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="text-center">
          <p className="text-muted-foreground">No services match the current filters.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full w-full" role="application" aria-label="Service topology graph">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodeClick={onNodeClick}
        nodeTypes={nodeTypes}
        fitView
        minZoom={0.1}
        maxZoom={1.5}
      >
        <Background />
        <Controls />
        <MiniMap
          nodeColor={(node) => {
            const status = (node.data as ServiceNode).status;
            // Use CSS custom properties that match Tailwind colors
            if (status === 'healthy') return 'hsl(142 76% 36%)'; // green-600
            if (status === 'degraded') return 'hsl(48 96% 53%)'; // yellow-500
            if (status === 'down') return 'hsl(0 84% 60%)'; // red-500
            return 'hsl(220 9% 46%)'; // gray-600
          }}
          maskColor="hsl(var(--background) / 0.8)"
        />
      </ReactFlow>
    </div>
  );
}
