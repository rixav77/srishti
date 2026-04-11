import { Project, getSponsorsForProject, getSpeakersForProject, getVenuesForProject, getPricingForProject } from "@/lib/data";
import { Badge } from "@/components/ui/badge";
import { MapPin, Users, Tag, Building2, Mic2, Handshake, DollarSign } from "lucide-react";

export default function OverviewPage({ project }: { project: Project }) {
  const sponsors = getSponsorsForProject(project);
  const speakers = getSpeakersForProject(project);
  const venues = getVenuesForProject(project);
  const pricing = getPricingForProject(project);

  return (
    <div className="max-w-4xl space-y-5">
      <div>
        <h2 className="text-lg font-semibold text-foreground">{project.name}</h2>
        <p className="text-xs text-muted-foreground mt-0.5">Project overview and agent summary</p>
      </div>

      <div className="workspace-block">
        <div className="px-4 py-2.5 border-b">
          <span className="section-label">Configuration</span>
        </div>
        <div className="px-4 py-3 grid grid-cols-3 gap-4 text-xs">
          <div className="flex items-center gap-2">
            <Tag className="w-3.5 h-3.5 text-muted-foreground" />
            <div>
              <p className="text-muted-foreground">Category</p>
              <p className="font-medium text-foreground">{project.category}</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <MapPin className="w-3.5 h-3.5 text-muted-foreground" />
            <div>
              <p className="text-muted-foreground">Geography</p>
              <p className="font-medium text-foreground">{project.geography.join(", ")}</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Users className="w-3.5 h-3.5 text-muted-foreground" />
            <div>
              <p className="text-muted-foreground">Audience</p>
              <p className="font-medium text-foreground">{project.audienceSize.toLocaleString()}</p>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-4 gap-3">
        {[
          { label: "Sponsors", value: sponsors.length, icon: Handshake },
          { label: "Speakers", value: speakers.length, icon: Mic2 },
          { label: "Venues", value: venues.length, icon: Building2 },
          { label: "Est. Revenue", value: pricing.revenueEstimate, icon: DollarSign },
        ].map((stat) => (
          <div key={stat.label} className="workspace-block px-3 py-3">
            <div className="flex items-center gap-2 mb-1.5">
              <stat.icon className="w-3.5 h-3.5 text-primary" />
              <span className="text-[10px] text-muted-foreground uppercase tracking-wide">{stat.label}</span>
            </div>
            <p className="text-xl font-bold text-foreground">{stat.value}</p>
          </div>
        ))}
      </div>

      <div className="workspace-block">
        <div className="px-4 py-2.5 border-b">
          <span className="section-label">Top Recommendations</span>
        </div>
        <div className="divide-y">
          {sponsors.slice(0, 2).map((s) => (
            <div key={s.name} className="flex items-center justify-between text-xs px-4 py-2.5">
              <div className="flex items-center gap-2">
                <Handshake className="w-3 h-3 text-muted-foreground" />
                <span className="text-foreground font-medium">{s.name}</span>
                <Badge variant="secondary" className="text-[10px] h-4 px-1.5">{s.tier}</Badge>
              </div>
              <span className="text-muted-foreground font-mono text-[11px]">{s.matchScore}%</span>
            </div>
          ))}
          {speakers.slice(0, 2).map((s) => (
            <div key={s.name} className="flex items-center justify-between text-xs px-4 py-2.5">
              <div className="flex items-center gap-2">
                <Mic2 className="w-3 h-3 text-muted-foreground" />
                <span className="text-foreground font-medium">{s.name}</span>
                <Badge variant="outline" className="text-[10px] h-4 px-1.5">{s.topic}</Badge>
              </div>
              <span className="text-muted-foreground font-mono text-[11px]">{s.matchScore}%</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
