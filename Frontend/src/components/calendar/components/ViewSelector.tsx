import React from 'react';
import { cn } from '@/lib/utils';

type ViewType = 'day' | 'threeDays' | 'week' | 'month';

interface ViewSelectorProps {
  currentView: ViewType;
  onViewChange: (view: ViewType) => void;
}

const ViewSelector: React.FC<ViewSelectorProps> = ({ currentView, onViewChange }) => {
  const views: { value: ViewType; label: string }[] = [
    { value: 'day', label: 'Day' },
    { value: 'threeDays', label: '3 Days' },
    { value: 'week', label: 'Week' },
    { value: 'month', label: 'Month' },
  ];

  return (
    <div className="flex rounded-md shadow-sm">
      {views.map(({ value, label }) => (
        <button
          key={value}
          onClick={() => onViewChange(value)}
          className={cn(
            "px-3 py-1.5 text-sm font-medium first:rounded-l-md last:rounded-r-md",
            currentView === value
              ? "bg-primary text-primary-foreground"
              : "bg-secondary text-secondary-foreground hover:bg-secondary/80"
          )}
        >
          {label}
        </button>
      ))}
    </div>
  );
};

export default ViewSelector;
