export type WorkflowStatus = 
  | "pending"
  | "active"
  | "paused"
  | "completed"
  | "failed"
  | "cancelled"
  | "archived"
  | "under_review"
  | "optimizing";

export type WorkflowType = 
  | "sequential"
  | "parallel"
  | "conditional"
  | "ai_driven"
  | "hybrid";

export type StepType = 
  | "manual"
  | "automated"
  | "approval"
  | "notification"
  | "integration"
  | "decision"
  | "ai_task"
  | "start"
  | "process"
  | "end";

export type StepStatus = 
  | "pending"
  | "active"
  | "completed"
  | "failed"
  | "cancelled"
  | "skipped";

export interface WorkflowStep {
  id: string;
  workflowId: string;
  name: string;
  description: string;
  type: StepType;
  stepOrder: number;
  status: StepStatus;
  config?: Record<string, any>;
  conditions?: Record<string, any>;
  timeout?: number;
  retryConfig?: Record<string, any>;
  isRequired: boolean;
  autoAdvance: boolean;
  canRevert: boolean;
  dependencies?: string[];
  version: string;
  previousVersionId?: string;
  averageExecutionTime: number;
  successRate: number;
  lastExecutionResult?: Record<string, any>;
  assignedTo?: string;
  notificationConfig?: Record<string, any>;
  createdAt: string;
  updatedAt: string;
}

export interface WorkflowTransition {
  id: string;
  fromStepId: string;
  toStepId: string;
  condition?: string;
  workflowId: string;
  conditions?: Record<string, any>;
  triggers?: Record<string, any>;
}

export interface WorkflowDetail {
  id: string;
  name: string;
  description: string;
  workflowType: WorkflowType;
  createdBy: string;
  organizationId: string;
  status: WorkflowStatus;
  config?: Record<string, any>;
  workflowMetadata?: Record<string, any>;
  version: string;
  tags: string[];
  
  // AI Integration
  aiEnabled: boolean;
  aiConfidenceThreshold?: number;
  aiOverrideRules?: Record<string, any>;
  aiLearningData?: Record<string, any>;

  // Performance Metrics
  averageCompletionTime?: number;
  successRate?: number;
  optimizationScore?: number;
  bottleneckAnalysis?: Record<string, any>;

  // Time Management
  estimatedDuration?: number;
  actualDuration?: number;
  scheduleConstraints?: Record<string, any>;
  deadline?: string;

  // Error Handling
  errorHandlingConfig?: Record<string, any>;
  retryPolicy?: Record<string, any>;
  fallbackSteps?: Record<string, any>;

  // Audit & Compliance
  complianceRules?: Record<string, any>;
  auditTrail?: Record<string, any>;
  accessControl?: Record<string, any>;

  // Timestamps
  createdAt: string;
  updatedAt: string;
  lastExecutedAt?: string;
  nextScheduledRun?: string;

  // Relations
  steps: WorkflowStep[];
  transitions: WorkflowTransition[];
}

export interface WorkflowListItem {
  id: string;
  name: string;
  description: string;
  workflowType: WorkflowType;
  createdBy: string;
  organizationId: string;
  status: WorkflowStatus;
  config: Record<string, any>;
  workflowMetadata: {
    version: string;
    createdAt: string;
    creatorId: string;
  };
  version: string;
  tags: string[] | null;
  aiEnabled: boolean;
  aiConfidenceThreshold: number;
  aiOverrideRules: Record<string, any>;
  aiLearningData: Record<string, any>;
  averageCompletionTime: number;
  successRate: number;
  optimizationScore: number;
  bottleneckAnalysis: Record<string, any>;
  estimatedDuration: number | null;
  actualDuration: number | null;
  scheduleConstraints: Record<string, any>;
  deadline: string | null;
  errorHandlingConfig: Record<string, any>;
  retryPolicy: Record<string, any>;
  fallbackSteps: Record<string, any>;
  complianceRules: Record<string, any>;
  auditTrail: Record<string, any>;
  accessControl: Record<string, any>;
  createdAt: string;
  updatedAt: string;
  lastExecutedAt: string | null;
  nextScheduledRun: string | null;
}

export interface CreateWorkflowRequest {
  name: string;
  description: string;
  workflow_type: WorkflowType;
  organization_id: string;
  config?: Record<string, any>;
  ai_enabled?: boolean;
  tags?: string[];
  estimated_duration?: number;
  deadline?: string;
}

export interface UpdateWorkflowRequest {
  name?: string;
  description?: string;
  status?: WorkflowStatus;
  config?: Record<string, any>;
  aiEnabled?: boolean;
  tags?: string[];
  estimatedDuration?: number;
  deadline?: string;
}

export interface WorkflowStepRequest {
  name: string;
  description: string;
  type: StepType;
  stepOrder: number;
  status?: StepStatus;
  config?: Record<string, any>;
  conditions?: Record<string, any>;
  timeout?: number;
  isRequired?: boolean;
  autoAdvance?: boolean;
  canRevert?: boolean;
  dependencies?: string[];
  assignedTo?: string;
  notificationConfig?: Record<string, any>;
}

export interface WorkflowTransitionRequest {
  fromStepId: string;
  toStepId: string;
  conditions?: Record<string, any>;
  triggers?: Record<string, any>;
}

export interface WorkflowExecutionResponse {
  id: string;
  workflowId: string;
  status: WorkflowStatus;
  startedAt: string;
  completedAt?: string;
  error?: string;
  result?: Record<string, any>;
  metadata?: Record<string, any>;
}

export interface WorkflowAnalysisResponse {
  workflowId: string;
  metrics: {
    averageCompletionTime: number;
    successRate: number;
    bottlenecks: Array<{
      stepId: string;
      name: string;
      averageExecutionTime: number;
      recommendation: string;
    }>;
  };
  recommendations: Array<{
    type: string;
    description: string;
    priority: 'high' | 'medium' | 'low';
  }>;
} 