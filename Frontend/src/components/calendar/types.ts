export interface CalendarEvent {
  id: string;
  title: string;
  start: Date;
  end: Date;
  description?: string;
  location?: string;
  priority: 'high' | 'medium' | 'low';
  category: string;
  participants?: {
    name: string;
    status: 'accepted' | 'pending' | 'rejected';
  }[];
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
