import React, { useState } from 'react';
import { X, Plus, Tag as TagIcon, CalendarIcon } from 'lucide-react';
import DatePicker from 'react-datepicker';
import "react-datepicker/dist/react-datepicker.css";
import { Button } from "../ui/button";
import { Input } from "../ui/input";
import { Textarea } from "../ui/textarea";
import { Badge } from "../ui/badge";
import { Label } from "../ui/label";
import { cn } from "@/lib/utils";

interface Tag {
  id: string;
  name: string;
  color: string;
}

interface TaskFormProps {
  onClose: () => void;
  onSubmit: (task: { 
    title: string; 
    description?: string; 
    dueDate?: Date;
    priority: 'high' | 'medium' | 'low';
    tags: Tag[];
  }) => void;
  task?: {
    title: string;
    description?: string;
    dueDate?: Date;
    priority: 'high' | 'medium' | 'low';
    tags: Tag[];
  } | null;
  column?: 'log' | 'thisWeek' | 'today';
}

const TaskForm: React.FC<TaskFormProps> = ({ onClose, onSubmit, task, column }) => {
  const [title, setTitle] = useState(task?.title || '');
  const [description, setDescription] = useState(task?.description || '');
  const [startTime, setStartTime] = useState<Date>(() => {
    if (task?.dueDate) return task.dueDate;
    
    const now = new Date();
    let dueDate = new Date();
    
    switch (column) {
      case 'thisWeek':
        dueDate.setDate(now.getDate() + (6 - now.getDay()));
        dueDate.setHours(23, 59, 59, 999);
        break;
      case 'log':
        dueDate.setDate(now.getDate() + 14);
        break;
      case 'today':
      default:
        dueDate.setHours(23, 59, 59, 999);
        break;
    }
    
    return dueDate;
  });
  const [priority, setPriority] = useState<'high' | 'medium' | 'low'>(task?.priority || 'medium');
  const [tags, setTags] = useState<Tag[]>(task?.tags || []);
  const [newTagName, setNewTagName] = useState('');
  const [showTagInput, setShowTagInput] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) return;

    onSubmit({
      title: title.trim(),
      description: description.trim(),
      dueDate: startTime,
      priority,
      tags
    });
  };

  const handleRemoveTag = (tagId: string) => {
    setTags(tags.filter(tag => tag.id !== tagId));
  };

  const handleAddTag = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTagName.trim()) return;

    const tagColors = [
      '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEEAD',
      '#D4A5A5', '#9B59B6', '#3498DB', '#F1C40F', '#2ECC71'
    ];
    const randomColor = tagColors[Math.floor(Math.random() * tagColors.length)];
    
    const newTag: Tag = {
      id: Math.random().toString(36).substr(2, 9),
      name: newTagName.trim(),
      color: randomColor
    };

    setTags([...tags, newTag]);
    setNewTagName('');
    setShowTagInput(false);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="space-y-2">
        <Label htmlFor="title">Title</Label>
        <Input
          id="title"
          type="text"
          placeholder="Task title"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          className="w-full"
        />
      </div>

      <div className="space-y-2">
        <Label htmlFor="description">Description</Label>
        <Textarea
          id="description"
          placeholder="Task description"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          className="w-full min-h-[100px]"
        />
      </div>

      <div className="space-y-2">
        <Label>Due Date</Label>
        <div className="flex items-center gap-2">
          <DatePicker
            selected={startTime}
            onChange={(date) => setStartTime(date || new Date())}
            showTimeSelect
            dateFormat="MMMM d, yyyy h:mm aa"
            className="w-full rounded-md border border-input bg-card px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 text-card-foreground"
          />
          <Button
            type="button"
            variant="outline"
            size="icon"
            onClick={() => setStartTime(new Date())}
          >
            <CalendarIcon className="h-4 w-4" />
          </Button>
        </div>
      </div>

      <div className="space-y-2">
        <Label>Priority</Label>
        <div className="flex gap-2">
          {(['high', 'medium', 'low'] as const).map((p) => (
            <Button
              key={p}
              type="button"
              variant={priority === p ? 'default' : 'outline'}
              onClick={() => setPriority(p)}
              className={cn(
                'capitalize',
                priority === p && p === 'high' && 'bg-[#4A2020] hover:bg-[#5A2525] text-red-400',
                priority === p && p === 'medium' && 'bg-[#3D3420] hover:bg-[#4D4225] text-yellow-400',
                priority === p && p === 'low' && 'bg-[#203D20] hover:bg-[#254D25] text-green-400'
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
          {tags.map((tag) => (
            <Badge
              key={tag.id}
              variant="outline"
              style={{ 
                backgroundColor: `color-mix(in srgb, ${tag.color} 10%, var(--card))`,
                borderColor: tag.color,
                color: tag.color
              }}
            >
              {tag.name}
              <button
                type="button"
                onClick={() => handleRemoveTag(tag.id)}
                className="ml-2 hover:text-destructive"
              >
                <X className="h-3 w-3" />
              </button>
            </Badge>
          ))}
          {showTagInput ? (
            <form onSubmit={handleAddTag} className="flex gap-2">
              <Input
                type="text"
                value={newTagName}
                onChange={(e) => setNewTagName(e.target.value)}
                placeholder="Tag name"
                className="w-32"
              />
              <Button type="submit" size="sm" variant="outline">
                Add
              </Button>
              <Button
                type="button"
                size="sm"
                variant="outline"
                onClick={() => setShowTagInput(false)}
              >
                Cancel
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
              <Plus className="h-3 w-3" />
              Add Tag
            </Button>
          )}
        </div>
      </div>

      <div className="flex justify-end gap-2 pt-4">
        <Button type="button" variant="outline" onClick={onClose}>
          Cancel
        </Button>
        <Button type="submit">Create Task</Button>
      </div>
    </form>
  );
};

export default TaskForm;