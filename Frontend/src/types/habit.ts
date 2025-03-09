export interface Habit {
  id: string;
  title: string;
  completed: boolean;
  streak: number;
}

export interface HabitFormData {
  title: string;
} 