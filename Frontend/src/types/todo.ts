export enum TodoPriority {
  HIGH = "high",
  MEDIUM = "medium",
  LOW = "low"
}

export enum TodoStatus {
  PENDING = "pending",
  IN_PROGRESS = "in_progress",
  COMPLETED = "completed",
  ARCHIVED = "archived"
}

export interface ChecklistItem {
  id: string;
  title: string;
  completed: boolean;
}

export interface Todo {
  id: number;
  user_id: number;
  title: string;
  description?: string;
  status: TodoStatus;
  priority: TodoPriority;
  due_date?: string;
  reminder_time?: string;
  is_recurring: boolean;
  recurrence_pattern?: Record<string, any>;
  tags?: string[];
  checklist?: ChecklistItem[];
  linked_task_id?: number;
  linked_calendar_event_id?: number;
  completion_date?: string;
  created_at: string;
  updated_at: string;
}

export interface TodoFormData {
  title: string;
  description?: string;
  due_date?: Date;
  priority: TodoPriority;
  reminder_time?: Date;
  is_recurring: boolean;
  tags?: string[];
} 