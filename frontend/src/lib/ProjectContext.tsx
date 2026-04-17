import React, { createContext, useContext, useState, useCallback } from "react";
import { Project, MOCK_PROJECTS } from "./data";
import { AgentPlan } from "./api";

interface ProjectContextType {
  projects: Project[];
  addProject: (p: Omit<Project, "id" | "createdAt" | "updatedAt">) => Project;
  getProject: (id: string) => Project | undefined;
  updateProject: (id: string, updates: Partial<Project>) => void;
  agentResults: Record<string, AgentPlan>;
  setAgentResults: (projectId: string, plan: AgentPlan) => void;
  getAgentResults: (projectId: string) => AgentPlan | undefined;
}

const ProjectContext = createContext<ProjectContextType | null>(null);

export function ProjectProvider({ children }: { children: React.ReactNode }) {
  const [projects, setProjects] = useState<Project[]>(MOCK_PROJECTS);
  const [agentResults, setAllResults] = useState<Record<string, AgentPlan>>({});

  const addProject = useCallback((p: Omit<Project, "id" | "createdAt" | "updatedAt">) => {
    const now = new Date().toISOString().split("T")[0];
    const newProj: Project = { ...p, id: `proj-${Date.now()}`, createdAt: now, updatedAt: now };
    setProjects((prev) => [newProj, ...prev]);
    return newProj;
  }, []);

  const getProject = useCallback((id: string) => projects.find((p) => p.id === id), [projects]);

  const updateProject = useCallback((id: string, updates: Partial<Project>) => {
    setProjects((prev) =>
      prev.map((p) => (p.id === id ? { ...p, ...updates, updatedAt: new Date().toISOString().split("T")[0] } : p))
    );
  }, []);

  const setAgentResults = useCallback((projectId: string, plan: AgentPlan) => {
    setAllResults((prev) => ({ ...prev, [projectId]: plan }));
  }, []);

  const getAgentResults = useCallback(
    (projectId: string) => agentResults[projectId],
    [agentResults]
  );

  return (
    <ProjectContext.Provider value={{ projects, addProject, getProject, updateProject, agentResults, setAgentResults, getAgentResults }}>
      {children}
    </ProjectContext.Provider>
  );
}

export function useProjects() {
  const ctx = useContext(ProjectContext);
  if (!ctx) throw new Error("useProjects must be used within ProjectProvider");
  return ctx;
}
