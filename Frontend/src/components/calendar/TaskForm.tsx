import React, { useState, useEffect } from 'react';
import DatePicker from 'react-datepicker';
import { X } from 'lucide-react';
import { useCreateTask, useUpdateTask, useDeleteTask } from '@/hooks/useTasks';
import { CalendarEvent } from './types';
import { Button } from '@/components/ui/button';
import "react-datepicker/dist/react-datepicker.css";
import './TaskForm.css';

interface TaskFormProps {
  task?: CalendarEvent | null;
  onClose: () => void;
  userId?: number;
}

const TaskForm: React.FC<TaskFormProps> = ({ task, onClose, userId = 1 }) => {
  const createTask = useCreateTask(userId);
  const updateTask = useUpdateTask(userId);
  const deleteTask = useDeleteTask(userId);
  const [isClosing, setIsClosing] = useState(false);

  const statuses = [
    { value: 'To Do', label: 'To Do' },
    { value: 'In Progress', label: 'In Progress' },
    { value: 'Completed', label: 'Completed' },
    { value: 'Cancelled', label: 'Cancelled' },
    { value: 'Blocked', label: 'Blocked' },
    { value: 'Under Review', label: 'Under Review' },
    { value: 'Deferred', label: 'Deferred' }
  ];

  const priorities = [
    { value: 'High', label: 'High' },
    { value: 'Medium', label: 'Medium' },
    { value: 'Low', label: 'Low' },
    { value: 'Urgent', label: 'Urgent' }
  ];

  const categories = [
    { value: 'work', label: 'Work' },
    { value: 'personal', label: 'Personal' },
    { value: 'study', label: 'Study' },
    { value: 'health', label: 'Health' },
    { value: 'other', label: 'Other' }
  ];

  const [formData, setFormData] = useState<Partial<CalendarEvent>>({
    title: task?.title || '',
    description: task?.description || '',
    category: task?.category || 'work',
    priority: task?.priority || 'Medium',
    location: task?.location || '',
    start_date: task?.start || new Date(),
    end_date: task?.end || new Date(Date.now() + 30 * 60000),
    status: task?.status || 'To Do',
    project_id: task?.project_id || 1,
    organization_id: task?.organization_id || 1,
    creator_id: userId,
    user_id: userId,
  });

  useEffect(() => {
    if (task) {
      setFormData({
        ...task,
        start_date: task.start,
        end_date: task.end,
        user_id: userId,
      });
    }
  }, [task, userId]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsClosing(true);

    try {
      if (task?.id) {
        await updateTask.mutateAsync({
          taskId: task.id,
          task: {
            ...formData,
            start: formData.start_date,
            end: formData.end_date,
          }
        });
      } else {
        await createTask.mutateAsync({
          ...formData,
          start: formData.start_date,
          end: formData.end_date,
        });
      }
      setTimeout(onClose, 300);
    } catch (error) {
      console.error('Failed to save task:', error);
      setIsClosing(false);
    }
  };

  const handleDelete = async () => {
    if (!task?.id) return;
    setIsClosing(true);
    try {
      await deleteTask.mutateAsync(task.id);
      setTimeout(onClose, 300);
    } catch (error) {
      console.error('Failed to delete task:', error);
      setIsClosing(false);
    }
  };

  const handleClose = () => {
    setIsClosing(true);
    setTimeout(onClose, 300);
  };

  return (
    <div className={`fixed inset-0 bg-black/50 flex items-center justify-center z-50 
      ${isClosing ? 'animate-fade-out' : 'animate-fade-in'}`}
    >
      <div className={`bg-gray-900 rounded-lg shadow-xl w-full max-w-md p-6 relative 
        ${isClosing ? 'animate-slide-out' : 'animate-slide-in'}`}
      >
        <button
          onClick={handleClose}
          className="absolute right-4 top-4 text-gray-400 hover:text-gray-200"
        >
          <X className="w-5 h-5" />
        </button>

        <h2 className="text-xl font-semibold text-gray-100 mb-6">
          {task ? 'Update Task' : 'Create New Task'}
        </h2>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-300">Title</label>
            <input
              type="text"
              value={formData.title}
              onChange={(e) => setFormData({ ...formData, title: e.target.value })}
              className="mt-1 block w-full rounded-md bg-gray-800 border-gray-700 text-gray-100 shadow-sm focus:border-gray-500 focus:ring-gray-500"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300">Description</label>
            <textarea
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              className="mt-1 block w-full rounded-md bg-gray-800 border-gray-700 text-gray-100 shadow-sm focus:border-gray-500 focus:ring-gray-500"
              rows={3}
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-300">Status</label>
              <select
                value={formData.status}
                onChange={(e) => setFormData({ ...formData, status: e.target.value as CalendarEvent['status'] })}
                className="mt-1 block w-full rounded-md bg-gray-800 border-gray-700 text-gray-100 shadow-sm focus:border-gray-500 focus:ring-gray-500"
              >
                {statuses.map(status => (
                  <option key={status.value} value={status.value} className="bg-gray-800">
                    {status.label}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300">Priority</label>
              <select
                value={formData.priority}
                onChange={(e) => setFormData({ ...formData, priority: e.target.value as CalendarEvent['priority'] })}
                className="mt-1 block w-full rounded-md bg-gray-800 border-gray-700 text-gray-100 shadow-sm focus:border-gray-500 focus:ring-gray-500"
              >
                {priorities.map(priority => (
                  <option key={priority.value} value={priority.value} className="bg-gray-800">
                    {priority.label}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-300">Category</label>
              <select
                value={formData.category}
                onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                className="mt-1 block w-full rounded-md bg-gray-800 border-gray-700 text-gray-100 shadow-sm focus:border-gray-500 focus:ring-gray-500"
              >
                {categories.map(category => (
                  <option key={category.value} value={category.value} className="bg-gray-800">
                    {category.label}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300">Location</label>
              <input
                type="text"
                value={formData.location}
                onChange={(e) => setFormData({ ...formData, location: e.target.value })}
                className="mt-1 block w-full rounded-md bg-gray-800 border-gray-700 text-gray-100 shadow-sm focus:border-gray-500 focus:ring-gray-500"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-300">Start Time</label>
              <DatePicker
                selected={formData.start_date}
                onChange={(date: Date) => setFormData({ ...formData, start_date: date })}
                showTimeSelect
                dateFormat="MMMM d, yyyy h:mm aa"
                className="mt-1 block w-full rounded-md bg-gray-800 border-gray-700 text-gray-100 shadow-sm focus:border-gray-500 focus:ring-gray-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300">End Time</label>
              <DatePicker
                selected={formData.end_date}
                onChange={(date: Date) => setFormData({ ...formData, end_date: date })}
                showTimeSelect
                dateFormat="MMMM d, yyyy h:mm aa"
                className="mt-1 block w-full rounded-md bg-gray-800 border-gray-700 text-gray-100 shadow-sm focus:border-gray-500 focus:ring-gray-500"
                minDate={formData.start_date}
              />
            </div>
          </div>

          <div className="flex justify-between gap-3 mt-6">
            {task && (
              <Button
                type="button"
                onClick={handleDelete}
                variant="destructive"
                disabled={deleteTask.isPending}
                className="px-4 py-2"
              >
                {deleteTask.isPending ? 'Deleting...' : 'Delete Task'}
              </Button>
            )}
            <div className="flex gap-3 ml-auto">
              <Button
                type="button"
                onClick={handleClose}
                variant="outline"
                className="px-4 py-2"
              >
                Cancel
              </Button>
              <Button
                type="submit"
                disabled={createTask.isPending || updateTask.isPending}
                className="px-4 py-2"
              >
                {createTask.isPending || updateTask.isPending 
                  ? 'Saving...' 
                  : task ? 'Update Task' : 'Create Task'}
              </Button>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
};

export default TaskForm;