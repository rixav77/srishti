import { useState, useMemo } from "react";
import { Project, Sponsor, getSponsorsForProject } from "@/lib/data";
import { useProjects } from "@/lib/ProjectContext";
import { mapSponsors } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import AgentPageControls, { ItemFormDialog, AddCustomItemButton } from "@/components/AgentPageControls";
import { Pencil, X, Mail, Loader2, Copy, Check } from "lucide-react";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "https://srishti-production.up.railway.app";

const SPONSOR_FIELDS = [
  { key: "name", label: "Sponsor Name", placeholder: "e.g. NVIDIA" },
  { key: "tier", label: "Tier", type: "select" as const, options: ["Platinum", "Gold", "Silver", "Bronze", "Custom"] },
  { key: "estimatedBudget", label: "Estimated Budget", placeholder: "e.g. $100K–$200K" },
  { key: "matchScore", label: "Match Score (0–100)", type: "number" as const, placeholder: "e.g. 90" },
  { key: "reasoning", label: "Reasoning", type: "textarea" as const, placeholder: "Why this sponsor is a good fit..." },
];

const emptyForm = (): Record<string, string> => ({ name: "", tier: "Gold", estimatedBudget: "", matchScore: "0", reasoning: "" });

interface OutreachDraft {
  email_subject: string;
  email_body: string;
  linkedin_message: string;
}

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

  // Outreach state
  const [outreachOpen, setOutreachOpen] = useState(false);
  const [outreachLoading, setOutreachLoading] = useState(false);
  const [outreachDraft, setOutreachDraft] = useState<OutreachDraft | null>(null);
  const [outreachTarget, setOutreachTarget] = useState("");
  const [copied, setCopied] = useState<string | null>(null);

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

  const generateOutreach = async (sponsor: Sponsor) => {
    setOutreachTarget(sponsor.name);
    setOutreachDraft(null);
    setOutreachOpen(true);
    setOutreachLoading(true);
    try {
      const resp = await fetch(`${API_BASE}/api/outreach/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          target_type: "sponsor",
          target_name: sponsor.name,
          target_context: { tier: sponsor.tier, budget: sponsor.estimatedBudget },
          event_name: project.name,
          event_category: project.category,
          event_geography: project.geography.join(", "),
          event_audience: project.audienceSize,
          recommended_tier: sponsor.tier,
          relevance_reason: sponsor.reasoning,
        }),
      });
      const data = await resp.json();
      if (data.drafts) setOutreachDraft(data.drafts);
    } catch {
      // ignore
    } finally {
      setOutreachLoading(false);
    }
  };

  const copyText = (text: string, label: string) => {
    navigator.clipboard.writeText(text);
    setCopied(label);
    setTimeout(() => setCopied(null), 2000);
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
                  <button onClick={() => generateOutreach(sponsor)} className="p-1 rounded bg-blue-500/10 hover:bg-blue-500/20 text-blue-600" title="Generate outreach"><Mail className="w-3 h-3" /></button>
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

      {/* Outreach Draft Dialog */}
      <Dialog open={outreachOpen} onOpenChange={setOutreachOpen}>
        <DialogContent className="sm:max-w-lg max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="text-base">Outreach Draft — {outreachTarget}</DialogTitle>
          </DialogHeader>
          {outreachLoading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="w-5 h-5 animate-spin text-muted-foreground mr-2" />
              <span className="text-sm text-muted-foreground">Generating personalized draft...</span>
            </div>
          ) : outreachDraft ? (
            <div className="space-y-4">
              <div>
                <div className="flex items-center justify-between mb-1">
                  <span className="text-[10px] text-muted-foreground uppercase tracking-wide">Email Subject</span>
                  <button onClick={() => copyText(outreachDraft.email_subject, "subject")} className="text-[10px] text-primary flex items-center gap-1">
                    {copied === "subject" ? <Check className="w-3 h-3" /> : <Copy className="w-3 h-3" />}
                    {copied === "subject" ? "Copied" : "Copy"}
                  </button>
                </div>
                <p className="text-sm font-medium bg-muted/50 rounded p-2">{outreachDraft.email_subject}</p>
              </div>
              <div>
                <div className="flex items-center justify-between mb-1">
                  <span className="text-[10px] text-muted-foreground uppercase tracking-wide">Email Body</span>
                  <button onClick={() => copyText(outreachDraft.email_body, "body")} className="text-[10px] text-primary flex items-center gap-1">
                    {copied === "body" ? <Check className="w-3 h-3" /> : <Copy className="w-3 h-3" />}
                    {copied === "body" ? "Copied" : "Copy"}
                  </button>
                </div>
                <p className="text-xs text-muted-foreground bg-muted/50 rounded p-3 whitespace-pre-wrap leading-relaxed">{outreachDraft.email_body}</p>
              </div>
              <div>
                <div className="flex items-center justify-between mb-1">
                  <span className="text-[10px] text-muted-foreground uppercase tracking-wide">LinkedIn Message</span>
                  <button onClick={() => copyText(outreachDraft.linkedin_message, "linkedin")} className="text-[10px] text-primary flex items-center gap-1">
                    {copied === "linkedin" ? <Check className="w-3 h-3" /> : <Copy className="w-3 h-3" />}
                    {copied === "linkedin" ? "Copied" : "Copy"}
                  </button>
                </div>
                <p className="text-xs text-muted-foreground bg-muted/50 rounded p-3 whitespace-pre-wrap leading-relaxed">{outreachDraft.linkedin_message}</p>
              </div>
            </div>
          ) : (
            <p className="text-sm text-muted-foreground py-4">Failed to generate draft. Try again.</p>
          )}
        </DialogContent>
      </Dialog>
    </AgentPageControls>
  );
}
