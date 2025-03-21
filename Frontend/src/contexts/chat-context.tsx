import { createContext, ReactNode, useContext, useState } from 'react';
import { llmService } from '@/services/llmService';

export interface Message {
  id: string;
  text: string;
  sender: 'user' | 'assistant';
  timestamp: Date;
  intent?: string;
  target?: string;
  description?: string;
  rag_used?: boolean;
  cached?: boolean;
  confidence?: number;
}

interface ChatContextType {
  messages: Message[];
  isLoading: boolean;
  streamingText: string;
  addMessage: (message: Message) => void;
  sendMessage: (text: string) => Promise<void>;
  clearMessages: () => void;
  resetToDefault: () => void;
}

const defaultMessages: Message[] = [
  {
    id: "1",
    text: "👋 Hello! I'm your AI assistant. I can help you manage tasks, plan your day, and answer any questions about your workspace.",
    sender: 'assistant',
    timestamp: new Date(),
  }
];

const ChatContext = createContext<ChatContextType | undefined>(undefined);

export const ChatProvider = ({ children }: { children: ReactNode }) => {
  const [messages, setMessages] = useState<Message[]>(defaultMessages);
  const [isLoading, setIsLoading] = useState(false);
  const [streamingText, setStreamingText] = useState('');

  const addMessage = (message: Message) => {
    const messageWithId = {
      ...message,
      id: message.id || Date.now().toString() + Math.random().toString(36).substring(2, 9),
    };
    setMessages(prev => [...prev, messageWithId]);
  };

  const clearMessages = () => {
    setMessages(defaultMessages);
  };

  const resetToDefault = () => {
    setMessages(defaultMessages);
  };

  const sendMessage = async (text: string) => {
    if (!text.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      text: text.trim(),
      sender: 'user',
      timestamp: new Date(),
    };
    
    addMessage(userMessage);
    setIsLoading(true);

    try {
      const response = await llmService.generateResponse({
        prompt: text,
        context: {
          messages: messages.slice(-5) // Send last 5 messages for context
        }
      });

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        text: response.response, // Updated to match backend response
        sender: 'assistant',
        timestamp: new Date(),
        intent: response.intent,
        target: response.target,
        description: response.description,
        rag_used: response.rag_used,
        cached: response.cached,
        confidence: response.confidence
      };
      
      addMessage(assistantMessage);
    } catch (error) {
      console.error('Error sending message:', error);
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        text: "Sorry, I encountered an error while processing your request. Please try again later.",
        sender: 'assistant',
        timestamp: new Date(),
      };
      
      addMessage(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <ChatContext.Provider
      value={{
        messages,
        isLoading,
        streamingText,
        addMessage,
        sendMessage,
        clearMessages,
        resetToDefault,
      }}
    >
      {children}
    </ChatContext.Provider>
  );
};

export const useChat = (): ChatContextType => {
  const context = useContext(ChatContext);
  if (context === undefined) {
    throw new Error('useChat must be used within a ChatProvider');
  }
  return context;
}; 