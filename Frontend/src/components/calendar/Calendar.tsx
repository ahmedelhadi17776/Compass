import React, { useState } from 'react';
import { cn } from '@/lib/utils';
import { format } from 'date-fns';
import { ChevronLeft, ChevronRight, Plus } from 'lucide-react';
import DayView from './DayView';
import WeekView from './WeekView';
import ThreeDayView from './ThreeDayView';
import MonthView from './MonthView';
import TaskForm from './TaskForm';
import ViewSelector from './ViewSelector';
import { CalendarEvent } from './types';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";

type ViewType = 'day' | 'threeDays' | 'week' | 'month';

interface CalendarProps {
  darkMode?: boolean;
  userId?: number;
}

const Calendar: React.FC<CalendarProps> = ({ darkMode = false, userId = 1 }) => {
  const [currentDate, setCurrentDate] = useState(new Date());
  const [currentView, setCurrentView] = useState<ViewType>('week');
  const [showTaskForm, setShowTaskForm] = useState(false);
  const [editingEvent, setEditingEvent] = useState<CalendarEvent | null>(null);
  const [events, setEvents] = useState<CalendarEvent[]>([
    {
      id: '1',
      title: 'Sample Event',
      start: new Date(),
      end: new Date(new Date().setHours(new Date().getHours() + 1)),
      status: 'TODO',
      priority: 'MEDIUM',
      project_id: 1,
      organization_id: 1,
      creator_id: 1,
      user_id: 1,
      category: 'Work'
    }
  ]);

  const handleEventClick = (event: CalendarEvent) => {
    setEditingEvent(event);
    setShowTaskForm(true);
  };

  const handlePrevious = () => {
    const newDate = new Date(currentDate);
    switch (currentView) {
      case 'day':
        newDate.setDate(newDate.getDate() - 1);
        break;
      case 'week':
        newDate.setDate(newDate.getDate() - 7);
        break;
      case 'threeDays':
        newDate.setDate(newDate.getDate() - 3);
        break;
      case 'month':
        newDate.setMonth(newDate.getMonth() - 1);
        break;
    }
    setCurrentDate(newDate);
  };

  const handleNext = () => {
    const newDate = new Date(currentDate);
    switch (currentView) {
      case 'day':
        newDate.setDate(newDate.getDate() + 1);
        break;
      case 'week':
        newDate.setDate(newDate.getDate() + 7);
        break;
      case 'threeDays':
        newDate.setDate(newDate.getDate() + 3);
        break;
      case 'month':
        newDate.setMonth(newDate.getMonth() + 1);
        break;
    }
    setCurrentDate(newDate);
  };

  const handleViewChange = (view: ViewType) => {
    setCurrentView(view);
  };

  const handleCreateEvent = (event: Partial<CalendarEvent>) => {
    const newEvent: CalendarEvent = {
      ...event,
      id: Date.now().toString(),
      status: 'TODO',
      priority: 'MEDIUM',
      project_id: 1,
      organization_id: 1,
      creator_id: 1,
      user_id: 1,
      category: event.category || 'Default'
    } as CalendarEvent;
    
    setEvents(prev => [...prev, newEvent]);
    setShowTaskForm(false);
  };

  const handleUpdateEvent = (updatedEvent: CalendarEvent) => {
    setEvents(prev => prev.map(event => 
      event.id === updatedEvent.id ? updatedEvent : event
    ));
    setShowTaskForm(false);
  };

  const handleDeleteEvent = (eventId: string) => {
    setEvents(prev => prev.filter(event => event.id !== eventId));
    setShowTaskForm(false);
  };

  const renderView = () => {
    const commonProps = {
      date: currentDate,
      onEventClick: handleEventClick,
      darkMode
    };

    switch (currentView) {
      case 'day':
        return <DayView {...commonProps} />;
      case 'threeDays':
        return <ThreeDayView {...commonProps} />;
      case 'week':
        return <WeekView {...commonProps} />;
      case 'month':
        return <MonthView {...commonProps} />;
      default:
        return <WeekView {...commonProps} />;
    }
  };

  return (
    <div className={cn("h-full flex flex-col p-4", darkMode ? "bg-gray-900 text-white" : "bg-background text-foreground")}>
      <div className="flex justify-between items-center mb-4">
        <div className="flex items-center gap-4">
          <button
            onClick={handlePrevious}
            className={cn("p-2 rounded-md", darkMode ? "hover:bg-gray-700" : "hover:bg-accent hover:text-accent-foreground")}
          >
            <ChevronLeft className="w-5 h-5" />
          </button>
          <button
            onClick={handleNext}
            className={cn("p-2 rounded-md", darkMode ? "hover:bg-gray-700" : "hover:bg-accent hover:text-accent-foreground")}
          >
            <ChevronRight className="w-5 h-5" />
          </button>
          <h2 className="text-xl font-semibold">
            {format(currentDate, 'MMMM yyyy')}
          </h2>
        </div>
        <div className="flex items-center gap-2">
          <ViewSelector
            currentView={currentView}
            onViewChange={handleViewChange}
          />
          <button
            onClick={() => setCurrentDate(new Date())}
            className={cn(
              "px-3 py-1.5 rounded-md text-sm font-medium",
              darkMode ? "bg-gray-700 hover:bg-gray-600" : "bg-secondary text-secondary-foreground hover:bg-secondary/90"
            )}
          >
            Today
          </button>
          <Button 
            variant="outline" 
            size="sm" 
            className="gap-2"
            onClick={() => setShowTaskForm(true)}
          >
            <Plus className="h-4 w-4" />
            New Task
          </Button>
        </div>
      </div>
      
      {showTaskForm && (
        <TaskForm
          task={editingEvent}
          onClose={() => {
            setShowTaskForm(false);
            setEditingEvent(null);
          }}
          userId={userId}
        />
      )}
      
      <div className="flex-1 min-h-0">
        {renderView()}
      </div>
    </div>
  );
};

export default Calendar;
