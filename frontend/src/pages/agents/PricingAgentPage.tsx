import { useMemo, useState, useCallback } from "react";
import { Project, getPricingForProject } from "@/lib/data";
import { useProjects } from "@/lib/ProjectContext";
import { mapPricing } from "@/lib/api";
import AgentPageControls from "@/components/AgentPageControls";
import { Slider } from "@/components/ui/slider";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { RefreshCw, TrendingUp, TrendingDown, Minus } from "lucide-react";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "https://srishti-production.up.railway.app";

interface TierState {
  name: string;
  price: number;
  allocation_pct: number;
}

interface SimResult {
  tiers: { name: string; price: number; allocation_pct: number; estimated_sales: number; revenue: number }[];
  total_ticket_revenue: number;
  total_revenue: number;
  total_costs: number;
  profit: number;
  margin_pct: number;
  break_even_attendees: number;
  estimated_total_attendees: number;
  safety_margin_pct: number;
  revenue_breakdown: { tickets: number; sponsors: number; exhibitors: number };
}

function formatCurrency(n: number): string {
  if (n >= 100000) return `₹${(n / 100000).toFixed(1)}L`;
  if (n >= 1000) return `₹${(n / 1000).toFixed(0)}K`;
  return `₹${Math.round(n)}`;
}

export default function PricingAgentPage({ project }: { project: Project }) {
  const { getAgentResults } = useProjects();
  const agentPricing = useMemo(() => {
    const results = getAgentResults(project.id);
    return (results?.pricing ? mapPricing(results.pricing) : null) ?? getPricingForProject(project);
  }, [project, getAgentResults]);

  // Simulation state
  const [tiers, setTiers] = useState<TierState[]>([
    { name: "Early Bird", price: 3000, allocation_pct: 25 },
    { name: "Standard", price: 5000, allocation_pct: 45 },
    { name: "VIP", price: 15000, allocation_pct: 15 },
    { name: "Student", price: 1500, allocation_pct: 15 },
  ]);
  const [fixedCosts, setFixedCosts] = useState(500000);
  const [simResult, setSimResult] = useState<SimResult | null>(null);
  const [loading, setLoading] = useState(false);

  const runSimulation = useCallback(async () => {
    setLoading(true);
    try {
      const resp = await fetch(`${API_BASE}/api/simulation/pricing`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          tiers,
          total_target_audience: project.audienceSize,
          fixed_costs: fixedCosts,
          variable_cost_per_attendee: 500,
          sponsor_revenue: 200000,
          exhibitor_revenue: 100000,
          price_elasticity: 1.2,
        }),
      });
      const data = await resp.json();
      setSimResult(data);
    } catch {
      // ignore
    } finally {
      setLoading(false);
    }
  }, [tiers, fixedCosts, project.audienceSize]);

  const updateTierPrice = (idx: number, price: number) => {
    setTiers((prev) => prev.map((t, i) => (i === idx ? { ...t, price } : t)));
  };

  return (
    <AgentPageControls project={project} agentId="pricing" agentName="Pricing & Footfall Agent" description="Ticket pricing model, simulation, and break-even analysis.">
      {/* Agent results (from pipeline) */}
      <div className="workspace-block">
        <div className="px-4 py-2.5 border-b">
          <span className="section-label">Agent Recommendation</span>
        </div>
        <div className="grid grid-cols-3 divide-x">
          {[
            { label: "Early Bird", value: agentPricing.earlyBird },
            { label: "Standard", value: agentPricing.standard },
            { label: "VIP", value: agentPricing.vip },
          ].map((tier) => (
            <div key={tier.label} className="px-4 py-3 text-center">
              <p className="text-[10px] text-muted-foreground uppercase tracking-wide mb-1">{tier.label}</p>
              <p className="text-2xl font-bold text-foreground">{tier.value}</p>
            </div>
          ))}
        </div>
        <div className="grid grid-cols-3 divide-x border-t">
          <div className="px-4 py-3">
            <p className="text-[10px] text-muted-foreground uppercase tracking-wide mb-1">Expected Attendance</p>
            <p className="text-lg font-semibold">{typeof agentPricing.expectedAttendance === "number" ? agentPricing.expectedAttendance.toLocaleString() : agentPricing.expectedAttendance}</p>
          </div>
          <div className="px-4 py-3">
            <p className="text-[10px] text-muted-foreground uppercase tracking-wide mb-1">Fill Rate</p>
            <p className="text-lg font-semibold">{agentPricing.fillRate}</p>
          </div>
          <div className="px-4 py-3">
            <p className="text-[10px] text-muted-foreground uppercase tracking-wide mb-1">Revenue Est.</p>
            <p className="text-lg font-semibold text-primary">{agentPricing.revenueEstimate}</p>
          </div>
        </div>
      </div>

      {/* Interactive Simulation */}
      <div className="workspace-block">
        <div className="px-4 py-2.5 border-b flex items-center justify-between">
          <span className="section-label">What-If Simulation</span>
          <Button size="sm" variant="outline" className="h-7 text-xs" onClick={runSimulation} disabled={loading}>
            <RefreshCw className={`w-3 h-3 mr-1.5 ${loading ? "animate-spin" : ""}`} />
            {loading ? "Simulating..." : "Run Simulation"}
          </Button>
        </div>
        <div className="p-4 space-y-4">
          {tiers.map((tier, idx) => (
            <div key={tier.name}>
              <div className="flex items-center justify-between mb-1.5">
                <span className="text-xs font-medium">{tier.name}</span>
                <div className="flex items-center gap-2">
                  <Badge variant="secondary" className="text-[10px] h-4">{tier.allocation_pct}% allocation</Badge>
                  <span className="text-sm font-bold text-primary w-16 text-right">₹{tier.price.toLocaleString()}</span>
                </div>
              </div>
              <Slider
                value={[tier.price]}
                onValueChange={([v]) => updateTierPrice(idx, v)}
                min={500}
                max={25000}
                step={500}
                className="w-full"
              />
            </div>
          ))}
          <div>
            <div className="flex items-center justify-between mb-1.5">
              <span className="text-xs font-medium">Fixed Costs</span>
              <span className="text-sm font-bold w-20 text-right">{formatCurrency(fixedCosts)}</span>
            </div>
            <Slider
              value={[fixedCosts]}
              onValueChange={([v]) => setFixedCosts(v)}
              min={100000}
              max={2000000}
              step={50000}
              className="w-full"
            />
          </div>
        </div>
      </div>

      {/* Simulation Results */}
      {simResult && (
        <div className="workspace-block">
          <div className="px-4 py-2.5 border-b">
            <span className="section-label">Simulation Results</span>
          </div>

          {/* Revenue breakdown */}
          <div className="grid grid-cols-4 divide-x border-b">
            <div className="px-4 py-3 text-center">
              <p className="text-[10px] text-muted-foreground uppercase mb-1">Ticket Revenue</p>
              <p className="text-lg font-bold text-primary">{formatCurrency(simResult.total_ticket_revenue)}</p>
            </div>
            <div className="px-4 py-3 text-center">
              <p className="text-[10px] text-muted-foreground uppercase mb-1">Total Revenue</p>
              <p className="text-lg font-bold">{formatCurrency(simResult.total_revenue)}</p>
            </div>
            <div className="px-4 py-3 text-center">
              <p className="text-[10px] text-muted-foreground uppercase mb-1">Total Costs</p>
              <p className="text-lg font-bold">{formatCurrency(simResult.total_costs)}</p>
            </div>
            <div className="px-4 py-3 text-center">
              <p className="text-[10px] text-muted-foreground uppercase mb-1">Profit</p>
              <p className={`text-lg font-bold ${simResult.profit >= 0 ? "text-green-600" : "text-red-600"}`}>
                {simResult.profit >= 0 ? "+" : ""}{formatCurrency(simResult.profit)}
              </p>
            </div>
          </div>

          {/* Break-even + margin */}
          <div className="grid grid-cols-3 divide-x border-b">
            <div className="px-4 py-3 text-center">
              <p className="text-[10px] text-muted-foreground uppercase mb-1">Break-Even</p>
              <p className="text-lg font-semibold">{simResult.break_even_attendees} attendees</p>
            </div>
            <div className="px-4 py-3 text-center">
              <p className="text-[10px] text-muted-foreground uppercase mb-1">Projected Attendance</p>
              <p className="text-lg font-semibold">{simResult.estimated_total_attendees}</p>
            </div>
            <div className="px-4 py-3 text-center">
              <p className="text-[10px] text-muted-foreground uppercase mb-1">Safety Margin</p>
              <div className="flex items-center justify-center gap-1">
                {simResult.safety_margin_pct > 10 ? (
                  <TrendingUp className="w-4 h-4 text-green-600" />
                ) : simResult.safety_margin_pct < 0 ? (
                  <TrendingDown className="w-4 h-4 text-red-600" />
                ) : (
                  <Minus className="w-4 h-4 text-yellow-600" />
                )}
                <p className={`text-lg font-semibold ${simResult.safety_margin_pct > 10 ? "text-green-600" : simResult.safety_margin_pct < 0 ? "text-red-600" : "text-yellow-600"}`}>
                  {simResult.safety_margin_pct}%
                </p>
              </div>
            </div>
          </div>

          {/* Per-tier breakdown */}
          <div className="px-4 py-2.5 border-b">
            <span className="text-[10px] text-muted-foreground uppercase tracking-wide">Per-Tier Breakdown</span>
          </div>
          <div className="divide-y">
            {simResult.tiers.map((t) => (
              <div key={t.name} className="px-4 py-2 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-medium w-24">{t.name}</span>
                  <span className="text-[11px] text-muted-foreground">₹{t.price.toLocaleString()} × {t.estimated_sales} seats</span>
                </div>
                <span className="text-xs font-semibold text-primary">{formatCurrency(t.revenue)}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </AgentPageControls>
  );
}
