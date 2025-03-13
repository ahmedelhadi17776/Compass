import axios from 'axios';
import { CalendarEvent } from '@/components/calendar/types';

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
  (response) => {
    // Transform the response data if needed
    return response;
  },
  (error) => {
    console.error('API Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

export const tasksApi = {
  getTasks: async ({
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

      let endpoint = '/tasks/';
      const params: Record<string, any> = {
        user_id,
      };

      if (due_date_start && due_date_end) {
        endpoint = '/tasks/calendar';
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

      const response = await axiosInstance.get(endpoint, { params });

      if (Array.isArray(response.data)) {
        return response.data.map(task => ({
          ...task,
          id: String(task.id),
          start: task.start_date ? new Date(task.start_date) : null,
          end: task.due_date ? new Date(task.due_date) : null,
          // Map additional fields from backend to frontend model
          project_id: task.project_id || 1,
          organization_id: task.organization_id || 1,
          creator_id: task.creator_id || user_id,
          status: task.status || 'TODO',
          priority: task.priority || 'MEDIUM',
          is_recurring: task.is_recurring || false,
          is_original: task.is_original,
          original_id: task.original_id,
          occurrence_num: task.occurrence_num
        }));
      }
      return []
    } catch (error) {
      console.error('Error fetching tasks:', error);
      return [];
    }
  },

  getTaskById: async (taskId: string, user_id: number = 1) => {
    const { data } = await axiosInstance.get(`/tasks/by_id/${taskId}`, {
      params: { user_id }
    });
    return data;
  },

  createTask: async (task: Partial<CalendarEvent>, user_id: number = 1) => {
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

      if (['To Do', 'In Progress', 'Completed', 'Cancelled', 'Blocked', 'Under Review', 'Deferred'].includes(status)) {
        return status;
      }

      const statusMap: Record<string, string> = {
        'TODO': 'To Do',
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
    if (task.start && task.end) {
      // Duration in hours
      duration = (task.end.getTime() - task.start.getTime()) / (1000 * 60 * 60);
    }

    // Prioritize due_date if it's explicitly provided
    const dueDate = task.due_date ? formatDate(task.due_date) : 
                   task.end ? formatDate(task.end) : 
                   task.end_date ? formatDate(task.end_date) : undefined;

    const { data } = await axiosInstance.post(`/tasks`, {
      ...task,
      start_date: formatDate(task.start_date || task.start),
      due_date: dueDate,
      duration: duration,
      project_id: task.project_id || 1,
      organization_id: task.organization_id || 1,
      creator_id: task.creator_id || user_id,
      status: mapStatusForBackend(task.status),
      priority: mapPriorityForBackend(task.priority),
    }, {
      params: { user_id }
    });
    return data;
  },

  updateTask: async (taskId: string, task: Partial<CalendarEvent>, user_id: number = 1) => {
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

      if (['To Do', 'In Progress', 'Completed', 'Cancelled', 'Blocked', 'Under Review', 'Deferred'].includes(status)) {
        return status;
      }

      const statusMap: Record<string, string> = {
        'TODO': 'To Do',
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
    if (task.start && task.end) {
      // Duration in hours
      duration = (task.end.getTime() - task.start.getTime()) / (1000 * 60 * 60);
    }

    const originalId = taskId.split('_')[0];

    // Prioritize due_date if it's explicitly provided
    const dueDate = task.due_date ? formatDate(task.due_date) : 
                   task.end ? formatDate(task.end) : 
                   task.end_date ? formatDate(task.end_date) : undefined;

    const { data } = await axiosInstance.put(`/tasks/${originalId}`, {
      ...task,
      start_date: formatDate(task.start_date || task.start),
      due_date: dueDate,
      duration: duration,
      status: mapStatusForBackend(task.status),
      priority: mapPriorityForBackend(task.priority),
    }, {
      params: { user_id }
    });
    return data;
  },

  deleteTask: async (taskId: string, user_id: number = 1) => {
    const originalId = taskId.split('_')[0];

    await axiosInstance.delete(`/tasks/${originalId}`, {
      params: { user_id }
    });
  },
};