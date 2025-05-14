import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from "@/components/ui/breadcrumb"
import { Separator } from "@/components/ui/separator"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Progress } from "@/components/ui/progress"
import { useEffect, useState } from "react"
import { Plus, Calendar, Brain, Video, Activity, Clock, Focus, Keyboard, ActivityIcon } from "lucide-react"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"

interface TaskMetrics {
  completed: number
  total: number
  upcoming: number
}

interface FocusMetrics {
  todayMinutes: number
  weeklyGoal: number
  weeklyProgress: number
}

interface SystemMetrics {
  keyboardUsage: number
  screenTime: number
  focusScore: number
  productivityScore: number
}

interface Meeting {
  id: string
  time: string
  period: 'AM' | 'PM'
  title: string
  hasVideo?: boolean
  type?: string
}

interface DashboardProps {
  view?: 'tasks' | 'calendar' | 'monitoring';
}

export default function Dashboard({ view }: DashboardProps) {
  const [taskMetrics, setTaskMetrics] = useState<TaskMetrics>({
    completed: 0,
    total: 0,
    upcoming: 0,
  })

  const [focusMetrics, setFocusMetrics] = useState<FocusMetrics>({
    todayMinutes: 0,
    weeklyGoal: 1500,
    weeklyProgress: 0,
  })

  const [systemMetrics, setSystemMetrics] = useState<SystemMetrics>({
    keyboardUsage: 0,
    screenTime: 0,
    focusScore: 0,
    productivityScore: 0,
  })

  const [meetings, setMeetings] = useState<Meeting[]>([
    {
      id: '1',
      time: '10:00',
      period: 'AM',
      title: 'Present the project and gather feedback',
      type: 'presentation'
    },
    {
      id: '2',
      time: '01:00',
      period: 'PM',
      title: 'Meeting with UX team',
      hasVideo: true
    },
    {
      id: '3',
      time: '03:00',
      period: 'PM',
      title: 'Onboarding of the project',
      type: 'onboarding'
    }
  ])

  // Simulated data - replace with actual API calls
  useEffect(() => {
    setTaskMetrics({
      completed: 12,
      total: 20,
      upcoming: 5,
    })
    setFocusMetrics({
      todayMinutes: 120,
      weeklyGoal: 1500,
      weeklyProgress: 65,
    })
    setSystemMetrics({
      keyboardUsage: 85,
      screenTime: 320,
      focusScore: 78,
      productivityScore: 82,
    })
  }, [])

  return (
    <>
      <div className="flex flex-1 flex-col gap-4 p-6">
        {/* Quick Actions */}
        <div className="flex gap-4">
          <Button variant="outline" className="flex items-center gap-2">
            <Plus className="h-4 w-4" />
            New Task
          </Button>
          <Button variant="outline" className="flex items-center gap-2">
            <Calendar className="h-4 w-4" />
            Schedule Meeting
          </Button>
          <Button variant="outline" className="flex items-center gap-2">
            <Brain className="h-4 w-4" />
            AI Assistant
          </Button>
          <Dialog>
            <DialogTrigger asChild>
              <Button variant="outline" className="flex items-center gap-2">
                <ActivityIcon className="h-4 w-4" />
                System Status
              </Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-[425px]">
              <DialogHeader>
                <DialogTitle>System Status</DialogTitle>
              </DialogHeader>
              <div className="space-y-4 pt-4">
                <div className="flex items-center justify-between rounded-lg bg-green-900 p-3">
                  <span className="flex items-center gap-2">
                    <div className="rounded-full p-1.5">
                      <ActivityIcon className="h-4 w-4" />
                    </div>
                    Vision Module
                  </span>
                  <span className="flex items-center gap-1.5 text-green-500">
                    <span className="h-2 w-2 rounded-full bg-green-500"></span>
                    Active
                  </span>
                </div>
                <div className="flex items-center justify-between rounded-lg bg-green-900 p-3">
                  <span className="flex items-center gap-2">
                    <div className="rounded-full p-1.5">
                      <Brain className="h-4 w-4" />
                    </div>
                    Audio Module
                  </span>
                  <span className="flex items-center gap-1.5 text-green-500">
                    <span className="h-2 w-2 rounded-full bg-green-500"></span>
                    Active
                  </span>
                </div>
                <div className="flex items-center justify-between rounded-lg bg-green-900 p-3">
                  <span className="flex items-center gap-2">
                    <div className="rounded-full p-1.5">
                      <Brain className="h-4 w-4" />
                    </div>
                    RAG System
                  </span>
                  <span className="flex items-center gap-1.5 text-green-500">
                    <span className="h-2 w-2 rounded-full bg-green-500"></span>
                    Active
                  </span>
                </div>
                <div className="flex items-center justify-between rounded-lg bg-green-900 p-3">
                  <span className="flex items-center gap-2">
                    <div className="rounded-full p-1.5">
                      <Brain className="h-4 w-4" />
                    </div>
                    Agent Ecosystem
                  </span>
                  <span className="flex items-center gap-1.5 text-green-500">
                    <span className="h-2 w-2 rounded-full bg-green-500"></span>
                    Active
                  </span>
                </div>
              </div>
            </DialogContent>
          </Dialog>
        </div>

        {/* Today's Meetings */}
        <Card className="col-span-3">
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle>Today's meetings</CardTitle>
            <Button
              variant="ghost"
              className="text-sm text-blue-500 hover:text-blue-600"
            >
              View all
            </Button>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4 md:grid-cols-4">
              {meetings.map((meeting) => (
                <div
                  key={meeting.id}
                  className="rounded-lg bg-zinc-900 p-4 dark:bg-zinc-800/90"
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="text-sm text-zinc-500">{meeting.period}</div>
                      <div className="text-xl font-semibold">{meeting.time}</div>
                    </div>
                    {meeting.hasVideo && (
                      <Video className="h-5 w-5 text-zinc-400" />
                    )}
                  </div>
                  <div className="mt-2 text-sm text-zinc-300">
                    {meeting.title}
                  </div>
                </div>
              ))}
              <div
                className="flex cursor-pointer items-center justify-center rounded-lg bg-blue-950/50 p-4 hover:bg-blue-900/50"
              >
                <div className="text-center">
                  <Plus className="mx-auto h-6 w-6 text-blue-500" />
                  <div className="mt-1 text-sm text-blue-500">
                    Schedule meeting
                  </div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Main Grid */}
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {/* Task Overview */}
          <Card>
            <CardHeader>
              <CardTitle>Task Overview</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex justify-between">
                  <span>Completed Tasks</span>
                  <span className="font-medium">{taskMetrics.completed}/{taskMetrics.total}</span>
                </div>
                <Progress value={(taskMetrics.completed / taskMetrics.total) * 100} />
                <div className="flex justify-between text-sm text-muted-foreground">
                  <span>Upcoming: {taskMetrics.upcoming}</span>
                  <span>{((taskMetrics.completed / taskMetrics.total) * 100).toFixed(0)}% Complete</span>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Focus Time */}
          <Card>
            <CardHeader>
              <CardTitle>Focus Time</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex justify-between">
                  <span>Today's Focus</span>
                  <span className="font-medium">{focusMetrics.todayMinutes} minutes</span>
                </div>
                <Progress value={focusMetrics.weeklyProgress} />
                <div className="flex justify-between text-sm text-muted-foreground">
                  <span>Weekly Goal: {focusMetrics.weeklyGoal}min</span>
                  <span>{focusMetrics.weeklyProgress}% Progress</span>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* AI Assistant Status */}
          <Card>
            <CardHeader>
              <CardTitle>AI Assistant</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex items-center gap-2">
                  <div className="h-2 w-2 rounded-full bg-green-500" />
                  <span>Active and Ready</span>
                </div>
                <div className="space-y-2">
                  <div className="text-sm text-muted-foreground">Recent Activities:</div>
                  <ul className="space-y-2 text-sm">
                    <li>• Calendar synced (2m ago)</li>
                    <li>• Task priorities updated (5m ago)</li>
                    <li>• Focus session completed (15m ago)</li>
                  </ul>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* System Monitoring Grid */}
        <div className="grid gap-4 md:grid-cols-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Keyboard Usage</CardTitle>
              <Keyboard className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{systemMetrics.keyboardUsage}%</div>
              <p className="text-xs text-muted-foreground">
                Optimal typing patterns
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Screen Time</CardTitle>
              <Clock className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{Math.floor(systemMetrics.screenTime / 60)}h {systemMetrics.screenTime % 60}m</div>
              <p className="text-xs text-muted-foreground">
                Today's active time
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Focus Score</CardTitle>
              <Focus className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{systemMetrics.focusScore}</div>
              <Progress value={systemMetrics.focusScore} className="mt-2" />
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Productivity</CardTitle>
              <Activity className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{systemMetrics.productivityScore}%</div>
              <Progress value={systemMetrics.productivityScore} className="mt-2" />
            </CardContent>
          </Card>
        </div>

        {/* Secondary Grid */}
        <div className="grid gap-4 md:grid-cols-2">
          {/* System Status */}
          
        </div>
      </div>
    </>
  )
}
