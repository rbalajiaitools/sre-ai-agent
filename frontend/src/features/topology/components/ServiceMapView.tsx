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

const edgeStyles = {
  DEPENDS_ON: { strokeDasharray: '0', animated: false },
  CALLS: { strokeDasharray: '5,5', animated: true },
  READS_FROM: { strokeDasharray: '2,2', animated: false },
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
    const flowEdges: Edge[] = filteredEdges.map((edge: ServiceEdge) => ({
      id: edge.id,
      source: edge.source,
      target: edge.target,
      type: 'smoothstep',
      animated: edgeStyles[edge.relationship].animated,
      style: {
        strokeDasharray: edgeStyles[edge.relationship].strokeDasharray,
        stroke: 'hsl(var(--muted-foreground))',
      },
      markerEnd: {
        type: MarkerType.ArrowClosed,
        color: 'hsl(var(--muted-foreground))',
      },
      label: edge.relationship.replace('_', ' '),
      labelStyle: { fontSize: 10, fill: 'hsl(var(--muted-foreground))' },
    }));

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
    return (
      <div className="flex h-full items-center justify-center">
        <div className="text-center">
          <p className="text-sm text-red-500">
            Failed to load topology: {topologyQuery.error?.message}
          </p>
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
    <div className="h-full w-full">
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
            return status === 'healthy'
              ? '#22c55e'
              : status === 'degraded'
              ? '#eab308'
              : status === 'down'
              ? '#ef4444'
              : '#6b7280';
          }}
          maskColor="rgba(0, 0, 0, 0.1)"
        />
      </ReactFlow>
    </div>
  );
}
