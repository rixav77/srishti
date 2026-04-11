import { useState, useEffect, useRef, useCallback } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useProjects } from "@/lib/ProjectContext";
import { getSponsorsForProject, getSpeakersForProject, getVenuesForProject, getPricingForProject, getGTMForProject, getOpsForProject } from "@/lib/data";
import { motion, AnimatePresence } from "framer-motion";
import { CheckCircle2, Loader2, Circle, SkipForward, MapPin, Users, Tag, Sparkles, Play } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Textarea } from "@/components/ui/textarea";

type AgentStatus = "waiting" | "running" | "done";

interface AgentStep { id: string; name: string; status: AgentStatus; output: string; logs: string[]; }

const AGENT_DEFS = [
  { id: "sponsor", name: "Sponsor Agent", getLogs: () => ["Scanning sponsor database...", "Matching sponsors to event profile...", "Ranking by budget alignment..."],
    getOutput: (p: any) => { const s = getSponsorsForProject(p); return `${s.length} sponsors matched. Top: ${s[0]?.name} (${s[0]?.matchScore}% match).`; } },
  { id: "speaker", name: "Speaker Agent", getLogs: () => ["Querying speaker graph...", "Filtering by topic relevance...", "Ranking candidates..."],
    getOutput: (p: any) => { const s = getSpeakersForProject(p); return `${s.length} speakers identified. Top: ${s[0]?.name} — ${s[0]?.topic}.`; } },
  { id: "venue", name: "Venue Agent", getLogs: () => ["Evaluating venue options...", "Scoring by capacity and location...", "Finalizing shortlist..."],
    getOutput: (p: any) => { const v = getVenuesForProject(p); return `${v.length} venues shortlisted. Top: ${v[0]?.name}, ${v[0]?.city}.`; } },
  { id: "pricing", name: "Pricing Agent", getLogs: () => ["Running pricing model...", "Predicting footfall...", "Optimizing ticket tiers..."],
    getOutput: (p: any) => { const pr = getPricingForProject(p); return `Tickets: ${pr.earlyBird}–${pr.vip}. Revenue est: ${pr.revenueEstimate}.`; } },
  { id: "gtm", name: "GTM Agent", getLogs: () => ["Generating GTM strategy...", "Selecting channels...", "Computing reach estimates..."],
    getOutput: (p: any) => { const g = getGTMForProject(p); return `${g.channels.length} channels. ${g.timeline.length} campaign phases.`; } },
  { id: "ops", name: "Ops Agent", getLogs: () => ["Compiling ops plan...", "Identifying workstreams...", "Calculating critical path..."],
    getOutput: (p: any) => { const o = getOpsForProject(p); return `${o.checklist.length} tasks. ${o.daysToSetup} setup days. Staff: ${o.staffEstimate}.`; } },
];

export default function GeneratingPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { projects, updateProject } = useProjects();
  const project = projects.find((p) => p.id === id);

  const [phase, setPhase] = useState<"instructions" | "running">(project?.customizationEnabled ? "instructions" : "running");
  const [instructions, setInstructions] = useState<Record<string, string>>({});
  const [agents, setAgents] = useState<AgentStep[]>(AGENT_DEFS.map((d) => ({ id: d.id, name: d.name, status: "waiting", output: "", logs: [] })));
  const [logEntries, setLogEntries] = useState<{ agent: string; message: string }[]>([]);
  const [done, setDone] = useState(false);
  const logsEndRef = useRef<HTMLDivElement>(null);
  const hasStarted = useRef(false);

  useEffect(() => { logsEndRef.current?.scrollIntoView({ behavior: "smooth" }); }, [logEntries]);

  const skip = useCallback(() => { navigate(`/project/${id}`); }, [navigate, id]);

  const runPipeline = useCallback(async () => {
    if (!project) return;
    if (Object.keys(instructions).length > 0) updateProject(project.id, { agentInstructions: instructions });

    for (let i = 0; i < AGENT_DEFS.length; i++) {
      const def = AGENT_DEFS[i];
      setAgents((prev) => prev.map((a, idx) => idx === i ? { ...a, status: "running" } : a));
      setLogEntries((prev) => [...prev, { agent: def.name, message: "Activated" }]);

      if (instructions[def.id]) {
        await new Promise((r) => setTimeout(r, 300));
        setLogEntries((prev) => [...prev, { agent: def.name, message: `Instruction: "${instructions[def.id]}"` }]);
      }

      for (const log of def.getLogs()) {
        await new Promise((r) => setTimeout(r, 350 + Math.random() * 350));
        setLogEntries((prev) => [...prev, { agent: def.name, message: log }]);
      }

      await new Promise((r) => setTimeout(r, 250));
      const output = def.getOutput(project);
      setAgents((prev) => prev.map((a, idx) => idx === i ? { ...a, status: "done", output } : a));
      setLogEntries((prev) => [...prev, { agent: def.name, message: "Complete ✓" }]);
    }

    setLogEntries((prev) => [...prev, { agent: "System", message: "All agents complete — redirecting..." }]);
    setDone(true);
    await new Promise((r) => setTimeout(r, 1200));
    navigate(`/project/${id}`);
  }, [project, id, navigate, instructions, updateProject]);

  useEffect(() => {
    if (!project || hasStarted.current) return;
    if (phase === "running") { hasStarted.current = true; runPipeline(); }
  }, [project, phase, runPipeline]);

  const handleStartWithInstructions = () => { setPhase("running"); hasStarted.current = true; runPipeline(); };

  if (!project) return <div className="min-h-screen flex items-center justify-center bg-background"><p className="text-muted-foreground text-sm">Project not found.</p></div>;

  const completedCount = agents.filter((a) => a.status === "done").length;
  const progressValue = (completedCount / agents.length) * 100;

  const StatusIcon = ({ status }: { status: AgentStatus }) => {
    if (status === "done") return <CheckCircle2 className="w-4 h-4 text-green-600" />;
    if (status === "running") return <Loader2 className="w-4 h-4 text-primary animate-spin" />;
    return <Circle className="w-4 h-4 text-muted-foreground/30" />;
  };

  if (phase === "instructions") {
    return (
      <div className="min-h-screen bg-background flex flex-col">
        <header className="border-b bg-card h-10 flex items-center px-5">
          <div className="max-w-3xl mx-auto w-full flex items-center justify-between">
            <div className="flex items-center gap-2">
               <span className="text-xs font-semibold text-foreground tracking-tighter uppercase">Orchestra</span>
              <span className="text-xs font-medium text-foreground">{project.name}</span>
            </div>
            <Button variant="ghost" size="sm" onClick={skip} className="text-muted-foreground h-7 text-xs"><SkipForward className="w-3.5 h-3.5 mr-1" />Skip</Button>
          </div>
        </header>
        <div className="flex-1 max-w-3xl mx-auto w-full px-5 py-5">
          <div className="flex items-center gap-2 mb-1">
            <Sparkles className="w-4 h-4 text-primary" />
            <h2 className="text-sm font-semibold text-foreground">Customize Agent Instructions</h2>
          </div>
          <p className="text-[11px] text-muted-foreground mb-5">Provide optional instructions for each agent. Leave blank for defaults.</p>
          <div className="space-y-3">
            {AGENT_DEFS.map((def) => (
              <div key={def.id} className="workspace-block p-3">
                <label className="text-xs font-medium text-foreground block mb-1.5">{def.name}</label>
                <Textarea placeholder={`e.g. "Focus on tier-1 only" or "Prioritize European options"`} value={instructions[def.id] || ""} onChange={(e) => setInstructions((prev) => ({ ...prev, [def.id]: e.target.value }))} className="min-h-[50px] text-xs" />
              </div>
            ))}
          </div>
          <div className="mt-5 flex gap-2">
            <Button onClick={handleStartWithInstructions} className="flex-1 h-8 text-xs"><Play className="w-3.5 h-3.5 mr-1.5" />Run Pipeline</Button>
            <Button variant="outline" size="sm" className="h-8 text-xs" onClick={() => { setPhase("running"); hasStarted.current = true; runPipeline(); }}>Skip & Run</Button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background flex flex-col">
      <header className="border-b bg-card h-10 flex items-center px-5">
        <div className="max-w-3xl mx-auto w-full flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold text-foreground tracking-tighter uppercase">Orchestra</span>
            <span className="text-xs font-medium text-foreground">{project.name}</span>
            <span className="text-[10px] text-muted-foreground ml-1 hidden sm:inline">{project.category} · {project.geography.join(", ")}</span>
          </div>
          <Button variant="ghost" size="sm" onClick={skip} className="text-muted-foreground h-7 text-xs"><SkipForward className="w-3.5 h-3.5 mr-1" />Skip</Button>
        </div>
      </header>

      <div className="flex-1 max-w-3xl mx-auto w-full px-5 py-5 flex flex-col gap-4">
        <div className="space-y-1.5">
          <div className="flex items-center justify-between text-xs">
            <span className="text-muted-foreground">Generating project insights...</span>
            <span className="text-muted-foreground font-mono">{completedCount}/{agents.length}</span>
          </div>
          <Progress value={progressValue} className="h-1.5" />
        </div>

        <div className="space-y-1.5 flex-1">
          {agents.map((agent) => (
            <motion.div key={agent.id} layout className={`workspace-block px-3.5 py-2.5 transition-colors ${agent.status === "running" ? "border-primary/40 bg-primary/[0.02]" : agent.status === "done" ? "" : "opacity-50"}`}>
              <div className="flex items-center gap-2.5">
                <StatusIcon status={agent.status} />
                <span className={`text-xs font-medium ${agent.status === "waiting" ? "text-muted-foreground" : "text-foreground"}`}>{agent.name}</span>
                {instructions[agent.id] && <span className="text-[9px] text-primary bg-primary/10 px-1.5 py-0.5 rounded">Custom</span>}
              </div>
              <AnimatePresence>
                {agent.status === "done" && agent.output && (
                  <motion.p initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: "auto" }} exit={{ opacity: 0, height: 0 }} className="text-[11px] text-muted-foreground mt-1 ml-6.5 pl-[26px]">{agent.output}</motion.p>
                )}
              </AnimatePresence>
              {agent.status === "running" && (
                <div className="mt-1.5 ml-[26px]">
                  <div className="h-1 w-full bg-secondary rounded overflow-hidden">
                    <motion.div className="h-full bg-primary rounded" initial={{ width: "0%" }} animate={{ width: "100%" }} transition={{ duration: 1.8, ease: "linear" }} />
                  </div>
                </div>
              )}
            </motion.div>
          ))}
        </div>

        <div className="workspace-block p-3 h-36 overflow-y-auto">
          <div className="section-label mb-2">Activity Log</div>
          <div className="space-y-0.5 text-[11px] font-mono">
            {logEntries.map((entry, i) => (
              <motion.div key={i} initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex gap-1.5">
                <span className="text-primary font-semibold shrink-0">[{entry.agent}]</span>
                <span className="text-muted-foreground">{entry.message}</span>
              </motion.div>
            ))}
            <div ref={logsEndRef} />
          </div>
        </div>
      </div>
    </div>
  );
}
