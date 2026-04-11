import { PenSquare, Search, Rocket } from "lucide-react";

export default function Workflow() {
  const steps = [
    {
      id: "foundation",
      title: "1. Foundation",
      icon: PenSquare,
      description: "Establish your core details, build out your budget framework, and set up ticket tiers.",
    },
    {
      id: "sourcing",
      title: "2. Sourcing",
      icon: Search,
      description: "Discover and evaluate venues, match with relevant speakers, and secure early sponsorships.",
    },
    {
      id: "execution",
      title: "3. Execution",
      icon: Rocket,
      description: "Finalize vendor contracts, launch your marketing campaigns, and manage the live run-of-show.",
    },
  ];

  return (
    <section id="workflows" className="w-full py-24 px-6 lg:px-12 bg-zinc-50 border-b border-zinc-200/80">
      <div className="max-w-6xl mx-auto">
        <div className="text-center max-w-2xl mx-auto mb-16">
          <h2 className="text-3xl font-semibold tracking-tight text-zinc-900 mb-4">A streamlined path to launch</h2>
          <p className="text-sm text-zinc-500">
            Eliminate the scattered tools. Orchestra connects every phase of your planning lifecycle into one linear workflow.
          </p>
        </div>

        <div className="relative grid grid-cols-1 md:grid-cols-3 gap-8 md:gap-6">
          <div className="hidden md:block absolute top-10 left-[16%] right-[16%] h-[1px] bg-zinc-200 z-0" />

          {steps.map((step) => (
            <div key={step.id} className="relative z-10 flex flex-col items-center md:items-start text-center md:text-left group cursor-default">
              <div className="w-20 h-20 bg-white border border-zinc-200 rounded-2xl shadow-sm flex items-center justify-center mb-6 group-hover:border-zinc-300 group-hover:shadow-md transition-all duration-300 group-hover:-translate-y-1">
                <step.icon className="w-7 h-7 text-zinc-900 transition-transform group-hover:scale-110 duration-300" />
              </div>
              <h3 className="text-base font-semibold text-zinc-900 mb-2">{step.title}</h3>
              <p className="text-sm text-zinc-500 leading-relaxed">{step.description}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
