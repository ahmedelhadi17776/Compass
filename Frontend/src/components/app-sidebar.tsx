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
  GalleryVerticalEnd,
  Calendar,
  Activity,
  StickyNote,
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
import { NotificationsPanel } from "./notifications-panel"

export function AppSidebar({ ...props }: React.ComponentProps<typeof Sidebar>) {
  const { logout, user } = useAuth();

  // Updated data structure with flattened navigation
  const data = {
    user: {
      name: user ? `${user.first_name} ${user.last_name}` : 'Loading...',
      email: user?.email || 'Loading...',
      avatar: userAvatar,
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
      },
      {
        title: "Todos & Habits",
        url: "/Todos&Habits",
        icon: ListTodo,
      },
      {
        title: "Calendar",
        url: "/calendar",
        icon: Calendar,
      },
      {
        title: "Notes",
        url: "/notes",
        icon: StickyNote,
      },
      {
        title: "Workflows",
        url: "/workflow",
        icon: Command,
      },
      {
        title: "AI Assistant",
        url: "/ai",
        icon: Brain,
      },
      {
        title: "Focus Mode",
        url: "/focus",
        icon: Timer,
      },
      {
        title: "Search",
        url: "/files",
        icon: FolderSearch,
      },
    ],
    projects: [
      {
        name: "Task Management",
        url: "/projects/Todos&Habits",
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
      className="sidebar text-small" 
      collapsible="icon" 
      {...props}
    >
      <SidebarHeader>
        <TeamSwitcher teams={data.teams} />
      </SidebarHeader>
      <SidebarContent className="text-small">
        <NavMain items={data.navMain} />
        <NavProjects projects={data.projects} />
      </SidebarContent>
      <SidebarFooter className="text-small">
        <NotificationsPanel />
        <NavUser defaultUser={data.user} onLogout={logout.mutate} />
      </SidebarFooter>
      <SidebarRail />
    </Sidebar>
  )
}
