import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import Calendar from '../calendar/Calendar';
import TodoList from '../todo/TodoList';
import Notes from './Notes';
import Inbox from './Inbox';
import { cn } from '../../lib/utils';

interface TaskManagementProps {
  darkMode: boolean;
}

const TaskManagement: React.FC<TaskManagementProps> = ({ darkMode }) => {
  return (
    <div className={cn(
      "min-h-screen p-6",
      darkMode ? "bg-[#1A1B1E] text-white" : "bg-gray-50 text-gray-900"
    )}>
      <Routes>
        <Route path="/" element={<Navigate to="calendar" replace />} />
        <Route path="/calendar" element={<Calendar darkMode={darkMode} />} />
        <Route path="/todo" element={<TodoList darkMode={darkMode} />} />
        <Route path="/notes" element={<Notes darkMode={darkMode} />} />
        <Route path="/inbox" element={<Inbox darkMode={darkMode} />} />
      </Routes>
    </div>
  );
};

export default TaskManagement;
