import React, { useState } from 'react';
import { cn } from '@/lib/utils';
import { format } from 'date-fns';
import { ChevronLeft, ChevronRight, Plus } from 'lucide-react';
import DayView from './DayView';
import WeekView from './WeekView';
import ThreeDayView from './ThreeDayView';
import MonthView from './MonthView';
import EventForm from './EventForm';
import ViewSelector from './ViewSelector';
import { CalendarEvent } from '../types';
import { Button } from "@/components/ui/button";

type ViewType = 'day' | 'threeDays' | 'week' | 'month';

interface CalendarProps {
  darkMode?: boolean;
  userId?: number;
}

const Calendar: React.FC<CalendarProps> = ({ darkMode = false, userId = 1 }) => {
  const [currentDate, setCurrentDate] = useState(new Date());
  const [currentView, setCurrentView] = useState<ViewType>('week');
  const [showEventForm, setShowEventForm] = useState(false);
  const [editingEvent, setEditingEvent] = useState<CalendarEvent | null>(null);

  const handleEventClick = (event: CalendarEvent) => {
    setEditingEvent(event);
    setShowEventForm(true);
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

      {/* Header container */}
      <div className="flex justify-between items-center mt-4">
        {/* Header for name and date */}
        <div className="flex items-center gap-1">
          <h2 className="text-xl font-semibold ml-4">
            {format(currentDate, 'MMMM yyyy')} / W{format(currentDate, 'w')}
          </h2>
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
        </div>

        {/* Header for view selector and New Event button */}
        <div className="flex items-center gap-2 mr-4">
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
            onClick={() => setShowEventForm(true)}
          >
            <Plus className="h-4 w-4" />
            New Event
          </Button>
        </div>
      </div>
      
      {showEventForm && (
        <EventForm
          task={editingEvent}
          onClose={() => {
            setShowEventForm(false);
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
