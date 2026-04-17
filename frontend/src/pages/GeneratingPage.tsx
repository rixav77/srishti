import { useState, useEffect, useRef, useCallback } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useProjects } from "@/lib/ProjectContext";
import { runAgentsStream, AgentPlan } from "@/lib/api";
import { motion, AnimatePresence } from "framer-motion";
import { CheckCircle2, Loader2, Circle, SkipForward, Sparkles, Play, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Textarea } from "@/components/ui/textarea";

type AgentStatus = "waiting" | "running" | "done" | "error";

interface AgentStep {
  id: string;
  name: string;
  status: AgentStatus;
  output: string;
}

const AGENT_DEFS = [
  { id: "sponsor_agent",   name: "Sponsor Agent"   },
  { id: "speaker_agent",   name: "Speaker Agent"   },
  { id: "venue_agent",     name: "Venue Agent"     },
  { id: "exhibitor_agent", name: "Exhibitor Agent" },
  { id: "pricing_agent",   name: "Pricing Agent"   },
  { id: "ops_agent",       name: "Ops Agent"       },
  { id: "gtm_agent",       name: "GTM Agent"       },
];

export default function GeneratingPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { projects, updateProject, setAgentResults } = useProjects();
  const project = projects.find((p) => p.id === id);

  const [phase, setPhase] = useState<"instructions" | "running">(
    project?.customizationEnabled ? "instructions" : "running"
  );
  const [instructions, setInstructions] = useState<Record<string, string>>({});
  const [agents, setAgents] = useState<AgentStep[]>(
    AGENT_DEFS.map((d) => ({ id: d.id, name: d.name, status: "waiting", output: "" }))
  );
  const [logEntries, setLogEntries] = useState<{ agent: string; message: string }[]>([]);
  const [done, setDone] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const logsEndRef = useRef<HTMLDivElement>(null);
  const hasStarted = useRef(false);

  useEffect(() => { logsEndRef.current?.scrollIntoView({ behavior: "smooth" }); }, [logEntries]);

  const skip = useCallback(() => { navigate(`/project/${id}`); }, [navigate, id]);

  const addLog = useCallback((agent: string, message: string) => {
    setLogEntries((prev) => [...prev, { agent, message }]);
  }, []);

  const runPipeline = useCallback(async () => {
    if (!project) return;
    if (Object.keys(instructions).length > 0) {
      updateProject(project.id, { agentInstructions: instructions });
    }

    addLog("System", "Connecting to AI pipeline...");

    try {
      const plan = await runAgentsStream(project, (update) => {
        const agentId = update.agent;
        const status  = update.status;

        if (agentId === "orchestrator") return;

        if (status === "running") {
          setAgents((prev) =>
            prev.map((a) => a.id === agentId ? { ...a, status: "running" } : a)
          );
          addLog(agentId.replace("_agent", "").toUpperCase(), "Activated");
          return;
        }

        const isError    = status === "error";
        const outputText = isError
          ? `Error: ${update.results?.error?.slice(0, 80) ?? "unknown"}`
          : `Completed in ${((update.elapsed_ms ?? 0) / 1000).toFixed(1)}s`;

        setAgents((prev) =>
          prev.map((a) =>
            a.id === agentId
              ? { ...a, status: isError ? "error" : "done", output: outputText }
              : a
          )
        );
        addLog(
          agentId.replace("_agent", "").toUpperCase(),
          isError ? "⚠ Error" : "Complete ✓"
        );
      });

      if (plan) {
        setAgentResults(project.id, plan as AgentPlan);
        addLog("System", "Results saved — redirecting...");
      } else {
        addLog("System", "Pipeline complete — redirecting...");
      }

      setDone(true);
      await new Promise((r) => setTimeout(r, 1000));
      navigate(`/project/${id}`);
    } catch (err: any) {
      const msg = err?.message ?? "Pipeline failed";
      setError(msg);
      addLog("System", `Error: ${msg}`);
    }
  }, [project, id, navigate, instructions, updateProject, setAgentResults, addLog]);

  useEffect(() => {
    if (!project || hasStarted.current) return;
    if (phase === "running") {
      hasStarted.current = true;
      runPipeline();
    }
  }, [project, phase, runPipeline]);

  const handleStartWithInstructions = () => {
    setPhase("running");
    hasStarted.current = true;
    runPipeline();
  };

  if (!project) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <p className="text-muted-foreground text-sm">Project not found.</p>
      </div>
    );
  }

  const completedCount = agents.filter((a) => a.status === "done" || a.status === "error").length;
  const progressValue  = (completedCount / agents.length) * 100;

  const StatusIcon = ({ status }: { status: AgentStatus }) => {
    if (status === "done")    return <CheckCircle2  className="w-4 h-4 text-green-600" />;
    if (status === "error")   return <AlertCircle   className="w-4 h-4 text-destructive" />;
    if (status === "running") return <Loader2       className="w-4 h-4 text-primary animate-spin" />;
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
            <Button variant="ghost" size="sm" onClick={skip} className="text-muted-foreground h-7 text-xs">
              <SkipForward className="w-3.5 h-3.5 mr-1" />Skip
            </Button>
          </div>
        </header>
        <div className="flex-1 max-w-3xl mx-auto w-full px-5 py-5">
          <div className="flex items-center gap-2 mb-1">
            <Sparkles className="w-4 h-4 text-primary" />
            <h2 className="text-sm font-semibold text-foreground">Customize Agent Instructions</h2>
          </div>
          <p className="text-[11px] text-muted-foreground mb-5">Provide optional instructions for each agent. Leave blank for defaults.</p>
          <div className="space-y-3">
            {AGENT_DEFS.filter((d) => d.id !== "exhibitor_agent").map((def) => (
              <div key={def.id} className="workspace-block p-3">
                <label className="text-xs font-medium text-foreground block mb-1.5">{def.name}</label>
                <Textarea
                  placeholder={`e.g. "Focus on tier-1 only" or "Prioritize European options"`}
                  value={instructions[def.id] || ""}
                  onChange={(e) => setInstructions((prev) => ({ ...prev, [def.id]: e.target.value }))}
                  className="min-h-[50px] text-xs"
                />
              </div>
            ))}
          </div>
          <div className="mt-5 flex gap-2">
            <Button onClick={handleStartWithInstructions} className="flex-1 h-8 text-xs">
              <Play className="w-3.5 h-3.5 mr-1.5" />Run Pipeline
            </Button>
            <Button variant="outline" size="sm" className="h-8 text-xs" onClick={() => { setPhase("running"); hasStarted.current = true; runPipeline(); }}>
              Skip & Run
            </Button>
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
            <span className="text-[10px] text-muted-foreground ml-1 hidden sm:inline">
              {project.category} · {project.geography.join(", ")}
            </span>
          </div>
          <Button variant="ghost" size="sm" onClick={skip} className="text-muted-foreground h-7 text-xs">
            <SkipForward className="w-3.5 h-3.5 mr-1" />Skip
          </Button>
        </div>
      </header>

      <div className="flex-1 max-w-3xl mx-auto w-full px-5 py-5 flex flex-col gap-4">
        <div className="space-y-1.5">
          <div className="flex items-center justify-between text-xs">
            <span className="text-muted-foreground">
              {error ? "Pipeline encountered errors" : done ? "Complete" : "Generating project insights..."}
            </span>
            <span className="text-muted-foreground font-mono">{completedCount}/{agents.length}</span>
          </div>
          <Progress value={progressValue} className="h-1.5" />
        </div>

        <div className="space-y-1.5 flex-1">
          {agents.map((agent) => (
            <motion.div
              key={agent.id}
              layout
              className={`workspace-block px-3.5 py-2.5 transition-colors ${
                agent.status === "running" ? "border-primary/40 bg-primary/[0.02]" :
                agent.status === "error"   ? "border-destructive/30" :
                agent.status === "waiting" ? "opacity-50" : ""
              }`}
            >
              <div className="flex items-center gap-2.5">
                <StatusIcon status={agent.status} />
                <span className={`text-xs font-medium ${agent.status === "waiting" ? "text-muted-foreground" : "text-foreground"}`}>
                  {agent.name}
                </span>
              </div>
              <AnimatePresence>
                {(agent.status === "done" || agent.status === "error") && agent.output && (
                  <motion.p
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: "auto" }}
                    exit={{ opacity: 0, height: 0 }}
                    className={`text-[11px] mt-1 pl-[26px] ${agent.status === "error" ? "text-destructive/70" : "text-muted-foreground"}`}
                  >
                    {agent.output}
                  </motion.p>
                )}
              </AnimatePresence>
              {agent.status === "running" && (
                <div className="mt-1.5 ml-[26px]">
                  <div className="h-1 w-full bg-secondary rounded overflow-hidden">
                    <motion.div
                      className="h-full bg-primary rounded"
                      initial={{ width: "0%" }}
                      animate={{ width: "100%" }}
                      transition={{ duration: 1.8, ease: "linear" }}
                    />
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

        {error && (
          <div className="flex gap-2">
            <Button size="sm" className="h-8 text-xs flex-1" onClick={() => { hasStarted.current = false; setError(null); setAgents(AGENT_DEFS.map((d) => ({ id: d.id, name: d.name, status: "waiting", output: "" }))); setLogEntries([]); hasStarted.current = true; runPipeline(); }}>
              Retry
            </Button>
            <Button size="sm" variant="outline" className="h-8 text-xs" onClick={skip}>
              Skip to Dashboard
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}
