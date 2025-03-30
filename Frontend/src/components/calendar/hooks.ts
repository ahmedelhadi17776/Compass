import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { eventsApi } from './api';
import { CalendarEvent } from './types';
import { startOfWeek, endOfWeek, startOfDay, endOfDay, addDays, startOfMonth, endOfMonth } from 'date-fns';

export const useCalendarEvents = (
  startDate: Date,
  endDate: Date,
  userId: number = 1,
  options?: {
    expand_recurring?: boolean;
    project_id?: number;
  }
) => {
  return useQuery({
    queryKey: [
      'events',
      'calendar',
      startDate.toISOString(),
      endDate.toISOString(),
      userId,
      options?.expand_recurring,
      options?.project_id
    ],
    queryFn: () => eventsApi.getEvents({
      due_date_start: startDate,
      due_date_end: endDate,
      user_id: userId,
      project_id: options?.project_id,
    }),
    staleTime: 0,
    gcTime: 5 * 60 * 1000,
    refetchOnMount: true,
    refetchOnWindowFocus: true,
    refetchOnReconnect: true,
  });
};

export const useWeekEvents = (date: Date, userId: number = 1, options?: { expand_recurring?: boolean; project_id?: number }) => {
  const startDate = startOfWeek(date);
  const endDate = endOfWeek(date);
  return useCalendarEvents(startDate, endDate, userId, options);
};

export const useDayEvents = (date: Date, userId: number = 1, options?: { expand_recurring?: boolean; project_id?: number }) => {
  const startDate = startOfDay(date);
  const endDate = endOfDay(date);
  return useCalendarEvents(startDate, endDate, userId, options);
};

export const useThreeDayEvents = (date: Date, userId: number = 1, options?: { expand_recurring?: boolean; project_id?: number }) => {
  const startDate = startOfDay(date);
  const endDate = endOfDay(addDays(date, 2));
  return useCalendarEvents(startDate, endDate, userId, options);
};

export const useMonthEvents = (date: Date, userId: number = 1, options?: { expand_recurring?: boolean; project_id?: number }) => {
  const startDate = startOfMonth(date);
  const endDate = endOfMonth(date);
  return useCalendarEvents(startDate, endDate, userId, options);
};

export const useCreateEvent = (userId: number) => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (event: Partial<CalendarEvent>) => eventsApi.createEvent(event, userId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['events'] });
    },
  });
};

export const useUpdateEvent = (userId: number) => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ eventId, event }: { eventId: string; event: Partial<CalendarEvent> }) =>
      eventsApi.updateEvent(eventId, event, userId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['events'] });
    },
  });
};

export const useDeleteEvent = (userId: number) => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (eventId: string) => eventsApi.deleteEvent(eventId, userId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['events'] });
    },
  });
}; 