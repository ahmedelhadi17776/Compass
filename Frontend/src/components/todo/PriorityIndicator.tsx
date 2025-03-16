import React from 'react';
import { ArrowUp, ArrowDown, Minus } from 'lucide-react';
import cn from 'classnames';
import { TodoPriority } from '@/types/todo';

interface PriorityIndicatorProps {
  priority: string;
}

const PriorityIndicator: React.FC<PriorityIndicatorProps> = ({ priority }) => {
  const getIcon = () => {
    switch (priority.toLowerCase()) {
      case TodoPriority.HIGH:
        return <ArrowUp className="h-4 w-4" />;
      case TodoPriority.MEDIUM:
        return <Minus className="h-4 w-4" />;
      case TodoPriority.LOW:
        return <ArrowDown className="h-4 w-4" />;
      default:
        return <Minus className="h-4 w-4" />; // Default to medium
    }
  };

  const getPriorityClass = () => {
    switch (priority.toLowerCase()) {
      case TodoPriority.HIGH:
        return 'text-red-500';
      case TodoPriority.MEDIUM:
        return 'text-amber-500';
      case TodoPriority.LOW:
        return 'text-green-500';
      default:
        return 'text-amber-500'; // Default to medium
    }
  };

  return (
    <div className={cn('flex items-center justify-center mr-2', getPriorityClass())}>
      {getIcon()}
    </div>
  );
};

export default PriorityIndicator;