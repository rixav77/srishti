import { useState, useMemo } from "react";
import { Project, getOpsForProject } from "@/lib/data";
import { useProjects } from "@/lib/ProjectContext";
import { mapOps } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { Checkbox } from "@/components/ui/checkbox";
import { Users, Clock, Pencil, X } from "lucide-react";
import AgentPageControls, { ItemFormDialog, AddCustomItemButton } from "@/components/AgentPageControls";

interface OpsTask { task: string; status: string; priority: string; }

const TASK_FIELDS = [
  { key: "name", label: "Task Name", placeholder: "e.g. Venue contract finalization" },
  { key: "priority", label: "Priority", type: "select" as const, options: ["High", "Medium", "Low"] },
  { key: "status", label: "Status", type: "select" as const, options: ["Pending", "In Progress", "Done"] },
];

const emptyForm = (): Record<string, string> => ({ name: "", priority: "Medium", status: "Pending" });

export default function OpsAgentPage({ project }: { project: Project }) {
  const { getAgentResults } = useProjects();
  const ops = useMemo(() => {
    const results = getAgentResults(project.id);
    return (results?.ops ? mapOps(results.ops) : null) ?? getOpsForProject(project);
  }, [project, getAgentResults]);
  const [checklist, setChecklist] = useState<OpsTask[]>(ops.checklist);
  const [formOpen, setFormOpen] = useState(false);
  const [formValues, setFormValues] = useState<Record<string, string>>(emptyForm());
  const [editIndex, setEditIndex] = useState<number | null>(null);

  const handleChange = (key: string, value: string) => setFormValues((prev) => ({ ...prev, [key]: value }));
  const handleSubmit = () => {
    const task: OpsTask = { task: formValues.name, status: formValues.status || "Pending", priority: formValues.priority || "Medium" };
    if (editIndex !== null) { setChecklist((prev) => prev.map((t, i) => (i === editIndex ? task : t))); }
    else { setChecklist((prev) => [...prev, task]); }
    setFormOpen(false); setEditIndex(null); setFormValues(emptyForm());
  };

  const openAdd = () => { setEditIndex(null); setFormValues(emptyForm()); setFormOpen(true); };
  const openEdit = (i: number) => {
    const t = checklist[i]; setEditIndex(i);
    setFormValues({ name: t.task, priority: t.priority, status: t.status });
    setFormOpen(true);
  };

  return (
    <AgentPageControls project={project} agentId="ops" agentName="Event Ops Agent" description="Operational planning, staffing, and logistics checklist.">
      <div className="grid grid-cols-2 gap-3">
        <div className="workspace-block px-3.5 py-3 flex items-center gap-2.5">
          <Users className="w-4 h-4 text-primary" />
          <div>
            <p className="text-[10px] text-muted-foreground uppercase tracking-wide">Staff Required</p>
            <p className="text-lg font-bold text-foreground">{ops.staffEstimate} people</p>
          </div>
        </div>
        <div className="workspace-block px-3.5 py-3 flex items-center gap-2.5">
          <Clock className="w-4 h-4 text-primary" />
          <div>
            <p className="text-[10px] text-muted-foreground uppercase tracking-wide">Setup Time</p>
            <p className="text-lg font-bold text-foreground">{ops.daysToSetup} days</p>
          </div>
        </div>
      </div>

      <div className="workspace-block">
        <div className="px-4 py-2.5 border-b">
          <span className="section-label">Operations Checklist</span>
        </div>
        <div className="divide-y">
          {checklist.map((item, i) => (
            <div key={`${item.task}-${i}`} className="flex items-center justify-between px-4 py-2.5 group">
              <div className="flex items-center gap-2.5">
                <Checkbox />
                <span className="text-xs text-foreground">{item.task}</span>
              </div>
              <div className="flex items-center gap-2">
                <Badge variant={item.priority === "High" ? "default" : item.priority === "Medium" ? "secondary" : "outline"} className="text-[10px] h-4 px-1.5">{item.priority}</Badge>
                <div className="opacity-0 group-hover:opacity-100 transition-opacity flex items-center gap-1">
                  <button onClick={() => openEdit(i)} className="p-1 rounded bg-primary/10 hover:bg-primary/20 text-primary"><Pencil className="w-3 h-3" /></button>
                  <button onClick={() => setChecklist((prev) => prev.filter((_, idx) => idx !== i))} className="p-1 rounded bg-destructive/10 hover:bg-destructive/20 text-destructive"><X className="w-3 h-3" /></button>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
      <AddCustomItemButton label="Add Custom Task" onClick={openAdd} />

      <ItemFormDialog
        open={formOpen} onOpenChange={(v) => { setFormOpen(v); if (!v) setEditIndex(null); }}
        title={editIndex !== null ? "Edit Task" : "Add Custom Task"} fields={TASK_FIELDS}
        values={formValues} onChange={handleChange} onSubmit={handleSubmit}
        submitLabel={editIndex !== null ? "Save Changes" : "Add Task"}
      />
    </AgentPageControls>
  );
}
