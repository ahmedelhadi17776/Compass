import React from 'react';
import { cn } from '../../lib/utils';

interface NotesProps {
  darkMode: boolean;
}

const Notes: React.FC<NotesProps> = ({ darkMode }) => {
  return (
    <div className={cn(
      "p-6",
      darkMode ? "text-white" : "text-gray-900"
    )}>
      <h2 className="text-2xl font-bold mb-4">Notes</h2>
      <p>Notes feature coming soon...</p>
    </div>
  );
};

export default Notes;
