import axios from 'axios';
import { Todo, TodosResponse, TodoList, TodoListsResponse, CreateTodoListInput, UpdateTodoListInput } from './types-todo';
import { Habit } from './types-habit';

const API_BASE_URL = 'http://localhost:8000';
// Todo API functions
export const fetchTodos = async (userId: string, listId?: string): Promise<Todo[]> => {
  const url = listId ? 
    `${API_BASE_URL}/api/todos?list_id=${listId}` :
    `${API_BASE_URL}/api/todos`;
  const response = await axios.get<{ data: TodosResponse }>(url);
  return response.data.data.todos;
};

export const createTodo = async (newTodo: Omit<Todo, 'id' | 'created_at' | 'updated_at' | 'completed_at'>): Promise<Todo> => {
  // Remove list_id if it's undefined to let backend handle default list
  const todoData = { ...newTodo };
  if (!todoData.list_id) {
    delete todoData.list_id;
  }

  const response = await axios.post<Todo>(
    `${API_BASE_URL}/api/todos`,
    todoData
  );
  return response.data;
};

export const updateTodo = async (id: string, updates: Partial<Todo>): Promise<Todo> => {
  const response = await axios.put<Todo>(
    `${API_BASE_URL}/api/todos/${id}`,
    updates
  );
  return response.data;
};

export const deleteTodo = async (id: string): Promise<void> => {
  await axios.delete(
    `${API_BASE_URL}/api/todos/${id}`
  );
};

export const completeTodo = async (id: string): Promise<Todo> => {
  const response = await axios.patch<{ data: Todo }>(`${API_BASE_URL}/api/todos/${id}/complete`);
  return response.data.data;
};

export const uncompleteTodo = async (id: string): Promise<Todo> => {
  const response = await axios.patch<{ data: Todo }>(`${API_BASE_URL}/api/todos/${id}/uncomplete`);
  return response.data.data;
};

// Habit API functions
export const fetchHabits = async (): Promise<Habit[]> => {
  const response = await axios.get<{ data: { habits: Habit[] } }>(`${API_BASE_URL}/api/habits`);
  return response.data.data.habits;
};

interface CreateHabitData {
  title: string;
  description: string;
  start_day: string;
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

export const fetchTodoLists = async (): Promise<TodoList[]> => {
  const response = await axios.get<{ data: TodoListsResponse }>(`${API_BASE_URL}/api/todo-lists`);
  return response.data.data.lists;
};

export const createTodoList = async (data: CreateTodoListInput): Promise<TodoList> => {
  const response = await axios.post<{ data: TodoList }>(`${API_BASE_URL}/api/todo-lists`, data);
  return response.data.data;
};

export const updateTodoList = async (id: string, data: UpdateTodoListInput): Promise<TodoList> => {
  const response = await axios.put<{ data: TodoList }>(`${API_BASE_URL}/api/todo-lists/${id}`, data);
  return response.data.data;
};

export const deleteTodoList = async (id: string): Promise<void> => {
  await axios.delete(`${API_BASE_URL}/api/todo-lists/${id}`);
};
