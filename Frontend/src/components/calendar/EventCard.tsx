import React from 'react';
import { format } from 'date-fns';
import { cn } from '@/lib/utils';
import './EventCard.css';
import { CalendarEvent } from './types';

interface EventCardProps {
  event: CalendarEvent;
  onClick: (event: CalendarEvent) => void;
  onDragStart?: (event: CalendarEvent, e: React.DragEvent) => void;
  style?: React.CSSProperties;
}

const EventCard: React.FC<EventCardProps> = ({ 
  event, 
  onClick, 
  onDragStart,
  style 
}) => {
  const handleDragStart = (e: React.DragEvent) => {
    if (onDragStart) {
      onDragStart(event, e);
      e.dataTransfer.setData('text/plain', ''); // Required for Firefox
    }
  };

  return (
    <div 
      className={cn(
        "event-card",
        `priority-${event.priority}`
      )}
      draggable={!!onDragStart}
      onDragStart={handleDragStart}
      onClick={() => onClick(event)}
      style={style}
    >
      <div className="event-title">
        {event.title || 'Untitled'}
      </div>
      <div className="event-time">
        {format(new Date(event.start), 'h:mm a')}
        {event.location && ` • ${event.location}`}
      </div>
    </div>
  );
};

export default EventCard; 