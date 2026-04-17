import { useMemo } from "react";
import { Project, getPricingForProject } from "@/lib/data";
import { useProjects } from "@/lib/ProjectContext";
import { mapPricing } from "@/lib/api";
import AgentPageControls from "@/components/AgentPageControls";

export default function PricingAgentPage({ project }: { project: Project }) {
  const { getAgentResults } = useProjects();
  const pricing = useMemo(() => {
    const results = getAgentResults(project.id);
    return (results?.pricing ? mapPricing(results.pricing) : null) ?? getPricingForProject(project);
  }, [project, getAgentResults]);

  return (
    <AgentPageControls project={project} agentId="pricing" agentName="Pricing & Footfall Agent" description="Ticket pricing model and expected attendance based on market analysis.">
      <div className="workspace-block">
        <div className="px-4 py-2.5 border-b">
          <span className="section-label">Ticket Tiers</span>
        </div>
        <div className="grid grid-cols-3 divide-x">
          {[
            { label: "Early Bird", value: pricing.earlyBird },
            { label: "Standard",   value: pricing.standard  },
            { label: "VIP",        value: pricing.vip       },
          ].map((tier) => (
            <div key={tier.label} className="px-4 py-3 text-center">
              <p className="text-[10px] text-muted-foreground uppercase tracking-wide mb-1">{tier.label}</p>
              <p className="text-2xl font-bold text-foreground">{tier.value}</p>
            </div>
          ))}
        </div>
      </div>

      <div className="workspace-block">
        <div className="px-4 py-2.5 border-b">
          <span className="section-label">Attendance Forecast</span>
        </div>
        <div className="grid grid-cols-3 divide-x">
          <div className="px-4 py-3">
            <p className="text-[10px] text-muted-foreground uppercase tracking-wide mb-1">Expected</p>
            <p className="text-lg font-semibold text-foreground">
              {typeof pricing.expectedAttendance === "number"
                ? pricing.expectedAttendance.toLocaleString()
                : pricing.expectedAttendance}
            </p>
          </div>
          <div className="px-4 py-3">
            <p className="text-[10px] text-muted-foreground uppercase tracking-wide mb-1">Fill Rate</p>
            <p className="text-lg font-semibold text-foreground">{pricing.fillRate}</p>
          </div>
          <div className="px-4 py-3">
            <p className="text-[10px] text-muted-foreground uppercase tracking-wide mb-1">Revenue Est.</p>
            <p className="text-lg font-semibold text-primary">{pricing.revenueEstimate}</p>
          </div>
        </div>
      </div>
    </AgentPageControls>
  );
}
