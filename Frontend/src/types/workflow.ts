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

export interface WorkflowStep {
  id: string;
  name: string;
  description: string;
  type: "start" | "process" | "decision" | "end";
  workflowId: string;
  stepOrder: number;
  status: string;
  config?: Record<string, any>;
  conditions?: Record<string, any>;
  isRequired: boolean;
  assignedTo?: string;
  timeout?: number;
  averageExecutionTime?: number;
  successRate?: number;
}

export interface WorkflowTransition {
  id: string;
  from: string;
  to: string;
  condition?: string;
  workflowId: string;
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
  status: WorkflowStatus;
  createdAt: string;
  updatedAt: string;
  lastExecutedAt?: string;
  tags: string[];
} 