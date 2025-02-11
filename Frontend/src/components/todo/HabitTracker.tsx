import React, { useState } from 'react';
import { Repeat, Plus, X, ArrowLeft } from 'lucide-react';
import { Button } from "../ui/button";
import { Input } from "../ui/input";
import { Progress } from "../ui/progress";
import { Checkbox } from "../ui/checkbox";
import cn from 'classnames';

interface Habit {
  id: string;
  title: string;
  completed: boolean;
  streak: number;
}

interface HabitTrackerProps {
  onFlip: () => void;
}

const HabitTracker: React.FC<HabitTrackerProps> = ({ onFlip }) => {
  const [habits, setHabits] = useState<Habit[]>(() => {
    const saved = localStorage.getItem('habits');
    return saved ? JSON.parse(saved) : [];
  });
  const [newHabit, setNewHabit] = useState('');
  const [showInput, setShowInput] = useState(false);

  const saveHabits = (updatedHabits: Habit[]) => {
    localStorage.setItem('habits', JSON.stringify(updatedHabits));
    setHabits(updatedHabits);
  };

  const handleAddHabit = () => {
    if (!newHabit.trim()) return;

    const habit: Habit = {
      id: Math.random().toString(36).substr(2, 9),
      title: newHabit.trim(),
      completed: false,
      streak: 0,
    };

    saveHabits([...habits, habit]);
    setNewHabit('');
    setShowInput(false);
  };

  const toggleHabit = (id: string) => {
    const updatedHabits = habits.map(habit => {
      if (habit.id === id) {
        return {
          ...habit,
          completed: !habit.completed,
          streak: !habit.completed ? habit.streak + 1 : habit.streak - 1,
        };
      }
      return habit;
    });
    saveHabits(updatedHabits);
  };

  const deleteHabit = (id: string) => {
    const updatedHabits = habits.filter(habit => habit.id !== id);
    saveHabits(updatedHabits);
  };

  const completedCount = habits.filter(h => h.completed).length;
  const progress = habits.length > 0 ? (completedCount / habits.length) * 100 : 0;

  return (
    <div className="flex flex-col h-full w-full">
      <div className="mb-4 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Repeat className="h-4 w-4 text-muted-foreground" />
          <h3 className="font-medium">Daily Habits</h3>
        </div>
        <div className="flex flex-col items-end">
          <span className="text-sm text-muted-foreground">{completedCount}/{habits.length}</span>
          <span className="text-sm text-muted-foreground">Done</span>
        </div>
        <div className="flex gap-2">
          <Button
            size="sm"
            variant="ghost"
            onClick={onFlip}
            className="text-muted-foreground hover:text-foreground"
          >
            <ArrowLeft className="w-4 h-4" />
          </Button>
          <Button
            size="sm"
            variant="ghost"
            onClick={() => setShowInput(true)}
            className="text-muted-foreground hover:text-foreground"
          >
            <Plus className="w-4 h-4" />
          </Button>
        </div>
      </div>

      {showInput && (
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
            onClick={() => setShowInput(false)}
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
                  checked={habit.completed}
                  onCheckedChange={() => toggleHabit(habit.id)}
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
  );
};

export default HabitTracker;
