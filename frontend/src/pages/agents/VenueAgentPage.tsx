import { useState, useMemo } from "react";
import { Project, Venue, getVenuesForProject } from "@/lib/data";
import { useProjects } from "@/lib/ProjectContext";
import { mapVenues } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { MapPin, Users, Star } from "lucide-react";
import AgentPageControls, { RemovableItem, ItemFormDialog, AddCustomItemButton } from "@/components/AgentPageControls";

const VENUE_FIELDS = [
  { key: "name", label: "Venue Name", placeholder: "e.g. Moscone Center" },
  { key: "city", label: "City", placeholder: "e.g. San Francisco, CA" },
  { key: "capacity", label: "Capacity", type: "number" as const, placeholder: "e.g. 5000" },
  { key: "pricePerDay", label: "Price Per Day", placeholder: "e.g. $45,000" },
  { key: "rating", label: "Rating (0–5)", type: "number" as const, placeholder: "e.g. 4.8" },
];

const emptyForm = (): Record<string, string> => ({ name: "", city: "", capacity: "0", pricePerDay: "", rating: "0" });

export default function VenueAgentPage({ project }: { project: Project }) {
  const { getAgentResults } = useProjects();
  const initialVenues = useMemo(() => {
    const results = getAgentResults(project.id);
    const real = results?.venues ? mapVenues(results.venues) : [];
    return real.length > 0 ? real : getVenuesForProject(project);
  }, [project, getAgentResults]);
  const [venues, setVenues] = useState<Venue[]>(initialVenues);
  const [formOpen, setFormOpen] = useState(false);
  const [formValues, setFormValues] = useState<Record<string, string>>(emptyForm());
  const [editIndex, setEditIndex] = useState<number | null>(null);

  const handleChange = (key: string, value: string) => setFormValues((prev) => ({ ...prev, [key]: value }));
  const handleSubmit = () => {
    const venue: Venue = { name: formValues.name, city: formValues.city || "TBD", capacity: Number(formValues.capacity) || 0, pricePerDay: formValues.pricePerDay || "TBD", rating: Number(formValues.rating) || 0 };
    if (editIndex !== null) { setVenues((prev) => prev.map((v, i) => (i === editIndex ? venue : v))); }
    else { setVenues((prev) => [...prev, venue]); }
    setFormOpen(false); setEditIndex(null); setFormValues(emptyForm());
  };

  const openAdd = () => { setEditIndex(null); setFormValues(emptyForm()); setFormOpen(true); };
  const openEdit = (i: number) => {
    const v = venues[i]; setEditIndex(i);
    setFormValues({ name: v.name, city: v.city, capacity: String(v.capacity), pricePerDay: v.pricePerDay, rating: String(v.rating) });
    setFormOpen(true);
  };

  return (
    <AgentPageControls project={project} agentId="venue" agentName="Venue Agent" description="Recommended venues filtered by geography, capacity, and pricing.">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {venues.map((v, i) => (
          <RemovableItem key={`${v.name}-${i}`} onRemove={() => setVenues((prev) => prev.filter((_, idx) => idx !== i))} onEdit={() => openEdit(i)}>
            <div className="workspace-block p-3.5">
              <h3 className="text-sm font-medium text-foreground mb-1.5">{v.name}</h3>
              <div className="space-y-1 text-[11px] text-muted-foreground">
                <div className="flex items-center gap-1.5"><MapPin className="w-3 h-3" />{v.city}</div>
                {v.capacity > 0 && <div className="flex items-center gap-1.5"><Users className="w-3 h-3" />Capacity: {v.capacity.toLocaleString()}</div>}
                {v.rating > 0 && <div className="flex items-center gap-1.5"><Star className="w-3 h-3" />{v.rating}/5</div>}
              </div>
              <div className="mt-2">
                <Badge variant="secondary" className="text-[10px] h-4 px-1.5">{v.pricePerDay}/day</Badge>
              </div>
            </div>
          </RemovableItem>
        ))}
      </div>
      <AddCustomItemButton label="Add Custom Venue" onClick={openAdd} />
      <ItemFormDialog
        open={formOpen} onOpenChange={(v) => { setFormOpen(v); if (!v) setEditIndex(null); }}
        title={editIndex !== null ? "Edit Venue" : "Add Custom Venue"} fields={VENUE_FIELDS}
        values={formValues} onChange={handleChange} onSubmit={handleSubmit}
        submitLabel={editIndex !== null ? "Save Changes" : "Add Venue"}
      />
    </AgentPageControls>
  );
}
