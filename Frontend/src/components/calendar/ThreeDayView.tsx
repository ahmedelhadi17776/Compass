import React from 'react';
import { format, isSameDay, addDays } from 'date-fns';
import { cn } from '@/lib/utils';
import './ThreeDayView.css';
import EventCard from './EventCard';
import { CalendarEvent } from './types';

interface ThreeDayViewProps {
  events: CalendarEvent[];
  date: Date;
  onEventClick: (event: CalendarEvent) => void;
  onEventDrop?: (event: CalendarEvent, hour: number, minutes: number) => void;
}

const ThreeDayView: React.FC<ThreeDayViewProps> = ({ events, date, onEventClick, onEventDrop }) => {
  const [draggingEvent, setDraggingEvent] = React.useState<CalendarEvent | null>(null);
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

  const threeDayEvents = events.filter(event => {
    const eventStart = new Date(event.start);
    const startOfRange = new Date(date);
    startOfRange.setHours(0, 0, 0, 0);
    
    const endOfRange = addDays(startOfRange, 2);
    endOfRange.setHours(23, 59, 59, 999);
    
    return eventStart >= startOfRange && eventStart <= endOfRange;
  });

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

  const getDurationInMinutes = (start: Date, end: Date): number => {
    return (new Date(end).getTime() - new Date(start).getTime()) / (1000 * 60);
  };

  const timeSlots = Array.from({ length: 24 }, (_, i) => i);
  const days = [date, addDays(date, 1), addDays(date, 2)];

  return (
    <div className="three-day-view">
      <div className="three-day-container">
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
              <div className="day-name">{format(day, 'EEEE')}</div>
              <div className="day-date">{format(day, 'd MMMM')}</div>
            </div>
          ))}
        </div>
        <div className="time-slots">
          {timeSlots.map(hour => (
            <div key={hour} className="time-slot">
              <div className="time-label">
                {format(new Date().setHours(hour, 0), 'h:mm a')}
              </div>
              <div className="time-content">
                {days.map(day => (
                  <div
                    key={day.toISOString()}
                    className={cn(
                      "day-column",
                      isSameDay(day, currentTime) && hour === currentTime.getHours() && "has-current-time"
                    )}
                    onDragOver={handleDragOver}
                    onDrop={(e) => handleDrop(hour, e)}
                    style={
                      isSameDay(day, currentTime) && hour === currentTime.getHours() 
                        ? { '--current-time-top': currentTime.getMinutes() } as React.CSSProperties 
                        : undefined
                    }
                  >
                    {isSameDay(day, currentTime) && hour === currentTime.getHours() && (
                      <div 
                        className="current-time-indicator"
                        style={{
                          top: `${currentTime.getMinutes()}px`,
                        }}
                      />
                    )}
                    {threeDayEvents
                      .filter(event => {
                        const eventStart = new Date(event.start);
                        const eventHour = eventStart.getHours();
                        return eventHour === hour && isSameDay(eventStart, day);
                      })
                      .map(event => (
                        <EventCard
                          key={event.id}
                          event={event}
                          onClick={onEventClick}
                          onDragStart={handleDragStart}
                          style={{
                            height: `${getDurationInMinutes(event.start, event.end)}px`,
                            top: `${new Date(event.start).getMinutes()}px`
                          }}
                        />
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

export default ThreeDayView; 