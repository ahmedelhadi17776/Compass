import { useState, useEffect } from "react"
import { cn } from "@/lib/utils"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { 
  History, 
  Command, 
  Activity, 
  Brain,
  Plus, 
  ChevronRight
} from "lucide-react"
import { Button } from "../ui/button"
import { useNavigate } from "react-router-dom"

interface Workflow {
  id: string
  name: string
  description: string
  lastRun: string
}

const mockWorkflows: Workflow[] = [
  {
    id: '1',
    name: 'Workflow 1',
    description: 'This is a description of the workflow',
    lastRun: '2025-01-20T10:00:00'
  },
  {
    id: '2', 
    name: 'Workflow 2',
    description: 'This is another description of the workflow',
    lastRun: '2025-01-19T23:00:00'
  },
  {
    id: '3',
    name: 'Workflow 3',
    description: 'This is another description of the workflow',
    lastRun: '2025-01-01T00:00:00'
  }
]

interface WorkflowProps {
  darkMode?: boolean
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
                <CardTitle className="text-lg">{workflow.name}</CardTitle>
                <ChevronRight className="h-5 w-5 text-muted-foreground" />
              </div>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground mb-2">{workflow.description}</p>
              <p className="text-xs text-muted-foreground">Last Modified: {new Date(workflow.lastRun).toLocaleString()}</p>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )
}
