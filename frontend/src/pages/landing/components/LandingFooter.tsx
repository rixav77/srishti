import { Link } from "react-router-dom";

export default function LandingFooter() {
  return (
    <footer className="bg-white border-t border-zinc-200/80 py-12 px-6">
      <div className="max-w-screen-xl mx-auto flex flex-col md:flex-row justify-between items-start md:items-center gap-6">
        <div className="flex flex-col gap-2">
          <Link to="/" className="font-semibold text-sm tracking-tighter uppercase text-zinc-900">Orchestra</Link>
          <span className="text-xs text-zinc-500">© 2024 Orchestra Technologies, Inc.</span>
        </div>
        <div className="flex flex-wrap gap-6 text-xs font-medium text-zinc-500">
          <a href="#" className="hover:text-zinc-900 transition-colors">Twitter</a>
          <a href="#" className="hover:text-zinc-900 transition-colors">GitHub</a>
          <a href="#" className="hover:text-zinc-900 transition-colors">Changelog</a>
          <a href="#" className="hover:text-zinc-900 transition-colors">Privacy</a>
          <a href="#" className="hover:text-zinc-900 transition-colors">Terms</a>
        </div>
      </div>
    </footer>
  );
}
