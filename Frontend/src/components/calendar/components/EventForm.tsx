import React, { useState, useEffect } from 'react';
import DatePicker from 'react-datepicker';
import { X } from 'lucide-react';
import { useCreateEvent, useUpdateEvent, useDeleteEvent } from '@/components/calendar/hooks';
import { CalendarEvent } from '../types';
import { Button } from '@/components/ui/button';
import "react-datepicker/dist/react-datepicker.css";
import './EventForm.css';

interface EventFormProps {
  task?: CalendarEvent | null;
  onClose: () => void;
  userId?: number;
}

const EventForm: React.FC<EventFormProps> = ({ task, onClose, userId = 1 }) => {
  const createEvent = useCreateEvent(userId);
  const updateEvent = useUpdateEvent(userId);
  const deleteEvent = useDeleteEvent(userId);
  const [isClosing, setIsClosing] = useState(false);

  const statuses = [
    { value: 'Upcoming', label: 'Upcoming' },
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
    { value: 'Low', label: 'Low' }
  ];

  type RecurrenceType = NonNullable<CalendarEvent['recurrence']>;

  const recurrenceTypes: { value: RecurrenceType; label: string }[] = [
    { value: 'None', label: 'None' },
    { value: 'Daily', label: 'Daily' },
    { value: 'Weekly', label: 'Weekly' },
    { value: 'Biweekly', label: 'Bi-Weekly' },
    { value: 'Monthly', label: 'Monthly' },
    { value: 'Yearly', label: 'Yearly' },
    { value: 'Weekdays', label: 'Weekdays (Mon-Fri)' },
    { value: 'Custom', label: 'Custom' }
  ];

  const [formData, setFormData] = useState<Partial<CalendarEvent> & { recurrence: RecurrenceType }>({
    title: task?.title || '',
    description: task?.description || '',
    priority: task?.priority || 'Medium',
    location: task?.location || '',
    start_date: task?.start || new Date(),
    end_date: task?.end || new Date(Date.now() + 60 * 60000),
    status: task?.status || 'Upcoming',
    user_id: userId,
    recurrence: (task?.recurrence || 'None') as RecurrenceType,
    recurrence_end_date: task?.recurrence_end_date || (task?.is_recurring ? new Date(Date.now() + 30 * 24 * 60 * 60 * 1000) : undefined),
  });

  useEffect(() => {
    if (task) {
      setFormData({
        ...task,
        start_date: new Date(task.start),
        end_date: new Date(task.end),
        user_id: userId,
        recurrence: (task.recurrence || 'None') as RecurrenceType,
        recurrence_end_date: task.recurrence_end_date ? new Date(task.recurrence_end_date) : (task.is_recurring ? new Date(Date.now() + 30 * 24 * 60 * 60 * 1000) : undefined),
      });
    }
  }, [task, userId]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsClosing(true);

    try {
      const taskData = {
        ...formData,
        start: formData.start_date,
        end: formData.end_date,
        is_recurring: formData.recurrence !== 'None',
        recurrence: formData.recurrence,
        recurrence_end_date: formData.recurrence !== 'None' && formData.recurrence_end_date ? new Date(formData.recurrence_end_date) : undefined,
      };

      if (task?.id) {
        await updateEvent.mutateAsync({
          eventId: task.id,
          event: taskData
        });
      } else {
        await createEvent.mutateAsync(taskData);
      }
      setTimeout(onClose, 300);
    } catch (error) {
      console.error('Failed to save event:', error);
      setIsClosing(false);
    }
  };

  const handleDelete = async () => {
    if (!task?.id) return;
    setIsClosing(true);
    try {
      await deleteEvent.mutateAsync(task.id);
      setTimeout(onClose, 300);
    } catch (error) {
      console.error('Failed to delete event:', error);
      setIsClosing(false);
    }
  };

  const handleClose = () => {
    setIsClosing(true);
    setTimeout(onClose, 300);
  };

  // Show recurrence end date only if recurrence is not None
  const showRecurrenceEndDate = formData.recurrence !== 'None';

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
          {task ? 'Update Event' : 'Create New Event'}
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

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-300">Recurrence</label>
              <select
                value={formData.recurrence}
                onChange={(e) => setFormData({ ...formData, recurrence: e.target.value as RecurrenceType })}
                className="mt-1 block w-full rounded-md bg-gray-800 border-gray-700 text-gray-100 shadow-sm focus:border-gray-500 focus:ring-gray-500"
              >
                {recurrenceTypes.map(type => (
                  <option key={type.value} value={type.value} className="bg-gray-800">
                    {type.label}
                  </option>
                ))}
              </select>
            </div>

            {showRecurrenceEndDate && (
              <div>
                <label className="block text-sm font-medium text-gray-300">Recurrence End Date</label>
                <DatePicker
                  selected={formData.recurrence_end_date}
                  onChange={(date: Date) => setFormData({ ...formData, recurrence_end_date: date })}
                  dateFormat="MMMM d, yyyy"
                  className="mt-1 block w-full rounded-md bg-gray-800 border-gray-700 text-gray-100 shadow-sm focus:border-gray-500 focus:ring-gray-500"
                  minDate={formData.start_date}
                />
              </div>
            )}
          </div>

          <div className="flex justify-between gap-3 mt-6">
            {task && (
              <Button
                type="button"
                onClick={handleDelete}
                variant="destructive"
                disabled={deleteEvent.isPending}
                className="px-4 py-2"
              >
                {deleteEvent.isPending ? 'Deleting...' : 'Delete Event'}
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
                disabled={createEvent.isPending || updateEvent.isPending}
                className="px-4 py-2"
              >
                {createEvent.isPending || updateEvent.isPending 
                  ? 'Saving...' 
                  : task ? 'Update Event' : 'Create Event'}
              </Button>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
};

export default EventForm;