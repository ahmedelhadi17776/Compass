export interface Habit {
  id: string;
  title: string;
  description: string;
  start_day: string;
  end_day: string | null;
  current_streak: number;
  longest_streak: number;
  is_completed: boolean;
  last_completed_date: string | null;
  created_at: string;
  user_id: string;
  updated_at: string;
}

export interface HabitFormData {
  habit_name: string;
  description?: string;
  start_day: Date;
  end_day?: Date;
} 