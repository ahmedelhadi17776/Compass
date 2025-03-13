import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { tasksApi } from '@/api/tasks';
import { CalendarEvent } from '@/components/calendar/types';
import { startOfWeek, endOfWeek } from 'date-fns';

export const useWeekTasks = (date: Date, user_id: number = 1) => {
  const startDate = startOfWeek(date);
  const endDate = endOfWeek(date);

  return useQuery({
    queryKey: ['tasks', 'week', startDate.toISOString(), user_id],
    queryFn: () => tasksApi.getTasks({
      due_date_start: startDate,
      due_date_end: endDate,
      limit: 100,
      user_id
    }),
    staleTime: 0,
    gcTime: 5 * 60 * 1000,
    refetchOnMount: true,
    refetchOnWindowFocus: true,
    refetchOnReconnect: true,
  });
};

export const useCreateTask = (user_id: number = 1) => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (task: Partial<CalendarEvent>) => tasksApi.createTask(task, user_id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tasks'] });
    },
  });
};

export const useUpdateTask = (user_id: number = 1) => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ taskId, task }: { taskId: string; task: Partial<CalendarEvent> }) => 
      tasksApi.updateTask(taskId, task, user_id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tasks'] });
    },
  });
};

export const useDeleteTask = (user_id: number = 1) => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (taskId: string) => tasksApi.deleteTask(taskId, user_id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tasks'] });
    },
  });
}; 