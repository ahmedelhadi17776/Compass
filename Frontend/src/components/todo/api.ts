import axios from 'axios';
import { Todo } from './types-todo';
import { Habit } from './types-habit';

const API_BASE_URL = 'http://localhost:8000';

// Todo API functions
export const fetchTodos = async (userId: string): Promise<Todo[]> => {
  const response = await axios.get<Todo[]>(`${API_BASE_URL}/todos/user/${userId}`);
  
  // Ensure we're returning an array
  if (!Array.isArray(response.data)) {
    console.error('API did not return an array:', response.data);
    return [];
  }

  return response.data;
};

export const createTodo = async (newTodo: Omit<Todo, 'id' | 'created_at' | 'updated_at' | 'completion_date'>): Promise<Todo> => {
  const response = await axios.post<Todo>(
    `${API_BASE_URL}/todos`,
    newTodo
  );
  return response.data;
};

export const updateTodo = async (id: string, updates: Partial<Todo>): Promise<Todo> => {
  const response = await axios.put<Todo>(
    `${API_BASE_URL}/todos/${id}`,
    updates
  );
  return response.data;
};

export const deleteTodo = async (id: string): Promise<void> => {
  await axios.delete(
    `${API_BASE_URL}/todos/${id}`
  );
};

// Habit API functions
export const fetchHabits = async (userId: string): Promise<Habit[]> => {
  const response = await axios.get<{ data: Habit[] }>(`${API_BASE_URL}/api/habits/user/${userId}`);
  
  // Ensure we're returning an array from the data wrapper
  if (!Array.isArray(response.data.data)) {
    console.error('API did not return an array:', response.data);
    return [];
  }

  return response.data.data;
};

interface CreateHabitData {
  title: string;
  description: string;
  start_day: string;
  user_id: string;
}

export const createHabit = async (data: CreateHabitData) => {
  return axios.post(`${API_BASE_URL}/api/habits`, data);
};

export const completeHabit = async (habitId: string) => {
  return axios.post(`${API_BASE_URL}/api/habits/${habitId}/complete`);
};

export const uncompleteHabit = async (habitId: string) => {
  return axios.post(`${API_BASE_URL}/api/habits/${habitId}/uncomplete`);
};

export const deleteHabit = async (habitId: string) => {
  return axios.delete(`${API_BASE_URL}/api/habits/${habitId}`);
};

export const updateHabit = async (habitId: string, title: string) => {
  return axios.put(
    `${API_BASE_URL}/api/habits/${habitId}`,
    { title }
  );
};
