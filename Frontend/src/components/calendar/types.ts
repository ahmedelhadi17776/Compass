export interface CalendarEvent {
  id: string;
  user_id: string;
  title: string;
  description: string;
  event_type: 'None' | 'Task' | 'Meeting' | 'Todo' | 'Holiday' | 'Reminder';
  start_time: Date;
  end_time: Date;
  is_all_day: boolean;
  location?: string;
  color?: string;
  transparency: 'opaque' | 'transparent';
  created_at: Date;
  updated_at: Date;
  recurrence_rules?: RecurrenceRule[];
  occurrences?: OccurrenceResponse[];
  exceptions?: EventException[];
  reminders?: EventReminder[];
}

export interface CreateEventData {
  title: string;
  description: string;
  start_time: Date;
  end_time: Date;
  is_all_day: boolean;
  location?: string;
  color?: string;
  transparency: 'opaque' | 'transparent';
}

export interface RecurrenceRule {
  id: string;
  event_id: string;
  freq: 'None' | 'Daily' | 'Weekly' | 'Biweekly' | 'Monthly' | 'Yearly' | 'Custom';
  interval: number;
  by_day?: string[];
  by_month?: number[];
  by_month_day?: number[];
  count?: number;
  until?: Date;
  created_at: Date;
  updated_at: Date;
}

export interface OccurrenceResponse {
  id: string;
  event_id: string;
  occurrence_time: Date;
  status: 'Upcoming' | 'Cancelled' | 'Completed';
  created_at: Date;
  updated_at: Date;
  title?: string;
  description?: string;
  location?: string;
  color?: string;
  transparency?: 'opaque' | 'transparent';
}

export interface EventException {
  id: string;
  event_id: string;
  original_time: Date;
  is_deleted: boolean;
  override_start_time?: Date;
  override_end_time?: Date;
  override_title?: string;
  override_description?: string;
  override_location?: string;
  override_color?: string;
  override_transparency?: 'opaque' | 'transparent';
  created_at: Date;
  updated_at: Date;
}

export interface EventReminder {
  id: string;
  event_id: string;
  minutes_before: number;
  method: 'Email' | 'Push' | 'SMS';
  created_at: Date;
  updated_at: Date;
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
