import { Project, Sponsor, Speaker, Venue } from "./data";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "https://srishti-production.up.railway.app";

// ── EventConfig mapping ────────────────────────────────────────────────────────

const DOMAIN_MAP: Record<string, string> = {
  "AI / ML":     "conference",
  "Web3":        "conference",
  "FinTech":     "conference",
  "HealthTech":  "conference",
  "Gaming":      "conference",
  "Climate":     "conference",
  "Music & Arts":"music_festival",
};

const CATEGORY_MAP: Record<string, string> = {
  "AI / ML":     "AI/ML",
  "Web3":        "Web3",
  "FinTech":     "FinTech",
  "HealthTech":  "HealthTech",
  "Gaming":      "Gaming",
  "Climate":     "Climate",
  "Music & Arts":"Music",
};

const GEO_MAP: Record<string, string> = {
  "North America": "USA",
  "Europe":        "Europe",
  "Asia Pacific":  "India",
  "Middle East":   "UAE",
  "Latin America": "Brazil",
};

export function buildEventConfig(project: Project) {
  return {
    domain:          DOMAIN_MAP[project.category]    || "conference",
    category:        CATEGORY_MAP[project.category]  || project.category,
    geography:       GEO_MAP[project.geography[0]]   || "India",
    city:            project.city                    || undefined,
    target_audience: project.audienceSize,
    budget_min:      project.audienceSize * 500,
    budget_max:      project.audienceSize * 2000,
    currency:        "INR",
    event_name:      project.name,
  };
}

// ── Types ──────────────────────────────────────────────────────────────────────

export interface AgentPlan {
  sponsors:   any[];
  speakers:   any[];
  venues:     any[];
  exhibitors: any[];
  pricing:    any;
  gtm:        any;
  ops:        any;
}

export interface AgentStreamUpdate {
  wave:       number;
  agent:      string;
  status:     string;
  results:    any;
  confidence?: number;
  elapsed_ms?: number;
  plan?:      AgentPlan;
}

// ── SSE stream consumer ────────────────────────────────────────────────────────

export async function runAgentsStream(
  project: Project,
  onUpdate: (update: AgentStreamUpdate) => void,
): Promise<AgentPlan | null> {
  const config = buildEventConfig(project);

  const response = await fetch(`${API_BASE}/api/agents/run/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(config),
  });

  if (!response.ok || !response.body) {
    throw new Error(`API error: ${response.status}`);
  }

  const reader  = response.body.getReader();
  const decoder = new TextDecoder();
  let plan: AgentPlan | null = null;
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() ?? "";

    for (const line of lines) {
      if (!line.startsWith("data: ")) continue;
      try {
        const update: AgentStreamUpdate = JSON.parse(line.slice(6));
        onUpdate(update);
        if (update.agent === "orchestrator" && update.plan) {
          plan = update.plan;
        }
      } catch {
        // malformed JSON line — skip
      }
    }
  }

  return plan;
}

// ── Response mappers ───────────────────────────────────────────────────────────

function scoreToInfluence(score: number): string {
  if (score >= 0.9) return "Very High";
  if (score >= 0.75) return "High";
  if (score >= 0.55) return "Medium";
  return "Low";
}

function formatPrice(value: any): string {
  if (!value && value !== 0) return "TBD";
  const n = Number(value);
  if (isNaN(n)) return String(value);
  if (n >= 100000) return `₹${(n / 100000).toFixed(1)}L`;
  if (n >= 1000)   return `₹${(n / 1000).toFixed(0)}K`;
  return `₹${n}`;
}

function capitalizeFirst(s: string): string {
  if (!s) return "Custom";
  return s.charAt(0).toUpperCase() + s.slice(1).toLowerCase();
}

export function mapSponsors(raw: any[]): Sponsor[] {
  if (!raw?.length) return [];
  return raw.map((s) => ({
    name:            s.company_name || s.name || "Unknown",
    tier:            capitalizeFirst(s.recommended_tier || s.tier || "silver"),
    matchScore:      Math.round((s.total_score ?? 0.7) * 100),
    reasoning:       s.why || s.reasoning || "",
    estimatedBudget: s.estimated_budget_range || "TBD",
  }));
}

export function mapSpeakers(raw: any[]): Speaker[] {
  if (!raw?.length) return [];
  return raw.map((s) => ({
    name:       s.name || "Unknown",
    topic:      Array.isArray(s.topics) ? s.topics[0] : (s.topic || s.role || "General"),
    influence:  scoreToInfluence(s.total_score ?? 0.7),
    pastTalks:  s.followers ? Math.floor(s.followers / 1000) : 0,
    matchScore: Math.round((s.total_score ?? 0.7) * 100),
  }));
}

export function mapVenues(raw: any[]): Venue[] {
  if (!raw?.length) return [];
  return raw.map((v) => ({
    name:       v.name || v.venue_name || "Unknown",
    city:       [v.city, v.country].filter(Boolean).join(", ") || "TBD",
    capacity:   v.estimated_capacity || v.max_capacity || 0,
    pricePerDay: v.daily_rate_estimate ? formatPrice(v.daily_rate_estimate) : "TBD",
    rating:     Math.min(5, Math.round((v.total_score ?? 0.7) * 5 * 10) / 10),
  }));
}

export function mapPricing(raw: any) {
  if (!raw || raw.error || !raw.tiers) return null;
  const tiers: any[] = raw.tiers || [];
  const find = (kws: string[]) =>
    tiers.find((t) => kws.some((kw) => t.name?.toLowerCase().includes(kw)));
  const early    = find(["early"]) || tiers[0];
  const standard = find(["standard", "regular", "general"]) || tiers[1] || tiers[0];
  const vip      = find(["vip", "premium", "executive"]) || tiers[tiers.length - 1];
  const revenue  = raw.total_projected_revenue;

  return {
    earlyBird:          early    ? formatPrice(early.price    ?? early.price_inr)    : "TBD",
    standard:           standard ? formatPrice(standard.price ?? standard.price_inr) : "TBD",
    vip:                vip      ? formatPrice(vip.price      ?? vip.price_inr)      : "TBD",
    expectedAttendance: raw.expected_attendance ?? raw.break_even_attendees ?? 0,
    fillRate:           raw.fill_rate           ?? "—",
    revenueEstimate:    revenue  ? formatPrice(revenue) : "TBD",
  };
}

export function mapGTM(raw: any) {
  if (!raw || raw.error) return null;

  const communities: any[]   = raw.communities     || [];
  const phases: any[]        = raw.strategy_phases || [];

  return {
    channels: communities.slice(0, 5).map((c: any) => ({
      name:     c.name || c.platform || "Community",
      reach:    c.members
                  ? `${Number(c.members).toLocaleString()} members`
                  : (c.estimated_reach || "TBD"),
      cost:     c.cost || "$0",
      priority: c.relevance === "high" ? "High" : c.relevance === "medium" ? "Medium" : "Low",
    })),
    timeline: phases.slice(0, 3).map((p: any) => ({
      phase:  p.phase || p.name || "Phase",
      weeks:  p.timeline || p.duration || "TBD",
      status: "Planned",
    })),
  };
}

export function mapOps(raw: any) {
  if (!raw || raw.error) return null;

  const checklist = (raw.checklist || []).map((item: any) => ({
    task:     item.task || item.name || "Task",
    priority: item.priority || "Medium",
    status:   "Pending",
  }));

  const resource = raw.resource_plan || {};

  return {
    checklist,
    staffEstimate: resource.staff_count  || resource.total_staff || 10,
    daysToSetup:   resource.setup_days   || resource.days_to_setup || 2,
  };
}
