import React from 'react';
import { format, isSameDay, addDays } from 'date-fns';
import { cn } from '@/lib/utils';
import './ThreeDayView.css';
import EventCard from './EventCard';
import { CalendarEvent } from './types';
import { useWeekTasks, useUpdateTask } from '@/hooks/useTasks';
import { Skeleton } from '@/components/ui/skeleton';

interface ThreeDayViewProps {
  date: Date;
  onEventClick: (event: CalendarEvent) => void;
  darkMode?: boolean;
}

const ThreeDayView: React.FC<ThreeDayViewProps> = ({ date, onEventClick, darkMode }) => {
  const [draggingEvent, setDraggingEvent] = React.useState<CalendarEvent | null>(null);
  const [currentTime, setCurrentTime] = React.useState(new Date());

  const { 
    data: events = [], 
    isLoading, 
    isError,
    error,
    refetch 
  } = useWeekTasks(date);
  
  const updateTaskMutation = useUpdateTask();

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

  const handleDrop = async (hour: number, e: React.DragEvent) => {
    e.preventDefault();
    if (!draggingEvent) return;
    
    const rect = (e.target as HTMLElement).getBoundingClientRect();
    const minutes = Math.floor(((e.clientY - rect.top) / rect.height) * 60);
    
    const newStart = new Date(draggingEvent.start);
    newStart.setHours(hour);
    newStart.setMinutes(minutes);

    const duration = draggingEvent.end.getTime() - draggingEvent.start.getTime();
    const newEnd = new Date(newStart.getTime() + duration);

    try {
      await updateTaskMutation.mutateAsync({
        taskId: draggingEvent.id,
        task: {
          ...draggingEvent,
          start: newStart,
          end: newEnd,
        }
      });
    } catch (error) {
      console.error('Failed to update task:', error);
    }

    setDraggingEvent(null);
  };

  const getDurationInMinutes = (start: Date, end: Date): number => {
    return (new Date(end).getTime() - new Date(start).getTime()) / (1000 * 60);
  };

  const timeSlots = Array.from({ length: 24 }, (_, i) => i);
  const days = [date, addDays(date, 1), addDays(date, 2)];

  if (isLoading) {
    return <div className="three-day-view"><Skeleton className="w-full h-full" /></div>;
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
            darkMode ? "bg-gray-800 text-white hover:bg-gray-700" : "bg-white text-gray-900 hover:bg-gray-50"
          )}
        >
          Retry
        </button>
      </div>
    );
  }

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