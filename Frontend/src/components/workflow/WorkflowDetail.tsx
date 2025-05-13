import { useState, useEffect } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { cn } from "@/lib/utils";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { 
  ChevronLeft, 
  CheckCircle2, 
  CircleDot, 
  AlertCircle, 
  CircleX, 
  Clock,
  CheckIcon,
  ArrowRightCircle,
  MoreHorizontal
} from "lucide-react";
import { Button } from "../ui/button";
import { Badge } from "@/components/ui/badge";
import { motion } from "framer-motion";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { WorkflowDetail, WorkflowStep } from "@/types/workflow";
import { calculateLineAnimations } from "@/utils/workflowAnimation";
import ParallelWorkflowDetailPage from "./ParallelWorkflowDetail";

// Mock data for workflow details with steps and transitions
const mockWorkflowDetails: Record<string, WorkflowDetail> = {
  "1": {
    id: "1",
    name: "Workflow 1",
    description: "This is a description of the workflow",
    workflowType: "sequential",
    createdBy: "user-1",
    organizationId: "org-1",
    status: "active",
    config: {},
    workflowMetadata: {},
    version: "1.0.0",
    tags: ["automation", "test"],
    aiEnabled: false,
    createdAt: "2025-01-20T10:00:00",
    updatedAt: "2025-01-20T10:00:00",
    lastExecutedAt: "2025-01-20T10:00:00",
    steps: [
      { 
        id: "s1", 
        name: "Start", 
        description: "Initial step", 
        type: "start",
        workflowId: "1",
        stepOrder: 1,
        status: "completed",
        isRequired: true
      },
      { 
        id: "s2", 
        name: "Process Data", 
        description: "Process incoming data", 
        type: "process",
        workflowId: "1",
        stepOrder: 2,
        status: "active",
        isRequired: true
      },
      { 
        id: "s3", 
        name: "Validate Results", 
        description: "Ensure data meets criteria", 
        type: "decision",
        workflowId: "1",
        stepOrder: 3,
        status: "pending",
        isRequired: true
      },
      { 
        id: "s4", 
        name: "Complete", 
        description: "Workflow completed", 
        type: "end",
        workflowId: "1",
        stepOrder: 4,
        status: "pending",
        isRequired: true
      }
    ],
    transitions: [
      { id: "t1", from: "s1", to: "s2", workflowId: "1" },
      { id: "t2", from: "s2", to: "s3", workflowId: "1" },
      { id: "t3", from: "s3", to: "s4", condition: "Valid data", workflowId: "1" }
    ]
  },
  "2": {
    id: "2",
    name: "Workflow 2",
    description: "This is another description of the workflow",
    workflowType: "parallel",
    createdBy: "user-1",
    organizationId: "org-1",
    status: "completed",
    config: {},
    workflowMetadata: {},
    version: "1.0.0",
    tags: ["production"],
    aiEnabled: true,
    createdAt: "2025-01-19T23:00:00",
    updatedAt: "2025-01-19T23:00:00",
    lastExecutedAt: "2025-01-19T23:00:00",
    steps: [
      { 
        id: "s1", 
        name: "Start", 
        description: "Initial step", 
        type: "start",
        workflowId: "2",
        stepOrder: 1,
        status: "completed",
        isRequired: true
      },
      { 
        id: "s2", 
        name: "Collect Data", 
        description: "Gather information", 
        type: "process",
        workflowId: "2",
        stepOrder: 2,
        status: "completed",
        isRequired: true
      },
      { 
        id: "s3a", 
        name: "Process Images", 
        description: "Process image data", 
        type: "process",
        workflowId: "2",
        stepOrder: 3,
        status: "completed",
        isRequired: true
      },
      { 
        id: "s3b", 
        name: "Process Text", 
        description: "Process text data", 
        type: "process",
        workflowId: "2",
        stepOrder: 3,
        status: "completed",
        isRequired: true
      },
      { 
        id: "s4", 
        name: "Merge Results", 
        description: "Join: Combine analysis results", 
        type: "decision",
        workflowId: "2",
        stepOrder: 4,
        status: "completed",
        isRequired: true
      },
      { 
        id: "s5", 
        name: "Final Review", 
        description: "Review the results", 
        type: "process",
        workflowId: "2",
        stepOrder: 5,
        status: "completed",
        isRequired: true
      },
      { 
        id: "s6", 
        name: "Complete", 
        description: "Workflow completed", 
        type: "end",
        workflowId: "2",
        stepOrder: 6,
        status: "completed",
        isRequired: true
      }
    ],
    transitions: [
      { id: "t1", from: "s1", to: "s2", workflowId: "2" },
      { id: "t2a", from: "s2", to: "s3a", workflowId: "2" },
      { id: "t2b", from: "s2", to: "s3b", workflowId: "2" },
      { id: "t3a", from: "s3a", to: "s4", workflowId: "2" },
      { id: "t3b", from: "s3b", to: "s4", workflowId: "2" },
      { id: "t4", from: "s4", to: "s5", workflowId: "2" },
      { id: "t5", from: "s5", to: "s6", workflowId: "2" }
    ]
  },
  "3": {
    id: "3",
    name: "Workflow 3",
    description: "This is another description of the workflow",
    workflowType: "conditional",
    createdBy: "user-1",
    organizationId: "org-1",
    status: "pending",
    config: {},
    workflowMetadata: {},
    version: "1.0.0",
    tags: [],
    aiEnabled: false,
    createdAt: "2025-01-01T00:00:00",
    updatedAt: "2025-01-01T00:00:00",
    steps: [
      { 
        id: "s1", 
        name: "Start", 
        description: "Initial step", 
        type: "start",
        workflowId: "3",
        stepOrder: 1,
        status: "pending",
        isRequired: true
      },
      { 
        id: "s2", 
        name: "Data Collection", 
        description: "Gather required information", 
        type: "process",
        workflowId: "3",
        stepOrder: 2,
        status: "pending",
        isRequired: true
      },
      { 
        id: "s3", 
        name: "Data Processing", 
        description: "Process the collected data", 
        type: "process",
        workflowId: "3",
        stepOrder: 3,
        status: "pending",
        isRequired: true
      },
      { 
        id: "s4", 
        name: "Validation", 
        description: "Validate the results", 
        type: "decision",
        workflowId: "3",
        stepOrder: 4,
        status: "pending",
        isRequired: true
      },
      { 
        id: "s5", 
        name: "Finalize", 
        description: "Finalize the workflow", 
        type: "end",
        workflowId: "3",
        stepOrder: 5,
        status: "pending",
        isRequired: true
      }
    ],
    transitions: [
      { id: "t1", from: "s1", to: "s2", workflowId: "3" },
      { id: "t2", from: "s2", to: "s3", workflowId: "3" },
      { id: "t3", from: "s3", to: "s4", workflowId: "3" },
      { id: "t4", from: "s4", to: "s5", condition: "Valid", workflowId: "3" }
    ]
  }
};

interface WorkflowDetailProps {
  darkMode?: boolean;
}

export default function WorkflowDetailPage({ darkMode = false }: WorkflowDetailProps) {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [workflow, setWorkflow] = useState<WorkflowDetail | null>(null);

  useEffect(() => {
    // In a real app, fetch the workflow detail from an API
    // For now, use our mock data
    if (id && mockWorkflowDetails[id]) {
      setWorkflow(mockWorkflowDetails[id]);
    }
  }, [id]);

  if (!workflow) {
    return (
      <div className="flex flex-1 flex-col p-6 h-[calc(100vh-32px)] overflow-hidden">
        <p>Workflow not found</p>
      </div>
    );
  }

  // Render different workflow visualizations based on workflow type
  switch (workflow.workflowType) {
    case "parallel":
      return <ParallelWorkflowDetailPage darkMode={darkMode} mockData={workflow} />;
    case "sequential":
    default:
      return <SequentialWorkflowDetail workflow={workflow} darkMode={darkMode} />;
  }
}

// Sequential workflow visualization component
interface SequentialWorkflowDetailProps {
  workflow: WorkflowDetail;
  darkMode?: boolean;
}

function SequentialWorkflowDetail({ workflow, darkMode = false }: SequentialWorkflowDetailProps) {
  const navigate = useNavigate();
  const [activeStep, setActiveStep] = useState<string | null>(null);
  const [completedSteps, setCompletedSteps] = useState<string[]>([]);
  const [expandedStep, setExpandedStep] = useState<string | null>(null);
  const [lastCompletedStep, setLastCompletedStep] = useState<string | null>(null);

  useEffect(() => {
    // Initialize from workflow data
    if (workflow.steps.length > 0) {
      // Set first step as active by default
      setActiveStep(workflow.steps[0].id);
      
      // Set completed steps based on the workflow data
      const completed = workflow.steps
        .filter(step => step.status === "completed")
        .map(step => step.id);
        
      setCompletedSteps(completed);
      
      if (completed.length > 0) {
        setLastCompletedStep(completed[completed.length - 1]);
      }
    }
  }, [workflow]);

  const handleBack = () => {
    navigate(-1); // Go back to the previous page
  };

  const getStepIcon = (type: string, isCompleted: boolean = false) => {
    if (isCompleted) {
      return <CheckCircle2 className="h-6 w-6 text-white" />;
    }
    
    switch (type) {
      case "start":
        return <CircleDot className="h-6 w-6 text-emerald-500" />;
      case "process":
        return <ArrowRightCircle className="h-6 w-6 text-primary" />;
      case "decision":
        return <AlertCircle className="h-6 w-6 text-amber-500" />;
      case "end":
        return <CheckCircle2 className="h-6 w-6 text-destructive" />;
      default:
        return <CircleDot className="h-6 w-6" />;
    }
  };

  const getStepBadgeStyles = (type: string) => {
    switch (type) {
      case "start":
        return "text-emerald-600 border-emerald-200 bg-emerald-50 dark:text-emerald-400 dark:border-emerald-950 dark:bg-emerald-950 dark:bg-opacity-20";
      case "process":
        return "text-primary border-primary/20 bg-primary/10 dark:text-primary dark:border-primary/20 dark:bg-primary/10";
      case "decision":
        return "text-amber-600 border-amber-200 bg-amber-50 dark:text-amber-400 dark:border-amber-950 dark:bg-amber-950 dark:bg-opacity-20";
      case "end":
        return "text-destructive border-destructive/20 bg-destructive/10 dark:text-destructive dark:border-destructive/20 dark:bg-destructive/10";
      default:
        return "text-muted-foreground border-border bg-muted dark:text-muted-foreground dark:border-border dark:bg-muted";
    }
  };

  const getStepRingStyle = (type: string) => {
    switch (type) {
      case "start":
        return "ring-emerald-500";
      case "process":
        return "ring-primary";
      case "decision":
        return "ring-amber-500";
      case "end":
        return "ring-destructive";
      default:
        return "ring-muted-foreground";
    }
  };

  const handleToggleStepCompletion = (stepId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    const newCompletedSteps = completedSteps.includes(stepId)
      ? completedSteps.filter(id => id !== stepId)
      : [...completedSteps, stepId];
      
    setCompletedSteps(newCompletedSteps);
    
    if (!completedSteps.includes(stepId)) {
      setLastCompletedStep(stepId);
    } else if (stepId === lastCompletedStep) {
      // If we're un-completing the last step, find the new "last" completed step
      const remainingCompleted = newCompletedSteps.filter(id => id !== stepId);
      setLastCompletedStep(remainingCompleted.length > 0 ? remainingCompleted[remainingCompleted.length - 1] : null);
    }
  };

  const handleExpandStep = (stepId: string) => {
    setExpandedStep(expandedStep === stepId ? null : stepId);
    setActiveStep(stepId);
  };

  // Calculate progress percentage
  const progressPercentage = workflow.steps.length > 0
    ? (completedSteps.length / workflow.steps.length) * 100
    : 0;

  // Group steps into rows of 3
  const groupedSteps = workflow.steps.reduce<WorkflowStep[][]>((acc, step, index) => {
    const rowIndex = Math.floor(index / 3);
    if (!acc[rowIndex]) {
      acc[rowIndex] = [];
    }
    acc[rowIndex].push(step);
    return acc;
  }, []);
  
  // Calculate animations for all lines
  const { horizontalLines, verticalLines, getConnectionPath } = calculateLineAnimations(groupedSteps, completedSteps);

  return (
    <div className="flex flex-1 flex-col gap-4 p-6 h-[calc(100vh-32px)] overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Button 
            variant="ghost" 
            size="sm" 
            onClick={handleBack}
            className="p-0 h-8 w-8 mr-1"
          >
            <ChevronLeft className="h-5 w-5" />
          </Button>
          <h2 className="text-3xl font-bold tracking-tight">{workflow.name}</h2>
        </div>

        <div className="flex items-center gap-2">
          <Button 
            variant="outline" 
            size="sm" 
            className="gap-1.5 h-8"
          >
            <CheckIcon className="h-3.5 w-3.5" />
            Auto-Run
          </Button>
        </div>
      </div>

      {/* Main content container */}
      <div className="flex-1 flex flex-col min-h-0">
        {/* Workflow Status Bar - simplified to a single line */}
        <div className="flex items-center justify-between mb-3 px-1 py-1.5">
          <div className="flex items-center gap-2">
            <Badge variant="outline" className="text-xs">
              {workflow.steps.length} steps
            </Badge>
            <Badge 
              variant="outline" 
              className={cn(
                "text-xs",
                completedSteps.length === workflow.steps.length 
                  ? "bg-emerald-50 text-emerald-600 border-emerald-200 dark:bg-emerald-950/20 dark:text-emerald-400 dark:border-emerald-900/30"
                  : "bg-amber-50 text-amber-600 border-amber-200 dark:bg-amber-950/20 dark:text-amber-400 dark:border-amber-900/30"
              )}
            >
              {completedSteps.length === workflow.steps.length ? "Complete" : "In Progress"}
            </Badge>
            <span className="text-xs text-muted-foreground flex items-center">
              <Clock className="h-3 w-3 mr-1 inline" />
              {workflow.lastExecutedAt ? new Date(workflow.lastExecutedAt).toLocaleDateString() : 'Never'}
            </span>
          </div>
          
          <div className="flex items-center gap-2">
            <span className="text-xs font-medium">{Math.round(progressPercentage)}%</span>
            <div className="h-1.5 w-24 bg-muted rounded-full overflow-hidden">
              <motion.div 
                className={cn(
                  "h-full rounded-full",
                  completedSteps.length === workflow.steps.length
                    ? "bg-emerald-500 dark:bg-emerald-500"
                    : "bg-primary"
                )}
                initial={{ width: 0 }}
                animate={{ width: `${progressPercentage}%` }}
                transition={{ duration: 0.5, ease: "easeOut" }}
              />
            </div>
            <span className="text-xs text-muted-foreground">
              {completedSteps.length}/{workflow.steps.length}
            </span>
          </div>
        </div>

        {/* Workflow Steps Container */}
        <div className="flex-1 bg-background border border-border rounded-xl overflow-hidden flex flex-col min-h-0">
          <div className="p-4 border-b border-border flex items-center justify-between bg-card">
            <h3 className="font-medium">Sequential Workflow</h3>
            <div className="flex items-center text-sm">
              <span className="mr-2 text-muted-foreground">Completion Flow</span>
              <div className="w-16 h-1.5 bg-muted rounded-full overflow-hidden">
                <motion.div 
                  className="h-full bg-primary rounded-full"
                  initial={{ width: 0 }}
                  animate={{ width: `${progressPercentage}%` }}
                  transition={{ duration: 0.5, ease: "easeOut" }}
                />
              </div>
            </div>
          </div>
          
          <div className="flex-1 overflow-auto p-4 min-h-0">
            {groupedSteps.map((rowSteps, rowIndex) => {
              const isRtl = rowIndex % 2 !== 0; // Every odd row is right-to-left
              // Don't reverse the steps array, we'll handle the visual order with flex-row-reverse
              const sortedSteps = rowSteps;
              
              return (
                <div key={`row-${rowIndex}`} className={`mb-16 relative ${rowIndex === 0 ? 'pt-4' : ''}`}>
                  {/* Background horizontal line for the row */}
                  <div 
                    className="absolute h-1.5 bg-border dark:bg-muted rounded-full z-0 overflow-hidden"
                    style={{
                      top: 'calc(50% + 12px)', // Adjusted position
                      left: '15%', // Pushed inward from left side
                      right: '15%', // Pushed inward from right side
                      transform: 'translateY(-50%)'
                    }}
                  >
                    {/* Animated horizontal line fill based on completion */}
                    <motion.div 
                      className="h-full bg-primary rounded-full"
                      initial={{ width: 0 }}
                      animate={{ width: `${horizontalLines[rowIndex]}%` }}
                      transition={{ 
                        duration: 0.5, 
                        ease: "easeOut",
                        // If there's a previous row, delay this row's animation slightly to create a sequence effect
                        delay: rowIndex > 0 ? 0.05 * rowIndex : 0
                      }}
                      style={{
                        transformOrigin: isRtl ? 'right' : 'left',
                        marginLeft: isRtl ? 'auto' : '0'
                      }}
                    />
                  </div>
                  
                  {/* Vertical connecting line to previous row */}
                  {rowIndex > 0 && (
                    <div 
                      className="absolute w-1.5 bg-border dark:bg-muted rounded-full z-0 overflow-hidden"
                      style={{
                        top: '-70px', // Connect to previous row
                        height: '70px',
                        // Position based on the zigzag pattern - correctly align connection points
                        // Apply different adjustments based on the direction:
                        // - For LTR to RTL transitions (row 1 to 2): move right (+5px)
                        // - For RTL to LTR transitions (row 2 to 3): move left (-5px)
                        left: `calc(${(rowIndex-1) % 2 === 0 ? '85%' : '15%'} ${(rowIndex-1) % 2 === 0 ? '+' : '-'} 17px)`,
                        transform: 'translateX(-50%)'
                      }}
                    >
                      {/* Animated vertical line fill based on completion */}
                      <motion.div 
                        className="w-full bg-primary rounded-full"
                        initial={{ height: 0 }}
                        animate={{ height: `${verticalLines[rowIndex-1]}%` }}
                        transition={{ 
                          duration: 0.4, 
                          ease: "easeOut",
                          // Time the vertical animation to happen after the previous row's horizontal animation
                          // but before the current row's horizontal animation
                          delay: 0.05 * (rowIndex - 0.5)
                        }}
                        style={{ transformOrigin: 'top' }}
                      />
                    </div>
                  )}
                  
                  <div className={`flex items-center justify-between px-4 relative ${isRtl ? 'flex-row-reverse' : 'flex-row'}`}>
                    {sortedSteps.map((step, colIndex) => {
                      // Use simple index calculation since we're handling direction with CSS
                      const actualIndex = colIndex;
                      const stepIndex = rowIndex * 3 + actualIndex;
                      const isCompleted = completedSteps.includes(step.id);
                      const isExpanded = expandedStep === step.id;
                      
                      return (
                        <motion.div 
                          key={step.id} 
                          className="flex flex-col items-center relative z-10"
                          initial={{ opacity: 0, y: 20 }}
                          animate={{ opacity: 1, y: 0 }}
                          transition={{ duration: 0.3, delay: stepIndex * 0.1 }}
                          style={{ width: 'calc(27.33% - 1rem)' }}
                        >
                          {/* Step Node */}
                          <motion.div 
                            className={cn(
                              "relative w-full p-5 rounded-xl shadow-md transition-all duration-200 mt-4",
                              "bg-card border border-border",
                              activeStep === step.id && `ring-2 ${getStepRingStyle(step.type)} ring-opacity-70`,
                              isCompleted && "border-primary/30 dark:border-primary/30",
                              "cursor-pointer group z-10"
                            )}
                            layout
                            onClick={() => handleExpandStep(step.id)}
                            whileHover={{ scale: 1.02, y: -2 }}
                            transition={{ 
                              layout: { duration: 0.2 },
                              scale: { duration: 0.1 }
                            }}
                          >
                            {/* Step Icon - Improved positioning and sizing */}
                            <motion.div
                              className={cn(
                                "absolute top-0 rounded-full p-2.5 shadow-md border border-border",
                                "bg-background group-hover:scale-110 transition-transform",
                                isCompleted ? "bg-emerald-600" : ""
                              )}
                              onClick={(e) => handleToggleStepCompletion(step.id, e)}
                              style={{ 
                                left: '50%',
                                transform: 'translate(-50%, -50%)',
                                zIndex: 30
                              }}
                            >
                              {getStepIcon(step.type, isCompleted)}
                            </motion.div>
                            
                            <div className="w-full pt-4">
                              <div className="flex justify-between items-start">
                                <h3 className={cn(
                                  "font-medium text-base text-card-foreground",
                                  isCompleted && "text-primary dark:text-primary"
                                )}>{step.name}</h3>
                                <Badge variant="outline" className={cn(
                                  "text-xs capitalize",
                                  getStepBadgeStyles(step.type)
                                )}>
                                  {step.type}
                                </Badge>
                              </div>
                              <p className="text-sm text-muted-foreground mt-1.5">{step.description}</p>
                              
                              {/* Expanded Actions - Only show when expanded */}
                              {isExpanded && (
                                <motion.div 
                                  className="mt-4 pt-3 border-t border-border flex justify-end gap-2"
                                  initial={{ opacity: 0, height: 0 }}
                                  animate={{ opacity: 1, height: "auto" }}
                                  exit={{ opacity: 0, height: 0 }}
                                >
                                  <TooltipProvider>
                                    <Tooltip>
                                      <TooltipTrigger asChild>
                                        <Button 
                                          size="sm" 
                                          variant="outline"
                                          className="h-8 px-2.5 text-xs"
                                          onClick={(e) => {
                                            e.stopPropagation();
                                            handleToggleStepCompletion(step.id, e);
                                          }}
                                        >
                                          <CheckIcon className="h-3.5 w-3.5 mr-1.5" />
                                          {isCompleted ? "Mark Incomplete" : "Mark Complete"}
                                        </Button>
                                      </TooltipTrigger>
                                      <TooltipContent>
                                        <p>Toggle step completion status</p>
                                      </TooltipContent>
                                    </Tooltip>
                                  </TooltipProvider>
                                  
                                  <TooltipProvider>
                                    <Tooltip>
                                      <TooltipTrigger asChild>
                                        <Button 
                                          size="sm" 
                                          variant="ghost"
                                          className="h-8 w-8 p-0 text-muted-foreground"
                                          onClick={(e) => e.stopPropagation()}
                                        >
                                          <MoreHorizontal className="h-4 w-4" />
                                        </Button>
                                      </TooltipTrigger>
                                      <TooltipContent>
                                        <p>More actions</p>
                                      </TooltipContent>
                                    </Tooltip>
                                  </TooltipProvider>
                                </motion.div>
                              )}
                            </div>
                          </motion.div>
                        </motion.div>
                      );
                    })}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}