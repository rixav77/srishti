import { Sparkles } from "lucide-react";
import { Link } from "react-router-dom";

export default function CTA() {
  return (
    <section className="w-full py-32 px-6 bg-zinc-950 text-center relative overflow-hidden">
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full max-w-2xl h-[400px] bg-zinc-800 rounded-full blur-[120px] opacity-20 pointer-events-none" />

      <div className="max-w-2xl mx-auto relative z-10 flex flex-col items-center">
        <Sparkles className="w-7 h-7 text-zinc-400 mb-6" />
        <h2 className="text-4xl md:text-5xl font-semibold tracking-tighter text-white mb-6 leading-tight">
          Ready to elevate your next conference?
        </h2>
        <p className="text-base text-zinc-400 mb-10">
          Join hundreds of event professionals who rely on Orchestra to deliver flawless experiences.
        </p>
        <div className="flex flex-col sm:flex-row items-center gap-4">
          <Link
            to="/app"
            className="w-full sm:w-auto bg-white text-zinc-950 px-6 py-2.5 rounded-full text-sm font-medium hover:bg-zinc-100 transition-colors shadow-lg shadow-white/10 active:scale-95"
          >
            Start for free
          </Link>
          <button className="w-full sm:w-auto bg-zinc-900 text-white border border-zinc-800 px-6 py-2.5 rounded-full text-sm font-medium hover:bg-zinc-800 transition-colors active:scale-95">
            Talk to sales
          </button>
        </div>
      </div>
    </section>
  );
}
