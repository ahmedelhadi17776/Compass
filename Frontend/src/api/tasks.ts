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
    return response.data;
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
  }: {
    skip?: number;
    limit?: number;
    status?: string;
    priority?: string;
    project_id?: number;
    assignee_id?: number;
    creator_id?: number;
    due_date_start?: Date;
    due_date_end?: Date;
  }) => {
    const { data } = await axiosInstance.get(`/tasks`, {
      params: {
        skip,
        limit,
        status,
        priority,
        project_id,
        assignee_id,
        creator_id,
        due_date_start: due_date_start?.toISOString(),
        due_date_end: due_date_end?.toISOString(),
      }
    });
    return Array.isArray(data) ? data : [];  // Ensure we always return an array
  },

  getTaskById: async (taskId: string) => {
    const { data } = await axiosInstance.get(`/tasks/by_id/${taskId}`);
    return data;
  },

  createTask: async (task: Partial<CalendarEvent>) => {
    const { data } = await axiosInstance.post(`/tasks`, task);
    return data;
  },

  updateTask: async (taskId: string, task: Partial<CalendarEvent>) => {
    const { data } = await axiosInstance.put(`/tasks/${taskId}`, task);
    return data;
  },

  deleteTask: async (taskId: string) => {
    await axiosInstance.delete(`/tasks/${taskId}`);
  },
}; 