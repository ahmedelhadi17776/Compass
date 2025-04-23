"use client"

import { Bell, ChevronsUpDown, CreditCard, LogOut, Settings, Sparkles } from "lucide-react"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { DropdownMenu, DropdownMenuContent, DropdownMenuGroup, DropdownMenuItem, DropdownMenuLabel, DropdownMenuSeparator, DropdownMenuTrigger } from "@/components/ui/dropdown-menu"
import { SidebarMenu, SidebarMenuButton, SidebarMenuItem, useSidebar } from "@/components/ui/sidebar"
import { useNavigate } from "react-router-dom"
import { useAuth, User } from '@/hooks/useAuth'
import { useQueryClient } from '@tanstack/react-query'
import SettingsForm from "@/components/settings-form"
import { useState } from "react"

interface DefaultUser {
  name: string
  email: string
  avatar: string
}

interface NavUserProps {
  defaultUser?: DefaultUser
  onLogout?: () => void
}

export function NavUser({ defaultUser, onLogout }: NavUserProps) {
  const { isMobile } = useSidebar()
  const { logout, user } = useAuth()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [showSettings, setShowSettings] = useState(false)

  const handleLogout = () => {
    logout.mutate(undefined, {
      onSuccess: () => {
        queryClient.clear()
        navigate('/login', { replace: true })
      }
    })
    onLogout?.()
  }

  const fallbackUser: DefaultUser = {
    name: 'Anonymous',
    email: 'anonymous@example.com',
    avatar: ''
  }

  const getInitials = () => {
    if (user) {
      return `${user.first_name[0]}${user.last_name[0]}`.toUpperCase();
    }
    return (defaultUser || fallbackUser).name.slice(0, 2).toUpperCase();
  };

  const getDisplayName = () => {
    if (user) {
      return `${user.first_name} ${user.last_name}`.trim() || user.username;
    }
    return (defaultUser || fallbackUser).name;
  };

  const getAvatarUrl = () => {
    if (user?.avatar) return user.avatar;
    return (defaultUser || fallbackUser).avatar;
  };

  const getEmail = () => {
    if (user?.email) return user.email;
    return (defaultUser || fallbackUser).email;
  };

  return (
    <SidebarMenu>
      <SidebarMenuItem>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <SidebarMenuButton
              size="lg"
              className="data-[state=open]:bg-sidebar-accent data-[state=open]:text-sidebar-accent-foreground"
            >
              <div className="flex aspect-square size-8 items-center justify-center">
                <Avatar className="h-full w-full rounded-lg">
                  <AvatarImage src={getAvatarUrl()} alt={getDisplayName()} />
                  <AvatarFallback className="rounded-lg">
                    {getInitials()}
                  </AvatarFallback>
                </Avatar>
              </div>
              <div className="grid flex-1 text-left text-sm leading-tight">
                <span className="truncate font-semibold">{getDisplayName()}</span>
                <span className="truncate text-xs">{getEmail()}</span>
              </div>
              <ChevronsUpDown className="ml-auto size-4" />
            </SidebarMenuButton>
          </DropdownMenuTrigger>
          <DropdownMenuContent
            className="w-[--radix-dropdown-menu-trigger-width] min-w-56 rounded-lg"
            side={isMobile ? "bottom" : "right"}
            align="end"
            sideOffset={4}
          >
            <DropdownMenuLabel className="p-0 font-normal">
              <div className="flex items-center gap-2 px-1 py-1.5 text-left text-sm">
                <div className="flex aspect-square size-8 items-center justify-center">
                  <Avatar className="h-full w-full rounded-lg">
                    <AvatarImage src={getAvatarUrl()} alt={getDisplayName()} />
                    <AvatarFallback className="rounded-lg">
                      {getInitials()}
                    </AvatarFallback>
                  </Avatar>
                </div>
                <div className="grid flex-1 text-left text-sm leading-tight">
                  <span className="truncate font-semibold">{getDisplayName()}</span>
                  <span className="truncate text-xs">{getEmail()}</span>
                </div>
              </div>
            </DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuGroup>
              <DropdownMenuItem>
                <Sparkles />
                Upgrade to Pro
              </DropdownMenuItem>
            </DropdownMenuGroup>
            <DropdownMenuSeparator />
            <DropdownMenuGroup>
              <DropdownMenuItem onSelect={() => setShowSettings(true)}>
                <Settings />
                Settings
              </DropdownMenuItem>
              <DropdownMenuItem>
                <CreditCard />
                Billing
              </DropdownMenuItem>
              <DropdownMenuItem>
                <Bell />
                Notifications
              </DropdownMenuItem>
            </DropdownMenuGroup>
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={handleLogout}>
              <LogOut/>
              <span>Log out</span>
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </SidebarMenuItem>
      {showSettings && <SettingsForm onClose={() => setShowSettings(false)} />}
    </SidebarMenu>
  )
}
