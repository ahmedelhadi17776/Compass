export interface Habit {
  id: number;
  user_id: number;
  habit_name: string;
  description?: string;
  start_day: string;
  end_day?: string;
  current_streak: number;
  longest_streak: number;
  is_completed: boolean;
  last_completed_date?: string;
  created_at: string;
  updated_at: string;
}

export interface HabitFormData {
  habit_name: string;
  description?: string;
  start_day: Date;
  end_day?: Date;
} 