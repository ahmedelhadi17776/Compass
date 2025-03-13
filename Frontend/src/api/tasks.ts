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

      const params: Record<string, any> = {
        skip,
        limit,
        user_id,
      };

      if (status) params.status = status;
      if (priority) params.priority = priority;
      if (project_id) params.project_id = project_id;
      if (assignee_id) params.assignee_id = assignee_id;
      if (creator_id) params.creator_id = creator_id;
      if (due_date_start) params.start_date = formattedStartDate;
      if (due_date_end) params.end_date = formattedEndDate;

      const response = await axiosInstance.get('/tasks/', { params });

      if (Array.isArray(response.data)) {
        return response.data.map(task => ({
          ...task,
          start: task.start_date ? new Date(task.start_date) : null,
          end: task.end_date ? new Date(task.end_date) : null,
          // Map additional fields from backend to frontend model
          project_id: task.project_id || 1,
          organization_id: task.organization_id || 1,
          creator_id: task.creator_id || user_id,
          status: task.status || 'TODO',
          priority: task.priority || 'MEDIUM',
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
    const { data } = await axiosInstance.post(`/tasks`, {
      ...task,
      user_id,
      project_id: task.project_id || 1,
      organization_id: task.organization_id || 1,
      creator_id: task.creator_id || user_id,
    });
    return data;
  },

  updateTask: async (taskId: string, task: Partial<CalendarEvent>, user_id: number = 1) => {
    const { data } = await axiosInstance.put(`/tasks/${taskId}`, task, {
      params: { user_id }
    });
    return data;
  },

  deleteTask: async (taskId: string, user_id: number = 1) => {
    await axiosInstance.delete(`/tasks/${taskId}`, {
      params: { user_id }
    });
  },
};