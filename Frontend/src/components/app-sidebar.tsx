"use client"

import * as React from "react"
import {
  LayoutDashboard,
  Brain,
  Timer,
  FolderSearch,
  ListTodo,
  AudioWaveform,
  Command,
  Mail,
  GalleryVerticalEnd,
} from "lucide-react"

import { NavMain } from "../components/nav-main"
import { NavProjects } from "../components/nav-projects"
import { NavUser } from "../components/nav-user"
import { TeamSwitcher } from "../components/team-switcher"
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarHeader,
  SidebarRail,
} from "@/components/ui/sidebar"

import userAvatar from "../components/user.jpg"
import { useAuth } from '@/hooks/useAuth';

export function AppSidebar({ ...props }: React.ComponentProps<typeof Sidebar>) {
  const { logout, user } = useAuth();

  // Read from cookie only if global state is not set
  const defaultOpen = React.useMemo(() => {
    if (typeof window === 'undefined') return true;
    
    return document.cookie
      .split(';')
      .find(cookie => cookie.trim().startsWith('sidebar:state='))
      ?.split('=')[1] === 'true' ?? true;
  }, []);

  // Update the data object to use the authenticated user
  const data = {
    user: {
      name: user ? `${user.first_name} ${user.last_name}` : 'Loading...',
      email: user?.email || 'Loading...',
      avatar: userAvatar, // Keep the default avatar for now
    },
    teams: [
      {
        name: "NMU Inc",
        logo: GalleryVerticalEnd,
        plan: "Enterprise",
      },
      {
        name: "GUC Corp.",
        logo: AudioWaveform,
        plan: "Startup",
      },
      {
        name: "AUC Corp.",
        logo: Command,
        plan: "Free",
      },
    ],
    navMain: [
      {
        title: "Dashboard",
        url: "/dashboard",
        icon: LayoutDashboard,
        isActive: true,
        items: [
          {
            title: "Overview",
            url: "/dashboard",
          },
          {
            title: "Task List",
            url: "/tasks",
          },
          {
            title: "Calendar Overview",
            url: "/calendar",
          },
          {
            title: "Productivity Insights",
            url: "/health",
          },
          {
            title: "Emotional Intelligence",
            url: "/wellness",
          },
        ],
      },
      {
        title: "Workflow",
        url: "/workflow",
        icon: Command,
        items: [
          {
            title: "Overview",
            url: "/workflow",
          },
          {
            title: "Builder",
            url: "/workflow/builder",
          },
          {
            title: "Templates",
            url: "/workflow/templates",
          },
          {
            title: "History",
            url: "/workflow/history",
          },
        ],
      },
      {
        title: "TaskManagement",
        url: "/tasks",
        icon: ListTodo,
        items: [
          {
            title: "Todo List",
            url: "/tasks",
          },
          {
            title: "Calendar View",
            url: "/calendar",
          },
        ],
      },
      {
        title: "AIAssistant",
        url: "/ai",
        icon: Brain,
        items: [
          {
            title: "Chatbot",
            url: "/ai",
          },
        ],
      },
      {
        title: "Focus",
        url: "/focus",
        icon: Timer,
        items: [
          {
            title: "Focus Mode",
            url: "/focus",
          },
        ],
      },
      {
        title: "Search",
        url: "/files",
        icon: FolderSearch,
        items: [
          {
            title: "Search & Retrieval",
            url: "/files",
          },
        ],
      },
    ],
    projects: [
      {
        name: "Task Management",
        url: "/projects/tasks",
        icon: ListTodo,
      },
      {
        name: "AI Workflows",
        url: "/projects/workflows",
        icon: Brain,
      },
      {
        name: "Focus Sessions",
        url: "/projects/focus",
        icon: Timer,
      },
    ],
  }

  return (
    <Sidebar 
      className="sidebar" 
      collapsible="icon" 
      defaultOpen={defaultOpen}
      {...props}
    >
      <SidebarHeader>
        <TeamSwitcher teams={data.teams} />
      </SidebarHeader>
      <SidebarContent>
        <NavMain items={data.navMain} />
        <NavProjects projects={data.projects} />
      </SidebarContent>
      <SidebarFooter>
        <NavUser user={data.user} onLogout={logout.mutate} />
      </SidebarFooter>
      <SidebarRail />
    </Sidebar>
  )
}
