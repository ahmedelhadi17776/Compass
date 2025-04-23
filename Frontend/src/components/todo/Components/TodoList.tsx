import React, { useState, useRef } from 'react';
import { Plus, X, MoreVertical, CalendarFold, Repeat, Check, ArrowLeft, CalendarSync, CalendarCheck, CalendarClock, ChevronDown, ListFilter } from 'lucide-react';
import PriorityIndicator from './PriorityIndicator';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "../../ui/dropdown-menu";
import { Button } from "../../ui/button";
import { Input } from "../../ui/input";
import { Progress } from "../../ui/progress";
import Checkbox from "../../ui/checkbox";
import TodoForm from './TodoForm';
import { Badge } from "../../ui/badge";
import cn from 'classnames';
import { useTheme } from '@/contexts/theme-provider';
import { useQuery } from '@tanstack/react-query';
import authApi, { User } from '@/api/auth';
import { Habit } from '@/components/todo/types-habit';
import { Todo, TodoFormData, TodoStatus, TodoPriority } from '@/components/todo/types-todo';
import { useTodos, useCreateTodo, useUpdateTodo, useDeleteTodo, useToggleTodoStatus, useHabits, useCreateHabit, useToggleHabit, useDeleteHabit, useUpdateHabit } from '../hooks';
import { Separator } from '@/components/ui/separator';

const TodoList: React.FC = () => {
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
  
  // New state for managing multiple lists
  const [currentListId, setCurrentListId] = useState<string>('default');
  const [showNewListInput, setShowNewListInput] = useState(false);
  const [newListName, setNewListName] = useState('');
  const newListInputRef = useRef<HTMLInputElement>(null);
  
  // Mock data for lists - to be replaced with API data later
  const todoLists = [
    { id: 'default', name: 'Default List' },
    { id: 'work', name: 'Work' },
    { id: 'personal', name: 'Personal' },
    { id: 'shopping', name: 'Shopping' },
    { id: 'projects', name: 'Projects' }
  ];

  // User authentication query
  const { data: user } = useQuery<User>({
    queryKey: ['user'],
    queryFn: async () => {
      const token = localStorage.getItem('token');
      if (!token) throw new Error('No token found');
      return authApi.getMe(token);
    },
  });

  // Use the custom hooks
  const { data: todoList, isLoading } = useTodos(user);
  const { data: habits = [] } = useHabits(user);
  const createTodoMutation = useCreateTodo();
  const updateTodoMutation = useUpdateTodo();
  const deleteTodoMutation = useDeleteTodo();
  const toggleTodoStatus = useToggleTodoStatus();
  const createHabitMutation = useCreateHabit();
  const toggleHabitMutation = useToggleHabit();
  const deleteHabitMutation = useDeleteHabit();
  const updateHabitMutation = useUpdateHabit();

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
        // In future when backend supports multiple lists, we would add list_id: currentListId here
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
        // In future when backend supports multiple lists, we would add list_id: currentListId here
      };
      createTodoMutation.mutate(newTodo);
    }
    setShowTodoForm(false);
    setEditingTask(null);
  };

  const handleToggleTodo = (todo: Todo) => {
    toggleTodoStatus(todo);
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
                "group relative rounded-lg border bg-card p-3 transition-all hover:border-border/50",
                todo.status === TodoStatus.COMPLETED && "bg-muted"
              )}
            >
              <div className="flex items-start gap-4">
                <Checkbox
                  name={`todo-${todo.id}`}
                  checked={todo.status === TodoStatus.COMPLETED}
                  onChange={() => handleToggleTodo(todo)}
                  darkMode={isDarkMode}
                  className="mt-0.5"
                />
                <div className="flex-1 space-y-2">
                  <div className="flex items-center">
                    <span className={cn(
                      "text-sm font-medium",
                      todo.status === TodoStatus.COMPLETED && "line-through text-muted-foreground"
                    )}>
                      {todo.title}
                    </span>
                  </div>
                  <div className="flex flex-wrap items-center gap-2">
                    <PriorityIndicator priority={todo.priority || TodoPriority.MEDIUM} />
                    {todo.tags?.map((tag) => (
                      <Badge
                        key={tag}
                        variant="default"
                        className="text-xs text-black hover:bg-white/100 transition-colors"
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
      updateHabitMutation.mutate({
        habitId: editingHabit.id,
        habit_name: newHabit.trim()
      });
    } else {
      createHabitMutation.mutate(newHabit.trim());
    }
  };

  const toggleHabit = (id: number, isCompleted: boolean) => {
    toggleHabitMutation.mutate({ habitId: id, isCompleted });
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
                  <CalendarFold className="h-4 w-4 text-muted-foreground" />
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
                        <CalendarSync className="h-4 w-4 text-muted-foreground" />
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
                            className="mt-0.5"
                          />
                          <div className="flex-1 space-y-2">
                            <div className="flex items-center">
                              <span className={cn(
                                "text-sm font-medium",
                                habit.is_completed && "line-through text-muted-foreground"
                              )}>
                                {habit.habit_name}
                              </span>
                            </div>
                            {habit.current_streak > 0 && (
                              <div className="flex items-center gap-1 text-xs text-muted-foreground">
                                <Repeat className="w-3 h-3" />
                                <span>{habit.current_streak} day streak</span>
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
            {type === 'log' && <CalendarFold className="h-4 w-4 text-muted-foreground" />}
            {type === 'thisWeek' && <CalendarClock className="h-4 w-4 text-muted-foreground" />}
            {type === 'today' && <CalendarCheck className="h-4 w-4 text-muted-foreground" />}
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

  // Add list selection handler
  const handleListChange = (listId: string) => {
    setCurrentListId(listId);
    // In future implementation, this would fetch the todos for the selected list from the backend
  };

  // Add new list handler
  const handleAddNewList = () => {
    if (!newListName.trim()) return;
    
    // Create a unique ID for the list (in a real app, this would come from the backend)
    const listId = `list-${Date.now()}`;
    
    // Add the new list to the todoLists array
    const newList = {
      id: listId,
      name: newListName.trim()
    };
    
    todoLists.push(newList);
    
    // Set the current list to the newly created one
    setCurrentListId(listId);
    
    // Reset state
    setNewListName('');
    setShowNewListInput(false);
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
        <div className="flex items-baseline gap-2">
          <h2 className="text-xl font-semibold">Todos & Habits</h2>
          <Separator orientation="vertical" className="h-5 my-auto z-[100] -mr-1" />
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button size="sm" className="-ml-2 bg-[#1a1a1a] text-white">
                {todoLists.find(list => list.id === currentListId)?.name}
                <ChevronDown className="h-4 w-4 opacity-70" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="center" className="w-[180px]">
              {todoLists.map(list => (
                <DropdownMenuItem 
                  key={list.id}
                  onClick={() => handleListChange(list.id)}
                  className={cn(
                    "cursor-pointer",
                    currentListId === list.id && "bg-muted"
                  )}
                >
                  {list.name}
                </DropdownMenuItem>
              ))}
              <DropdownMenuItem 
                className="border-t mt-1 pt-1 cursor-pointer text-primary font-medium"
                onClick={() => {
                  setShowNewListInput(true);
                  // Focus the input after it's rendered
                  setTimeout(() => {
                    newListInputRef.current?.focus();
                  }, 0);
                }}
              >
                <Plus className="h-4 w-4 mr-2" />
                Create new list
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
          
          {/* New list input */}
          {showNewListInput && (
            <div className="flex gap-2 items-center">
              <Input
                ref={newListInputRef}
                value={newListName}
                onChange={(e) => setNewListName(e.target.value)}
                placeholder="List name..."
                className="w-40 h-8"
                onKeyDown={(e) => e.key === 'Enter' && handleAddNewList()}
              />
              <Button
                variant="ghost"
                size="icon"
                onClick={() => setShowNewListInput(false)}
                className="h-8 w-8 p-0"
              >
                <X className="h-4 w-4" />
              </Button>
              <Button
                variant="ghost"
                size="icon"
                onClick={handleAddNewList}
                className="h-8 w-8 p-0"
              >
                <Check className="h-4 w-4" />
              </Button>
            </div>
          )}
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
          // Pass the current list ID to the form - to be implemented in TodoForm
          currentListId={currentListId}
        />
      )}
    </div>
  );
};

export default TodoList;