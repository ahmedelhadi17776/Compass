export interface CalendarEvent {
  id: string;
  title: string;
  description?: string;
  start: Date;
  end: Date;
  start_date?: Date;
  end_date?: Date;
  location?: string;
  status: 'To Do' | 'In Progress' | 'Completed' | 'Cancelled' | 'Blocked' | 'Under Review' | 'Deferred';
  priority: 'Low' | 'Medium' | 'High' | 'Urgent';
  category?: string;
  project_id: number;
  organization_id: number;
  creator_id: number;
  user_id: number;
  assignee_id?: number;
  reviewer_id?: number;
  category_id?: number;
  workflow_id?: number;
  parent_task_id?: number;
  estimated_hours?: number;
  actual_hours?: number;
  participants?: {
    name: string;
    status: 'accepted' | 'pending' | 'rejected';
  }[];
  dependencies?: number[];
  ai_suggestions?: Record<string, any>;
  complexity_score?: number;
  time_estimates?: Record<string, any>;
  focus_sessions?: Record<string, any>;
  interruption_logs?: Record<string, any>;
  progress_metrics?: Record<string, any>;
  blockers?: string[];
  health_score?: number;
  risk_factors?: Record<string, any>;
  is_recurring?: boolean;
  is_original?: boolean;
  original_id?: string;
  occurrence_num?: number;
  due_date?: Date;
  recurrence?: 'None' | 'Daily' | 'Weekly' | 'Biweekly' | 'Monthly' | 'Yearly' | 'Weekdays' | 'Custom';
  recurrence_end_date?: Date;
}

export interface CalendarViewProps {
  date: Date;
  events: CalendarEvent[];
  onEventClick: (event: CalendarEvent) => void;
}

export interface CalendarHeaderProps {
  view: 'day' | 'threeDays' | 'week' | 'month';
  onViewChange: (view: 'day' | 'threeDays' | 'week' | 'month') => void;
  currentDate: Date;
  onNavigate: (direction: 'prev' | 'next' | 'today') => void;
}

export interface EventFormProps {
  event?: CalendarEvent;
  onClose: () => void;
  onSubmit: (event: CalendarEvent) => void;
  onDelete?: (eventId: string) => void;
}

export type CalendarView = 'sync' | 'schedule' | 'notes';
