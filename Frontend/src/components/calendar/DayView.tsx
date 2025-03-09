import React, { useState, useEffect } from 'react';
import { format, isSameDay } from 'date-fns';
import './DayView.css';
import { cn } from '@/lib/utils';

interface Event {
  id: string;
  title: string;
  start: Date;
  end: Date;
  participants?: {
    name: string;
    status: 'accepted' | 'pending' | 'rejected';
  }[];
  location?: string;
  description?: string;
  priority: 'high' | 'medium' | 'low';
}

interface DayViewProps {
  events: Event[];
  date: Date;
  onEventClick: (event: Event) => void;
  onEventDrop?: (event: Event, hour: number, minutes: number) => void;
  darkMode: boolean;
}

const DayView: React.FC<DayViewProps> = ({ events, date, onEventClick, onEventDrop, darkMode }) => {
  const [draggingEvent, setDraggingEvent] = React.useState<Event | null>(null);
  const [currentTime, setCurrentTime] = useState<Date>(new Date());

  useEffect(() => {
    const updateTimeIndicator = () => {
      setCurrentTime(new Date());
    };

    updateTimeIndicator();
    const interval = setInterval(updateTimeIndicator, 60000); // Update every minute

    return () => clearInterval(interval);
  }, []);

  const getCurrentTimePosition = () => {
    const hours = currentTime.getHours();
    const minutes = currentTime.getMinutes();
    return (hours * 60) + minutes;
  };

  const todayEvents = events.filter(event => isSameDay(new Date(event.start), date));
  const sortedEvents = todayEvents.sort((a, b) => a.start.getTime() - b.start.getTime());
  const timeSlots = Array.from({ length: 24 }, (_, i) => i);

  const handleDragStart = (event: Event, e: React.DragEvent) => {
    setDraggingEvent(event);
    e.dataTransfer.setData('text/plain', ''); // Required for Firefox
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

  return (
    <div className="day-view">
      <div className="day-container">
        <div className="day-header">
          <div className="time-label-header"></div>
          <div className={cn(
            "date-header",
            isSameDay(date, new Date()) && "current-day"
          )}>
            <div className="day-name">{format(date, 'EEEE')}</div>
            <div className="day-date">{format(date, 'MMMM d, yyyy')}</div>
          </div>
        </div>
        <div className="time-slots">
          {timeSlots.map(hour => (
            <div key={hour} className="time-slot">
              <div className="time-label">
                {format(new Date().setHours(hour, 0), 'h:mm a')}
              </div>
              <div className="time-content">
                <div
                  className={cn(
                    "day-column",
                    hour === 0 && "has-current-time"
                  )}
                  onDragOver={handleDragOver}
                  onDrop={(e) => handleDrop(hour, e)}
                  style={hour === 0 ? { '--current-time-top': getCurrentTimePosition() } as React.CSSProperties : undefined}
                >
                  {isSameDay(date, currentTime) && hour === currentTime.getHours() && (
                    <div 
                      className="current-time-indicator"
                      style={{
                        top: `${currentTime.getMinutes()}px`,
                      }}
                    />
                  )}
                  {sortedEvents
                    .filter(event => {
                      const eventStart = new Date(event.start);
                      return eventStart.getHours() === hour && isSameDay(eventStart, date);
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
                          top: `${new Date(event.start).getMinutes()}px`,
                          height: `${getDurationInMinutes(event.start, event.end)}px`,
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
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

const getDurationInMinutes = (start: Date, end: Date): number => {
  return (new Date(end).getTime() - new Date(start).getTime()) / (1000 * 60);
};

export default DayView;