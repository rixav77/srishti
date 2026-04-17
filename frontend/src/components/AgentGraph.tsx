import { useMemo } from "react";
import {
  ReactFlow,
  Background,
  Controls,
  type Node,
  type Edge,
  Position,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";

type AgentStatus = "waiting" | "running" | "done" | "error";

interface AgentGraphProps {
  agents: { id: string; name: string; status: AgentStatus }[];
}

const STATUS_COLORS: Record<AgentStatus, { bg: string; border: string; text: string }> = {
  waiting: { bg: "#f4f4f5", border: "#d4d4d8", text: "#71717a" },
  running: { bg: "#eff6ff", border: "#3b82f6", text: "#1d4ed8" },
  done:    { bg: "#f0fdf4", border: "#22c55e", text: "#15803d" },
  error:   { bg: "#fef2f2", border: "#ef4444", text: "#b91c1c" },
};

const STATUS_LABELS: Record<AgentStatus, string> = {
  waiting: "⏳",
  running: "⚡",
  done: "✅",
  error: "❌",
};

export default function AgentGraph({ agents }: AgentGraphProps) {
  const agentMap = useMemo(() => {
    const m: Record<string, AgentStatus> = {};
    agents.forEach((a) => { m[a.id] = a.status; });
    return m;
  }, [agents]);

  const nodes: Node[] = useMemo(() => {
    const positions: Record<string, { x: number; y: number }> = {
      sponsor_agent:   { x: 0,   y: 0   },
      speaker_agent:   { x: 200, y: 0   },
      venue_agent:     { x: 400, y: 0   },
      exhibitor_agent: { x: 600, y: 0   },
      pricing_agent:   { x: 100, y: 140 },
      ops_agent:       { x: 300, y: 140 },
      gtm_agent:       { x: 500, y: 140 },
    };

    const labels: Record<string, string> = {
      sponsor_agent: "Sponsor",
      speaker_agent: "Speaker",
      venue_agent: "Venue",
      exhibitor_agent: "Exhibitor",
      pricing_agent: "Pricing",
      ops_agent: "Ops",
      gtm_agent: "GTM",
    };

    return Object.entries(positions).map(([id, pos]) => {
      const status = agentMap[id] || "waiting";
      const colors = STATUS_COLORS[status];
      return {
        id,
        position: pos,
        sourcePosition: Position.Bottom,
        targetPosition: Position.Top,
        data: {
          label: `${STATUS_LABELS[status]} ${labels[id] || id}`,
        },
        style: {
          background: colors.bg,
          border: `2px solid ${colors.border}`,
          borderRadius: 8,
          padding: "8px 16px",
          fontSize: 12,
          fontWeight: 600,
          color: colors.text,
          minWidth: 110,
          textAlign: "center" as const,
          boxShadow: status === "running" ? `0 0 12px ${colors.border}40` : "none",
        },
      };
    });
  }, [agentMap]);

  const edges: Edge[] = useMemo(() => [
    { id: "e1", source: "sponsor_agent",   target: "pricing_agent", animated: agentMap["pricing_agent"] === "running" },
    { id: "e2", source: "speaker_agent",   target: "pricing_agent", animated: agentMap["pricing_agent"] === "running" },
    { id: "e3", source: "venue_agent",     target: "ops_agent",     animated: agentMap["ops_agent"] === "running" },
    { id: "e4", source: "exhibitor_agent", target: "gtm_agent",     animated: agentMap["gtm_agent"] === "running" },
    { id: "e5", source: "sponsor_agent",   target: "gtm_agent",     animated: agentMap["gtm_agent"] === "running" },
    { id: "e6", source: "pricing_agent",   target: "ops_agent",     animated: agentMap["ops_agent"] === "running" },
  ], [agentMap]);

  return (
    <div className="w-full h-[260px] border rounded bg-card">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        fitView
        fitViewOptions={{ padding: 0.3 }}
        nodesDraggable={false}
        nodesConnectable={false}
        elementsSelectable={false}
        panOnDrag={false}
        zoomOnScroll={false}
        zoomOnPinch={false}
        proOptions={{ hideAttribution: true }}
      >
        <Background gap={20} size={1} color="#e4e4e7" />
      </ReactFlow>
    </div>
  );
}
