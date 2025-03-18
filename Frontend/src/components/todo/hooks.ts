import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Todo, TodoStatus } from './types-todo';
import { Habit } from './types-habit';
import { User } from '@/api/auth';
import * as api from './api';

// Todo hooks
export const useTodos = (user: User | undefined) => {
  return useQuery<Todo[]>({
    queryKey: ['todos', user?.id],
    queryFn: async () => {
      const token = localStorage.getItem('token');
      if (!token || !user?.id) throw new Error('Authentication required');
      
      return api.fetchTodos(user.id, token);
    },
    enabled: !!user?.id,
    initialData: [],
    staleTime: 0,
  });
};

export const useCreateTodo = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (newTodo: Omit<Todo, 'id' | 'created_at' | 'updated_at' | 'completion_date'>) => {
      const token = localStorage.getItem('token');
      if (!token) throw new Error('No token found');
      
      return api.createTodo(newTodo, token);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['todos'] });
    },
  });
};

export const useUpdateTodo = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async ({ id, updates }: { id: number; updates: Partial<Todo> }) => {
      const token = localStorage.getItem('token');
      const user = queryClient.getQueryData<User>(['user']);
      if (!token || !user?.id) throw new Error('No token found or user not authenticated');
      
      return api.updateTodo(id, user.id, updates, token);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['todos'] });
    },
  });
};

export const useDeleteTodo = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (id: number) => {
      const token = localStorage.getItem('token');
      const user = queryClient.getQueryData<User>(['user']);
      if (!token || !user?.id) throw new Error('No token found or user not authenticated');
      
      return api.deleteTodo(id, user.id, token);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['todos'] });
    },
  });
};

export const useToggleTodoStatus = () => {
  const updateTodoMutation = useUpdateTodo();
  
  return (todo: Todo) => {
    const newStatus = todo.status === TodoStatus.COMPLETED ? TodoStatus.PENDING : TodoStatus.COMPLETED;
    updateTodoMutation.mutate({
      id: todo.id,
      updates: {
        status: newStatus,
        completion_date: newStatus === TodoStatus.COMPLETED ? new Date().toISOString() : undefined
      }
    });
  };
};

// Habit hooks
export const useHabits = (user: User | undefined) => {
  return useQuery<Habit[]>({
    queryKey: ['habits', user?.id],
    queryFn: async () => {
      const token = localStorage.getItem('token');
      if (!token || !user?.id) throw new Error('Authentication required');
      
      return api.fetchHabits(user.id, token);
    },
    enabled: !!user?.id,
    initialData: [],
    staleTime: 0,
  });
};

export const useCreateHabit = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (habit_name: string) => {
      const token = localStorage.getItem('token');
      const user = queryClient.getQueryData<User>(['user']);
      if (!token || !user?.id) throw new Error('Authentication required');
      
      return api.createHabit(habit_name, user.id, token);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['habits'] });
    },
  });
};

export const useToggleHabit = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async ({ habitId, isCompleted }: { habitId: number; isCompleted: boolean }) => {
      const token = localStorage.getItem('token');
      const user = queryClient.getQueryData<User>(['user']);
      if (!token || !user?.id) throw new Error('Authentication required');
      
      if (isCompleted) {
        return api.uncompleteHabit(habitId, user.id, token);
      } else {
        return api.completeHabit(habitId, user.id, token);
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['habits'] });
    },
  });
};

export const useDeleteHabit = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (habitId: number) => {
      const token = localStorage.getItem('token');
      const user = queryClient.getQueryData<User>(['user']);
      if (!token || !user?.id) throw new Error('Authentication required');
      
      return api.deleteHabit(habitId, user.id, token);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['habits'] });
    },
  });
};

export const useUpdateHabit = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async ({ habitId, habit_name }: { habitId: number; habit_name: string }) => {
      const token = localStorage.getItem('token');
      const user = queryClient.getQueryData<User>(['user']);
      if (!token || !user?.id) throw new Error('Authentication required');
      
      return api.updateHabit(habitId, habit_name, user.id, token);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['habits'] });
    },
  });
};
