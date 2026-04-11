import { Tag, Building2, Handshake, Mic2, ArrowRight } from "lucide-react";

export default function Features() {
  const features = [
    {
      id: "budgeting",
      title: "Dynamic Budgeting",
      icon: Tag,
      description: "Automatically track expenses against projected revenue. See your margin evolve in real-time as you book vendors.",
    },
    {
      id: "venue",
      title: "Venue Sourcing",
      icon: Building2,
      description: "Compare capacities, A/V capabilities, and cost estimates across a curated network of event spaces instantly.",
    },
    {
      id: "sponsor",
      title: "Sponsor Management",
      icon: Handshake,
      description: "Create structured tiers, manage deliverables, and track outreach status to secure essential funding.",
    },
    {
      id: "speaker",
      title: "Speaker Coordination",
      icon: Mic2,
      description: "Collect abstracts, review submissions, and manage travel logistics and scheduling for your talent.",
    },
  ];

  return (
    <section id="features" className="w-full py-24 px-6 lg:px-12 bg-white">
      <div className="max-w-6xl mx-auto flex flex-col md:flex-row gap-16">
        <div className="md:w-1/3 flex flex-col items-start sticky top-24 h-fit">
          <h2 className="text-3xl font-semibold tracking-tight text-zinc-900 mb-4">Everything you need to orchestrate.</h2>
          <p className="text-sm text-zinc-500 mb-8 leading-relaxed">
            We've built specialized tools for every facet of conference management. Stop jumping between fragmented apps.
          </p>
          <button className="text-sm font-medium text-zinc-900 flex items-center gap-1.5 hover:text-zinc-600 transition-colors group">
            View all features
            <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-1 transition-transform" />
          </button>
        </div>

        <div className="md:w-2/3 grid grid-cols-1 sm:grid-cols-2 gap-4">
          {features.map((feature) => (
            <div key={feature.id} className="p-6 rounded-2xl border border-zinc-200/80 bg-zinc-50/50 hover:bg-zinc-50 transition-all duration-300 hover:shadow-sm hover:-translate-y-0.5 group">
              <div className="w-10 h-10 rounded-xl bg-white border border-zinc-200 shadow-sm flex items-center justify-center mb-5 group-hover:border-zinc-300 transition-colors">
                <feature.icon className="w-5 h-5 text-zinc-700" />
              </div>
              <h3 className="text-sm font-semibold text-zinc-900 mb-2">{feature.title}</h3>
              <p className="text-xs text-zinc-500 leading-relaxed">{feature.description}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
