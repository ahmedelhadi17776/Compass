import React from 'react';
import { cn } from '../../lib/utils';

interface InboxProps {
  darkMode: boolean;
}

const Inbox: React.FC<InboxProps> = ({ darkMode }) => {
  return (
    <div className={cn(
      "p-6",
      darkMode ? "text-white" : "text-gray-900"
    )}>
      <h2 className="text-2xl font-bold mb-4">Inbox</h2>
      <p>Inbox feature coming soon...</p>
    </div>
  );
};

export default Inbox;
