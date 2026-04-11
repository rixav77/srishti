import { useState } from "react";
import { Project, getGTMForProject } from "@/lib/data";
import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import AgentPageControls, { ItemFormDialog, AddCustomItemButton } from "@/components/AgentPageControls";
import { Pencil, X } from "lucide-react";

interface Channel { name: string; reach: string; cost: string; priority: string; }

const CHANNEL_FIELDS = [
  { key: "name", label: "Channel Name", placeholder: "e.g. LinkedIn Ads" },
  { key: "reach", label: "Estimated Reach", placeholder: "e.g. 45K professionals" },
  { key: "cost", label: "Cost", placeholder: "e.g. $8,500" },
  { key: "priority", label: "Priority", type: "select" as const, options: ["High", "Medium", "Low"] },
];

const emptyForm = (): Record<string, string> => ({ name: "", reach: "", cost: "", priority: "Medium" });

export default function GTMAgentPage({ project }: { project: Project }) {
  const gtm = getGTMForProject(project);
  const [channels, setChannels] = useState<Channel[]>(gtm.channels);
  const [formOpen, setFormOpen] = useState(false);
  const [formValues, setFormValues] = useState<Record<string, string>>(emptyForm());
  const [editIndex, setEditIndex] = useState<number | null>(null);

  const handleChange = (key: string, value: string) => setFormValues((prev) => ({ ...prev, [key]: value }));
  const handleSubmit = () => {
    const channel: Channel = { name: formValues.name, reach: formValues.reach || "TBD", cost: formValues.cost || "TBD", priority: formValues.priority || "Medium" };
    if (editIndex !== null) { setChannels((prev) => prev.map((c, i) => (i === editIndex ? channel : c))); }
    else { setChannels((prev) => [...prev, channel]); }
    setFormOpen(false); setEditIndex(null); setFormValues(emptyForm());
  };

  const openAdd = () => { setEditIndex(null); setFormValues(emptyForm()); setFormOpen(true); };
  const openEdit = (i: number) => {
    const c = channels[i]; setEditIndex(i);
    setFormValues({ name: c.name, reach: c.reach, cost: c.cost, priority: c.priority });
    setFormOpen(true);
  };

  return (
    <AgentPageControls project={project} agentId="gtm" agentName="Communication GTM Agent" description="Go-to-market strategy with channel recommendations and campaign timeline.">
      <div className="workspace-block overflow-hidden">
        <div className="px-4 py-2.5 border-b">
          <span className="section-label">Recommended Channels</span>
        </div>
        <Table>
          <TableHeader>
            <TableRow className="bg-muted/30">
              <TableHead className="text-[10px] uppercase tracking-wider font-semibold h-8">Channel</TableHead>
              <TableHead className="text-[10px] uppercase tracking-wider font-semibold h-8">Reach</TableHead>
              <TableHead className="text-[10px] uppercase tracking-wider font-semibold h-8">Cost</TableHead>
              <TableHead className="text-[10px] uppercase tracking-wider font-semibold h-8">Priority</TableHead>
              <TableHead className="w-16 h-8"></TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {channels.map((ch, i) => (
              <TableRow key={`${ch.name}-${i}`} className="group">
                <TableCell className="text-xs font-medium py-2">{ch.name}</TableCell>
                <TableCell className="text-xs">{ch.reach}</TableCell>
                <TableCell className="text-xs">{ch.cost}</TableCell>
                <TableCell><Badge variant={ch.priority === "High" ? "default" : "secondary"} className="text-[10px] h-4 px-1.5">{ch.priority}</Badge></TableCell>
                <TableCell>
                  <div className="opacity-0 group-hover:opacity-100 transition-opacity flex items-center gap-1 justify-end">
                    <button onClick={() => openEdit(i)} className="p-1 rounded bg-primary/10 hover:bg-primary/20 text-primary"><Pencil className="w-3 h-3" /></button>
                    <button onClick={() => setChannels((prev) => prev.filter((_, idx) => idx !== i))} className="p-1 rounded bg-destructive/10 hover:bg-destructive/20 text-destructive"><X className="w-3 h-3" /></button>
                  </div>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
      <AddCustomItemButton label="Add Custom Channel" onClick={openAdd} />

      <div className="workspace-block">
        <div className="px-4 py-2.5 border-b">
          <span className="section-label">Campaign Timeline</span>
        </div>
        <div className="divide-y">
          {gtm.timeline.map((phase, i) => (
            <div key={i} className="flex items-center justify-between text-xs px-4 py-2.5">
              <div>
                <p className="font-medium text-foreground">{phase.phase}</p>
                <p className="text-[10px] text-muted-foreground">{phase.weeks}</p>
              </div>
              <Badge variant="outline" className="text-[10px] h-4 px-1.5">{phase.status}</Badge>
            </div>
          ))}
        </div>
      </div>

      <ItemFormDialog
        open={formOpen} onOpenChange={(v) => { setFormOpen(v); if (!v) setEditIndex(null); }}
        title={editIndex !== null ? "Edit Channel" : "Add Custom Channel"} fields={CHANNEL_FIELDS}
        values={formValues} onChange={handleChange} onSubmit={handleSubmit}
        submitLabel={editIndex !== null ? "Save Changes" : "Add Channel"}
      />
    </AgentPageControls>
  );
}
