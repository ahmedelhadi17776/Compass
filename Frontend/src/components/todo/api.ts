import axios from 'axios';
import { Todo } from './types-todo';
import { Habit } from './types-habit';

const API_BASE_URL = 'http://localhost:8000';

// Todo API functions
export const fetchTodos = async (userId: number, token: string): Promise<Todo[]> => {
  const response = await axios.get<Todo[]>(`${API_BASE_URL}/todos/user/${userId}`, {
    headers: { Authorization: `Bearer ${token}` }
  });
  
  // Ensure we're returning an array
  if (!Array.isArray(response.data)) {
    console.error('API did not return an array:', response.data);
    return [];
  }

  return response.data;
};

export const createTodo = async (newTodo: Omit<Todo, 'id' | 'created_at' | 'updated_at' | 'completion_date'>, token: string): Promise<Todo> => {
  const response = await axios.post<Todo>(
    `${API_BASE_URL}/todos`,
    newTodo,
    { headers: { Authorization: `Bearer ${token}` } }
  );
  return response.data;
};

export const updateTodo = async (id: number, userId: number, updates: Partial<Todo>, token: string): Promise<Todo> => {
  const response = await axios.put<Todo>(
    `${API_BASE_URL}/todos/${id}?user_id=${userId}`,
    updates,
    { headers: { Authorization: `Bearer ${token}` } }
  );
  return response.data;
};

export const deleteTodo = async (id: number, userId: number, token: string): Promise<void> => {
  await axios.delete(
    `${API_BASE_URL}/todos/${id}?user_id=${userId}`,
    { headers: { Authorization: `Bearer ${token}` } }
  );
};

// Habit API functions
export const fetchHabits = async (userId: number, token: string): Promise<Habit[]> => {
  const response = await axios.get<Habit[]>(`${API_BASE_URL}/daily-habits/user/${userId}`, {
    headers: { Authorization: `Bearer ${token}` }
  });
  return response.data;
};

export const createHabit = async (habit_name: string, userId: number, token: string) => {
  return axios.post(`${API_BASE_URL}/daily-habits`, {
    habit_name,
    user_id: userId,
    start_day: new Date().toISOString().split('T')[0],
  }, {
    headers: { Authorization: `Bearer ${token}` }
  });
};

export const completeHabit = async (habitId: number, userId: number, token: string) => {
  return axios.post(`${API_BASE_URL}/daily-habits/${habitId}/complete`, null, {
    params: { user_id: userId },
    headers: { Authorization: `Bearer ${token}` }
  });
};

export const uncompleteHabit = async (habitId: number, userId: number, token: string) => {
  return axios.post(`${API_BASE_URL}/daily-habits/${habitId}/uncomplete`, null, {
    params: { user_id: userId },
    headers: { Authorization: `Bearer ${token}` }
  });
};

export const deleteHabit = async (habitId: number, userId: number, token: string) => {
  return axios.delete(`${API_BASE_URL}/daily-habits/${habitId}`, {
    params: { user_id: userId },
    headers: { Authorization: `Bearer ${token}` }
  });
};

export const updateHabit = async (habitId: number, habit_name: string, userId: number, token: string) => {
  return axios.put(
    `${API_BASE_URL}/daily-habits/${habitId}`,
    { habit_name },
    {
      params: { user_id: userId },
      headers: { Authorization: `Bearer ${token}` }
    }
  );
};
