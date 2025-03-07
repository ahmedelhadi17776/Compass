import React, { useState } from 'react';
import { Plus, X, ChevronUp, ChevronRight, ChevronDown, Tag, MoreVertical, Clock, Eye, Repeat, Check, ArrowLeft } from 'lucide-react';
import { DragDropContext, Draggable, Droppable } from 'react-beautiful-dnd';
import { isToday } from 'date-fns';
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

interface Tag {
  id: string;
  name: string;
  color: string;
}

interface Subtask {
  id: string;
  title: string;
  completed: boolean;
}

interface Todo {
  id: string;
  title: string;
  completed: boolean;
  priority: 'high' | 'medium' | 'low';
  tags: Tag[];
  subtasks: Subtask[];
  dueDate?: Date;
  color?: string;
}

interface TodoListProps {
  todos: Todo[];
  onAddTodo: (todo: Omit<Todo, 'id'>) => void;
  onToggleTodo: (id: string) => void;
  onDeleteTodo: (id: string) => void;
  onUpdateTodo: (id: string, updates: Partial<Todo>) => void;
  onReorderTodo: (startIndex: number, endIndex: number) => void;
}

const TodoList: React.FC<TodoListProps> = ({
  todos,
  onAddTodo,
  onToggleTodo,
  onDeleteTodo,
  onUpdateTodo,
  onReorderTodo,
}) => {
  const { data: user } = useQuery<User>({
    queryKey: ['user'],
    queryFn: async () => {
      const token = localStorage.getItem('token');
      if (!token) throw new Error('No token found');
      return authApi.getMe(token);
    },
  });

  const [newTodoTitle, setNewTodoTitle] = useState('');
  const [showQuickAdd, setShowQuickAdd] = useState(false);
  const [activeColumn, setActiveColumn] = useState<'log' | 'thisWeek' | 'today' | 'done'>('today');
  const [editingTask, setEditingTask] = useState<Todo | null>(null);
  const [showTodoForm, setShowTodoForm] = useState(false);
  const { theme } = useTheme();
  const isDarkMode = theme === 'dark';
  const [addingToColumn, setAddingToColumn] = useState<'log' | 'thisWeek' | 'today' | null>(null);
  const [isFlipping, setIsFlipping] = useState(false);
  const [habits, setHabits] = useState<{ id: string; title: string; completed: boolean; streak: number; }[]>(() => {
    const saved = localStorage.getItem('habits');
    return saved ? JSON.parse(saved) : [];
  });
  const [newHabit, setNewHabit] = useState('');
  const [showHabitInput, setShowHabitInput] = useState(false);
  const [showHabitTracker, setShowHabitTracker] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (newTodoTitle.trim()) {
      const now = new Date();
      let dueDate = new Date();
      
      // Set due date based on the column
      switch (addingToColumn) {
        case 'thisWeek': {
          // Set to tomorrow by default for week view
          dueDate = new Date();
          dueDate.setDate(now.getDate() + 1);
          dueDate.setHours(23, 59, 59, 999);
          break;
        }
        case 'log': {
          // Set to 8 days from now
          dueDate = new Date();
          dueDate.setDate(now.getDate() + 8);
          dueDate.setHours(23, 59, 59, 999);
          break;
        }
        case 'today':
        default: {
          // Set to end of today
          dueDate = new Date();
          dueDate.setHours(23, 59, 59, 999);
          break;
        }
      }

      onAddTodo({
        title: newTodoTitle.trim(),
        completed: false,
        priority: 'medium',
        tags: [],
        subtasks: [],
        dueDate: dueDate,
      });
      setNewTodoTitle('');
      setShowQuickAdd(false);
      setAddingToColumn(null);
    }
  };

  const handleDragEnd = (result: any) => {
    if (!result.destination) return;
    onReorderTodo(result.source.index, result.destination.index);
  };

  const getPriorityIcon = (priority: Todo['priority']) => {
    switch (priority) {
      case 'high':
        return <ChevronUp className="w-4 h-4 text-red-500" />;
      case 'medium':
        return <ChevronRight className="w-4 h-4 text-yellow-500" />;
      case 'low':
        return <ChevronDown className="w-4 h-4 text-green-500" />;
    }
  };

  const filterTodos = (type: 'log' | 'thisWeek' | 'today' | 'done') => {
    return todos.filter(todo => {
      if (type === 'done') return todo.completed;
      if (!todo.dueDate || todo.completed) return false;
      
      const dueDate = new Date(todo.dueDate);
      const today = new Date();
      today.setHours(0, 0, 0, 0);
      
      // Calculate 7 days from today
      const sevenDaysFromNow = new Date(today);
      sevenDaysFromNow.setDate(today.getDate() + 7);
      sevenDaysFromNow.setHours(23, 59, 59, 999);
      
      switch (type) {
        case 'today':
          return isToday(dueDate);
        case 'thisWeek': {
          // Show tasks due between tomorrow and next 7 days
          return dueDate > today && dueDate <= sevenDaysFromNow && !isToday(dueDate);
        }
        case 'log': {
          // Show tasks due beyond 7 days from now
          return dueDate > sevenDaysFromNow;
        }
        default:
          return false;
      }
    });
  };

  const renderTodoList = (todos: Todo[], type: 'log' | 'thisWeek' | 'today' | 'done') => {
    const isDoneColumn = type === 'done';

    return (
      <Droppable droppableId={type}>
        {(provided) => (
          <div
            ref={provided.innerRef}
            {...provided.droppableProps}
            className="space-y-2"
          >
            {todos.map((todo, index) => (
              <Draggable key={todo.id} draggableId={todo.id} index={index}>
                {(provided, snapshot) => (
                  <div
                    ref={provided.innerRef}
                    {...provided.draggableProps}
                    {...provided.dragHandleProps}
                    className={cn(
                      "group relative rounded-lg border bg-card p-4 transition-all hover:border-border/50",
                      snapshot.isDragging && "shadow-lg",
                      todo.completed && "bg-muted"
                    )}
                  >
                    <div className="flex items-start gap-4">
                      <Checkbox
                        name={`todo-${todo.id}`}
                        checked={todo.completed}
                        onChange={() => onToggleTodo(todo.id)}
                        darkMode={isDarkMode}
                        className="mt-1"
                      />
                      <div className="flex-1 space-y-1">
                        <div className="flex items-center gap-2">
                          <span className={cn(
                            "text-sm font-medium",
                            todo.completed && "line-through text-muted-foreground"
                          )}>
                            {todo.title}
                          </span>
                          {todo.tags.map((tag) => (
                            <Badge
                              key={tag.id}
                              variant="secondary"
                              className="text-xs"
                            >
                              {tag.name}
                            </Badge>
                          ))}
                        </div>
                        {todo.subtasks.length > 0 && (
                          <div className="mt-2">
                            <Progress
                              value={
                                (todo.subtasks.filter((st) => st.completed).length /
                                  todo.subtasks.length) *
                                100
                              }
                              className="h-1"
                            />
                            <div className="mt-2 text-xs text-muted-foreground">
                              {todo.subtasks.filter((st) => st.completed).length} of{" "}
                              {todo.subtasks.length} subtasks completed
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
                          <DropdownMenuItem onClick={() => onDeleteTodo(todo.id)}>
                            Delete
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </div>
                  </div>
                )}
              </Draggable>
            ))}
            {provided.placeholder}
          </div>
        )}
      </Droppable>
    );
  };

  const saveHabits = (updatedHabits: { id: string; title: string; completed: boolean; streak: number; }[]) => {
    localStorage.setItem('habits', JSON.stringify(updatedHabits));
    setHabits(updatedHabits);
  };

  const handleAddHabit = () => {
    if (!newHabit.trim()) return;

    const habit = {
      id: Math.random().toString(36).substr(2, 9),
      title: newHabit.trim(),
      completed: false,
      streak: 0,
    };

    saveHabits([...habits, habit]);
    setNewHabit('');
    setShowHabitInput(false);
  };

  const toggleHabit = (id: string) => {
    const updatedHabits = habits.map(habit => {
      if (habit.id === id) {
        return {
          ...habit,
          completed: !habit.completed,
          streak: !habit.completed ? habit.streak + 1 : habit.streak,
        };
      }
      return habit;
    });
    saveHabits(updatedHabits);
  };

  const deleteHabit = (id: string) => {
    saveHabits(habits.filter(habit => habit.id !== id));
  };

  const handleEditTask = (task: Todo) => {
    setEditingTask(task);
    setShowTodoForm(true);
  };

  const handleTodoFormSubmit = (taskData: { 
    title: string; 
    description?: string; 
    dueDate?: Date;
    priority: 'high' | 'medium' | 'low';
    tags: Tag[];
  }) => {
    if (editingTask) {
      onUpdateTodo(editingTask.id, {
        ...taskData,
        completed: editingTask.completed,
        subtasks: editingTask.subtasks
      });
    } else {
      onAddTodo({
        title: taskData.title,
        completed: false,
        priority: taskData.priority,
        tags: taskData.tags,
        subtasks: [],
        dueDate: taskData.dueDate
      });
    }
    setShowTodoForm(false);
    setEditingTask(null);
  };

  const handleAddSubtask = (todoId: string) => {
    const todo = todos.find(t => t.id === todoId);
    if (!todo) return;

    const subtaskTitle = window.prompt('Enter subtask title:');
    if (!subtaskTitle?.trim()) return;

    onUpdateTodo(todoId, {
      subtasks: [
        ...todo.subtasks,
        {
          id: Math.random().toString(36).substr(2, 9),
          title: subtaskTitle.trim(),
          completed: false
        }
      ]
    });
  };

  const handleToggleSubtask = (todoId: string, subtaskId: string) => {
    const todo = todos.find(t => t.id === todoId);
    if (!todo) return;

    onUpdateTodo(todoId, {
      subtasks: todo.subtasks.map(st =>
        st.id === subtaskId ? { ...st, completed: !st.completed } : st
      )
    });
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

  const getCompletedCount = (type: 'log' | 'thisWeek' | 'today' | 'done') => {
    if (type === 'today') {
      // For today's column, count tasks completed today and tasks from this week that are due today
      const todayColumnCompleted = todos.filter(t => t.completed && isToday(new Date(t.dueDate))).length;
      const weeklyTodayCompleted = todos.filter(t => 
        !todos.find(tt => tt.id === t.id && isToday(new Date(tt.dueDate))) && // Avoid counting tasks already in today's column
        isToday(new Date(t.dueDate)) && 
        t.completed
      ).length;
      return todayColumnCompleted + weeklyTodayCompleted;
    } else if (type === 'thisWeek') {
      // Count all completed tasks that are due this week (including today), including those in the done column
      return todos.filter(t => {
        const dueDate = new Date(t.dueDate);
        return (isToday(dueDate) || (dueDate > new Date() && dueDate <= new Date(new Date().getTime() + 7 * 24 * 60 * 60 * 1000))) && // Task is due this week or today
               t.completed;            // Task is completed
      }).length;
    } else if (type === 'log') {
      // Count completed tasks that are beyond 7 days, whether in log or done column
      return todos.filter(t => {
        if (!t.dueDate) return false;
        const dueDate = new Date(t.dueDate);
        const sevenDaysFromNow = new Date();
        sevenDaysFromNow.setDate(sevenDaysFromNow.getDate() + 7);
        sevenDaysFromNow.setHours(23, 59, 59, 999);
        return dueDate > sevenDaysFromNow && t.completed;
      }).length;
    }
    return todos.filter(t => t.completed).length;
  };

  const getTotalCount = (type: 'log' | 'thisWeek' | 'today' | 'done') => {
    if (type === 'today') {
      // For today's column, include tasks from this week that are due today
      const todayColumnTotal = todos.filter(t => isToday(new Date(t.dueDate))).length;
      const weeklyTodayTotal = todos.filter(t => 
        !todos.find(tt => tt.id === t.id && isToday(new Date(tt.dueDate))) && // Avoid counting tasks already in today's column
        isToday(new Date(t.dueDate))
      ).length;
      return todayColumnTotal + weeklyTodayTotal;
    } else if (type === 'thisWeek') {
      // Count all tasks that are due this week (including today)
      return todos.filter(t => {
        const dueDate = new Date(t.dueDate);
        return isToday(dueDate) || (dueDate > new Date() && dueDate <= new Date(new Date().getTime() + 7 * 24 * 60 * 60 * 1000)); // Task is due this week or today
      }).length;
    } else if (type === 'log') {
      // Count all tasks that are beyond 7 days
      return todos.filter(t => {
        if (!t.dueDate) return false;
        const dueDate = new Date(t.dueDate);
        const sevenDaysFromNow = new Date();
        sevenDaysFromNow.setDate(sevenDaysFromNow.getDate() + 7);
        sevenDaysFromNow.setHours(23, 59, 59, 999);
        return dueDate > sevenDaysFromNow;
      }).length;
    }
    return todos.length;
  };

  const renderTodoColumn = (type: 'log' | 'thisWeek' | 'today' | 'done', title: string) => {
    const columnTodos = filterTodos(type);
    const completedCount = getCompletedCount(type);
    const totalCount = getTotalCount(type);
    const completionPercentage = totalCount > 0 ? (completedCount / totalCount) * 100 : 0;

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
                {renderTodoList(columnTodos, type)}
              </div>
            </div>
            
            {/* Back side - Habits */}
            <div className="absolute inset-0 w-full h-full rounded-lg border bg-card p-4 flex flex-col [backface-visibility:hidden] [transform:rotateY(180deg)]">
              <div className="flex flex-col h-full w-full">
                <div className="mb-4 flex items-center justify-between">
                  <div className="flex flex-col gap-1">
                    <div className="flex items-center gap-2">
                      <Repeat className="h-4 w-4 text-muted-foreground" />
                      <h3 className="font-medium">Daily Habits</h3>
                    </div>
                    <span className="text-sm text-muted-foreground">{habits.filter(h => h.completed).length}/{habits.length} Done</span>
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
                      onClick={() => setShowHabitInput(false)}
                      className="text-muted-foreground hover:text-foreground"
                    >
                      <X className="h-4 w-4" />
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
                          habit.completed && "bg-muted"
                        )}
                      >
                        <div className="flex items-start gap-4">
                          <Checkbox
                            name={`habit-${habit.id}`}
                            checked={habit.completed}
                            onChange={() => toggleHabit(habit.id)}
                            darkMode={isDarkMode}
                            className="mt-1"
                          />
                          <div className="flex-1 space-y-1">
                            <div className="flex items-center gap-2">
                              <span className={cn(
                                "text-sm font-medium",
                                habit.completed && "line-through text-muted-foreground"
                              )}>
                                {habit.title}
                              </span>
                              {habit.streak > 0 && (
                                <div className="flex items-center gap-1 text-xs text-muted-foreground">
                                  <Repeat className="w-3 h-3" />
                                  <span>{habit.streak} day streak</span>
                                </div>
                              )}
                            </div>
                          </div>
                          <Button
                            variant="ghost"
                            size="sm"
                            className="h-8 w-8 p-0 opacity-0 group-hover:opacity-100"
                            onClick={() => deleteHabit(habit.id)}
                          >
                            <X className="h-4 w-4" />
                          </Button>
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
          {renderTodoList(columnTodos, type)}
        </div>
      </div>
    );
  };

  if (!user) {
    return <div>Please log in to view todos</div>;
  }

  return (
    <DragDropContext onDragEnd={handleDragEnd}>
      <div className="grid grid-cols-4 gap-4 p-6 h-full w-full">
        <div className="col-span-4 mb-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <h2 className="text-lg font-semibold">Tasks</h2>
          </div>
          <Dialog>
            <DialogTrigger asChild>
              <Button variant="outline" size="sm" className="gap-2">
                <Plus className="h-4 w-4" />
                New Task
              </Button>
            </DialogTrigger>
            <DialogContent className="bg-card">
              <DialogHeader>
                <DialogTitle>Add New Task</DialogTitle>
              </DialogHeader>
              <div className="pt-4">
                <TodoForm
                  onClose={() => {}}
                  user={user}
                />
              </div>
            </DialogContent>
          </Dialog>
        </div>
        {renderTodoColumn('log', 'Log')}
        {renderTodoColumn('thisWeek', 'This Week')}
        {renderTodoColumn('today', 'Today')}
        {renderTodoColumn('done', 'Done')}
      </div>
    </DragDropContext>
  );
};

export default TodoList;