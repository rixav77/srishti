import { useState } from "react";
import { Project, Speaker, getSpeakersForProject } from "@/lib/data";
import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import AgentPageControls, { ItemFormDialog, AddCustomItemButton } from "@/components/AgentPageControls";
import { Pencil, X } from "lucide-react";

const SPEAKER_FIELDS = [
  { key: "name", label: "Speaker Name", placeholder: "e.g. Andrej Karpathy" },
  { key: "topic", label: "Topic", placeholder: "e.g. Neural Network Training" },
  { key: "influence", label: "Influence", type: "select" as const, options: ["Very High", "High", "Medium", "Low"] },
  { key: "pastTalks", label: "Past Talks", type: "number" as const, placeholder: "e.g. 25" },
  { key: "matchScore", label: "Match Score (0–100)", type: "number" as const, placeholder: "e.g. 90" },
];

const emptyForm = (): Record<string, string> => ({ name: "", topic: "", influence: "High", pastTalks: "0", matchScore: "0" });

export default function SpeakerAgentPage({ project }: { project: Project }) {
  const [speakers, setSpeakers] = useState<Speaker[]>(getSpeakersForProject(project));
  const [formOpen, setFormOpen] = useState(false);
  const [formValues, setFormValues] = useState<Record<string, string>>(emptyForm());
  const [editIndex, setEditIndex] = useState<number | null>(null);

  const handleChange = (key: string, value: string) => setFormValues((prev) => ({ ...prev, [key]: value }));
  const handleSubmit = () => {
    const speaker: Speaker = { name: formValues.name, topic: formValues.topic || "Custom", influence: formValues.influence || "Medium", pastTalks: Number(formValues.pastTalks) || 0, matchScore: Number(formValues.matchScore) || 0 };
    if (editIndex !== null) { setSpeakers((prev) => prev.map((s, i) => (i === editIndex ? speaker : s))); }
    else { setSpeakers((prev) => [...prev, speaker]); }
    setFormOpen(false); setEditIndex(null); setFormValues(emptyForm());
  };

  const openAdd = () => { setEditIndex(null); setFormValues(emptyForm()); setFormOpen(true); };
  const openEdit = (i: number) => {
    const s = speakers[i]; setEditIndex(i);
    setFormValues({ name: s.name, topic: s.topic, influence: s.influence, pastTalks: String(s.pastTalks), matchScore: String(s.matchScore) });
    setFormOpen(true);
  };

  return (
    <AgentPageControls project={project} agentId="speaker" agentName="Speaker Agent" description="Suggested speakers matched by topic relevance, influence, and availability.">
      <div className="workspace-block overflow-hidden">
        <Table>
          <TableHeader>
            <TableRow className="bg-muted/30">
              <TableHead className="text-[10px] uppercase tracking-wider font-semibold h-8">Speaker</TableHead>
              <TableHead className="text-[10px] uppercase tracking-wider font-semibold h-8">Topic</TableHead>
              <TableHead className="text-[10px] uppercase tracking-wider font-semibold h-8">Influence</TableHead>
              <TableHead className="text-[10px] uppercase tracking-wider font-semibold h-8 text-right">Talks</TableHead>
              <TableHead className="text-[10px] uppercase tracking-wider font-semibold h-8 text-right">Match</TableHead>
              <TableHead className="w-16 h-8"></TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {speakers.map((s, i) => (
              <TableRow key={`${s.name}-${i}`} className="group">
                <TableCell className="text-xs font-medium py-2">{s.name}</TableCell>
                <TableCell><Badge variant="outline" className="text-[10px] h-4 px-1.5">{s.topic}</Badge></TableCell>
                <TableCell><Badge variant={s.influence === "Very High" ? "default" : "secondary"} className="text-[10px] h-4 px-1.5">{s.influence}</Badge></TableCell>
                <TableCell className="text-right text-xs">{s.pastTalks}</TableCell>
                <TableCell className="text-right text-xs font-semibold text-primary font-mono">{s.matchScore > 0 ? `${s.matchScore}%` : "—"}</TableCell>
                <TableCell>
                  <div className="opacity-0 group-hover:opacity-100 transition-opacity flex items-center gap-1 justify-end">
                    <button onClick={() => openEdit(i)} className="p-1 rounded bg-primary/10 hover:bg-primary/20 text-primary"><Pencil className="w-3 h-3" /></button>
                    <button onClick={() => setSpeakers((prev) => prev.filter((_, idx) => idx !== i))} className="p-1 rounded bg-destructive/10 hover:bg-destructive/20 text-destructive"><X className="w-3 h-3" /></button>
                  </div>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
      <AddCustomItemButton label="Add Custom Speaker" onClick={openAdd} />
      <ItemFormDialog
        open={formOpen} onOpenChange={(v) => { setFormOpen(v); if (!v) setEditIndex(null); }}
        title={editIndex !== null ? "Edit Speaker" : "Add Custom Speaker"} fields={SPEAKER_FIELDS}
        values={formValues} onChange={handleChange} onSubmit={handleSubmit}
        submitLabel={editIndex !== null ? "Save Changes" : "Add Speaker"}
      />
    </AgentPageControls>
  );
}
