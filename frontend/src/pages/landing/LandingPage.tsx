import LandingNavbar from "./components/LandingNavbar";
import Hero from "./components/Hero";
import Workflow from "./components/Workflow";
import Features from "./components/Features";
import CTA from "./components/CTA";
import LandingFooter from "./components/LandingFooter";

export default function LandingPage() {
  return (
    <div className="flex flex-col w-full min-h-screen bg-[#FAFAFA] text-zinc-900 antialiased">
      <LandingNavbar />
      <main className="relative z-10 flex-grow pt-14">
        <Hero />
        <Workflow />
        <Features />
        <CTA />
      </main>
      <LandingFooter />
    </div>
  );
}
