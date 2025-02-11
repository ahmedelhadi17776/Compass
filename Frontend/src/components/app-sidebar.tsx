"use client"

import * as React from "react"
import {
  LayoutDashboard,
  CheckSquare,
  Calendar,
  Brain,
  Timer,
  FolderSearch,
  Settings2,
  ListTodo,
  GitMerge,
  CalendarClock,
  AudioWaveform,
  Command,
  GalleryVerticalEnd,
  MessageSquareText,
  BarChart2,
  FileSearch,
  ClipboardList,
  Bot
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

const data = {
  user: {
    name: "Adham",
    email: "AdhamEhab@example.com",
    avatar: userAvatar,
  },
  teams: [
    {
      name: "Acme Inc",
      logo: GalleryVerticalEnd,
      plan: "Enterprise",
    },
    {
      name: "Acme Corp.",
      logo: AudioWaveform,
      plan: "Startup",
    },
    {
      name: "Evil Corp.",
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
          url: "/dashboard/tasks",
        },
        {
          title: "Calendar Overview",
          url: "/dashboard/calendar",
        },
        {
          title: "System Monitoring",
          url: "/dashboard/monitoring",
        },
      ],
    },
    {
      title: "Tasks",
      url: "/tasks",
      icon: ListTodo,
      items: [
        {
          title: "Create Task",
          url: "/tasks/create",
        },
        {
          title: "Manage Tasks",
          url: "/tasks/manage",
        },
        {
          title: "Dependencies",
          url: "/tasks/dependencies",
        },
        {
          title: "Automation",
          url: "/tasks/automation",
        },
      ],
    },
    {
      title: "Calendar",
      url: "/calendar",
      icon: Calendar,
      items: [
        {
          title: "Calendar Sync",
          url: "/calendar/sync",
        },
        {
          title: "Schedule Meeting",
          url: "/calendar/schedule",
        },
        {
          title: "Meeting Notes",
          url: "/calendar/notes",
        },
      ],
    },
    {
      title: "AIAssistant",
      url: "/ai",
      icon: Brain,
      items: [
        {
          title: "Smart Queries",
          url: "/ai/queries",
        },
        {
          title: "Reports & Insights",
          url: "/ai/reports",
        },
        {
          title: "Agent Management",
          url: "/ai/agents",
        },
      ],
    },
    {
      title: "Focus",
      url: "/productivity",
      icon: Timer,
      items: [
        {
          title: "Focus Mode",
          url: "/productivity/focus",
        },
        {
          title: "Metrics",
          url: "/productivity/metrics",
        },
        {
          title: "Wellness",
          url: "/productivity/wellness",
        },
      ],
    },
    {
      title: "Files",
      url: "/files",
      icon: FolderSearch,
      items: [
        {
          title: "Smart Search",
          url: "/files/search",
        },
        {
          title: "Clipboard History",
          url: "/files/clipboard",
        },
        {
          title: "Organization",
          url: "/files/organize",
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

export function AppSidebar({ onLogout, ...props }: React.ComponentProps<typeof Sidebar> & { onLogout?: () => void }) {
  return (
    <Sidebar className="sidebar" collapsible="icon" {...props}>
      <SidebarHeader>
        <TeamSwitcher teams={data.teams} />
      </SidebarHeader>
      <SidebarContent>
        <NavMain items={data.navMain} />
        <NavProjects projects={data.projects} />
      </SidebarContent>
      <SidebarFooter>
        <NavUser user={data.user} onLogout={onLogout} />
      </SidebarFooter>
      <SidebarRail />
    </Sidebar>
  )
}
