import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useProjects } from "@/lib/ProjectContext";
import { CATEGORIES, GEOGRAPHIES } from "@/lib/data";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Checkbox } from "@/components/ui/checkbox";
import { Switch } from "@/components/ui/switch";
import { Plus, FolderOpen, Calendar, Users, MapPin, Sparkles, ChevronRight, LayoutGrid, Zap } from "lucide-react";

export default function ProjectsPage() {
  const { projects, addProject } = useProjects();
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);
  const [name, setName] = useState("");
  const [category, setCategory] = useState("");
  const [geography, setGeography] = useState<string[]>([]);
  const [audienceSize, setAudienceSize] = useState("");
  const [customizationEnabled, setCustomizationEnabled] = useState(false);

  const handleCreate = () => {
    if (!category || geography.length === 0 || !audienceSize) return;
    const proj = addProject({
      name: name || `${category} Event`,
      category,
      geography,
      audienceSize: parseInt(audienceSize),
      customizationEnabled,
      agentInstructions: {},
    });
    setOpen(false);
    setName("");
    setCategory("");
    setGeography([]);
    setAudienceSize("");
    setCustomizationEnabled(false);
    navigate(`/project/${proj.id}/generating`);
  };

  const toggleGeo = (geo: string) => {
    setGeography((prev) => prev.includes(geo) ? prev.filter((g) => g !== geo) : [...prev, geo]);
  };

  const totalAudience = projects.reduce((sum, p) => sum + p.audienceSize, 0);
  const uniqueGeos = [...new Set(projects.flatMap((p) => p.geography))];

  return (
    <div className="min-h-screen bg-background">
      <header className="border-b bg-card">
        <div className="max-w-6xl mx-auto px-6 h-12 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <span className="text-sm font-semibold text-foreground tracking-tighter uppercase">Orchestra</span>
          </div>
          <Dialog open={open} onOpenChange={setOpen}>
            <DialogTrigger asChild>
              <Button size="sm" className="h-8 text-xs"><Plus className="w-3.5 h-3.5 mr-1.5" />New Project</Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-lg">
              <DialogHeader>
                <DialogTitle className="text-base">Create New Project</DialogTitle>
              </DialogHeader>
              <div className="space-y-4 pt-1">
                <div className="space-y-1.5">
                  <Label className="text-xs">Project Name (optional)</Label>
                  <Input placeholder="e.g. AI Summit 2026" value={name} onChange={(e) => setName(e.target.value)} className="h-9 text-sm" />
                </div>
                <div className="space-y-1.5">
                  <Label className="text-xs">Event Category *</Label>
                  <Select value={category} onValueChange={setCategory}>
                    <SelectTrigger className="h-9 text-sm"><SelectValue placeholder="Select category" /></SelectTrigger>
                    <SelectContent>
                      {CATEGORIES.map((c) => <SelectItem key={c} value={c}>{c}</SelectItem>)}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-1.5">
                  <Label className="text-xs">Geography *</Label>
                  <div className="grid grid-cols-2 gap-1">
                    {GEOGRAPHIES.map((geo) => (
                      <label key={geo} className="flex items-center gap-2 text-xs cursor-pointer p-1.5 rounded hover:bg-muted">
                        <Checkbox checked={geography.includes(geo)} onCheckedChange={() => toggleGeo(geo)} />
                        {geo}
                      </label>
                    ))}
                  </div>
                </div>
                <div className="space-y-1.5">
                  <Label className="text-xs">Audience Size *</Label>
                  <Input type="number" placeholder="e.g. 1600" value={audienceSize} onChange={(e) => setAudienceSize(e.target.value)} className="h-9 text-sm" />
                </div>
                <div className="flex items-center justify-between p-2.5 rounded border bg-muted/30">
                  <div className="flex items-center gap-2">
                    <Sparkles className="w-3.5 h-3.5 text-primary" />
                    <div>
                      <Label className="text-xs font-medium">Enable Customization</Label>
                      <p className="text-[10px] text-muted-foreground">Add custom instructions per agent</p>
                    </div>
                  </div>
                  <Switch checked={customizationEnabled} onCheckedChange={setCustomizationEnabled} />
                </div>
                <Button onClick={handleCreate} className="w-full h-9 text-sm" disabled={!category || geography.length === 0 || !audienceSize}>
                  Create Project
                </Button>
              </div>
            </DialogContent>
          </Dialog>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-6 py-6">
        {/* Stats row */}
        {projects.length > 0 && (
          <div className="grid grid-cols-3 gap-3 mb-5">
            <div className="border rounded bg-card px-4 py-3">
              <div className="flex items-center gap-2 mb-1">
                <LayoutGrid className="w-3.5 h-3.5 text-muted-foreground" />
                <span className="section-label">Projects</span>
              </div>
              <span className="text-xl font-semibold text-foreground">{projects.length}</span>
            </div>
            <div className="border rounded bg-card px-4 py-3">
              <div className="flex items-center gap-2 mb-1">
                <Users className="w-3.5 h-3.5 text-muted-foreground" />
                <span className="section-label">Total Audience</span>
              </div>
              <span className="text-xl font-semibold text-foreground">{totalAudience.toLocaleString()}</span>
            </div>
            <div className="border rounded bg-card px-4 py-3">
              <div className="flex items-center gap-2 mb-1">
                <MapPin className="w-3.5 h-3.5 text-muted-foreground" />
                <span className="section-label">Regions</span>
              </div>
              <span className="text-xl font-semibold text-foreground">{uniqueGeos.length}</span>
            </div>
          </div>
        )}

        {/* Projects list */}
        <div className="flex items-center justify-between mb-3">
          <span className="section-label">All Projects</span>
        </div>

        {projects.length === 0 ? (
          <div className="text-center py-16 text-muted-foreground border border-dashed rounded bg-card">
            <FolderOpen className="w-10 h-10 mx-auto mb-3 opacity-30" />
            <p className="text-sm mb-1">No projects yet</p>
            <p className="text-xs text-muted-foreground">Create your first project to get started.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {projects.map((proj) => (
              <div
                key={proj.id}
                className="border rounded bg-card cursor-pointer hover:border-primary/40 hover:shadow-sm transition-all group"
                onClick={() => navigate(`/project/${proj.id}`)}
              >
                <div className="px-4 py-3 border-b flex items-center justify-between">
                  <div className="flex items-center gap-2 min-w-0">
                    <span className="text-sm font-semibold text-foreground truncate">{proj.name}</span>
                    <Badge variant="secondary" className="text-[10px] px-1.5 py-0 h-4 shrink-0">{proj.category}</Badge>
                  </div>
                  <ChevronRight className="w-4 h-4 text-muted-foreground/30 group-hover:text-primary transition-colors shrink-0" />
                </div>
                <div className="px-4 py-2.5 flex items-center gap-4 text-[11px] text-muted-foreground">
                  <span className="flex items-center gap-1"><MapPin className="w-3 h-3" />{proj.geography.join(", ")}</span>
                  <span className="flex items-center gap-1"><Users className="w-3 h-3" />{proj.audienceSize.toLocaleString()}</span>
                </div>
                <div className="px-4 py-2 border-t bg-muted/20 flex items-center justify-between">
                  <span className="flex items-center gap-1 text-[10px] text-muted-foreground">
                    <Calendar className="w-3 h-3" />Updated {proj.updatedAt}
                  </span>
                  {proj.customizationEnabled && (
                    <span className="flex items-center gap-1 text-[10px] text-primary">
                      <Zap className="w-3 h-3" />Custom
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
