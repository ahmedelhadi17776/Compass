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
  Mail,
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
          url: "/dashboard/tasks",
        },
        {
          title: "Calendar Overview",
          url: "/dashboard/calendar",
        },
        {
          title: "Productivity Insights",
          url: "/dashboard/insights",
        },
        {
          title: "Emotional Intelligence",
          url: "/dashboard/wellness",
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
          url: "/tasks/create",
        },
        {
          title: "Calendar View",
          url: "/calendar",
        },
        {
          title: "Meeting Preparation",
          url: "/calendar/meetings",
        },
      ],
    },
    {
      title: "Workflows",
    url: "/workflows",
    icon: Command,
    items: [
      {
        title: "Workflow Builder",
        url: "/workflows/builder",
      },
      {
        title: "Active Workflows",
        url: "/workflows/active",
      },
      {
        title: "Workflow History",
        url: "/workflows/history",
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
      title: "Email",
      url: "/email",
      icon: Mail,
      items: [
        {
          title: "Inbox Management",
          url: "/email/inbox",
        },
        {
          title: "Email Automation",
          url: "/email/automation",
        },
        {
          title: "Communication Insights",
          url: "/email/insights",
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
      title: "Search",
      url: "/files",
      icon: FolderSearch,
      items: [
        {
          title: "Search & Retrieval",
          url: "/files/search",
        },
        {
          title: "Clipboard History",
          url: "/files/clipboard",
        },
        {
          title: "Research Agent",
          url: "/knowledge/research",
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
