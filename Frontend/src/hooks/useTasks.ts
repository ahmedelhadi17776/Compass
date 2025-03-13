import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { tasksApi } from '@/api/tasks';
import { CalendarEvent } from '@/components/calendar/types';
import { startOfWeek, endOfWeek } from 'date-fns';

export const useWeekTasks = (date: Date, userId: number = 1) => {
  const startDate = startOfWeek(date);
  const endDate = endOfWeek(date);

  return useQuery({
    queryKey: ['tasks', 'week', startDate.toISOString(), endDate.toISOString(), userId],
    queryFn: () => tasksApi.getTasks({
      start_date: startDate,
      end_date: endDate,
      user_id: userId,
    }),
    staleTime: 0,
    gcTime: 5 * 60 * 1000,
    refetchOnMount: true,
    refetchOnWindowFocus: true,
    refetchOnReconnect: true,
  });
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