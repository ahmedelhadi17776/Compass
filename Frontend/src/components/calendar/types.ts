export interface CalendarEvent {
  id: string;
  title: string;
  description?: string;
  start: Date;
  end: Date;
  start_date?: Date;
  end_date?: Date;
  location?: string;
  status: 'Upcoming' | 'In Progress' | 'Completed' | 'Cancelled' | 'Blocked' | 'Under Review' | 'Deferred';
  priority: 'Low' | 'Medium' | 'High';
  user_id: number;
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
