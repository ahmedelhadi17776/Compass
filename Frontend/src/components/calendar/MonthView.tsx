import React from 'react';
import { format, startOfMonth, endOfMonth, eachDayOfInterval, isSameMonth, isToday, startOfWeek, endOfWeek } from 'date-fns';
import './MonthView.css';

interface Event {
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

interface MonthViewProps {
  events: Event[];
  date: Date;
  onEventClick: (event: Event) => void;
}

const MonthView: React.FC<MonthViewProps> = ({ events, date, onEventClick }) => {
  const monthStart = startOfMonth(date);
  const monthEnd = endOfMonth(date);
  const calendarStart = startOfWeek(monthStart);
  const calendarEnd = endOfWeek(monthEnd);
  const days = eachDayOfInterval({ start: calendarStart, end: calendarEnd });

  const getEventsForDay = (day: Date) => {
    return events.filter(event => 
      format(new Date(event.start), 'yyyy-MM-dd') === format(day, 'yyyy-MM-dd')
    );
  };

  const getPriorityEmoji = (priority: string): string => {
    switch (priority) {
      case 'high': return '🔴';
      case 'medium': return '🟡';
      case 'low': return '🟢';
      default: return '';
    }
  };

  return (
    <div className="month-view">
      <div className="month-grid">
        {/* Week day headers */}
        {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map(day => (
          <div key={day} className="month-weekday-header">
            {day}
          </div>
        ))}

        {/* Calendar days */}
        {days.map(day => (
          <div 
            key={day.toISOString()}
            className={`month-day-cell ${!isSameMonth(day, date) ? 'month-other-day' : ''} ${isToday(day) ? 'month-today' : ''}`}
          >
            <div className="month-day-header">
              <span className="month-day-number">{format(day, 'd')}</span>
            </div>
            <div className="month-day-events">
              {getEventsForDay(day).map(event => (
                <div 
                  key={event.id}
                  className={`month-event-pill category-${event.category} priority-${event.priority}`}
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
  );
};

export default MonthView; 