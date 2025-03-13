import React, { useState } from 'react';
import { Plus, X, MoreVertical, Clock, Eye, Repeat, Check, ArrowLeft } from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "../ui/dialog";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "../ui/dropdown-menu";
import { Button } from "../ui/button";
import { Input } from "../ui/input";
import { Progress } from "../ui/progress";
import Checkbox from "../ui/checkbox";
import TodoForm from './TodoForm';
import { Badge } from "../ui/badge";
import cn from 'classnames';
import { useTheme } from '@/contexts/theme-provider';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import authApi, { User } from '@/api/auth';
import axios from 'axios';
import { Habit } from '@/types/habit';
import { Todo, TodoFormData, TodoStatus, TodoPriority } from '@/types/todo';

const API_BASE_URL = 'http://localhost:8000';

const TodoList: React.FC = () => {
  const queryClient = useQueryClient();
  const { theme } = useTheme();
  const isDarkMode = theme === 'dark';
  const [editingTask, setEditingTask] = useState<Todo | null>(null);
  const [showTodoForm, setShowTodoForm] = useState(false);
  const [addingToColumn, setAddingToColumn] = useState<'log' | 'thisWeek' | 'today' | null>(null);
  const [isFlipping, setIsFlipping] = useState(false);
  const [newHabit, setNewHabit] = useState('');
  const [showHabitInput, setShowHabitInput] = useState(false);
  const [showHabitTracker, setShowHabitTracker] = useState(false);
  const [editingHabit, setEditingHabit] = useState<Habit | null>(null);

  // User authentication query
  const { data: user } = useQuery<User>({
    queryKey: ['user'],
    queryFn: async () => {
      const token = localStorage.getItem('token');
      if (!token) throw new Error('No token found');
      return authApi.getMe(token);
    },
  });

  // Todos query
  const { data: todoList, isLoading } = useQuery<Todo[]>({
    queryKey: ['todos', user?.id],
    queryFn: async () => {
      const token = localStorage.getItem('token');
      if (!token || !user?.id) throw new Error('Authentication required');
      
      const response = await axios.get<Todo[]>(`${API_BASE_URL}/todos/user/${user.id}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      console.log('Raw API Response:', response);
      console.log('API Data:', response.data);
      
      // Ensure we're returning an array
      if (!Array.isArray(response.data)) {
        console.error('API did not return an array:', response.data);
        return [];
      }

      return response.data;
    },
    enabled: !!user?.id,
    initialData: [], // Provide initial data as empty array
    staleTime: 0, // Consider data fresh for 5 seconds
  });

  // Create todo mutation
  const createTodoMutation = useMutation({
    mutationFn: async (newTodo: Omit<Todo, 'id' | 'created_at' | 'updated_at' | 'completion_date'>) => {
      const token = localStorage.getItem('token');
      if (!token) throw new Error('No token found');
      
      const response = await axios.post<Todo>(
        `${API_BASE_URL}/todos`,
        newTodo,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['todos'] });
    },
  });

  // Update todo mutation
  const updateTodoMutation = useMutation({
    mutationFn: async ({ id, updates }: { id: number; updates: Partial<Todo> }) => {
      const token = localStorage.getItem('token');
      if (!token || !user?.id) throw new Error('No token found or user not authenticated');
      
      const response = await axios.put<Todo>(
        `${API_BASE_URL}/todos/${id}?user_id=${user.id}`,
        updates,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['todos'] });
    },
  });

  // Delete todo mutation
  const deleteTodoMutation = useMutation({
    mutationFn: async (id: number) => {
      const token = localStorage.getItem('token');
      if (!token || !user?.id) throw new Error('No token found or user not authenticated');
      
      await axios.delete(
        `${API_BASE_URL}/todos/${id}?user_id=${user.id}`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['todos'] });
    },
  });

  // Habits query
  const { data: habits = [] } = useQuery<Habit[]>({
    queryKey: ['habits', user?.id],
    queryFn: async () => {
      const token = localStorage.getItem('token');
      if (!token || !user?.id) throw new Error('Authentication required');
      
      const response = await axios.get<Habit[]>(`${API_BASE_URL}/daily-habits/user/${user.id}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      return response.data;
    },
    enabled: !!user?.id,
    initialData: [],
    staleTime: 0,
  });

  // Create habit mutation
  const createHabitMutation = useMutation({
    mutationFn: async (habit_name: string) => {
      const token = localStorage.getItem('token');
      if (!token || !user?.id) throw new Error('Authentication required');
      
      return axios.post(`${API_BASE_URL}/daily-habits`, {
        habit_name,
        user_id: user.id,
        start_day: new Date().toISOString().split('T')[0],
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['habits'] });
      setNewHabit('');
      setShowHabitInput(false);
    },
  });

  // Toggle habit completion mutation
  const toggleHabitMutation = useMutation({
    mutationFn: async (habitId: number) => {
      const token = localStorage.getItem('token');
      if (!token || !user?.id) throw new Error('Authentication required');
      
      return axios.post(`${API_BASE_URL}/daily-habits/${habitId}/complete`, null, {
        params: { user_id: user.id },
        headers: { Authorization: `Bearer ${token}` }
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['habits'] });
    },
  });

  const unmarkHabitMutation = useMutation({
    mutationFn: async (habitId: number) => {
      const token = localStorage.getItem('token');
      if (!token || !user?.id) throw new Error('Authentication required');

      return axios.post(`${API_BASE_URL}/daily-habits/${habitId}/uncomplete`, null, {
        params: { user_id: user.id },
        headers: { Authorization: `Bearer ${token}` }
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['habits'] });
    },
  });

  // Delete habit mutation
  const deleteHabitMutation = useMutation({
    mutationFn: async (habitId: number) => {
      const token = localStorage.getItem('token');
      if (!token || !user?.id) throw new Error('Authentication required');
      
      return axios.delete(`${API_BASE_URL}/daily-habits/${habitId}`, {
        params: { user_id: user.id },
        headers: { Authorization: `Bearer ${token}` }
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['habits'] });
    },
  });

  // Edit habit mutation
  const editHabitMutation = useMutation({
    mutationFn: async ({ habitId, habit_name }: { habitId: number; habit_name: string }) => {
      const token = localStorage.getItem('token');
      if (!token || !user?.id) throw new Error('Authentication required');
      
      return axios.put(
        `${API_BASE_URL}/daily-habits/${habitId}`,
        { habit_name },
        {
          params: { user_id: user.id },
          headers: { Authorization: `Bearer ${token}` }
        }
      );
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['habits'] });
      setNewHabit('');
      setShowHabitInput(false);
      setEditingHabit(null);
    },
  });

  const handleEditHabit = (habit: Habit) => {
    setEditingHabit(habit);
    setNewHabit(habit.habit_name);
    setShowHabitInput(true);
  };

  const handleEditTask = (task: Todo) => {
    setEditingTask(task);
    setShowTodoForm(true);
  };

  const handleTodoFormSubmit = (formData: TodoFormData) => {
    if (!user) return;

    if (editingTask) {
      const updates: Partial<Todo> = {
        ...formData,
        due_date: formData.due_date?.toISOString(),
        reminder_time: formData.reminder_time?.toISOString(),
      };
      updateTodoMutation.mutate({ id: editingTask.id, updates });
    } else {
      const newTodo: Omit<Todo, 'id' | 'created_at' | 'updated_at' | 'completion_date'> = {
        user_id: user.id,
        title: formData.title,
        description: formData.description,
        status: TodoStatus.PENDING,
        priority: formData.priority,
        is_recurring: formData.is_recurring,
        due_date: formData.due_date?.toISOString(),
        reminder_time: formData.reminder_time?.toISOString(),
        tags: formData.tags,
        checklist: [],
      };
      createTodoMutation.mutate(newTodo);
    }
    setShowTodoForm(false);
    setEditingTask(null);
  };

  const handleToggleTodo = (todo: Todo) => {
    const newStatus = todo.status === TodoStatus.COMPLETED ? TodoStatus.PENDING : TodoStatus.COMPLETED;
    updateTodoMutation.mutate({
      id: todo.id,
      updates: {
        status: newStatus,
        completion_date: newStatus === TodoStatus.COMPLETED ? new Date().toISOString() : undefined
      }
    });
  };

  const handleDeleteTodo = (id: number) => {
    deleteTodoMutation.mutate(id);
  };

  const renderTodoList = (todos: Todo[]) => {
    if (!todos || todos.length === 0) {
      return <div className="text-sm text-muted-foreground">No tasks</div>;
    }

    return (
      <div className="space-y-2">
        {todos.map((todo) => {
          return (
            <div
              key={todo.id}
              className={cn(
                "group relative rounded-lg border bg-card p-4 transition-all hover:border-border/50",
                todo.status === TodoStatus.COMPLETED && "bg-muted"
              )}
            >
              <div className="flex items-start gap-4">
                <Checkbox
                  name={`todo-${todo.id}`}
                  checked={todo.status === TodoStatus.COMPLETED}
                  onChange={() => handleToggleTodo(todo)}
                  darkMode={isDarkMode}
                  className="mt-1"
                />
                <div className="flex-1 space-y-1">
                  <div className="flex items-center gap-2">
                    <span className={cn(
                      "text-sm font-medium",
                      todo.status === TodoStatus.COMPLETED && "line-through text-muted-foreground"
                    )}>
                      {todo.title}
                    </span>
                    {todo.tags?.map((tag) => (
                      <Badge
                        key={tag}
                        variant="secondary"
                        className="text-xs"
                      >
                        {tag}
                      </Badge>
                    ))}
                  </div>
                  {todo.checklist && todo.checklist.length > 0 && (
                    <div className="mt-2">
                      <Progress
                        value={
                          (todo.checklist.filter(item => item.completed).length /
                            todo.checklist.length) *
                          100
                        }
                        className="h-1"
                      />
                      <div className="mt-2 text-xs text-muted-foreground">
                        {todo.checklist.filter(item => item.completed).length} of{" "}
                        {todo.checklist.length} subtasks completed
                      </div>
                    </div>
                  )}
                </div>
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button
                      variant="ghost"
                      className="h-8 w-8 p-0 opacity-0 group-hover:opacity-100"
                    >
                      <MoreVertical className="h-4 w-4" />
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end" className="w-[160px]">
                    <DropdownMenuItem onClick={() => handleEditTask(todo)}>
                      Edit
                    </DropdownMenuItem>
                    <DropdownMenuItem onClick={() => handleDeleteTodo(todo.id)}>
                      Delete
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              </div>
            </div>
          );
        })}
      </div>
    );
  };

  const handleAddHabit = () => {
    if (!newHabit.trim()) return;

    if (editingHabit) {
      editHabitMutation.mutate({
        habitId: editingHabit.id,
        habit_name: newHabit.trim()
      });
    } else {
      createHabitMutation.mutate(newHabit.trim());
    }
  };

  const toggleHabit = (id: number, isCompleted: boolean) => {
    if (isCompleted) {
      unmarkHabitMutation.mutate(id);
    } else {
      toggleHabitMutation.mutate(id);
    }
  };

  const deleteHabit = (id: number) => {
    deleteHabitMutation.mutate(id);
  };

  const handleFlipToHabits = () => {
    setIsFlipping(true);
    setShowHabitTracker(true);
    document.body.style.overflow = 'hidden';
    setTimeout(() => {
      setIsFlipping(false);
      document.body.style.overflow = '';
    }, 250);
  };

  const handleFlipToLog = () => {
    setShowHabitTracker(false);
    setIsFlipping(true);
    document.body.style.overflow = 'hidden';
    setTimeout(() => {
      setIsFlipping(false);
      document.body.style.overflow = '';
    }, 250);
  };

  const filterTodos = (type: 'log' | 'thisWeek' | 'today' | 'done') => {
    // Ensure we have an array to work with
    const todos = Array.isArray(todoList) ? todoList : [];
    
    const filtered = todos.filter(todo => {
      if (type === 'done') {
        return todo.status === TodoStatus.COMPLETED;
      }

      if (!todo.due_date || todo.status === TodoStatus.COMPLETED) {
        return false;
      }
      
      // Parse the due date string to a Date object
      const dueDate = new Date(todo.due_date);
      
      // Get current date at midnight in local timezone
      const now = new Date();
      const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
      
      // Calculate end of today in local timezone
      const endOfToday = new Date(today);
      endOfToday.setHours(23, 59, 59, 999);
      
      // Calculate end of week in local timezone
      const endOfWeek = new Date(today);
      endOfWeek.setDate(today.getDate() + 7);
      endOfWeek.setHours(23, 59, 59, 999);

      // Test each condition separately using timestamps for reliable comparison
      const isPastDue = dueDate < today; // New condition for past due tasks
      const isDueToday = dueDate >= today && dueDate <= endOfToday;
      const isDueThisWeek = dueDate > endOfToday && dueDate <= endOfWeek;
      const isDueLater = dueDate > endOfWeek;
      
      let result = false;
      switch (type) {
        case 'today':
          // Show both today's tasks and past due tasks in the Today column
          result = isDueToday || isPastDue;
          break;
        case 'thisWeek':
          result = isDueThisWeek;
          break;
        case 'log':
          result = isDueLater;
          break;
      }
      
      return result;
    });

    return filtered;
  };

  const renderTodoColumn = (type: 'log' | 'thisWeek' | 'today' | 'done', title: string) => {
    const columnTodos = filterTodos(type);

    if (type === 'log' && (showHabitTracker || isFlipping)) {
      return (
        <div className="h-[calc(100vh-190px)] w-full perspective-1000 -mt-4">
          <div className={cn(
            "relative h-full w-full [transition:transform_250ms_ease-in-out] [transform-style:preserve-3d]",
            showHabitTracker ? "[transform:rotateY(180deg)]" : ""
          )}>
            {/* Front side - Log */}
            <div className="absolute inset-0 w-full h-full rounded-lg border bg-card p-4 flex flex-col [backface-visibility:hidden]">
              <div className="mb-4 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Clock className="h-4 w-4 text-muted-foreground" />
                  <h3 className="font-medium">Log</h3>
                </div>
                <div className="flex gap-2">
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => handleFlipToHabits()}
                    className="text-muted-foreground hover:text-foreground"
                  >
                    <Repeat className="w-4 h-4" />
                  </Button>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => {
                      setAddingToColumn(type);
                      setShowTodoForm(true);
                    }}
                    className="text-muted-foreground hover:text-foreground"
                  >
                    <Plus className="w-4 h-4" />
                  </Button>
                </div>
              </div>
              <div className="flex-1 overflow-y-auto">
                {renderTodoList(columnTodos)}
              </div>
            </div>
            
            {/* Back side - Habits */}
            <div className="absolute inset-0 w-full h-full rounded-lg border bg-card p-4 flex flex-col [backface-visibility:hidden] [transform:rotateY(180deg)]">
              <div className="flex flex-col h-full w-full">
                <div className="mb-4 flex items-center justify-between">
                  <div className="flex flex-col gap-1">
                    <div className="flex items-center gap-2">
                      <div className="flex items-center gap-2">
                        <Repeat className="h-4 w-4 text-muted-foreground" />
                        <h3 className="font-medium">Daily Habits</h3>
                      </div>
                      <span className="text-sm text-muted-foreground">{habits.filter(h => h.is_completed).length}/{habits.length} Done</span>
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => handleFlipToLog()}
                      className="text-muted-foreground hover:text-foreground"
                    >
                      <ArrowLeft className="h-4 w-4" />
                    </Button>
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => setShowHabitInput(true)}
                      className="text-muted-foreground hover:text-foreground"
                    >
                      <Plus className="h-4 h-4" />
                    </Button>
                  </div>
                </div>

                {showHabitInput && (
                  <div className="flex gap-2 mb-4">
                    <Input
                      value={newHabit}
                      onChange={(e) => setNewHabit(e.target.value)}
                      placeholder="New habit..."
                      className="flex-1"
                      onKeyDown={(e) => e.key === 'Enter' && handleAddHabit()}
                    />
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => {
                        setShowHabitInput(false);
                        setEditingHabit(null);
                        setNewHabit('');
                      }}
                      className="text-muted-foreground hover:text-foreground"
                    >
                      <X className="h-4 w-4" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={handleAddHabit}
                      className="text-muted-foreground hover:text-foreground"
                    >
                      <Check className="h-4 w-4" />
                    </Button>
                  </div>
                )}

                <div className="flex-1 overflow-y-auto w-full">
                  <div className="space-y-2">
                    {habits.map((habit) => (
                      <div
                        key={habit.id}
                        className={cn(
                          "group relative rounded-lg border bg-card p-4 transition-all hover:border-border/50",
                          habit.is_completed && "bg-muted"
                        )}
                      >
                        <div className="flex items-start gap-4">
                          <Checkbox
                            name={`habit-${habit.id}`}
                            checked={habit.is_completed}
                            onChange={() => toggleHabit(habit.id, habit.is_completed)}
                            darkMode={isDarkMode}
                            className="mt-1"
                          />
                          <div className="flex-1 space-y-1">
                            <div className="flex items-center gap-2">
                              <span className={cn(
                                "text-sm font-medium",
                                habit.is_completed && "line-through text-muted-foreground"
                              )}>
                                {habit.habit_name}
                              </span>
                              {habit.current_streak > 0 && (
                                <div className="flex items-center gap-1 text-xs text-muted-foreground">
                                  <Repeat className="w-3 h-3" />
                                  <span>{habit.current_streak} day streak</span>
                                </div>
                              )}
                            </div>
                          </div>
                          <DropdownMenu>
                            <DropdownMenuTrigger asChild>
                              <Button
                                variant="ghost"
                                className="h-8 w-8 p-0 opacity-0 group-hover:opacity-100"
                              >
                                <MoreVertical className="h-4 w-4" />
                              </Button>
                            </DropdownMenuTrigger>
                            <DropdownMenuContent align="end" className="w-[160px]">
                              <DropdownMenuItem onClick={() => handleEditHabit(habit)}>
                                Edit
                              </DropdownMenuItem>
                              <DropdownMenuItem onClick={() => deleteHabit(habit.id)}>
                                Delete
                              </DropdownMenuItem>
                            </DropdownMenuContent>
                          </DropdownMenu>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      );
    }

    return (
      <div className="h-[calc(100vh-190px)] w-full rounded-lg border bg-card p-4 -mt-4 flex flex-col">
        <div className="mb-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            {type === 'log' && <Clock className="h-4 w-4 text-muted-foreground" />}
            {type === 'thisWeek' && <Eye className="h-4 w-4 text-muted-foreground" />}
            {type === 'today' && <Repeat className="h-4 w-4 text-muted-foreground" />}
            {type === 'done' && <Check className="h-4 w-4 text-muted-foreground" />}
            <h3 className="font-medium">{title}</h3>
          </div>
          <div className="flex gap-2">
            {type === 'log' && (
              <Button
                size="sm"
                variant="ghost"
                onClick={() => handleFlipToHabits()}
                className="text-muted-foreground hover:text-foreground"
              >
                <Repeat className="w-4 h-4" />
              </Button>
            )}
            {type !== 'done' && (
              <Button
                size="sm"
                variant="ghost"
                onClick={() => {
                  setAddingToColumn(type);
                  setShowTodoForm(true);
                }}
                className="text-muted-foreground hover:text-foreground"
              >
                <Plus className="w-4 h-4" />
              </Button>
            )}
          </div>
        </div>
        <div className="flex-1 overflow-y-auto">
          {renderTodoList(columnTodos)}
        </div>
      </div>
    );
  };

  if (!user) {
    return <div>Please log in to view todos</div>;
  }

  if (isLoading) {
    return <div>Loading todos...</div>;
  }

  return (
    <div className="grid grid-cols-4 gap-4 p-6 h-full w-full">
      <div className="col-span-4 mb-4 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <h2 className="text-lg font-semibold">Tasks</h2>
        </div>
        <Button 
          variant="outline" 
          size="sm" 
          className="gap-2" 
          onClick={() => {
            setEditingTask(null);
            setShowTodoForm(true);
          }}
        >
          <Plus className="h-4 w-4" />
          New Task
        </Button>
      </div>
      {renderTodoColumn('log', 'Log')}
      {renderTodoColumn('thisWeek', 'This Week')}
      {renderTodoColumn('today', 'Today')}
      {renderTodoColumn('done', 'Done')}

      {showTodoForm && (
        <TodoForm
          onClose={() => {
            setShowTodoForm(false);
            setEditingTask(null);
          }}
          user={user}
          todo={editingTask || undefined}
          onSubmit={handleTodoFormSubmit}
          onDelete={handleDeleteTodo}
        />
      )}
    </div>
  );
};

export default TodoList;