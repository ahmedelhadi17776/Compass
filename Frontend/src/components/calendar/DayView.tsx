import React, { useState, useEffect } from 'react';
import { format, isSameDay } from 'date-fns';
import './DayView.css';
import cn from 'classnames';

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
  const [currentTimePosition, setCurrentTimePosition] = useState<number>(0);

  useEffect(() => {
    const updateTimeIndicator = () => {
      const now = new Date();
      const hours = now.getHours();
      const minutes = now.getMinutes();
      
      // Calculate position based on hour slots (60px) and current minutes
      const position = (hours * 60) + minutes;
      setCurrentTimePosition(position);
    };

    updateTimeIndicator();
    const interval = setInterval(updateTimeIndicator, 60000);

    return () => clearInterval(interval);
  }, []);

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

  const getCurrentTimePosition = () => {
    return currentTimePosition;
  };

  return (
    <div className={cn(
      "h-full flex flex-col overflow-hidden",
      darkMode ? "bg-[#25262B] text-white" : "bg-white text-gray-900"
    )}>
      <div className="flex-1 overflow-y-auto">
        <div className="grid grid-cols-[60px_1fr] h-full">
          <div className="time-labels border-r border-gray-200 dark:border-gray-700">
            {timeSlots.map(hour => (
              <div key={hour} className="h-16 -mt-2 text-sm text-gray-500 dark:text-gray-400">
                {format(new Date().setHours(hour), 'ha')}
              </div>
            ))}
          </div>
          
          <div className="relative">
            {/* Current time indicator */}
            {isSameDay(date, new Date()) && (
              <div 
                className="absolute w-full border-t border-red-500 z-10"
                style={{ top: `${getCurrentTimePosition()}px` }}
              >
                <div className="w-2 h-2 rounded-full bg-red-500 -mt-1 -ml-1" />
              </div>
            )}
            
            {/* Time slots */}
            {timeSlots.map(hour => (
              <div 
                key={hour} 
                className="h-16 border-b border-gray-200 dark:border-gray-700 relative"
              >
                {events
                  .filter(event => {
                    const eventStart = new Date(event.start);
                    return eventStart.getHours() === hour && isSameDay(eventStart, date);
                  })
                  .map(event => (
                    <EventCard
                      key={event.id}
                      event={event}
                      onClick={() => onEventClick(event)}
                      darkMode={darkMode}
                    />
                  ))}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

interface EventCardProps {
  event: Event;
  onClick: () => void;
  darkMode: boolean;
}

const EventCard: React.FC<EventCardProps> = ({ event, onClick, darkMode }) => {
  const getDurationInMinutes = (start: Date, end: Date): number => {
    return (new Date(end).getTime() - new Date(start).getTime()) / (1000 * 60);
  };

  return (
    <div 
      className={cn(
        "absolute bg-white dark:bg-gray-800 shadow-md rounded p-2",
        darkMode ? "text-white" : "text-gray-900"
      )}
      style={{
        height: `${getDurationInMinutes(event.start, event.end)}px`,
        top: `${new Date(event.start).getMinutes()}px`
      }}
      onClick={onClick}
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
  );
};

export default DayView;