import React, { useState } from 'react'
import TodoList from '../todo/TodoList'
import { Separator } from "@/components/ui/separator"

interface TasksProps {
  view?: 'create' | 'manage' | 'dependencies' | 'automation'
}

export function Tasks({ view }: TasksProps) {
  const [todos, setTodos] = useState(() => {
    const saved = localStorage.getItem('todos');
    return saved ? JSON.parse(saved) : [];
  });

  const handleAddTodo = (todo: any) => {
    const newTodo = { ...todo, id: Date.now().toString() };
    setTodos((prev: any[]) => {
      const updated = [...prev, newTodo];
      localStorage.setItem('todos', JSON.stringify(updated));
      return updated;
    });
  };

  const handleToggleTodo = (id: string) => {
    setTodos((prev: any[]) => {
      const updated = prev.map(todo => 
        todo.id === id ? { ...todo, completed: !todo.completed } : todo
      );
      localStorage.setItem('todos', JSON.stringify(updated));
      return updated;
    });
  };

  const handleDeleteTodo = (id: string) => {
    setTodos((prev: any[]) => {
      const updated = prev.filter(todo => todo.id !== id);
      localStorage.setItem('todos', JSON.stringify(updated));
      return updated;
    });
  };

  const handleUpdateTodo = (id: string, updates: any) => {
    setTodos((prev: any[]) => {
      const updated = prev.map(todo => 
        todo.id === id ? { ...todo, ...updates } : todo
      );
      localStorage.setItem('todos', JSON.stringify(updated));
      return updated;
    });
  };

  const handleReorderTodo = (startIndex: number, endIndex: number) => {
    setTodos((prev: any[]) => {
      const updated = Array.from(prev);
      const [removed] = updated.splice(startIndex, 1);
      updated.splice(endIndex, 0, removed);
      localStorage.setItem('todos', JSON.stringify(updated));
      return updated;
    });
  };

  return (
    <>
      <div className="flex-1">
        <TodoList 
          todos={todos}
          onAddTodo={handleAddTodo}
          onToggleTodo={handleToggleTodo}
          onDeleteTodo={handleDeleteTodo}
          onUpdateTodo={handleUpdateTodo}
          onReorderTodo={handleReorderTodo}
        />
      </div>
    </>
  )
}