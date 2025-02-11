import React, { useState, useEffect } from 'react';
import DatePicker from 'react-datepicker';
import { X } from 'lucide-react';
import "react-datepicker/dist/react-datepicker.css";
import './EventForm.css';

interface Event {
  id: string;
  title: string;
  start: Date;
  end: Date;
  description?: string;
  location?: string;
  priority: 'high' | 'medium' | 'low';
  category: string;
  attachment?: {
    name: string;
    url: string;
    type: string;
  };
  participants?: {
    name: string;
    status: 'accepted' | 'pending' | 'rejected';
  }[];
}

interface EventFormProps {
  event?: Event | null;
  onClose: () => void;
  onSubmit: (eventData: EventFormData) => void;
  onDelete?: (eventId: string) => void;
}

interface EventFormData {
  title: string;
  description: string;
  category: string;
  priority: string;
  location: string;
  start: Date;
  end: Date;
  duration: number;
  durationUnit: 'minutes' | 'hours' | 'days';
  attachment?: {
    name: string;
    url: string;
    type: string;
  };
}

const EventForm: React.FC<EventFormProps> = ({ event, onClose, onSubmit, onDelete }) => {
  const [formData, setFormData] = useState({
    title: event?.title || '',
    description: event?.description || '',
    category: 'work',
    priority: 'medium',
    location: event?.location || '',
    start: event?.start || new Date(),
    end: event?.end || new Date(),
    duration: event ? Math.round((event.end.getTime() - event.start.getTime()) / 60000) : 30,
    durationUnit: 'minutes',
    attachment: event?.attachment || undefined,
  });

  const [isClosing, setIsClosing] = useState(false);

  useEffect(() => {
    if (event) {
      setFormData({
        title: event.title,
        description: event.description || '',
        category: event.category,
        priority: event.priority,
        location: event.location || '',
        start: event.start,
        end: event.end,
        duration: Math.round((event.end.getTime() - event.start.getTime()) / 60000),
        durationUnit: 'minutes',
        attachment: event.attachment || undefined,
      });
    }
  }, [event]);

  const categories = [
    { value: 'work', label: 'Work' },
    { value: 'personal', label: 'Personal' },
    { value: 'study', label: 'Study' },
    { value: 'health', label: 'Health' },
    { value: 'other', label: 'Other' }
  ];

  const priorities = [
    { value: 'high', label: 'High' },
    { value: 'medium', label: 'Medium' },
    { value: 'low', label: 'Low' }
  ];

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setIsClosing(true);
    setTimeout(() => {
      const durationInMinutes = convertDuration(formData.duration, formData.durationUnit, 'minutes');
      onSubmit({
        ...formData,
        duration: durationInMinutes,
        end: new Date(formData.start.getTime() + durationInMinutes * 60000)
      });
    }, 300);
  };

  const handleClose = () => {
    setIsClosing(true);
    setTimeout(() => {
      onClose();
    }, 300); // Increased to 300ms to match slide animation
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    try {
      // Create FormData object
      const formData = new FormData();
      formData.append('file', file);

      // Upload file to server
      const response = await fetch('http://localhost:5000/api/upload', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error('Failed to upload file');
      }

      const data = await response.json();
      
      // Update form data with attachment info
      setFormData(prev => ({
        ...prev,
        attachment: {
          name: file.name,
          url: data.url,
          type: file.type,
        },
      }));
    } catch (error) {
      console.error('Error uploading file:', error);
      alert('Failed to upload file');
    }
  };

  const handleRemoveAttachment = () => {
    setFormData(prev => ({
      ...prev,
      attachment: undefined,
    }));
  };

  const convertDuration = (value: number, fromUnit: string, toUnit: string): number => {
    const inMinutes = {
      minutes: (v: number) => v,
      hours: (v: number) => v * 60,
      days: (v: number) => v * 24 * 60
    };

    const fromMinutes = {
      minutes: (v: number) => v,
      hours: (v: number) => v / 60,
      days: (v: number) => v / (24 * 60)
    };

    const minutes = inMinutes[fromUnit as keyof typeof inMinutes](value);
    return Math.round(fromMinutes[toUnit as keyof typeof fromMinutes](minutes));
  };

  return (
    <div className={`fixed inset-0 bg-black/50 flex items-center justify-center z-50 
      ${isClosing ? 'animate-fade-out' : 'animate-fade-in'}`}
    >
      <div className={`bg-white rounded-lg shadow-xl w-full max-w-md p-6 relative 
        ${isClosing ? 'animate-slide-out' : 'animate-slide-in'}`}
      >
        <button
          onClick={handleClose}
          className="absolute right-4 top-4 text-gray-400 hover:text-gray-600"
        >
          <X className="w-5 h-5" />
        </button>

        <h2 className="text-xl font-semibold text-gray-900 mb-6">
          {event ? 'Update Event' : 'Create New Event'}
        </h2>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">Title</label>
            <input
              type="text"
              value={formData.title}
              onChange={(e) => setFormData({ ...formData, title: e.target.value })}
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-[#1f1f21] focus:ring-[#1f1f21]"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">Description</label>
            <textarea
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-[#1f1f21] focus:ring-[#1f1f21]"
              rows={3}
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">Category</label>
              <select
                value={formData.category}
                onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-[#1f1f21] focus:ring-[#1f1f21]"
              >
                {categories.map(category => (
                  <option key={category.value} value={category.value}>
                    {category.label}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">Priority</label>
              <select
                value={formData.priority}
                onChange={(e) => setFormData({ ...formData, priority: e.target.value })}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-[#1f1f21] focus:ring-[#1f1f21]"
              >
                {priorities.map(priority => (
                  <option key={priority.value} value={priority.value}>
                    {priority.label}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">Location</label>
            <input
              type="text"
              value={formData.location}
              onChange={(e) => setFormData({ ...formData, location: e.target.value })}
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-[#1f1f21] focus:ring-[#1f1f21]"
            />
          </div>

          <div className="grid grid-cols-10 gap-4">
            <div className="col-span-10 flex gap-8">
              <div>
                <label className="block text-sm font-medium text-gray-700">Start Time</label>
                <DatePicker
                  selected={formData.start}
                  onChange={(date) => setFormData({ ...formData, start: date || new Date() })}
                  showTimeSelect
                  dateFormat="MMMM d, yyyy h:mm aa"
                  className="mt-1 block w-[230px] rounded-md border-gray-300 shadow-sm focus:border-[#1f1f21] focus:ring-[#1f1f21]"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 -ml-[12px]">Duration</label>
                <div className="flex items-start space-x-2">
                  <input
                    type="number"
                    value={formData.duration}
                    onChange={(e) => {
                      const newValue = parseInt(e.target.value);
                      setFormData({ ...formData, duration: newValue });
                    }}
                    min="1"
                    className="mt-1 block w-[75px] h-[42px] -ml-[11px] rounded-md border-gray-300 shadow-sm focus:border-[#1f1f21] focus:ring-[#1f1f21]"
                  />
                  <select
                    value={formData.durationUnit}
                    onChange={(e) => {
                      const newUnit = e.target.value as 'minutes' | 'hours' | 'days';
                      const newDuration = convertDuration(formData.duration, formData.durationUnit, newUnit);
                      setFormData({ ...formData, durationUnit: newUnit, duration: newDuration });
                    }}
                    className="mt-1 block w-17 h-[42px] rounded-md border-gray-300 shadow-sm focus:border-[#1f1f21] focus:ring-[#1f1f21] text-sm"
                  >
                    <option value="minutes">M</option>
                    <option value="hours">H</option>
                    <option value="days">D</option>
                  </select>
                </div>
              </div>
            </div>
          </div>

          <div className="space-y-2">
            <label className="block text-sm font-medium text-gray-700">Attachment</label>
            {formData.attachment ? (
              <div className="flex items-center justify-between p-2 border rounded-md">
                <div className="flex items-center space-x-2">
                  <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13" />
                  </svg>
                  <span className="text-sm text-gray-600">{formData.attachment.name}</span>
                </div>
                <button
                  type="button"
                  onClick={handleRemoveAttachment}
                  className="text-red-500 hover:text-red-700"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            ) : (
              <div className="flex items-center justify-center w-full">
                <label className="w-full flex flex-col items-center px-4 py-6 bg-white text-gray-400 rounded-lg border-2 border-dashed border-gray-300 cursor-pointer hover:bg-gray-50">
                  <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                  </svg>
                  <span className="mt-2 text-sm">Drop a file or click to upload</span>
                  <input
                    type="file"
                    className="hidden"
                    onChange={handleFileUpload}
                    accept=".pdf,.doc,.docx,.txt,.jpg,.jpeg,.png"
                  />
                </label>
              </div>
            )}
          </div>

          <div className="flex justify-between gap-3 mt-6">
            {event && onDelete && (
              <button
                type="button"
                onClick={() => {
                  setIsClosing(true);
                  setTimeout(() => {
                    onDelete(event.id);
                  }, 300);
                }}
                className="px-4 py-2 text-sm font-medium text-white bg-red-600 border border-transparent rounded-md shadow-sm hover:bg-red-700"
              >
                Delete Event
              </button>
            )}
            <div className="flex gap-3 ml-auto">
              <button
                type="button"
                onClick={handleClose}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md shadow-sm hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-4 py-2 text-sm font-medium text-white bg-[#1f1f21] border border-transparent rounded-md shadow-sm hover:bg-[#2f2f31]"
              >
                {event ? 'Update Event' : 'Create Event'}
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
};

export default EventForm;