import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Todo, TodoStatus } from './types-todo';
import { Habit } from './types-habit';
import { User } from '@/api/auth';
import { fetchTodos, createTodo, updateTodo, deleteTodo, fetchHabits, createHabit, completeHabit, uncompleteHabit, deleteHabit, updateHabit } from './api';

// Todo hooks
export const useTodos = (user: User | undefined) => {
  return useQuery<Todo[]>({
    queryKey: ['todos', user?.id],
    queryFn: () => user ? fetchTodos(user.id) : Promise.resolve([]),
    enabled: !!user,
  });
};

export const useCreateTodo = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: createTodo,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['todos'] });
    },
  });
};

export const useUpdateTodo = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, updates }: { id: number; updates: Partial<Todo> }) =>
      updateTodo(id, updates.user_id!, updates),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['todos'] });
    },
  });
};

export const useDeleteTodo = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: deleteTodo,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['todos'] });
    },
  });
};

export const useToggleTodoStatus = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (todo: Todo) =>
      updateTodo(todo.id, todo.user_id, {
        status: todo.status === TodoStatus.COMPLETED ? TodoStatus.PENDING : TodoStatus.COMPLETED,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['todos'] });
    },
  });
};

// Habit hooks
export const useHabits = (user: User | undefined) => {
  return useQuery<Habit[]>({
    queryKey: ['habits', user?.id],
    queryFn: () => user ? fetchHabits(user.id) : Promise.resolve([]),
    enabled: !!user,
  });
};

interface CreateHabitData {
  title: string;
  description: string;
  start_day: string;
  user_id: string;
}

export const useCreateHabit = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: CreateHabitData) => createHabit(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['habits'] });
    },
  });
};

export const useToggleHabit = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ habitId, isCompleted }: { habitId: string; isCompleted: boolean }) =>
      isCompleted ? uncompleteHabit(habitId) : completeHabit(habitId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['habits'] });
    },
  });
};

export const useDeleteHabit = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: deleteHabit,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['habits'] });
    },
  });
};

interface UpdateHabitData {
  habitId: string;
  title: string;
}

export const useUpdateHabit = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: UpdateHabitData) => updateHabit(data.habitId, data.title),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['habits'] });
    },
  });
};
