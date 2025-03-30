import axios from 'axios';
import { CalendarEvent } from './types';

const API_BASE_URL = 'http://localhost:8000';

// Add error handling and response transformation
const axiosInstance = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add response transformation
axiosInstance.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

export const eventsApi = {
  getEvents: async ({
    skip = 0,
    limit = 100,
    status,
    priority,
    project_id,
    assignee_id,
    creator_id,
    due_date_start,
    due_date_end,
    user_id = 1, // TODO: Get from auth context
    expand_recurring = true, // New parameter for the calendar endpoint
  }: {
    skip?: number;
    limit?: number;
    status?: string;
    priority?: string;
    project_id?: number;
    assignee_id?: number;
    creator_id?: number;
    due_date_start?: Date | string;
    due_date_end?: Date | string;
    user_id?: number;
    expand_recurring?: boolean;
  }) => {
    try {
      const formatDateWithoutTimezone = (date: Date | string | undefined) => {
        if (!date) return undefined;
        const d = date instanceof Date ? date : new Date(date);
        return d.getFullYear() + '-' +
          String(d.getMonth() + 1).padStart(2, '0') + '-' +
          String(d.getDate()).padStart(2, '0') + 'T' +
          String(d.getHours()).padStart(2, '0') + ':' +
          String(d.getMinutes()).padStart(2, '0') + ':' +
          String(d.getSeconds()).padStart(2, '0') + '.' +
          String(d.getMilliseconds()).padStart(3, '0');
      };

      const formattedStartDate = formatDateWithoutTimezone(due_date_start);
      const formattedEndDate = formatDateWithoutTimezone(due_date_end);

      let endpoint = '/events/';
      const params: Record<string, any> = {
        user_id,
      };

      if (due_date_start && due_date_end) {
        endpoint = '/events/calendar';
        params.start_date = formattedStartDate;
        params.end_date = formattedEndDate;
        params.expand_recurring = expand_recurring;
        if (project_id) params.project_id = project_id;
      } else {
        params.skip = skip;
        params.limit = limit;
        if (status) params.status = status;
        if (priority) params.priority = priority;
        if (project_id) params.project_id = project_id;
        if (assignee_id) params.assignee_id = assignee_id;
        if (creator_id) params.creator_id = creator_id;
        if (due_date_start) params.start_date = formattedStartDate;
        if (due_date_end) params.end_date = formattedEndDate;
      }

      const { data } = await axiosInstance.get(endpoint, { params });
      return data;
    } catch (error) {
      console.error('Error fetching tasks:', error);
      return [];
    }
  },

  getEventById: async (eventId: string, user_id: number = 1) => {
    // If it's a recurring event occurrence, extract the original ID
    const originalId = eventId.includes('_') ? eventId.split('_')[0] : eventId;
    const { data } = await axiosInstance.get(`/events/by_id/${originalId}`, {
      params: { user_id }
    });
    
    // Format dates properly
    if (data) {
      // Create date objects without timezone information
      const startDate = data.start_date ? new Date(data.start_date) : null;
      const endDate = data.due_date ? new Date(data.due_date) : null;
      const recurrenceEndDate = data.recurrence_end_date ? new Date(data.recurrence_end_date) : undefined;
      
      return {
        ...data,
        start: startDate,
        end: endDate,
        recurrence_end_date: recurrenceEndDate,
        is_recurring: data.recurrence !== 'None',
        recurrence: data.recurrence || 'None', // Ensure recurrence is always set
      };
    }
    
    return data;
  },

  createEvent: async (event: Partial<CalendarEvent>, user_id: number = 1) => {
    const formatDate = (date: Date | string | undefined) => {
      if (!date) return undefined;
      const d = date instanceof Date ? date : new Date(date);
      return d.getFullYear() + '-' +
        String(d.getMonth() + 1).padStart(2, '0') + '-' +
        String(d.getDate()).padStart(2, '0') + 'T' +
        String(d.getHours()).padStart(2, '0') + ':' +
        String(d.getMinutes()).padStart(2, '0') + ':' +
        String(d.getSeconds()).padStart(2, '0') + '.' +
        String(d.getMilliseconds()).padStart(3, '0');
    };

    const mapStatusForBackend = (status: string | undefined) => {
      if (!status) return undefined;
      if (['Upcoming', 'In Progress', 'Completed', 'Cancelled', 'Blocked', 'Under Review', 'Deferred'].includes(status)) {
        return status;
      }
      const statusMap: Record<string, string> = {
        'UPCOMING': 'Upcoming',
        'IN_PROGRESS': 'In Progress',
        'COMPLETED': 'Completed',
        'CANCELLED': 'Cancelled',
        'BLOCKED': 'Blocked',
        'UNDER_REVIEW': 'Under Review',
        'DEFERRED': 'Deferred'
      };
      return statusMap[status] || status;
    };

    const mapPriorityForBackend = (priority: string | undefined) => {
      if (!priority) return undefined;
      if (['Low', 'Medium', 'High', 'Urgent'].includes(priority)) {
        return priority;
      }
      const priorityMap: Record<string, string> = {
        'LOW': 'Low',
        'MEDIUM': 'Medium',
        'HIGH': 'High',
        'URGENT': 'Urgent'
      };
      return priorityMap[priority] || priority;
    };

    // Calculate duration if start and end dates are provided
    let duration = undefined;
    if (event.start && event.end) {
      // Duration in hours
      duration = (event.end.getTime() - event.start.getTime()) / (1000 * 60 * 60);
    }

    // Prioritize due_date if it's explicitly provided
    const dueDate = event.due_date ? formatDate(event.due_date) : 
                   event.end ? formatDate(event.end) : 
                   event.end_date ? formatDate(event.end_date) : undefined;

    // Format recurrence_end_date without timezone information
    const recurrenceEndDate = event.recurrence_end_date ? formatDate(event.recurrence_end_date) : undefined;

    const { data } = await axiosInstance.post(`/events`, {
      ...event,
      start_date: formatDate(event.start_date || event.start),
      due_date: dueDate,
      duration: duration,
      status: mapStatusForBackend(event.status),
      priority: mapPriorityForBackend(event.priority),
      recurrence_end_date: recurrenceEndDate,
    }, {
      params: { user_id }
    });
    return data;
  },

  updateEvent: async (eventId: string, event: Partial<CalendarEvent>, user_id: number = 1) => {
    const formatDate = (date: Date | string | undefined) => {
      if (!date) return undefined;
      const d = date instanceof Date ? date : new Date(date);
      return d.getFullYear() + '-' +
        String(d.getMonth() + 1).padStart(2, '0') + '-' +
        String(d.getDate()).padStart(2, '0') + 'T' +
        String(d.getHours()).padStart(2, '0') + ':' +
        String(d.getMinutes()).padStart(2, '0') + ':' +
        String(d.getSeconds()).padStart(2, '0') + '.' +
        String(d.getMilliseconds()).padStart(3, '0');
    };

    const mapStatusForBackend = (status: string | undefined) => {
      if (!status) return undefined;
      if (['Upcoming', 'In Progress', 'Completed', 'Cancelled', 'Blocked', 'Under Review', 'Deferred'].includes(status)) {
        return status;
      }
      const statusMap: Record<string, string> = {
        'UPCOMING': 'Upcoming',
        'IN_PROGRESS': 'In Progress',
        'COMPLETED': 'Completed',
        'CANCELLED': 'Cancelled',
        'BLOCKED': 'Blocked',
        'UNDER_REVIEW': 'Under Review',
        'DEFERRED': 'Deferred'
      };
      return statusMap[status] || status;
    };

    const mapPriorityForBackend = (priority: string | undefined) => {
      if (!priority) return undefined;
      if (['Low', 'Medium', 'High', 'Urgent'].includes(priority)) {
        return priority;
      }
      const priorityMap: Record<string, string> = {
        'LOW': 'Low',
        'MEDIUM': 'Medium',
        'HIGH': 'High',
        'URGENT': 'Urgent'
      };
      return priorityMap[priority] || priority;
    };

    // Calculate duration if start and end dates are provided
    let duration = undefined;
    if (event.start && event.end) {
      // Duration in hours
      duration = (event.end.getTime() - event.start.getTime()) / (1000 * 60 * 60);
    }

    const originalId = eventId.split('_')[0];

    // Prioritize due_date if it's explicitly provided
    const dueDate = event.due_date ? formatDate(event.due_date) : 
                   event.end ? formatDate(event.end) : 
                   event.end_date ? formatDate(event.end_date) : undefined;

    // Format recurrence_end_date without timezone information
    const recurrenceEndDate = event.recurrence_end_date ? formatDate(event.recurrence_end_date) : undefined;

    const { data } = await axiosInstance.put(`/events/${originalId}`, {
      ...event,
      start_date: formatDate(event.start_date || event.start),
      due_date: dueDate,
      duration: duration,
      status: mapStatusForBackend(event.status),
      priority: mapPriorityForBackend(event.priority),
      recurrence_end_date: recurrenceEndDate,
    }, {
      params: { user_id }
    });
    return data;
  },

  deleteEvent: async (eventId: string, user_id: number = 1) => {
    const originalId = eventId.split('_')[0];
    await axiosInstance.delete(`/events/${originalId}`, {
      params: { user_id }
    });
  },
};