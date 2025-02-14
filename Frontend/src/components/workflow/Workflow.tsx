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
import { Plus, Play, Pause, History, Command, Activity, Brain, Settings2 } from "lucide-react"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"

interface WorkflowMetrics {
  active: number
  completed: number
  templates: number
  totalSavedTime: number
}

interface ActiveWorkflow {
  id: string
  name: string
  status: 'running' | 'paused' | 'completed'
  progress: number
  currentStep: string
  type: string
}

interface WorkflowTemplate {
  id: string
  name: string
  description: string
  category: string
  estimatedTime: string
}

interface WorkflowProps {
  view?: 'overview' | 'builder' | 'templates' | 'history'
}

export default function WorkflowPage({ view = 'overview' }: WorkflowProps) {
  const [metrics, setMetrics] = useState<WorkflowMetrics>({
    active: 0,
    completed: 0,
    templates: 0,
    totalSavedTime: 0,
  })

  const [activeWorkflows, setActiveWorkflows] = useState<ActiveWorkflow[]>([
    {
      id: '1',
      name: 'Meeting Preparation',
      status: 'running',
      progress: 65,
      currentStep: 'Gathering Documents',
      type: 'meeting'
    },
    {
      id: '2',
      name: 'Email Triage',
      status: 'paused',
      progress: 30,
      currentStep: 'Sorting Emails',
      type: 'email'
    }
  ])

  const [templates, setTemplates] = useState<WorkflowTemplate[]>([
    {
      id: '1',
      name: 'Meeting Preparation',
      description: 'Automates gathering documents and setting up meeting notes',
      category: 'Meetings',
      estimatedTime: '15 mins'
    },
    {
      id: '2',
      name: 'Email Triage',
      description: 'Automatically sorts and prioritizes emails',
      category: 'Communication',
      estimatedTime: '10 mins'
    },
    {
      id: '3',
      name: 'Research Assistant',
      description: 'Helps gather and summarize research materials',
      category: 'Research',
      estimatedTime: '30 mins'
    }
  ])

  // Simulated data - replace with actual API calls
  useEffect(() => {
    setMetrics({
      active: 2,
      completed: 15,
      templates: 8,
      totalSavedTime: 240, // in minutes
    })
  }, [])

  const renderBuilder = () => (
    <div className="flex flex-col">
      <div className="flex-1 space-y-4 p-8 pt-6">
        <div className="flex items-center justify-between space-y-2">
          <h2 className="text-3xl font-bold tracking-tight">Workflow Builder</h2>
        </div>
        <Separator />
        <div className="grid gap-4">
          <Card>
            <CardHeader>
              <CardTitle>Create New Workflow</CardTitle>
            </CardHeader>
            <CardContent>
              <p>Workflow builder implementation coming soon...</p>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )

  const renderTemplates = () => (
    <div className="flex flex-col">
      <div className="flex-1 space-y-4 p-8 pt-6">
        <div className="flex items-center justify-between space-y-2">
          <h2 className="text-3xl font-bold tracking-tight">Workflow Templates</h2>
        </div>
        <Separator />
        <div className="grid gap-4">
          {templates.map((template) => (
            <Card key={template.id}>
              <CardHeader>
                <CardTitle>{template.name}</CardTitle>
              </CardHeader>
              <CardContent>
                <p>{template.description}</p>
                <div className="flex items-center space-x-2 mt-4">
                  <span className="text-sm text-muted-foreground">{template.category}</span>
                  <span className="text-sm text-muted-foreground">•</span>
                  <span className="text-sm text-muted-foreground">{template.estimatedTime}</span>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    </div>
  )

  const renderHistory = () => (
    <div className="flex flex-col">
      <div className="flex-1 space-y-4 p-8 pt-6">
        <div className="flex items-center justify-between space-y-2">
          <h2 className="text-3xl font-bold tracking-tight">Workflow History</h2>
        </div>
        <Separator />
        <div className="grid gap-4">
          <Card>
            <CardHeader>
              <CardTitle>Past Workflows</CardTitle>
            </CardHeader>
            <CardContent>
              <p>Workflow history implementation coming soon...</p>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )

  const renderOverview = () => (
    <>
      <div className="flex flex-col">
        <div className="flex-1 space-y-4 p-8 pt-6">
          <div className="flex items-center justify-between space-y-2">
            <h2 className="text-3xl font-bold tracking-tight">Workflow Management</h2>
            <div className="flex items-center space-x-2">
              <Button>
                <Plus className="mr-2 h-4 w-4" />
                New Workflow
              </Button>
            </div>
          </div>
          <Separator />
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Active Workflows</CardTitle>
                <Activity className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{metrics.active}</div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Completed Workflows</CardTitle>
                <History className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{metrics.completed}</div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Available Templates</CardTitle>
                <Command className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{metrics.templates}</div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Time Saved</CardTitle>
                <Brain className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{Math.round(metrics.totalSavedTime / 60)}h</div>
              </CardContent>
            </Card>
          </div>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
            <Card className="col-span-4">
              <CardHeader>
                <CardTitle>Active Workflows</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-8">
                  {activeWorkflows.map((workflow) => (
                    <div key={workflow.id} className="flex items-center">
                      <div className="ml-4 space-y-1 flex-1">
                        <p className="text-sm font-medium leading-none">{workflow.name}</p>
                        <p className="text-sm text-muted-foreground">
                          {workflow.currentStep}
                        </p>
                        <Progress value={workflow.progress} className="mt-2" />
                      </div>
                      <div className="ml-auto flex space-x-2">
                        {workflow.status === 'running' ? (
                          <Button size="sm" variant="outline">
                            <Pause className="h-4 w-4" />
                          </Button>
                        ) : (
                          <Button size="sm" variant="outline">
                            <Play className="h-4 w-4" />
                          </Button>
                        )}
                        <Button size="sm" variant="outline">
                          <Settings2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
            <Card className="col-span-3">
              <CardHeader>
                <CardTitle>Quick Start Templates</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-8">
                  {templates.map((template) => (
                    <div key={template.id} className="flex items-center">
                      <div className="ml-4 space-y-1 flex-1">
                        <p className="text-sm font-medium leading-none">{template.name}</p>
                        <p className="text-sm text-muted-foreground">
                          {template.description}
                        </p>
                        <div className="flex items-center space-x-2 mt-1">
                          <span className="text-xs text-muted-foreground">{template.category}</span>
                          <span className="text-xs text-muted-foreground">•</span>
                          <span className="text-xs text-muted-foreground">{template.estimatedTime}</span>
                        </div>
                      </div>
                      <Button size="sm" variant="outline" className="ml-auto">
                        Use Template
                      </Button>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </>
  )

  const viewComponents = {
    overview: renderOverview,
    builder: renderBuilder,
    templates: renderTemplates,
    history: renderHistory,
  }

  return viewComponents[view]()
}
