import { createContext, ReactNode, useContext, useState, useEffect } from 'react';
import { llmService } from '@/services/llmService';
import { useAuth } from '@/hooks/useAuth';

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

const getTimeBasedGreeting = () => {
  const hour = new Date().getHours();
  if (hour < 12) return { text: 'Good morning', emoji: '☀️' };
  if (hour < 18) return { text: 'Good afternoon', emoji: '⛅' };
  return { text: 'Good evening', emoji: '🌙' };
};

// Initial empty default message that will be populated with user data
const defaultMessages: Message[] = [
  {
    id: "1",
    text: "✨ Hello! I'm Iris, Your AI assistant. I can help you manage tasks, plan your day, and answer any questions about your workspace.",
    sender: 'assistant',
    timestamp: new Date(),
  }
];

const ChatContext = createContext<ChatContextType | undefined>(undefined);

export const ChatProvider = ({ children }: { children: ReactNode }) => {
  const { user } = useAuth();
  const [messages, setMessages] = useState<Message[]>(defaultMessages);
  const [isLoading, setIsLoading] = useState(false);
  const [streamingText, setStreamingText] = useState('');

  // Update default message when user data is available
  useEffect(() => {
    if (user) {
      const greeting = getTimeBasedGreeting();
      const userName = user.first_name || '';
      const welcomeMessage = {
        id: "1",
        text: `${greeting.emoji} ${greeting.text}${userName ? `, ${userName}` : ''}! I'm Iris, Your AI assistant. I can help you manage tasks, plan your day, and answer any questions about your workspace.`,
        sender: 'assistant' as const,
        timestamp: new Date(),
      };
      
      setMessages(prev => {
        // Replace the first message if it exists, otherwise add the welcome message
        if (prev.length > 0 && prev[0].id === "1") {
          return [welcomeMessage, ...prev.slice(1)];
        }
        return [welcomeMessage, ...prev];
      });
    }
  }, [user]);

  const addMessage = (message: Message) => {
    const messageWithId = {
      ...message,
      id: message.id || Date.now().toString() + Math.random().toString(36).substring(2, 9),
    };
    setMessages(prev => [...prev, messageWithId]);
  };

  const clearMessages = () => {
    // Create a personalized default message
    const greeting = getTimeBasedGreeting();
    const userName = user?.first_name || '';
    const welcomeMessage = {
      id: "1",
      text: `${greeting.emoji} ${greeting.text}${userName ? `, ${userName}` : ''}! I'm Iris, Your AI assistant. I can help you manage tasks, plan your day, and answer any questions about your workspace.`,
      sender: 'assistant' as const,
      timestamp: new Date(),
    };
    
    setMessages([welcomeMessage]);
  };

  const resetToDefault = () => {
    // Create a personalized default message
    const greeting = getTimeBasedGreeting();
    const userName = user?.first_name || '';
    const welcomeMessage = {
      id: "1",
      text: `${greeting.emoji} ${greeting.text}${userName ? `, ${userName}` : ''}! I'm Iris, Your AI assistant. I can help you manage tasks, plan your day, and answer any questions about your workspace.`,
      sender: 'assistant' as const,
      timestamp: new Date(),
    };
    
    setMessages([welcomeMessage]);
  };

  const getPreviousMessages = (count: number = 5) => {
    // Get the most recent messages (excluding the default welcome message)
    const recentMessages = messages.filter(m => m.id !== "1").slice(-count);
    return recentMessages.map(msg => ({
      sender: msg.sender,
      text: msg.text
    }));
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
      // Get previous messages to maintain conversation context
      const previousMessages = getPreviousMessages();
      
      const response = await llmService.generateResponse({
        prompt: text,
        previous_messages: previousMessages,
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