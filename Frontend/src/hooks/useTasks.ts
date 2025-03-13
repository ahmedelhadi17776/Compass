import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { tasksApi } from '@/api/tasks';
import { CalendarEvent } from '@/components/calendar/types';
import { startOfWeek, endOfWeek, startOfDay, endOfDay, addDays, startOfMonth, endOfMonth } from 'date-fns';

export const useCalendarTasks = (
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
      'tasks',
      'calendar',
      startDate.toISOString(),
      endDate.toISOString(),
      userId,
      options?.expand_recurring,
      options?.project_id
    ],
    queryFn: () => tasksApi.getTasks({
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

export const useWeekTasks = (date: Date, userId: number = 1, options?: { expand_recurring?: boolean; project_id?: number }) => {
  const startDate = startOfWeek(date);
  const endDate = endOfWeek(date);
  return useCalendarTasks(startDate, endDate, userId, options);
};

export const useDayTasks = (date: Date, userId: number = 1, options?: { expand_recurring?: boolean; project_id?: number }) => {
  const startDate = startOfDay(date);
  const endDate = endOfDay(date);
  return useCalendarTasks(startDate, endDate, userId, options);
};

export const useThreeDayTasks = (date: Date, userId: number = 1, options?: { expand_recurring?: boolean; project_id?: number }) => {
  const startDate = startOfDay(date);
  const endDate = endOfDay(addDays(date, 2));
  return useCalendarTasks(startDate, endDate, userId, options);
};

export const useMonthTasks = (date: Date, userId: number = 1, options?: { expand_recurring?: boolean; project_id?: number }) => {
  const startDate = startOfMonth(date);
  const endDate = endOfMonth(date);
  return useCalendarTasks(startDate, endDate, userId, options);
};

export const useCreateTask = (userId: number) => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (task: Partial<CalendarEvent>) => tasksApi.createTask(task, userId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tasks'] });
    },
  });
};

export const useUpdateTask = (userId: number) => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ taskId, task }: { taskId: string; task: Partial<CalendarEvent> }) =>
      tasksApi.updateTask(taskId, task, userId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tasks'] });
    },
  });
};

export const useDeleteTask = (userId: number) => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (taskId: string) => tasksApi.deleteTask(taskId, userId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tasks'] });
    },
  });
}; 