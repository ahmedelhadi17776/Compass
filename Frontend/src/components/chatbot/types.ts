export interface Message {
  text: string;
  sender: 'user' | 'bot';
  timestamp: Date;
}

export interface Position {
  x: number;
  y: number;
} 