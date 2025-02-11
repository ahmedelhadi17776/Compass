import React from 'react';
import { format, isSameDay, addDays, startOfWeek } from 'date-fns';
import { cn } from '@/lib/utils';
import './WeekView.css';

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

interface WeekViewProps {
  events: Event[];
  date: Date;
  onEventClick: (event: Event) => void;
  onEventDrop?: (event: Event, hour: number, minutes: number) => void;
}

const WeekView: React.FC<WeekViewProps> = ({ events, date, onEventClick, onEventDrop }) => {
  const [draggingEvent, setDraggingEvent] = React.useState<Event | null>(null);
  const [currentTime, setCurrentTime] = React.useState(new Date());

  React.useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date());
    }, 60000); // Update every minute

    return () => clearInterval(timer);
  }, []);

  const getCurrentTimePosition = () => {
    const hours = currentTime.getHours();
    const minutes = currentTime.getMinutes();
    return (hours * 60) + minutes;
  };

  const weekStart = startOfWeek(date);
  const weekEvents = events.filter(event => {
    const eventStart = new Date(event.start);
    const startOfRange = startOfWeek(date);
    startOfRange.setHours(0, 0, 0, 0);
    
    const endOfRange = addDays(startOfRange, 6);
    endOfRange.setHours(23, 59, 59, 999);
    
    return eventStart >= startOfRange && eventStart <= endOfRange;
  });

  const timeSlots = Array.from({ length: 24 }, (_, i) => i);
  const days = [0, 1, 2, 3, 4, 5, 6].map(offset => addDays(weekStart, offset));

  const handleDragStart = (event: Event, e: React.DragEvent) => {
    setDraggingEvent(event);
    e.dataTransfer.setData('text/plain', '');
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
  };

  const handleDrop = (hour: number, e: React.DragEvent) => {
    e.preventDefault();
    if (!draggingEvent || !onEventDrop) return;

    const rect = (e.target as HTMLElement).getBoundingClientRect();
    const minutes = Math.floor(((e.clientY - rect.top) / rect.height) * 60);
    
    onEventDrop(draggingEvent, hour, minutes);
    setDraggingEvent(null);
  };

  const getPriorityEmoji = (priority: string): string => {
    switch (priority) {
      case 'high': return '🔴 ';
      case 'medium': return '🟡 ';
      case 'low': return '🟢 ';
      default: return '';
    }
  };

  const getDurationInMinutes = (start: Date, end: Date): number => {
    return (new Date(end).getTime() - new Date(start).getTime()) / (1000 * 60);
  };

  return (
    <div className="week-view">
      <div className="week-container">
        <div className="days-header">
          <div className="time-label-header"></div>
          {days.map(day => (
            <div 
              key={day.toISOString()} 
              className={cn(
                "day-header",
                isSameDay(day, new Date()) && "current-day"
              )}
            >
              <div className="day-name">{format(day, 'EEE')}</div>
              <div className="day-date">{format(day, 'MMM d')}</div>
            </div>
          ))}
        </div>
        <div className="time-slots">
          {timeSlots.map(hour => (
            <div key={hour} className="time-row">
              <div className="time-label">
                {format(new Date().setHours(hour, 0), 'h:mm a')}
              </div>
              <div className="days-content">
                {days.map(day => (
                  <div
                    key={day.toISOString()}
                    className={cn(
                      "day-column",
                      hour === 0 && "has-current-time"
                    )}
                    onDragOver={handleDragOver}
                    onDrop={(e) => handleDrop(hour, e)}
                    style={hour === 0 ? { '--current-time-top': getCurrentTimePosition() } as React.CSSProperties : undefined}
                  >
                    {isSameDay(day, currentTime) && hour === 0 && (
                      <div 
                        className="current-time-indicator"
                        style={{
                          top: `${getCurrentTimePosition()}px`,
                        }}
                      />
                    )}
                    {weekEvents
                      .filter(event => {
                        const eventHour = new Date(event.start).getHours();
                        return eventHour === hour && isSameDay(new Date(event.start), day);
                      })
                      .map(event => (
                        <div 
                          key={event.id} 
                          className={cn(
                            "event-card",
                            `priority-${event.priority}`
                          )}
                          draggable
                          onDragStart={(e) => handleDragStart(event, e)}
                          onClick={() => onEventClick(event)}
                          style={{
                            height: `${getDurationInMinutes(event.start, event.end)}px`,
                            top: `${new Date(event.start).getMinutes()}px`
                          }}
                        >
                          <div className="event-title">
                            <span className="priority-indicator">{getPriorityEmoji(event.priority)}</span>
                            {event.title || 'Untitled'}
                          </div>
                          <div className="event-time">
                            {format(new Date(event.start), 'h:mm a')} - {format(new Date(event.end), 'h:mm a')}
                            {event.location && ` - 📍 ${event.location}`}
                          </div>
                        </div>
                      ))}
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

export default WeekView;