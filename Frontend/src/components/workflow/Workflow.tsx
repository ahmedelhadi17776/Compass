import { useState, useEffect } from "react"
import { cn } from "@/lib/utils"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { 
  History, 
  Command, 
  Activity, 
  Brain,
  Plus, 
  ChevronRight,
  GitBranch,
  ArrowRight
} from "lucide-react"
import { Button } from "../ui/button"
import { useNavigate } from "react-router-dom"
import { WorkflowListItem, WorkflowStatus, WorkflowType } from "@/types/workflow"
import { Badge } from "../ui/badge"

const mockWorkflows: WorkflowListItem[] = [
  {
    id: '1',
    name: 'Workflow 1',
    description: 'This is a description of the workflow',
    workflowType: "sequential",
    status: "active",
    createdAt: '2025-01-20T10:00:00',
    updatedAt: '2025-01-20T10:00:00',
    lastExecutedAt: '2025-01-20T10:00:00',
    tags: ["automation", "test"]
  },
  {
    id: '2', 
    name: 'Workflow 2',
    description: 'This is another description of the workflow',
    workflowType: "parallel",
    status: "completed",
    createdAt: '2025-01-19T23:00:00',
    updatedAt: '2025-01-19T23:00:00',
    lastExecutedAt: '2025-01-19T23:00:00',
    tags: ["production"]
  },
  {
    id: '3',
    name: 'Workflow 3',
    description: 'This is another description of the workflow',
    workflowType: "conditional",
    status: "pending",
    createdAt: '2025-01-01T00:00:00',
    updatedAt: '2025-01-01T00:00:00',
    tags: []
  }
]

interface WorkflowProps {
  darkMode?: boolean
}

const getStatusColor = (status: WorkflowStatus) => {
  switch (status) {
    case "active":
      return "bg-emerald-50 text-emerald-600 border-emerald-200 dark:bg-emerald-950/20 dark:text-emerald-400 dark:border-emerald-900/30"
    case "completed":
      return "bg-blue-50 text-blue-600 border-blue-200 dark:bg-blue-950/20 dark:text-blue-400 dark:border-blue-900/30"
    case "failed":
      return "bg-red-50 text-red-600 border-red-200 dark:bg-red-950/20 dark:text-red-400 dark:border-red-900/30"
    case "cancelled":
      return "bg-orange-50 text-orange-600 border-orange-200 dark:bg-orange-950/20 dark:text-orange-400 dark:border-orange-900/30"
    default:
      return "bg-gray-50 text-gray-600 border-gray-200 dark:bg-gray-950/20 dark:text-gray-400 dark:border-gray-900/30"
  }
}

const getWorkflowTypeIcon = (type: WorkflowType) => {
  switch (type) {
    case "sequential":
      return <ArrowRight className="h-4 w-4" />
    case "parallel":
      return <GitBranch className="h-4 w-4" />
    case "conditional":
      return <Activity className="h-4 w-4" />
    case "ai_driven":
      return <Brain className="h-4 w-4" />
    default:
      return <Command className="h-4 w-4" />
  }
}

const getWorkflowTypeStyle = (type: WorkflowType) => {
  switch (type) {
    case "sequential":
      return "text-blue-600 border-blue-200 bg-blue-50 dark:text-blue-400 dark:border-blue-950 dark:bg-blue-950/20"
    case "parallel":
      return "text-indigo-600 border-indigo-200 bg-indigo-50 dark:text-indigo-400 dark:border-indigo-950 dark:bg-indigo-950/20"
    case "conditional":
      return "text-amber-600 border-amber-200 bg-amber-50 dark:text-amber-400 dark:border-amber-950 dark:bg-amber-950/20"
    case "ai_driven":
      return "text-emerald-600 border-emerald-200 bg-emerald-50 dark:text-emerald-400 dark:border-emerald-950 dark:bg-emerald-950/20"
    default:
      return "text-gray-600 border-gray-200 bg-gray-50 dark:text-gray-400 dark:border-gray-950 dark:bg-gray-950/20"
  }
}

export default function WorkflowPage({ darkMode = false }: WorkflowProps) {
  const navigate = useNavigate();

  const handleWorkflowClick = (workflowId: string) => {
    navigate(`/workflow/${workflowId}`);
  };

  const handleNewWorkflow = () => {
    // Placeholder for new workflow creation
    console.log("Create new workflow");
  };

  return (
    <div className={cn("h-full flex flex-col p-4", darkMode ? "bg-gray-900 text-white" : "bg-background text-foreground")}>
      
      {/* Header on the left */}
      <div className="flex justify-between items-center mt-4 mb-6 mx-4">
        <div className="flex items-center gap-1">
          <h2 className="text-xl font-semibold">Workflows</h2>
        </div>
      
        {/* Header on the right */}
        <div className="flex items-center gap-2">
          <Button 
            variant="outline" 
            size="sm" 
            className="gap-2"
            onClick={handleNewWorkflow}
          >
            <Plus className="h-4 w-4" />
            New Workflow
          </Button>
        </div>
      </div>

      {/* Workflow Cards */}
      <div className="space-y-4 mx-4">
        {mockWorkflows.map(workflow => (
          <Card 
            key={workflow.id} 
            className={cn(
              "cursor-pointer hover:bg-accent hover:text-accent-foreground transition-colors"
            )}
            onClick={() => handleWorkflowClick(workflow.id)}
          >
            <CardHeader>
              <div className="flex justify-between items-center">
                <div className="flex items-center gap-3">
                  <CardTitle className="text-lg">{workflow.name}</CardTitle>
                  <Badge variant="outline" className={cn(
                    "text-xs",
                    getStatusColor(workflow.status)
                  )}>
                    {workflow.status}
                  </Badge>
                </div>
                <div className="flex items-center gap-2">
                  <Badge variant="outline" className={cn(
                    "gap-1.5",
                    getWorkflowTypeStyle(workflow.workflowType)
                  )}>
                    {getWorkflowTypeIcon(workflow.workflowType)}
                    {workflow.workflowType}
                  </Badge>
                  <ChevronRight className="h-5 w-5 text-muted-foreground" />
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground mb-2">{workflow.description}</p>
              <div className="flex items-center gap-4">
                <p className="text-xs text-muted-foreground flex items-center gap-1">
                  <History className="h-3.5 w-3.5" />
                  Last Run: {workflow.lastExecutedAt ? new Date(workflow.lastExecutedAt).toLocaleString() : 'Never'}
                </p>
                {workflow.tags.length > 0 && (
                  <div className="flex items-center gap-1">
                    {workflow.tags.map((tag, index) => (
                      <Badge key={index} variant="secondary" className="text-xs">
                        {tag}
                      </Badge>
                    ))}
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )
}
