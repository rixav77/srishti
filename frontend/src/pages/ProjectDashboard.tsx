import { useParams, Routes, Route, useNavigate, useLocation } from "react-router-dom";
import { useProjects } from "@/lib/ProjectContext";
import { 
  SidebarProvider, 
  Sidebar, 
  SidebarContent, 
  SidebarGroup, 
  SidebarGroupLabel, 
  SidebarGroupContent, 
  SidebarMenu, 
  SidebarMenuItem, 
  SidebarMenuButton,
  SidebarTrigger,
} from "@/components/ui/sidebar";
import { NavLink } from "@/components/NavLink";
import { Button } from "@/components/ui/button";
import { ArrowLeft, LayoutDashboard, Handshake, Mic2, Building2, DollarSign, Megaphone, ClipboardList } from "lucide-react";
import OverviewPage from "./agents/OverviewPage";
import SponsorAgentPage from "./agents/SponsorAgentPage";
import SpeakerAgentPage from "./agents/SpeakerAgentPage";
import VenueAgentPage from "./agents/VenueAgentPage";
import PricingAgentPage from "./agents/PricingAgentPage";
import GTMAgentPage from "./agents/GTMAgentPage";
import OpsAgentPage from "./agents/OpsAgentPage";

const NAV_ITEMS = [
  { title: "Overview", path: "", icon: LayoutDashboard },
  { title: "Sponsors", path: "sponsors", icon: Handshake },
  { title: "Speakers", path: "speakers", icon: Mic2 },
  { title: "Venues", path: "venues", icon: Building2 },
  { title: "Pricing", path: "pricing", icon: DollarSign },
  { title: "GTM", path: "gtm", icon: Megaphone },
  { title: "Ops", path: "ops", icon: ClipboardList },
];

export default function ProjectDashboard() {
  const { id } = useParams();
  const { getProject } = useProjects();
  const navigate = useNavigate();
  const location = useLocation();
  const project = getProject(id || "");

  if (!project) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <p className="text-muted-foreground mb-4 text-sm">Project not found</p>
          <Button variant="outline" size="sm" onClick={() => navigate("/")}>Back to Projects</Button>
        </div>
      </div>
    );
  }

  const basePath = `/project/${project.id}`;

  return (
    <SidebarProvider>
      <div className="min-h-screen flex w-full">
        <Sidebar collapsible="icon" className="border-r">
          <SidebarContent className="pt-2">
            <div className="px-3 mb-2">
              <Button variant="ghost" size="sm" className="w-full justify-start text-muted-foreground text-xs h-7 px-2" onClick={() => navigate("/app")}>
                <ArrowLeft className="w-3.5 h-3.5 mr-1.5" />
                Projects
              </Button>
            </div>
            <div className="px-3 pb-2 mb-1 border-b">
              <p className="text-xs font-semibold text-foreground truncate">{project.name}</p>
              <p className="text-[10px] text-muted-foreground">{project.category}</p>
            </div>
            <SidebarGroup>
              <SidebarGroupLabel className="text-[10px] uppercase tracking-widest px-3">Agents</SidebarGroupLabel>
              <SidebarGroupContent>
                <SidebarMenu>
                  {NAV_ITEMS.map((item) => {
                    const fullPath = item.path ? `${basePath}/${item.path}` : basePath;
                    const isActive = item.path 
                      ? location.pathname === fullPath 
                      : location.pathname === basePath;
                    return (
                      <SidebarMenuItem key={item.title}>
                        <SidebarMenuButton asChild isActive={isActive}>
                          <NavLink
                            to={fullPath}
                            end
                            className="hover:bg-muted/60 text-xs py-1.5"
                            activeClassName="bg-muted text-foreground font-medium border-l-2 border-primary"
                          >
                            <item.icon className="w-3.5 h-3.5 mr-2" />
                            <span>{item.title}</span>
                          </NavLink>
                        </SidebarMenuButton>
                      </SidebarMenuItem>
                    );
                  })}
                </SidebarMenu>
              </SidebarGroupContent>
            </SidebarGroup>
          </SidebarContent>
        </Sidebar>

        <div className="flex-1 flex flex-col min-w-0">
          <header className="h-10 flex items-center border-b px-4 bg-card">
            <SidebarTrigger className="mr-2" />
            <span className="text-xs font-medium text-foreground">{project.name}</span>
            <span className="text-[10px] text-muted-foreground ml-2">{project.category} · {project.geography.join(", ")} · {project.audienceSize.toLocaleString()} attendees</span>
          </header>
          <main className="flex-1 overflow-auto p-5">
            <Routes>
              <Route path="/" element={<OverviewPage project={project} />} />
              <Route path="/sponsors" element={<SponsorAgentPage project={project} />} />
              <Route path="/speakers" element={<SpeakerAgentPage project={project} />} />
              <Route path="/venues" element={<VenueAgentPage project={project} />} />
              <Route path="/pricing" element={<PricingAgentPage project={project} />} />
              <Route path="/gtm" element={<GTMAgentPage project={project} />} />
              <Route path="/ops" element={<OpsAgentPage project={project} />} />
            </Routes>
          </main>
        </div>
      </div>
    </SidebarProvider>
  );
}
