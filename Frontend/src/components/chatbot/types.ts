export interface Message {
  text: string;
  sender: 'user' | 'assistant' | 'bot';
  timestamp: Date;
}

export interface Position {
  x: number;
  y: number;
} 