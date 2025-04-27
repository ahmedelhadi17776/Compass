import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { CalendarEvent, CreateEventData } from './types';
import { User } from '@/hooks/useAuth';
import { fetchEvents, createEvent, updateEvent, deleteEvent } from './api';
import { startOfMonth, endOfMonth, startOfDay, endOfDay, startOfWeek, addDays, endOfWeek } from 'date-fns';

// Calendar hooks
export const useEvents = (
  user: User | undefined, 
  date: Date = new Date(),
  viewType: 'day' | 'threeDays' | 'week' | 'month' = 'month'
) => {
  const startTime = viewType === 'day' ? startOfDay(date) : 
                   viewType === 'threeDays' ? startOfDay(date) : 
                   startOfWeek(date, { weekStartsOn: 1 });
                   
  const endTime = viewType === 'day' ? endOfDay(date) : 
                 viewType === 'threeDays' ? endOfDay(addDays(date, 2)) : 
                 endOfWeek(date, { weekStartsOn: 1 });

  return useQuery<CalendarEvent[]>({
    queryKey: ['events', user?.id, startTime, endTime, viewType],
    queryFn: () => user ? fetchEvents(startTime, endTime) : Promise.resolve([]),
    enabled: !!user,
  });
};

// Specific hook for day view
export const useDayEvents = (user: User | undefined, date: Date) => {
  return useEvents(user, date, 'day');
};

export const useThreeDayEvents = (user: User | undefined, date: Date) => {
  return useEvents(user, date, 'threeDays');
};

export const useCreateEvent = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: createEvent,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['events'] });
    },
  });
};

interface UpdateEventData {
  eventId: string;
  event: CalendarEvent;
}

export const useUpdateEvent = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: UpdateEventData) => updateEvent(data.eventId, data.event),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['events'] });
    },
  });
};

export const useDeleteEvent = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: deleteEvent,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['events'] });
    },
  });
};

