import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { tasksApi } from '@/api/tasks';
import { CalendarEvent } from '@/components/calendar/types';
import { startOfWeek, endOfWeek } from 'date-fns';

export const useWeekTasks = (date: Date) => {
  const startDate = startOfWeek(date);
  const endDate = endOfWeek(date);

  return useQuery({
    queryKey: ['tasks', 'week', startDate.toISOString()],
    queryFn: () => tasksApi.getTasks({
      due_date_start: startDate,
      due_date_end: endDate,
      limit: 100
    }),
  });
};

export const useCreateTask = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (task: Partial<CalendarEvent>) => tasksApi.createTask(task),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tasks'] });
    },
  });
};

export const useUpdateTask = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ taskId, task }: { taskId: string; task: Partial<CalendarEvent> }) => 
      tasksApi.updateTask(taskId, task),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tasks'] });
    },
  });
};

export const useDeleteTask = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (taskId: string) => tasksApi.deleteTask(taskId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tasks'] });
    },
  });
}; 