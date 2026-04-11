import { useState } from "react";
import { Project } from "@/lib/data";
import { useProjects } from "@/lib/ProjectContext";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { RefreshCw, Sparkles, X, Plus, Pencil } from "lucide-react";
import { Input } from "@/components/ui/input";

interface AgentPageControlsProps {
  project: Project;
  agentId: string;
  agentName: string;
  description: string;
  children: React.ReactNode;
}

export default function AgentPageControls({ project, agentId, agentName, description, children }: AgentPageControlsProps) {
  const { updateProject } = useProjects();
  const [regenerateOpen, setRegenerateOpen] = useState(false);
  const [instruction, setInstruction] = useState(project.agentInstructions?.[agentId] || "");
  const [isRegenerating, setIsRegenerating] = useState(false);

  const handleRegenerate = () => {
    updateProject(project.id, {
      agentInstructions: { ...project.agentInstructions, [agentId]: instruction },
    });
    setIsRegenerating(true);
    setTimeout(() => {
      setIsRegenerating(false);
      setRegenerateOpen(false);
    }, 1500);
  };

  return (
    <div className="max-w-4xl space-y-4">
      <div className="flex items-start justify-between pb-3 border-b">
        <div>
          <h2 className="text-base font-semibold text-foreground">{agentName}</h2>
          <p className="text-xs text-muted-foreground mt-0.5">{description}</p>
          {project.agentInstructions?.[agentId] && (
            <div className="mt-1.5 flex items-center gap-1.5 text-[10px]">
              <Sparkles className="w-3 h-3 text-primary" />
              <span className="text-primary bg-primary/10 px-1.5 py-0.5 rounded">
                "{project.agentInstructions[agentId]}"
              </span>
            </div>
          )}
        </div>
        <Dialog open={regenerateOpen} onOpenChange={setRegenerateOpen}>
          <DialogTrigger asChild>
            <Button variant="outline" size="sm" className="h-7 text-xs">
              <RefreshCw className="w-3 h-3 mr-1" />
              Regenerate
            </Button>
          </DialogTrigger>
          <DialogContent className="sm:max-w-md">
            <DialogHeader>
              <DialogTitle className="text-sm">Regenerate {agentName}</DialogTitle>
            </DialogHeader>
            <div className="space-y-3 pt-1">
              <div>
                <label className="text-xs font-medium text-foreground block mb-1.5">Custom Instruction (optional)</label>
                <Textarea
                  placeholder={`e.g. "Focus on tier-1 sponsors only"`}
                  value={instruction}
                  onChange={(e) => setInstruction(e.target.value)}
                  className="min-h-[70px] text-sm"
                />
              </div>
              <Button onClick={handleRegenerate} className="w-full h-8 text-xs" disabled={isRegenerating}>
                {isRegenerating ? (
                  <><RefreshCw className="w-3 h-3 mr-1.5 animate-spin" />Regenerating...</>
                ) : (
                  <><RefreshCw className="w-3 h-3 mr-1.5" />Regenerate Results</>
                )}
              </Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      {children}
    </div>
  );
}

export function RemovableItem({ children, onRemove, onEdit }: { children: React.ReactNode; onRemove: () => void; onEdit?: () => void }) {
  return (
    <div className="relative group">
      {children}
      <div className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity flex items-center gap-1">
        {onEdit && (
          <button onClick={onEdit} className="p-1 rounded bg-primary/10 hover:bg-primary/20 text-primary" title="Edit">
            <Pencil className="w-3.5 h-3.5" />
          </button>
        )}
        <button onClick={onRemove} className="p-1 rounded bg-destructive/10 hover:bg-destructive/20 text-destructive" title="Remove">
          <X className="w-3.5 h-3.5" />
        </button>
      </div>
    </div>
  );
}

interface FieldConfig {
  key: string;
  label: string;
  placeholder?: string;
  type?: "text" | "number" | "textarea" | "select";
  options?: string[];
}

export function ItemFormDialog({
  open, onOpenChange, title, fields, values, onChange, onSubmit, submitLabel,
}: {
  open: boolean; onOpenChange: (open: boolean) => void; title: string;
  fields: FieldConfig[]; values: Record<string, string>;
  onChange: (key: string, value: string) => void; onSubmit: () => void; submitLabel: string;
}) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="text-sm">{title}</DialogTitle>
        </DialogHeader>
        <div className="space-y-3 pt-1">
          {fields.map((field) => (
            <div key={field.key}>
              <label className="text-xs font-medium text-foreground block mb-1">{field.label}</label>
              {field.type === "textarea" ? (
                <Textarea placeholder={field.placeholder} value={values[field.key] || ""} onChange={(e) => onChange(field.key, e.target.value)} className="min-h-[60px] text-sm" />
              ) : field.type === "select" && field.options ? (
                <select value={values[field.key] || ""} onChange={(e) => onChange(field.key, e.target.value)} className="w-full h-8 rounded border border-input bg-background px-2 text-xs">
                  {field.options.map((opt) => <option key={opt} value={opt}>{opt}</option>)}
                </select>
              ) : (
                <Input type={field.type === "number" ? "number" : "text"} placeholder={field.placeholder} value={values[field.key] || ""} onChange={(e) => onChange(field.key, e.target.value)} className="h-8 text-sm" />
              )}
            </div>
          ))}
          <Button onClick={onSubmit} className="w-full h-8 text-xs" disabled={!values["name"]?.trim()}>
            {submitLabel}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}

export function AddCustomItemButton({ label, onClick }: { label: string; onClick: () => void }) {
  return (
    <Button variant="outline" size="sm" className="w-full border-dashed h-8 text-xs" onClick={onClick}>
      <Plus className="w-3 h-3 mr-1.5" />
      {label}
    </Button>
  );
}

export function AddCustomItem({ label, onAdd }: { label: string; onAdd: (value: string) => void }) {
  const [open, setOpen] = useState(false);
  const [value, setValue] = useState("");
  const handleAdd = () => { if (value.trim()) { onAdd(value.trim()); setValue(""); setOpen(false); } };
  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button variant="outline" size="sm" className="w-full border-dashed h-8 text-xs">
          <Plus className="w-3 h-3 mr-1.5" />{label}
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-md">
        <DialogHeader><DialogTitle className="text-sm">{label}</DialogTitle></DialogHeader>
        <div className="space-y-3 pt-1">
          <Input placeholder="Enter name or description..." value={value} onChange={(e) => setValue(e.target.value)} className="h-8 text-sm" />
          <Button onClick={handleAdd} className="w-full h-8 text-xs" disabled={!value.trim()}>Add</Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
