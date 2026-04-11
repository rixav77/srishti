import { ArrowRight, PlayCircle, Sparkles } from "lucide-react";
import { Link } from "react-router-dom";
import AppMockup from "./AppMockup";

export default function Hero() {
  return (
    <section className="relative w-full pt-24 pb-16 px-6 lg:px-12 overflow-hidden flex flex-col items-center border-b border-zinc-200/80 bg-white">
      <div className="absolute inset-0 bg-grid pointer-events-none z-0" />

      <div className="max-w-4xl mx-auto text-center relative z-10">
        <button className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-zinc-100 border border-zinc-200 text-xs font-medium text-zinc-600 mb-8 hover:bg-zinc-200 transition-colors">
          <span className="w-1.5 h-1.5 rounded-full bg-blue-500" />
          Introducing Smart Workflows
          <ArrowRight className="w-3 h-3" />
        </button>

        <h1 className="font-semibold text-5xl md:text-6xl lg:text-7xl tracking-tighter leading-[1.05] text-zinc-900 mb-6">
          Master your event planning.
        </h1>

        <p className="text-base md:text-lg text-zinc-500 mb-10 max-w-2xl mx-auto leading-relaxed">
          A unified platform to manage budgets, source vendors, and coordinate logistics. Focus on creating exceptional experiences, not maintaining spreadsheets.
        </p>

        <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
          <Link
            to="/app"
            className="w-full sm:w-auto bg-zinc-900 text-white px-6 py-2.5 rounded-full text-sm font-medium hover:bg-zinc-800 transition-colors shadow-md shadow-zinc-900/10"
          >
            Start planning for free
          </Link>
          <button className="w-full sm:w-auto bg-white text-zinc-900 border border-zinc-200 px-6 py-2.5 rounded-full text-sm font-medium hover:bg-zinc-50 transition-colors flex items-center justify-center gap-2">
            <PlayCircle className="w-4 h-4" />
            Watch demo
          </button>
        </div>
      </div>

      <div className="w-full max-w-5xl mx-auto mt-16 relative z-10">
        <AppMockup />
      </div>
    </section>
  );
}
