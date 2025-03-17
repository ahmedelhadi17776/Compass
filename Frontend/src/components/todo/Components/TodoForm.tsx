import React, { useState, useEffect } from 'react';
import { X, Plus, ArrowUp, ArrowDown, Minus } from 'lucide-react';
import DatePicker from 'react-datepicker';
import "react-datepicker/dist/react-datepicker.css";
import { Button } from "../../ui/button";
import { Input } from "../../ui/input";
import { Textarea } from "../../ui/textarea";
import { Badge } from "../../ui/badge";
import { Label } from "../../ui/label";
import { cn } from "@/lib/utils";
import { useQueryClient } from '@tanstack/react-query';
import { User } from '@/api/auth';
import { Todo, TodoFormData, TodoPriority, TodoStatus } from '@/components/todo/types-todo';
import { useCreateTodo, useDeleteTodo } from '../hooks';
import './TodoForm.css';

interface TodoFormProps {
  onClose: () => void;
  user: User;
  todo?: Todo;
  onSubmit?: (formData: TodoFormData) => void;
  onDelete?: (todoId: number) => void;
}

const TodoForm: React.FC<TodoFormProps> = ({ onClose, user, todo, onSubmit, onDelete }) => {
  const queryClient = useQueryClient();
  const [isClosing, setIsClosing] = useState(false);
  const [formData, setFormData] = useState<Required<TodoFormData>>({
    title: '',
    description: '',
    priority: TodoPriority.MEDIUM,
    due_date: new Date(),
    reminder_time: new Date(),
    is_recurring: false,
    tags: [],
  });

  // Initialize form with todo data if editing
  useEffect(() => {
    if (todo) {
      setFormData({
        title: todo.title || '',
        description: todo.description || '',
        priority: todo.priority || TodoPriority.MEDIUM,
        due_date: todo.due_date ? new Date(todo.due_date) : new Date(),
        reminder_time: todo.reminder_time ? new Date(todo.reminder_time) : new Date(),
        is_recurring: todo.is_recurring || false,
        tags: todo.tags || [],
      });
    }
  }, [todo]);

  const createTodoMutation = useCreateTodo();
  const deleteTodoMutation = useDeleteTodo();

  const [newTag, setNewTag] = useState('');
  const [showTagInput, setShowTagInput] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setIsClosing(true);
    
    if (onSubmit) {
      onSubmit(formData);
      setTimeout(onClose, 300);
    } else {
      const newTodo = {
        user_id: user.id,
        title: formData.title,
        description: formData.description,
        status: TodoStatus.PENDING,
        priority: formData.priority,
        is_recurring: formData.is_recurring,
        due_date: formData.due_date.toISOString(),
        reminder_time: formData.reminder_time?.toISOString(),
        tags: formData.tags || [],
        checklist: [],
      };
      
      createTodoMutation.mutate(newTodo, {
        onSuccess: () => {
          handleClose();
        },
        onError: (error) => {
          console.error("Failed to create todo:", error);
          setIsClosing(false);
        }
      });
    }
  };

  const handleClose = () => {
    setIsClosing(true);
    setTimeout(onClose, 300);
  };

  const handleDelete = () => {
    if (!todo) return;
    
    setIsClosing(true);
    if (onDelete) {
      onDelete(todo.id);
      setTimeout(onClose, 300);
    } else {
      deleteTodoMutation.mutate(todo.id);
    }
  };

  const handleAddTag = (e: React.FormEvent) => {
    e.preventDefault();
    if (newTag.trim()) {
      setFormData(prev => ({
        ...prev,
        tags: [...(prev.tags || []), newTag.trim()]
      }));
      setNewTag('');
      setShowTagInput(false);
    }
  };

  const handleRemoveTag = (tagToRemove: string) => {
    setFormData(prev => ({
      ...prev,
      tags: (prev.tags || []).filter(tag => tag !== tagToRemove)
    }));
  };

  return (
    <div className={`fixed inset-0 bg-black/50 flex items-center justify-center z-50 
      ${isClosing ? 'animate-fade-out' : 'animate-fade-in'}`}
    >
      <div className={`bg-background rounded-lg shadow-xl w-full max-w-md p-6 relative 
        ${isClosing ? 'animate-slide-out' : 'animate-slide-in'}`}
      >
        <button
          onClick={handleClose}
          className="absolute right-4 top-4 text-muted-foreground hover:text-foreground"
        >
          <X className="w-5 h-5" />
        </button>

        <h2 className="text-xl font-semibold mb-6">
          {todo ? 'Update Todo' : 'Create New Todo'}
        </h2>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="title">Title</Label>
            <Input
              id="title"
              value={formData.title}
              onChange={e => setFormData(prev => ({ ...prev, title: e.target.value }))}
              placeholder="Todo title"
              required
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="description">Description</Label>
            <Textarea
              id="description"
              value={formData.description || ''}
              onChange={e => setFormData(prev => ({ ...prev, description: e.target.value }))}
              placeholder="Todo description"
              className="min-h-[100px]"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>Due Date</Label>
              <div className="flex gap-2">
                <DatePicker
                  selected={formData.due_date}
                  onChange={(date: Date | null) => setFormData(prev => ({ ...prev, due_date: date || new Date() }))}
                  showTimeSelect
                  dateFormat="MMMM d, yyyy h:mm aa"
                  className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label>Reminder</Label>
              <div className="flex gap-2">
                <DatePicker
                  selected={formData.reminder_time}
                  onChange={(date: Date | null) => setFormData(prev => ({ ...prev, reminder_time: date || new Date() }))}
                  showTimeSelect
                  dateFormat="MMMM d, yyyy h:mm aa"
                  className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                  placeholderText="Set reminder"
                />
              </div>
            </div>
          </div>

          <div className="space-y-2">
            <Label>Priority</Label>
            <div className="flex gap-2">
              {Object.values(TodoPriority).map((p) => (
                <Button
                  key={p}
                  type="button"
                  variant={formData.priority === p ? 'default' : 'outline'}
                  onClick={() => setFormData(prev => ({ ...prev, priority: p }))}
                  className={cn(
                    'capitalize flex items-center gap-2',
                    formData.priority === p && p === TodoPriority.HIGH && 'bg-red-500/20 hover:bg-red-500/30 text-red-500',
                    formData.priority === p && p === TodoPriority.MEDIUM && 'bg-yellow-500/20 hover:bg-yellow-500/30 text-yellow-500',
                    formData.priority === p && p === TodoPriority.LOW && 'bg-green-500/20 hover:bg-green-500/30 text-green-500'
                  )}
                >
                  {p === TodoPriority.HIGH && <ArrowUp className="h-4 w-4" />}
                  {p === TodoPriority.MEDIUM && <Minus className="h-4 w-4" />}
                  {p === TodoPriority.LOW && <ArrowDown className="h-4 w-4" />}
                  {p}
                </Button>
              ))}
            </div>
          </div>

          <div className="space-y-2">
            <Label>Tags</Label>
            <div className="flex flex-wrap gap-2">
              {(formData.tags || []).map((tag) => (
                <Badge key={tag} variant="outline">
                  {tag}
                  <button
                    type="button"
                    onClick={() => handleRemoveTag(tag)}
                    className="ml-2 hover:text-destructive"
                  >
                    <X className="h-3 w-3" />
                  </button>
                </Badge>
              ))}
              {showTagInput ? (
                <form onSubmit={handleAddTag} className="flex gap-2">
                  <Input
                    value={newTag}
                    onChange={(e) => setNewTag(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' && newTag.trim()) {
                        e.preventDefault();
                        handleAddTag(e);
                      }
                    }}
                    placeholder="Add tag"
                    className="w-32"
                  />
                  <Button type="button" variant="outline" size="sm" onClick={() => setShowTagInput(false)}>
                    <X className="h-4 w-4" />
                  </Button>
                </form>
              ) : (
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => setShowTagInput(true)}
                  className="gap-1"
                >
                  <Plus className="h-4 w-4" />
                  Add Tag
                </Button>
              )}
            </div>
          </div>

          <div className="flex justify-between gap-3 mt-6">
            {todo && (
              <Button
                type="button"
                onClick={handleDelete}
                variant="destructive"
                className="px-4 py-2"
                disabled={deleteTodoMutation.isPending}
              >
                {deleteTodoMutation.isPending ? 'Deleting...' : 'Delete Todo'}
              </Button>
            )}
            <div className={`flex gap-3 ${todo ? 'ml-auto' : 'w-full justify-end'}`}>
              <Button type="button" variant="outline" onClick={handleClose} className="px-4 py-2">
                Cancel
              </Button>
              <Button type="submit" className="px-4 py-2" disabled={createTodoMutation.isPending}>
                {createTodoMutation.isPending ? 'Saving...' : todo ? 'Update Todo' : 'Create Todo'}
              </Button>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
};

export default TodoForm;