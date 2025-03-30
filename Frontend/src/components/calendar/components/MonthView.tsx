import React from 'react';
import { format, startOfMonth, endOfMonth, eachDayOfInterval, isSameMonth, isToday, startOfWeek, endOfWeek } from 'date-fns';
import { cn } from '@/lib/utils';
import './MonthView.css';
import { CalendarEvent } from '../types';
import { useMonthEvents, useUpdateEvent } from '@/components/calendar/hooks';
import { Skeleton } from '@/components/ui/skeleton';

interface MonthViewProps {
  date: Date;
  onEventClick: (event: CalendarEvent) => void;
  darkMode?: boolean;
}

const MonthView: React.FC<MonthViewProps> = ({ date, onEventClick, darkMode }) => {
  const monthStart = startOfMonth(date);
  const monthEnd = endOfMonth(date);
  const calendarStart = startOfWeek(monthStart);
  const calendarEnd = endOfWeek(monthEnd);
  const days = eachDayOfInterval({ start: calendarStart, end: calendarEnd });

  const { 
    data: events = [], 
    isLoading, 
    isError,
    error,
    refetch 
  } = useMonthEvents(date, 1, { expand_recurring: true });

  const getEventsForDay = (day: Date) => {
    return events.filter((event: CalendarEvent) => 
      format(new Date(event.start), 'yyyy-MM-dd') === format(day, 'yyyy-MM-dd')
    );
  };

  const getPriorityEmoji = (priority: string): string => {
    switch (priority) {
      case 'HIGH': return '🔴';
      case 'MEDIUM': return '🟡';
      case 'LOW': return '🟢';
      default: return '';
    }
  };

  if (isLoading) {
    return <div className="month-view"><Skeleton className="w-full h-full" /></div>;
  }

  if (isError) {
    return (
      <div className="flex flex-col items-center justify-center h-full p-4">
        <div className={cn(
          "p-4 mb-4 rounded-md",
          darkMode ? "bg-red-900/20 text-red-200" : "bg-red-50 text-red-500"
        )}>
          {error instanceof Error ? error.message : 'Failed to load events'}
        </div>
        <button
          onClick={() => refetch()}
          className={cn(
            "px-4 py-2 rounded-md",
            darkMode 
              ? "bg-gray-700 hover:bg-gray-600 text-white" 
              : "bg-blue-500 hover:bg-blue-600 text-white"
          )}
        >
          Try Again
        </button>
      </div>
    );
  }

  return (
    <div className={cn("month-view", darkMode && "dark")}>
      <div className="month-container">
        <div className="month-grid">
          {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map(day => (
            <div key={day} className="month-weekday-header">
              {day}
            </div>
          ))}

          {days.map(day => (
            <div 
              key={day.toISOString()}
              className={cn(
                "month-day-cell",
                !isSameMonth(day, date) && "month-other-day",
                isToday(day) && "month-today",
                darkMode && "dark"
              )}
            >
              <div className="month-day-header">
                <span className="month-day-number">{format(day, 'd')}</span>
              </div>
              <div className="month-day-events">
                {getEventsForDay(day).map((event: CalendarEvent) => (
                  <div 
                    key={event.id}
                    className={cn(
                      "month-event-pill",
                      `priority-${event.priority}`,
                      darkMode && "dark"
                    )}
                    onClick={() => onEventClick(event)}
                  >
                    <div className="month-event-time">{format(new Date(event.start), 'h:mm a')}</div>
                    <div className="month-event-title">
                      <span className="priority-emoji">{getPriorityEmoji(event.priority)}</span>
                      {event.title}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default MonthView;