import React, { createContext, ReactNode, useContext, useState, useEffect } from 'react';
import { llmService } from '@/services/llmService';

export interface Message {
  id: string;
  text: string;
  sender: 'user' | 'assistant';
  timestamp: Date;
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

// Patterns for recognizing todo-related queries
const TODO_PATTERNS = [
  // Summary/analytics patterns
  /summarize my todos?/i, 
  /todo summary/i,
  /how am i doing with my todos?/i,
  /todo analytics/i,
  /todo stats/i,
  /todo progress/i,
  
  // Suggestions patterns
  /suggest (some )?todos?/i,
  /recommend (some )?todos?/i,
  /todo ideas/i,
  /what should i do/i,
  /help me plan/i,
  
  // Similar todos patterns
  /similar todos?/i,
  /todos? like/i,
  /todos? related to/i,
  /find todos? about/i,
  
  // General todo queries
  /my todos?/i,
  /show me my todos?/i,
  /list my todos?/i,
  /find todos?/i,
  /search todos?/i
];

const ChatContext = createContext<ChatContextType | undefined>(undefined);

export const ChatProvider = ({ children }: { children: ReactNode }) => {
  const [messages, setMessages] = useState<Message[]>(defaultMessages);
  const [isLoading, setIsLoading] = useState(false);
  const [streamingText, setStreamingText] = useState('');

  // Function to check if a query is todo-related
  const isTodoQuery = (text: string): boolean => {
    return TODO_PATTERNS.some(pattern => pattern.test(text));
  };

  const addMessage = (message: Message) => {
    // Ensure the message has an ID
    const messageWithId = {
      ...message,
      id: message.id || Date.now().toString() + Math.random().toString(36).substring(2, 9),
    };
    
    setMessages(prev => [...prev, messageWithId]);
  };

  const clearMessages = () => {
    setMessages([]);
  };

  const resetToDefault = () => {
    setMessages(defaultMessages);
  };

  const sendMessage = async (text: string) => {
    if (!text.trim() || isLoading) return;

    // Create and add user message
    const userMessage: Message = {
      id: Date.now().toString(),
      text: text.trim(),
      sender: 'user',
      timestamp: new Date(),
    };
    
    addMessage(userMessage);
    setIsLoading(true);

    try {
      // Determine if this is a todo-related query
      const isTodoRelated = isTodoQuery(userMessage.text);
      
      // Start streaming response
      let fullResponse = '';
      let errorOccurred = false;
      let lastChunkEndsWithSpace = false;
      
      try {
        console.log(`Starting to stream ${isTodoRelated ? 'Todo RAG' : 'standard'} response...`);
        
        // Use todo RAG service if it's a todo-related query
        const streamSource = isTodoRelated 
          ? llmService.streamTodoQuery(userMessage.text)
          : llmService.streamResponse(userMessage.text);
          
        for await (const chunk of streamSource) {
          // Check if the chunk is an error message (JSON object)
          try {
            const jsonChunk = JSON.parse(chunk);
            if (jsonChunk.error) {
              errorOccurred = true;
              fullResponse = `Sorry, an error occurred: ${jsonChunk.error}`;
              setStreamingText(fullResponse);
              console.error('Error from service:', jsonChunk.error);
              break;
            }
          } catch (e) {
            // Not JSON, treat as normal text chunk
            console.log('Received chunk:', chunk);
            
            // Add a space between chunks if needed
            if (fullResponse && !lastChunkEndsWithSpace && !chunk.startsWith(' ')) {
              fullResponse += ' ';
            }
            
            fullResponse += chunk;
            lastChunkEndsWithSpace = chunk.endsWith(' ');
            
            setStreamingText(fullResponse);
          }
        }
        console.log('Finished streaming, final response:', fullResponse);
      } catch (streamError: any) {
        console.error('Error in streaming:', streamError);
        errorOccurred = true;
        fullResponse = `Sorry, an error occurred while streaming the response: ${streamError.message || 'Unknown error'}`;
        setStreamingText(fullResponse);
      }

      // Clean up the response - replace multiple spaces with a single space
      fullResponse = fullResponse.replace(/\s+/g, ' ').trim();

      // Clear streaming text
      setStreamingText('');
      
      // Only add the assistant message if we have a response
      if (fullResponse) {
        const assistantMessage: Message = {
          id: (Date.now() + 1).toString(),
          text: fullResponse,
          sender: 'assistant',
          timestamp: new Date(),
        };
        
        addMessage(assistantMessage);
      }
    } catch (error) {
      console.error('Error sending message:', error);
      // Add error message
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