import { useState, useMemo } from "react";
import { Project, Sponsor, getSponsorsForProject } from "@/lib/data";
import { useProjects } from "@/lib/ProjectContext";
import { mapSponsors } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import AgentPageControls, { ItemFormDialog, AddCustomItemButton } from "@/components/AgentPageControls";
import { Pencil, X } from "lucide-react";

const SPONSOR_FIELDS = [
  { key: "name", label: "Sponsor Name", placeholder: "e.g. NVIDIA" },
  { key: "tier", label: "Tier", type: "select" as const, options: ["Platinum", "Gold", "Silver", "Bronze", "Custom"] },
  { key: "estimatedBudget", label: "Estimated Budget", placeholder: "e.g. $100K–$200K" },
  { key: "matchScore", label: "Match Score (0–100)", type: "number" as const, placeholder: "e.g. 90" },
  { key: "reasoning", label: "Reasoning", type: "textarea" as const, placeholder: "Why this sponsor is a good fit..." },
];

const emptyForm = (): Record<string, string> => ({ name: "", tier: "Gold", estimatedBudget: "", matchScore: "0", reasoning: "" });

export default function SponsorAgentPage({ project }: { project: Project }) {
  const { getAgentResults } = useProjects();
  const initialSponsors = useMemo(() => {
    const results = getAgentResults(project.id);
    const real = results?.sponsors ? mapSponsors(results.sponsors) : [];
    return real.length > 0 ? real : getSponsorsForProject(project);
  }, [project, getAgentResults]);
  const [sponsors, setSponsors] = useState<Sponsor[]>(initialSponsors);
  const [formOpen, setFormOpen] = useState(false);
  const [formValues, setFormValues] = useState<Record<string, string>>(emptyForm());
  const [editIndex, setEditIndex] = useState<number | null>(null);

  const handleChange = (key: string, value: string) => setFormValues((prev) => ({ ...prev, [key]: value }));

  const handleSubmit = () => {
    const sponsor: Sponsor = {
      name: formValues.name, tier: formValues.tier || "Custom",
      matchScore: Number(formValues.matchScore) || 0, reasoning: formValues.reasoning || "",
      estimatedBudget: formValues.estimatedBudget || "TBD",
    };
    if (editIndex !== null) { setSponsors((prev) => prev.map((s, i) => (i === editIndex ? sponsor : s))); }
    else { setSponsors((prev) => [...prev, sponsor]); }
    setFormOpen(false); setEditIndex(null); setFormValues(emptyForm());
  };

  const openAdd = () => { setEditIndex(null); setFormValues(emptyForm()); setFormOpen(true); };
  const openEdit = (i: number) => {
    const s = sponsors[i]; setEditIndex(i);
    setFormValues({ name: s.name, tier: s.tier, estimatedBudget: s.estimatedBudget, matchScore: String(s.matchScore), reasoning: s.reasoning });
    setFormOpen(true);
  };

  return (
    <AgentPageControls project={project} agentId="sponsor" agentName="Sponsor Agent" description="Recommended sponsors based on event category, geography, and audience profile.">
      <div className="workspace-block divide-y">
        {sponsors.map((sponsor, i) => (
          <div key={`${sponsor.name}-${i}`} className="px-4 py-3 group relative">
            <div className="flex items-start justify-between">
              <div className="min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-sm font-medium text-foreground">{sponsor.name}</span>
                  <Badge variant={sponsor.tier === "Platinum" ? "default" : sponsor.tier === "Custom" ? "outline" : "secondary"} className="text-[10px] h-4 px-1.5">{sponsor.tier}</Badge>
                  <span className="text-[11px] text-muted-foreground">{sponsor.estimatedBudget}</span>
                </div>
                {sponsor.matchScore > 0 && <Progress value={sponsor.matchScore} className="h-1 w-48 mb-1.5" />}
                {sponsor.reasoning && <p className="text-[11px] text-muted-foreground leading-relaxed">{sponsor.reasoning}</p>}
              </div>
              <div className="flex items-center gap-2 shrink-0">
                {sponsor.matchScore > 0 && (
                  <span className="text-lg font-bold text-primary font-mono">{sponsor.matchScore}%</span>
                )}
                <div className="opacity-0 group-hover:opacity-100 transition-opacity flex items-center gap-1 ml-2">
                  <button onClick={() => openEdit(i)} className="p-1 rounded bg-primary/10 hover:bg-primary/20 text-primary"><Pencil className="w-3 h-3" /></button>
                  <button onClick={() => setSponsors((prev) => prev.filter((_, idx) => idx !== i))} className="p-1 rounded bg-destructive/10 hover:bg-destructive/20 text-destructive"><X className="w-3 h-3" /></button>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
      <AddCustomItemButton label="Add Custom Sponsor" onClick={openAdd} />
      <ItemFormDialog
        open={formOpen} onOpenChange={(v) => { setFormOpen(v); if (!v) setEditIndex(null); }}
        title={editIndex !== null ? "Edit Sponsor" : "Add Custom Sponsor"} fields={SPONSOR_FIELDS}
        values={formValues} onChange={handleChange} onSubmit={handleSubmit}
        submitLabel={editIndex !== null ? "Save Changes" : "Add Sponsor"}
      />
    </AgentPageControls>
  );
}
