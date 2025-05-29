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
            title: "Todos & Habits",
            url: "/Todos&Habits",
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
        url: "/Todos&Habits",
        icon: ListTodo,
        items: [
          {
            title: "Todos & Habits",
            url: "/Todos&Habits",
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
      className="sidebar" 
      collapsible="icon" 
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
        <NotificationsPanel />
        <NavUser defaultUser={data.user} onLogout={logout.mutate} />
      </SidebarFooter>
      <SidebarRail />
    </Sidebar>
  )
}
