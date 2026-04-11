import { Link } from "react-router-dom";

export default function LandingNavbar() {
  return (
    <nav className="fixed top-0 w-full z-50 bg-white/80 backdrop-blur-md border-b border-zinc-200/80">
      <div className="flex w-full h-14 px-6 items-center justify-between max-w-screen-xl mx-auto">
        <div className="flex items-center gap-8">
          <Link to="/" className="font-semibold text-base tracking-tighter uppercase text-zinc-900">
            Orchestra
          </Link>
          <div className="hidden md:flex items-center gap-6 text-sm text-zinc-500 font-medium">
            <a href="#features" className="hover:text-zinc-900 transition-colors">Features</a>
            <a href="#workflows" className="hover:text-zinc-900 transition-colors">Workflows</a>
          </div>
        </div>
        <div className="flex items-center gap-4 text-sm font-medium">
          <Link to="/app" className="text-zinc-500 hover:text-zinc-900 transition-colors hidden sm:block">
            Sign in
          </Link>
          <Link
            to="/app"
            className="bg-zinc-900 text-white px-4 py-1.5 rounded-full hover:bg-zinc-800 transition-colors shadow-sm"
          >
            Get started
          </Link>
        </div>
      </div>
    </nav>
  );
}
