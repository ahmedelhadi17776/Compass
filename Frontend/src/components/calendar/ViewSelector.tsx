import React from 'react';
import { cn } from '@/lib/utils';

interface ViewSelectorProps {
  currentView: string;
  onViewChange: (view: string) => void;
}

const ViewSelector: React.FC<ViewSelectorProps> = ({ currentView, onViewChange }) => {
  const views = [
    { id: 'day', label: 'Day' },
    { id: 'threeDays', label: '3 Days' },
    { id: 'week', label: 'Week' },
    { id: 'month', label: 'Month' },
  ];

  return (
    <div className="flex rounded-md bg-muted">
      {views.map(({ id, label }) => (
        <button
          key={id}
          onClick={() => onViewChange(id)}
          className={cn(
            "px-3 py-1.5 text-sm font-medium first:rounded-l-md last:rounded-r-md transition-colors",
            "text-muted-foreground hover:text-foreground",
            currentView === id && "bg-background text-primary shadow-sm"
          )}
        >
          {label}
        </button>
      ))}
    </div>
  );
};

export default ViewSelector;
