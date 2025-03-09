import React, { useState, useEffect } from 'react';
import { X, Plus } from 'lucide-react';
import DatePicker from 'react-datepicker';
import "react-datepicker/dist/react-datepicker.css";
import { Button } from "../ui/button";
import { Input } from "../ui/input";
import { Textarea } from "../ui/textarea";
import { Badge } from "../ui/badge";
import { Label } from "../ui/label";
import { cn } from "@/lib/utils";
import { useMutation, useQueryClient } from '@tanstack/react-query';
import axios from 'axios';
import authApi, { User } from '@/api/auth';
import { Todo, TodoFormData, TodoPriority } from '@/types/todo';

const API_BASE_URL = 'http://localhost:8000';

interface TodoFormProps {
  onClose: () => void;
  user: User;
  todo?: Todo;
  onSubmit?: (formData: TodoFormData) => void;
}

const TodoForm: React.FC<TodoFormProps> = ({ onClose, user, todo, onSubmit }) => {
  const queryClient = useQueryClient();
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

  const mutation = useMutation({
    mutationFn: async (data: Required<TodoFormData>) => {
      const token = localStorage.getItem('token');
      return axios.post<TodoFormData>(`${API_BASE_URL}/todos`, {
        ...data,
        user_id: user.id,
        due_date: data.due_date.toISOString(),
        reminder_time: data.reminder_time?.toISOString(),
        tags: data.tags || [],
        checklist: [],
        recurrence_pattern: {},
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['todos'] });
      onClose();
    },
    onError: (error) => {
      console.error("Failed to create todo:", error);
    },
  });

  const [newTag, setNewTag] = useState('');
  const [showTagInput, setShowTagInput] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (onSubmit) {
      onSubmit(formData);
    } else {
      mutation.mutate(formData);
    }
  };

  const handleCancel = (e: React.MouseEvent) => {
    e.preventDefault();
    onClose();
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
              className="w-full rounded-md border border-input bg-card px-3 py-2 text-sm"
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
              className="w-full rounded-md border border-input bg-card px-3 py-2 text-sm"
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
                'capitalize',
                formData.priority === p && p === TodoPriority.HIGH && 'bg-red-500/20 hover:bg-red-500/30 text-red-500',
                formData.priority === p && p === TodoPriority.MEDIUM && 'bg-yellow-500/20 hover:bg-yellow-500/30 text-yellow-500',
                formData.priority === p && p === TodoPriority.LOW && 'bg-green-500/20 hover:bg-green-500/30 text-green-500'
              )}
            >
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

      <div className="flex justify-end gap-2">
        <Button type="button" variant="outline" onClick={handleCancel}>
          Cancel
        </Button>
        <Button type="submit">
          {todo ? 'Update' : 'Create'} Todo
        </Button>
      </div>
    </form>
  );
};

export default TodoForm;