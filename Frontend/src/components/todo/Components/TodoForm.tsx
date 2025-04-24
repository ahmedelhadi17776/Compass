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
import { Todo, TodoPriority } from '@/components/todo/types-todo';
import { useCreateTodo, useDeleteTodo } from '../hooks';
import './TodoForm.css';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

interface TodoFormProps {
  onClose: () => void;
  user: User;
  todo?: Todo;
  onSubmit: (data: TodoFormData) => void;
  onDelete: (id: string) => void;
  currentListId: string;
  listId: string;
}

interface TodoFormData {
  title: string;
  description: string;
  due_date: Date | undefined;
  priority: TodoPriority;
  reminder_time: Date | undefined;
  is_recurring: boolean;
  tags: string[];
  list_id: string;
}

const TodoForm: React.FC<TodoFormProps> = ({
  onClose,
  user,
  todo,
  onSubmit,
  onDelete,
  currentListId,
  listId
}) => {
  const queryClient = useQueryClient();
  const [isClosing, setIsClosing] = useState(false);
  const [title, setTitle] = useState(todo?.title || '');
  const [description, setDescription] = useState(todo?.description || '');
  const [priority, setPriority] = useState<TodoPriority>(todo?.priority || TodoPriority.MEDIUM);
  const [dueDate, setDueDate] = useState<Date | undefined>(todo?.due_date ? new Date(todo.due_date) : undefined);
  const [reminderTime, setReminderTime] = useState<Date | undefined>(todo?.reminder_time ? new Date(todo.reminder_time) : undefined);
  const [isRecurring, setIsRecurring] = useState(todo?.is_recurring || false);
  const [selectedTags, setSelectedTags] = useState<string[]>(todo?.tags ? Object.keys(todo.tags) : []);
  const [newTag, setNewTag] = useState('');
  const [showTagInput, setShowTagInput] = useState(false);

  const createTodoMutation = useCreateTodo();
  const deleteTodoMutation = useDeleteTodo();

  // Initialize form with todo data if editing
  useEffect(() => {
    if (todo) {
      setTitle(todo.title || '');
      setDescription(todo.description || '');
      setPriority(todo.priority || TodoPriority.MEDIUM);
      setDueDate(todo.due_date ? new Date(todo.due_date) : undefined);
      setReminderTime(todo.reminder_time ? new Date(todo.reminder_time) : undefined);
      setIsRecurring(todo.is_recurring || false);
      setSelectedTags(todo.tags ? Object.keys(todo.tags) : []);
    }
  }, [todo]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!onSubmit) return;

    const formData: TodoFormData = {
      title,
      description,
      priority,
      due_date: dueDate,
      reminder_time: reminderTime,
      is_recurring: isRecurring,
      tags: selectedTags,
      list_id: listId
    };

    onSubmit(formData);
    onClose();
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
      setSelectedTags([...selectedTags, newTag.trim()]);
      setNewTag('');
      setShowTagInput(false);
    }
  };

  const handleRemoveTag = (tagToRemove: string) => {
    setSelectedTags(selectedTags.filter(tag => tag !== tagToRemove));
  };

  return (
    <div className={cn(
      "fixed inset-0 z-50 flex items-center justify-center bg-black/50",
      isClosing && "opacity-0 transition-opacity duration-300"
    )}>
      <div className="w-full max-w-md rounded-lg bg-card p-6">
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
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Todo title"
              required
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="description">Description</Label>
            <Textarea
              id="description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Todo description"
              className="min-h-[100px]"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>Due Date</Label>
              <div className="flex gap-2">
                <DatePicker
                  selected={dueDate}
                  onChange={(date: Date | null) => setDueDate(date || new Date())}
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
                  selected={reminderTime}
                  onChange={(date: Date | null) => setReminderTime(date || new Date())}
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
            <Select
              value={priority}
              onValueChange={(value: TodoPriority) => setPriority(value)}
            >
              <SelectTrigger>
                <SelectValue>
                  {priority === TodoPriority.HIGH && <ArrowUp className="h-4 w-4 inline mr-2" />}
                  {priority === TodoPriority.MEDIUM && <Minus className="h-4 w-4 inline mr-2" />}
                  {priority === TodoPriority.LOW && <ArrowDown className="h-4 w-4 inline mr-2" />}
                  {priority}
                </SelectValue>
              </SelectTrigger>
              <SelectContent>
                {Object.values(TodoPriority).map((p) => (
                  <SelectItem key={p} value={p}>
                    {p === TodoPriority.HIGH && <ArrowUp className="h-4 w-4 inline mr-2" />}
                    {p === TodoPriority.MEDIUM && <Minus className="h-4 w-4 inline mr-2" />}
                    {p === TodoPriority.LOW && <ArrowDown className="h-4 w-4 inline mr-2" />}
                    {p}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label>Tags</Label>
            <div className="flex flex-wrap gap-2">
              {(selectedTags || []).map((tag) => (
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