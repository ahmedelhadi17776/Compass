import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { CalendarEvent, CreateEventData } from './types';
import { User } from '@/hooks/useAuth';
import { fetchEvents, createEvent, updateEvent, deleteEvent } from './api';
import { startOfMonth, endOfMonth } from 'date-fns';

// Calendar hooks
export const useEvents = (user: User | undefined, date: Date = new Date()) => {
  const startTime = startOfMonth(date);
  const endTime = endOfMonth(date);

  return useQuery<CalendarEvent[]>({
    queryKey: ['events', user?.id, startTime, endTime],
    queryFn: () => user ? fetchEvents(startTime, endTime) : Promise.resolve([]),
    enabled: !!user,
  });
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

