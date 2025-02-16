import React, { useState } from 'react';
import { X, Calendar, Bell } from 'lucide-react';
import './NewTodoModal.css';

interface NewTodoModalProps {
  onClose: () => void;
  onSubmit: (todo: { title: string; description?: string; dueDate?: Date }) => void;
}

const NewTodoModal: React.FC<NewTodoModalProps> = ({ onClose, onSubmit }) => {
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');

  const handleSubmit = () => {
    if (!title.trim()) return;
    onSubmit({ title, description });
    onClose();
  };

  return (
    <div className="modal-overlay">
      <div className="modal-content">
        <input
          type="text"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="Task name"
          className="task-title-input"
          autoFocus
        />
        <textarea
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="Description"
          className="task-description"
        />
        
        <div className="modal-actions">
          <div className="action-buttons">
            <button className="action-button">
              <Calendar className="w-4 h-4" />
              Due date
            </button>
            <button className="action-button">
              <Bell className="w-4 h-4" />
              Reminders
            </button>
          </div>

          <div className="modal-footer">
            <button onClick={onClose} className="cancel-button">
              Cancel
            </button>
            <button 
              onClick={handleSubmit}
              className="add-task-button"
              disabled={!title.trim()}
            >
              Add task
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default NewTodoModal; 