import React from 'react';
import { format } from 'date-fns';
import { cn } from '@/lib/utils';
import './EventCard.css';
import { CalendarEvent } from '../types';

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

  const formatTimeRange = (start: Date, end: Date) => {
    const startTime = format(new Date(start), 'h:mm a');
    const endTime = format(new Date(end), 'h:mm a');
    return `${startTime} - ${endTime}`;
  };

  return (
    <div 
      className="event-card"
      draggable={!!onDragStart}
      onDragStart={handleDragStart}
      onClick={() => onClick(event)}
      style={style}
    >
      <div className="event-title">
        {event.title || 'Untitled'}
      </div>
      <div className="event-time">
        {formatTimeRange(event.start, event.end)}
        {event.location && ` • ${event.location}`}
      </div>
    </div>
  );
};

export default EventCard;