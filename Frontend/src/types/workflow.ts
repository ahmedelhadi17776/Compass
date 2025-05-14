export interface WorkflowStep {
  id: string;
  name: string;
  description: string;
  type: "start" | "process" | "decision" | "end";
}

export interface WorkflowTransition {
  from: string;
  to: string;
  condition?: string;
}

export interface WorkflowDetail {
  id: string;
  name: string;
  description: string;
  lastRun: string;
  steps: WorkflowStep[];
  transitions: WorkflowTransition[];
} 