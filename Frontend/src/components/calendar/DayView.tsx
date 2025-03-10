import React, { useState, useEffect } from 'react';
import { format, isSameDay } from 'date-fns';
import './DayView.css';
import { cn } from '@/lib/utils';
import EventCard from './EventCard';
import { CalendarEvent } from './types';

interface DayViewProps {
  events: CalendarEvent[];
  date: Date;
  onEventClick: (event: CalendarEvent) => void;
  onEventDrop?: (event: CalendarEvent, hour: number, minutes: number) => void;
  darkMode: boolean;
}

const DayView: React.FC<DayViewProps> = ({ events, date, onEventClick, onEventDrop, darkMode }) => {
  const [draggingEvent, setDraggingEvent] = React.useState<CalendarEvent | null>(null);
  const [currentTime, setCurrentTime] = useState<Date>(new Date());
  
  // Sample event for demonstration - can be removed later
  const sampleEvents = [
    ...events,
    {
      id: 'sample-event-1',
      title: 'Complete 2 blog posts on coffee',
      start: new Date(new Date(date).setHours(9, 30)),
      end: new Date(new Date(date).setHours(10, 30)),
      priority: 'medium' as 'high' | 'medium' | 'low',
      category: 'work',
    }
  ];

  // Use sampleEvents instead of events
  const todayEvents = sampleEvents.filter(event => isSameDay(new Date(event.start), date));
  const sortedEvents = todayEvents.sort((a, b) => a.start.getTime() - b.start.getTime());
  const timeSlots = Array.from({ length: 24 }, (_, i) => i);

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

  const handleDragStart = (event: CalendarEvent, e: React.DragEvent) => {
    setDraggingEvent(event);
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
            <div className="day-date">{format(date, 'd MMMM, yyyy')}</div>
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
                      <EventCard
                        key={event.id}
                        event={event}
                        onClick={onEventClick}
                        onDragStart={handleDragStart}
                        style={{
                          top: `${new Date(event.start).getMinutes()}px`,
                          height: `${getDurationInMinutes(event.start, event.end)}px`,
                        }}
                      />
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