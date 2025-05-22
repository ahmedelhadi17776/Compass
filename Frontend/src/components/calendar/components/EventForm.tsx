import React, { useState, useEffect } from 'react';
import DatePicker from 'react-datepicker';
import { X } from 'lucide-react';
import { useCreateEvent, useUpdateEvent, useDeleteEvent, useUpdateOccurrenceById } from '@/components/calendar/hooks';
import { 
  CalendarEvent, 
  EventType,
  CreateCalendarEventRequest, 
  UpdateCalendarEventRequest,
  RecurrenceType,
  CreateRecurrenceRuleRequest
} from '../types';
import { Button } from '@/components/ui/button';
import "react-datepicker/dist/react-datepicker.css";
import './EventForm.css';

interface EventFormProps {
  task?: CalendarEvent | null;
  onClose: () => void;
  userId?: string;
}

const EventForm: React.FC<EventFormProps> = ({ task, onClose, userId }) => {
  const createEvent = useCreateEvent();
  const updateEvent = useUpdateEvent();
  const updateOccurrenceById = useUpdateOccurrenceById();
  const deleteEvent = useDeleteEvent();
  const [isClosing, setIsClosing] = useState(false);
  const [updateOption, setUpdateOption] = useState<'single' | 'all'>('single');

  const eventTypes: { value: EventType; label: string }[] = [
    { value: 'None', label: 'None' },
    { value: 'Task', label: 'Task' },
    { value: 'Meeting', label: 'Meeting' },
    { value: 'Todo', label: 'Todo' },
    { value: 'Holiday', label: 'Holiday' },
    { value: 'Reminder', label: 'Reminder' }
  ];

  const priorityTypes = [
    { value: 'High', label: 'High' },
    { value: 'Medium', label: 'Medium' },
    { value: 'Low', label: 'Low' }
  ];

  const statusTypes = [
    { value: 'Upcoming', label: 'Upcoming' },
    { value: 'In Progress', label: 'In Progress' },
    { value: 'Completed', label: 'Completed' },
    { value: 'Cancelled', label: 'Cancelled' },
    { value: 'Blocked', label: 'Blocked' },
    { value: 'Under Review', label: 'Under Review' },
    { value: 'Deferred', label: 'Deferred' }
  ];

  const recurrenceTypes: { value: RecurrenceType; label: string }[] = [
    { value: 'None', label: 'None' },
    { value: 'Daily', label: 'Daily' },
    { value: 'Weekly', label: 'Weekly' },
    { value: 'Biweekly', label: 'Biweekly' },
    { value: 'Monthly', label: 'Monthly' },
    { value: 'Yearly', label: 'Yearly' },
    { value: 'Custom', label: 'Custom' }
  ];

  const [formData, setFormData] = useState<CreateCalendarEventRequest>({
    title: task?.title || '',
    description: task?.description || '',
    event_type: task?.event_type || 'None',
    start_time: task?.start_time ? new Date(task.start_time) : new Date(),
    end_time: task?.end_time ? new Date(task.end_time) : new Date(Date.now() + 60 * 60000),
    is_all_day: task?.is_all_day || false,
    location: task?.location,
    color: task?.color,
    transparency: task?.transparency || 'opaque',
  });

  const [recurrenceData, setRecurrenceData] = useState({
    enabled: false,
    freq: 'None' as RecurrenceType,
    interval: 1,
    byDay: [] as string[],
    byMonth: [] as number[],
    byMonthDay: [] as number[],
    until: null as Date | null,
    count: null as number | null,
  });

  useEffect(() => {
    if (task) {
      setFormData({
        title: task.title,
        description: task.description,
        event_type: task.event_type,
        start_time: new Date(task.start_time),
        end_time: new Date(task.end_time),
        is_all_day: task.is_all_day,
        location: task.location,
        color: task.color,
        transparency: task.transparency,
      });

      if (task.recurrence_rules?.[0]) {
        const rule = task.recurrence_rules[0];
        setRecurrenceData({
          enabled: true,
          freq: rule.freq,
          interval: rule.interval,
          byDay: rule.by_day || [],
          byMonth: rule.by_month?.map(Number) || [],
          byMonthDay: rule.by_month_day?.map(Number) || [],
          until: rule.until ? new Date(rule.until) : null,
          count: rule.count || null,
        });
      }
    }
  }, [task]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsClosing(true);

    try {
      const eventData: CreateCalendarEventRequest = {
        ...formData,
        recurrence_rule: recurrenceData.enabled ? {
          freq: recurrenceData.freq,
          interval: recurrenceData.interval,
          by_day: recurrenceData.byDay.length > 0 ? recurrenceData.byDay : undefined,
          by_month: recurrenceData.byMonth.length > 0 ? recurrenceData.byMonth : undefined,
          by_month_day: recurrenceData.byMonthDay.length > 0 ? recurrenceData.byMonthDay : undefined,
          until: recurrenceData.until || undefined,
          count: recurrenceData.count || undefined,
        } : undefined
      };

      if (task?.id) {
        const updateData: UpdateCalendarEventRequest = {
          title: eventData.title,
          description: eventData.description,
          event_type: eventData.event_type,
          start_time: eventData.start_time,
          end_time: eventData.end_time,
          is_all_day: eventData.is_all_day,
          location: eventData.location,
          color: eventData.color,
          transparency: eventData.transparency,
        };

        if (task.is_occurrence && task.original_event_id && task.occurrence_id) {
          if (updateOption === 'single') {
            await updateOccurrenceById.mutateAsync({
              occurrenceId: task.occurrence_id,
              updates: updateData
            });
          } else {
            await updateEvent.mutateAsync({
              eventId: task.original_event_id,
              event: updateData
            });
          }
        } else {
          await updateEvent.mutateAsync({
            eventId: task.id,
            event: updateData
          });
        }
      } else {
        await createEvent.mutateAsync(eventData);
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
          {task?.is_occurrence && (
            <div className="mb-4 p-4 bg-gray-800 rounded-md">
              <h3 className="text-sm font-medium text-gray-300 mb-2">Update Options</h3>
              <div className="space-y-2">
                <label className="flex items-center">
                  <input
                    type="radio"
                    name="updateOption"
                    checked={updateOption === 'single'}
                    onChange={() => setUpdateOption('single')}
                    className="h-4 w-4 border-gray-300 text-indigo-600 focus:ring-indigo-500"
                  />
                  <span className="ml-2 text-sm text-gray-300">Update only this occurrence</span>
                </label>
                <label className="flex items-center">
                  <input
                    type="radio"
                    name="updateOption"
                    checked={updateOption === 'all'}
                    onChange={() => setUpdateOption('all')}
                    className="h-4 w-4 border-gray-300 text-indigo-600 focus:ring-indigo-500"
                  />
                  <span className="ml-2 text-sm text-gray-300">Update all occurrences</span>
                </label>
              </div>
            </div>
          )}

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

          <div>
            <label className="block text-sm font-medium text-gray-300">Event Type</label>
            <select
              value={formData.event_type}
              onChange={(e) => setFormData({ ...formData, event_type: e.target.value as EventType })}
              className="mt-1 block w-full rounded-md bg-gray-800 border-gray-700 text-gray-100 shadow-sm focus:border-gray-500 focus:ring-gray-500"
            >
              {eventTypes.map(type => (
                <option key={type.value} value={type.value} className="bg-gray-800">
                  {type.label}
                </option>
              ))}
            </select>
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

            <div>
              <label className="block text-sm font-medium text-gray-300">Color</label>
              <input
                type="text"
                value={formData.color}
                onChange={(e) => setFormData({ ...formData, color: e.target.value })}
                className="mt-1 block w-full rounded-md bg-gray-800 border-gray-700 text-gray-100 shadow-sm focus:border-gray-500 focus:ring-gray-500"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-300">Priority</label>
              <select
                value={formData.priority}
                onChange={(e) => setFormData({ ...formData, priority: e.target.value as 'High' | 'Medium' | 'Low' })}
                className="mt-1 block w-full rounded-md bg-gray-800 border-gray-700 text-gray-100 shadow-sm focus:border-gray-500 focus:ring-gray-500"
              >
                {priorityTypes.map(type => (
                  <option key={type.value} value={type.value} className="bg-gray-800">
                    {type.label}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300">Status</label>
              <select
                value={formData.status}
                onChange={(e) => setFormData({ ...formData, status: e.target.value as typeof formData.status })}
                className="mt-1 block w-full rounded-md bg-gray-800 border-gray-700 text-gray-100 shadow-sm focus:border-gray-500 focus:ring-gray-500"
              >
                {statusTypes.map(type => (
                  <option key={type.value} value={type.value} className="bg-gray-800">
                    {type.label}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-300">Start Time</label>
              <DatePicker
                selected={formData.start_time}
                onChange={(date: Date) => setFormData({ ...formData, start_time: date })}
                showTimeSelect
                dateFormat="MMMM d, yyyy h:mm aa"
                className="mt-1 block w-full rounded-md bg-gray-800 border-gray-700 text-gray-100 shadow-sm focus:border-gray-500 focus:ring-gray-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300">End Time</label>
              <DatePicker
                selected={formData.end_time}
                onChange={(date: Date) => setFormData({ ...formData, end_time: date })}
                showTimeSelect
                dateFormat="MMMM d, yyyy h:mm aa"
                className="mt-1 block w-full rounded-md bg-gray-800 border-gray-700 text-gray-100 shadow-sm focus:border-gray-500 focus:ring-gray-500"
                minDate={formData.start_time}
              />
            </div>
          </div>

          <div className="space-y-4">
            <div className="flex items-center">
              <input
                type="checkbox"
                checked={recurrenceData.enabled}
                onChange={(e) => setRecurrenceData(prev => ({ 
                  ...prev, 
                  enabled: e.target.checked,
                  freq: e.target.checked ? 'Daily' : 'None'
                }))}
                className="h-4 w-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
              />
              <label className="ml-2 block text-sm text-gray-300">Recurring Event</label>
            </div>

            {recurrenceData.enabled && (
              <>
                <div>
                  <label className="block text-sm font-medium text-gray-300">Recurrence Pattern</label>
                  <select
                    value={recurrenceData.freq}
                    onChange={(e) => setRecurrenceData(prev => ({
                      ...prev,
                      freq: e.target.value as RecurrenceType
                    }))}
                    className="mt-1 block w-full rounded-md bg-gray-800 border-gray-700 text-gray-100 shadow-sm focus:border-gray-500 focus:ring-gray-500"
                  >
                    {recurrenceTypes.map(type => (
                      <option key={type.value} value={type.value} className="bg-gray-800">
                        {type.label}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-300">Interval</label>
                  <input
                    type="number"
                    min="1"
                    value={recurrenceData.interval}
                    onChange={(e) => setRecurrenceData(prev => ({
                      ...prev,
                      interval: parseInt(e.target.value) || 1
                    }))}
                    className="mt-1 block w-full rounded-md bg-gray-800 border-gray-700 text-gray-100 shadow-sm focus:border-gray-500 focus:ring-gray-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-300">End Recurrence</label>
                  <div className="space-y-2 mt-2">
                    <div className="flex items-center">
                      <input
                        type="radio"
                        checked={!recurrenceData.until && !recurrenceData.count}
                        onChange={() => setRecurrenceData(prev => ({
                          ...prev,
                          until: null,
                          count: null
                        }))}
                        className="h-4 w-4 border-gray-300 text-indigo-600 focus:ring-indigo-500"
                      />
                      <label className="ml-2 block text-sm text-gray-300">Never</label>
                    </div>

                    <div className="flex items-center">
                      <input
                        type="radio"
                        checked={!!recurrenceData.count}
                        onChange={() => setRecurrenceData(prev => ({
                          ...prev,
                          until: null,
                          count: 1
                        }))}
                        className="h-4 w-4 border-gray-300 text-indigo-600 focus:ring-indigo-500"
                      />
                      <label className="ml-2 block text-sm text-gray-300">After</label>
                      {recurrenceData.count !== null && (
                        <input
                          type="number"
                          min="1"
                          value={recurrenceData.count}
                          onChange={(e) => setRecurrenceData(prev => ({
                            ...prev,
                            count: parseInt(e.target.value) || 1
                          }))}
                          className="ml-2 w-20 rounded-md bg-gray-800 border-gray-700 text-gray-100 shadow-sm focus:border-gray-500 focus:ring-gray-500"
                        />
                      )}
                      <span className="ml-2 text-sm text-gray-300">occurrences</span>
                    </div>

                    <div className="flex items-center">
                      <input
                        type="radio"
                        checked={!!recurrenceData.until}
                        onChange={() => setRecurrenceData(prev => ({
                          ...prev,
                          until: new Date(),
                          count: null
                        }))}
                        className="h-4 w-4 border-gray-300 text-indigo-600 focus:ring-indigo-500"
                      />
                      <label className="ml-2 block text-sm text-gray-300">On date</label>
                      {recurrenceData.until && (
                        <div className="ml-2">
                          <DatePicker
                            selected={recurrenceData.until}
                            onChange={(date: Date) => setRecurrenceData(prev => ({
                              ...prev,
                              until: date
                            }))}
                            minDate={formData.start_time}
                            dateFormat="MMMM d, yyyy"
                            className="w-full rounded-md bg-gray-800 border-gray-700 text-gray-100 shadow-sm focus:border-gray-500 focus:ring-gray-500"
                          />
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </>
            )}
          </div>

          <div className="flex items-center">
            <input
              type="checkbox"
              checked={formData.is_all_day}
              onChange={(e) => setFormData({ ...formData, is_all_day: e.target.checked })}
              className="h-4 w-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
            />
            <label className="ml-2 block text-sm text-gray-300">All Day Event</label>
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