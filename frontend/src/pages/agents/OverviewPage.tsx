import { useState, useEffect } from "react";
import { Project, getSponsorsForProject, getSpeakersForProject, getVenuesForProject, getPricingForProject } from "@/lib/data";
import { useProjects } from "@/lib/ProjectContext";
import { mapSponsors, mapSpeakers, mapVenues, mapPricing } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { MapPin, Users, Tag, Building2, Mic2, Handshake, DollarSign, Database, Globe } from "lucide-react";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "https://srishti-production.up.railway.app";

interface DatasetStats {
  events: { total: number; by_domain: Record<string, number>; unique_cities: number; unique_countries: number };
  sponsors: { total: number };
  talents: { total: number };
  venues: { total: number };
}

export default function OverviewPage({ project }: { project: Project }) {
  const { getAgentResults } = useProjects();
  const results = getAgentResults(project.id);

  const sponsors = results?.sponsors ? mapSponsors(results.sponsors) : getSponsorsForProject(project);
  const speakers = results?.speakers ? mapSpeakers(results.speakers) : getSpeakersForProject(project);
  const venues = results?.venues ? mapVenues(results.venues) : getVenuesForProject(project);
  const pricing = results?.pricing ? mapPricing(results.pricing) ?? getPricingForProject(project) : getPricingForProject(project);

  const [stats, setStats] = useState<DatasetStats | null>(null);

  useEffect(() => {
    fetch(`${API_BASE}/api/datasets/stats`)
      .then((r) => r.json())
      .then(setStats)
      .catch(() => {});
  }, []);

  return (
    <div className="max-w-4xl space-y-5">
      <div>
        <h2 className="text-lg font-semibold text-foreground">{project.name}</h2>
        <p className="text-xs text-muted-foreground mt-0.5">
          {results ? "Results from AI agent pipeline" : "Project overview (run agents to see real data)"}
        </p>
      </div>

      <div className="workspace-block">
        <div className="px-4 py-2.5 border-b">
          <span className="section-label">Configuration</span>
        </div>
        <div className="grid grid-cols-4 divide-x">
          <div className="px-4 py-3 flex items-center gap-2">
            <Tag className="w-3.5 h-3.5 text-muted-foreground" />
            <div>
              <p className="text-[10px] text-muted-foreground">Category</p>
              <p className="text-xs font-medium">{project.category}</p>
            </div>
          </div>
          <div className="px-4 py-3 flex items-center gap-2">
            <MapPin className="w-3.5 h-3.5 text-muted-foreground" />
            <div>
              <p className="text-[10px] text-muted-foreground">Geography</p>
              <p className="text-xs font-medium">{project.geography.join(", ")}</p>
            </div>
          </div>
          <div className="px-4 py-3 flex items-center gap-2">
            <Users className="w-3.5 h-3.5 text-muted-foreground" />
            <div>
              <p className="text-[10px] text-muted-foreground">Audience</p>
              <p className="text-xs font-medium">{project.audienceSize.toLocaleString()}</p>
            </div>
          </div>
          <div className="px-4 py-3 flex items-center gap-2">
            <DollarSign className="w-3.5 h-3.5 text-muted-foreground" />
            <div>
              <p className="text-[10px] text-muted-foreground">Revenue Est.</p>
              <p className="text-xs font-medium text-primary">{pricing.revenueEstimate}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Agent Summary Cards */}
      <div className="grid grid-cols-3 gap-3">
        <div className="workspace-block p-4">
          <div className="flex items-center gap-2 mb-2">
            <Handshake className="w-4 h-4 text-primary" />
            <span className="text-xs font-semibold">Sponsors</span>
          </div>
          <p className="text-2xl font-bold">{sponsors.length}</p>
          <p className="text-[10px] text-muted-foreground mt-1">
            {sponsors.slice(0, 3).map((s) => s.name).join(", ")}
          </p>
        </div>
        <div className="workspace-block p-4">
          <div className="flex items-center gap-2 mb-2">
            <Mic2 className="w-4 h-4 text-primary" />
            <span className="text-xs font-semibold">Speakers</span>
          </div>
          <p className="text-2xl font-bold">{speakers.length}</p>
          <p className="text-[10px] text-muted-foreground mt-1">
            {speakers.slice(0, 3).map((s) => s.name).join(", ")}
          </p>
        </div>
        <div className="workspace-block p-4">
          <div className="flex items-center gap-2 mb-2">
            <Building2 className="w-4 h-4 text-primary" />
            <span className="text-xs font-semibold">Venues</span>
          </div>
          <p className="text-2xl font-bold">{venues.length}</p>
          <p className="text-[10px] text-muted-foreground mt-1">
            {venues.slice(0, 2).map((v) => v.name).join(", ")}
          </p>
        </div>
      </div>

      {/* Dataset Stats */}
      {stats && (
        <div className="workspace-block">
          <div className="px-4 py-2.5 border-b flex items-center gap-2">
            <Database className="w-3.5 h-3.5 text-muted-foreground" />
            <span className="section-label">Knowledge Base</span>
          </div>
          <div className="grid grid-cols-5 divide-x">
            <div className="px-4 py-3 text-center">
              <p className="text-lg font-bold">{stats.events.total}</p>
              <p className="text-[10px] text-muted-foreground">Events</p>
            </div>
            <div className="px-4 py-3 text-center">
              <p className="text-lg font-bold">{stats.sponsors.total}</p>
              <p className="text-[10px] text-muted-foreground">Sponsors</p>
            </div>
            <div className="px-4 py-3 text-center">
              <p className="text-lg font-bold">{stats.talents.total}</p>
              <p className="text-[10px] text-muted-foreground">Talents</p>
            </div>
            <div className="px-4 py-3 text-center">
              <p className="text-lg font-bold">{stats.venues.total}</p>
              <p className="text-[10px] text-muted-foreground">Venues</p>
            </div>
            <div className="px-4 py-3 text-center">
              <div className="flex items-center justify-center gap-1">
                <Globe className="w-3.5 h-3.5 text-muted-foreground" />
                <p className="text-lg font-bold">{stats.events.unique_countries}</p>
              </div>
              <p className="text-[10px] text-muted-foreground">Countries</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
