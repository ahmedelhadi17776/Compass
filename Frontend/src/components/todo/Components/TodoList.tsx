import React, { useState, useRef } from 'react';
import { Plus, X, MoreVertical, CalendarFold, Repeat, Check, ArrowLeft, CalendarSync, CalendarCheck, CalendarClock, ChevronDown } from 'lucide-react';
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
import { useTodos, useCreateTodo, useUpdateTodo, useDeleteTodo, useToggleTodoStatus, useHabits, useCreateHabit, useToggleHabit, useDeleteHabit, useUpdateHabit, useTodoLists, useCreateTodoList, useUpdateTodoList, useDeleteTodoList } from '../hooks';
import { Separator } from '@/components/ui/separator';

const TodoList: React.FC = () => {
  const { theme } = useTheme();
  const isDarkMode = theme === 'dark';
  const [editingTodo, setEditingTodo] = useState<Todo | null>(null);
  const [showTodoForm, setShowTodoForm] = useState(false);
  const [addingToColumn, setAddingToColumn] = useState<'log' | 'thisWeek' | 'today' | null>(null);
  const [isFlipping, setIsFlipping] = useState(false);
  const [newHabit, setNewHabit] = useState('');
  const [showHabitInput, setShowHabitInput] = useState(false);
  const [showHabitTracker, setShowHabitTracker] = useState(false);
  const [editingHabit, setEditingHabit] = useState<Habit | null>(null);
  
  // New state for managing multiple lists
  const [currentListId, setCurrentListId] = useState<string>('');
  const [showNewListInput, setShowNewListInput] = useState(false);
  const [newListName, setNewListName] = useState('');
  const newListInputRef = useRef<HTMLInputElement>(null);
  
  // User authentication query
  const { data: user } = useQuery<User>({
    queryKey: ['user'],
    queryFn: async () => {
      const token = localStorage.getItem('token');
      if (!token) throw new Error('No token found');
      return authApi.getMe();
    },
  });

  // Use the custom hooks
  const { data: todoLists = [] } = useTodoLists(user);
  const { data: habits = [] } = useHabits(user);
  const createTodoMutation = useCreateTodo();
  const updateTodoMutation = useUpdateTodo();
  const deleteTodoMutation = useDeleteTodo();
  const toggleTodoStatus = useToggleTodoStatus();
  const createHabitMutation = useCreateHabit();
  const toggleHabitMutation = useToggleHabit();
  const deleteHabitMutation = useDeleteHabit();
  const updateHabitMutation = useUpdateHabit();
  const createTodoListMutation = useCreateTodoList();
  const updateTodoListMutation = useUpdateTodoList();
  const deleteTodoListMutation = useDeleteTodoList();

  // Set default list ID on initial load
  React.useEffect(() => {
    if (todoLists.length > 0 && !currentListId) {
      const defaultList = todoLists.find(list => list.is_default);
      setCurrentListId(defaultList?.id || todoLists[0].id);
    }
  }, [todoLists, currentListId]);

  // Get current list and its todos
  const currentList = todoLists.find(list => list.id === currentListId);
  const todos = currentList?.todos || [];

  const handleEditHabit = (habit: Habit) => {
    setEditingHabit(habit);
    setNewHabit(habit.title);
    setShowHabitInput(true);
  };

  const handleEditTodo = (todo: Todo) => {
    setEditingTodo(todo);
    setShowTodoForm(true);
  };

  const handleTodoFormSubmit = (formData: TodoFormData) => {
    if (!user) return;

    if (editingTodo) {
      const updates: Partial<Todo> = {
        ...formData,
        due_date: formData.due_date?.toISOString() || null,
        reminder_time: formData.reminder_time?.toISOString() || null,
        tags: formData.tags?.reduce((acc, tag) => ({ ...acc, [tag]: {} }), {}),
        checklist: {},
        is_completed: editingTodo.is_completed
      };
      updateTodoMutation.mutate({ id: editingTodo.id, updates });
    } else {
      const newTodo = {
        user_id: user.id,
        list_id: currentListId === 'default' ? undefined : currentListId,
        title: formData.title,
        description: formData.description,
        status: TodoStatus.PENDING,
        priority: formData.priority,
        is_recurring: formData.is_recurring,
        due_date: formData.due_date?.toISOString() || null,
        reminder_time: formData.reminder_time?.toISOString() || null,
        tags: formData.tags?.reduce((acc, tag) => ({ ...acc, [tag]: {} }), {}),
        checklist: {},
        is_completed: false,
        linked_task_id: null,
        linked_calendar_event_id: null,
        recurrence_pattern: {}
      };
      createTodoMutation.mutate(newTodo);
    }
    setShowTodoForm(false);
    setEditingTodo(null);
  };

  const handleToggleTodo = (todo: Todo) => {
    toggleTodoStatus.mutate(todo);
  };

  const handleDeleteTodo = (id: string) => {
    deleteTodoMutation.mutate(id);
  };

  const renderTodoList = (todos: Todo[]) => {
    if (!todos || todos.length === 0) {
      return <div className="text-sm text-muted-foreground">No Todos</div>;
    }

    return (
      <div className="space-y-2">
        {todos.map((todo) => {
          return (
            <div
              key={todo.id}
              className={cn(
                "group relative rounded-lg border bg-card p-3 transition-all hover:border-border/50",
                todo.is_completed && "bg-muted"
              )}
            >
              <div className="flex items-start gap-4">
                <Checkbox
                  name={`todo-${todo.id}`}
                  checked={todo.is_completed}
                  onChange={() => handleToggleTodo(todo)}
                  darkMode={isDarkMode}
                  className="mt-0.5"
                />
                <div className="flex-1 space-y-2">
                  <div className="flex items-center">
                    <span className={cn(
                      "text-sm font-medium",
                      todo.is_completed && "line-through text-muted-foreground"
                    )}>
                      {todo.title}
                    </span>
                  </div>
                  <div className="flex flex-wrap items-center gap-2">
                    <PriorityIndicator priority={todo.priority || TodoPriority.MEDIUM} />
                    {todo.tags && typeof todo.tags === 'object' && Object.keys(todo.tags).map((tag) => (
                      <Badge
                        key={tag}
                        variant="default"
                        className="text-xs text-black hover:bg-white/100 transition-colors"
                      >
                        {tag}
                      </Badge>
                    ))}
                  </div>
                  {todo.checklist && typeof todo.checklist === 'object' && Object.entries(todo.checklist).map(([id, item]) => (
                    <div key={id} className="mt-2">
                      <Progress
                        value={item.completed ? 100 : 0}
                        className="h-1"
                      />
                      <div className="mt-2 text-xs text-muted-foreground">
                        {item.completed ? "Completed" : "Not completed"}
                      </div>
                    </div>
                  ))}
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
                    <DropdownMenuItem onClick={() => handleEditTodo(todo)}>
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
    if (!newHabit.trim() || !user) return;

    if (editingHabit) {
      updateHabitMutation.mutate({
        habitId: editingHabit.id,
        title: newHabit.trim()
      });
    } else {
      createHabitMutation.mutate({
        title: newHabit.trim(),
        description: '',
        start_day: new Date().toISOString(),
        user_id: user.id
      });
    }

    // Clear input and close form
    setNewHabit('');
    setShowHabitInput(false);
    setEditingHabit(null);
  };

  const toggleHabit = (habitId: string, isCompleted: boolean) => {
    toggleHabitMutation.mutate({ habitId, isCompleted });
  };

  const deleteHabit = (habitId: string) => {
    deleteHabitMutation.mutate(habitId);
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

  type TodoFilterType = 'log' | 'thisWeek' | 'today' | 'done';
  
  const filterTodos = (type: TodoFilterType): Todo[] => {
    // Ensure we have an array to work with
    if (!Array.isArray(todos)) {
      return [];
    }
    
    const filtered = todos.filter(todo => {
      // Handle completed todos first
      if (todo.is_completed) {
        return type === 'done';
      }

      // For non-completed todos, never show in done section
      if (type === 'done') {
        return false;
      }

      // If no due date, put it in the log
      if (!todo.due_date) {
        return type === 'log';
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
      const isPastDue = dueDate < today;
      const isDueToday = dueDate >= today && dueDate <= endOfToday;
      const isDueThisWeek = dueDate > endOfToday && dueDate <= endOfWeek;
      const isDueLater = dueDate > endOfWeek;
      
      switch (type) {
        case 'today':
          return isDueToday || isPastDue;
        case 'thisWeek':
          return isDueThisWeek;
        case 'log':
          return isDueLater || !todo.due_date;
        default:
          return false;
      }
    });

    return filtered;
  };

  const renderTodoColumn = (type: TodoFilterType, title: string) => {
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
                                {habit.title}
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
  };

  // Add new list handler
  const handleAddNewList = () => {
    if (!newListName.trim()) return;
    
    createTodoListMutation.mutate({
      name: newListName.trim(),
      description: '',
      is_default: false
    });
    
    setNewListName('');
    setShowNewListInput(false);
  };

  // Add delete list handler
  const handleDeleteList = (listId: string) => {
    deleteTodoListMutation.mutate(listId);
  };

  if (!user) {
    return <div>Please log in to view todos</div>;
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
                  className="flex items-center justify-between group"
                >
                  <span
                    onClick={() => handleListChange(list.id)}
                    className={cn(
                      "flex-1 cursor-pointer",
                      currentListId === list.id && "bg-muted"
                    )}
                  >
                    {list.name}
                  </span>
                  {!list.is_default && (
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDeleteList(list.id);
                      }}
                      className="h-8 w-8 p-0 opacity-0 group-hover:opacity-100"
                    >
                      <X className="h-4 w-4" />
                    </Button>
                  )}
                </DropdownMenuItem>
              ))}
              <DropdownMenuItem 
                className="border-t mt-1 pt-1 cursor-pointer text-primary font-medium"
                onClick={() => {
                  setShowNewListInput(true);
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
            setEditingTodo(null);
            setShowTodoForm(true);
          }}
        >
          <Plus className="h-4 w-4" />
          New Todo
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
            setEditingTodo(null);
          }}
          user={user}
          todo={editingTodo || undefined}
          onSubmit={handleTodoFormSubmit}
          onDelete={handleDeleteTodo}
          currentListId={currentListId}
          listId={currentListId}
        />
      )}
    </div>
  );
};

export default TodoList;