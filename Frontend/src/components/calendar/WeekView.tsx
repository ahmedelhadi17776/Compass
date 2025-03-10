import React from 'react';
import { format, isSameDay, startOfWeek, addDays } from 'date-fns';
import { cn } from '@/lib/utils';
import './WeekView.css';
import EventCard from './EventCard';
import { CalendarEvent } from './types';
import { useWeekTasks, useUpdateTask } from '@/hooks/useTasks';
import { Skeleton } from '@/components/ui/skeleton';

interface WeekViewProps {
  date: Date;
  onEventClick: (event: CalendarEvent) => void;
  darkMode?: boolean;
}

const WeekView: React.FC<WeekViewProps> = ({ date, onEventClick, darkMode }) => {
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

  const weekStart = startOfWeek(date);
  const days = [0, 1, 2, 3, 4, 5, 6].map(offset => addDays(weekStart, offset));
  const timeSlots = Array.from({ length: 24 }, (_, i) => i);

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
    return (end.getTime() - start.getTime()) / (1000 * 60);
  };

  if (isLoading) {
    return <WeekViewSkeleton />;
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
    <div className={cn("week-view", darkMode && "dark")}>
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
                      isSameDay(day, currentTime) && hour === currentTime.getHours() && "has-current-time"
                    )}
                    onDragOver={handleDragOver}
                    onDrop={(e) => handleDrop(hour, e)}
                  >
                    {isSameDay(day, currentTime) && hour === currentTime.getHours() && (
                      <div 
                        className="current-time-indicator"
                        style={{
                          top: `${currentTime.getMinutes()}px`,
                        }}
                      />
                    )}
                    {events
                      .filter((event: CalendarEvent) => {
                        const eventStart = new Date(event.start);
                        return eventStart.getHours() === hour && isSameDay(eventStart, day);
                      })
                      .map((event: CalendarEvent) => (
                        <EventCard
                          key={event.id}
                          event={event}
                          onClick={onEventClick}
                          onDragStart={handleDragStart}
                          style={{
                            height: `${getDurationInMinutes(new Date(event.start), new Date(event.end))}px`,
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

const WeekViewSkeleton = () => {
  const days = Array(7).fill(null);
  const timeSlots = Array(24).fill(null);

  return (
    <div className="week-view">
      <div className="week-container">
        <div className="days-header">
          <div className="time-label-header"></div>
          {days.map((_, i) => (
            <div key={i} className="day-header">
              <Skeleton className="h-6 w-20" />
            </div>
          ))}
        </div>
        <div className="time-slots">
          {timeSlots.map((_, hour) => (
            <div key={hour} className="time-row">
              <div className="time-label">
                <Skeleton className="h-4 w-16" />
              </div>
              <div className="days-content">
                {days.map((_, i) => (
                  <div key={i} className="day-column">
                    {Math.random() > 0.8 && (
                      <Skeleton 
                        className="absolute w-[calc(100%-8px)] rounded-md" 
                        style={{
                          height: `${Math.floor(Math.random() * 100 + 30)}px`,
                          top: `${Math.floor(Math.random() * 45)}px`
                        }}
                      />
                    )}
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