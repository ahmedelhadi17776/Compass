import axios from 'axios';
import { CalendarEvent, CreateEventData } from './types';

const API_BASE_URL = 'http://localhost:8000';

export const fetchEvents = async (startTime: Date, endTime: Date): Promise<CalendarEvent[]> => {
  const response = await axios.get<{ events: CalendarEvent[]; total: number }>(`${API_BASE_URL}/api/calendar/events`, {
    params: {
      start_time: startTime.toISOString(),
      end_time: endTime.toISOString(),
    }
  });
  return response.data.events;
};

export const createEvent = async (data: CreateEventData) => {
  const response = await axios.post(`${API_BASE_URL}/api/calendar/events`, data);
  return response.data;
};

export const updateEvent = async (eventId: string, event: CalendarEvent) => {
  const response = await axios.put(`${API_BASE_URL}/api/calendar/events/${eventId}`, event);
  return response.data;
};

export const deleteEvent = async (eventId: string) => {
  const response = await axios.delete(`${API_BASE_URL}/api/calendar/events/${eventId}`);
  return response.data;
};

export const fetchHeatmapData = async (period: 'week' | 'month' | 'year' = 'year') => {
  const response = await axios.get(`${API_BASE_URL}/api/habits/heatmap`, {
    params: { period }
  });
  return response.data.data.data;
};




