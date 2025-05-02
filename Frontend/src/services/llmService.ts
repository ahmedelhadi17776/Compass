import axios from 'axios';
import { useMutation, useQuery } from '@tanstack/react-query';
import { API_URL, PYTHON_API_URL } from '@/config';

// Types
export interface LLMRequest {
  prompt: string;
  context?: Record<string, any>;
  domain?: string;
  model_parameters?: Record<string, any>;
  previous_messages?: Array<{sender: string; text: string}>;
  session_id?: string;
}

export interface LLMResponse {
  response: string;
  intent?: string;
  target?: string;
  description?: string;
  rag_used: boolean;
  cached: boolean;
  confidence: number;
  error?: boolean;
  error_message?: string;
  session_id?: string;
  tool_used?: string;
  tool_args?: Record<string, any>;
  tool_success?: boolean;
}

// Local storage key for session ID
const SESSION_ID_KEY = 'ai_conversation_session_id';

// Helper to get or create a session ID
const getOrCreateSessionId = (): string => {
  const existingSessionId = localStorage.getItem(SESSION_ID_KEY);
  if (existingSessionId) {
    return existingSessionId;
  }
  
  // Create a new UUID for the session
  const newSessionId = crypto.randomUUID();
  localStorage.setItem(SESSION_ID_KEY, newSessionId);
  return newSessionId;
};

// LLM Service
export const llmService = {
  // Get current session ID
  getSessionId: (): string => {
    return getOrCreateSessionId();
  },
  
  // Create a new session ID (useful for starting a new conversation)
  createNewSession: (): string => {
    const newSessionId = crypto.randomUUID();
    localStorage.setItem(SESSION_ID_KEY, newSessionId);
    return newSessionId;
  },
  
  // Clear the current session
  clearSession: async (): Promise<void> => {
    const token = localStorage.getItem('token');
    if (!token) throw new Error('Authentication required');
    
    const sessionId = getOrCreateSessionId();
    
    try {
      await axios.post(
        `${PYTHON_API_URL}/ai/clear-session`,
        { session_id: sessionId },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      // Create a new session after clearing
      llmService.createNewSession();
    } catch (error) {
      console.error('Failed to clear session:', error);
      throw error;
    }
  },

  // Generate a response from the LLM
  generateResponse: async (request: LLMRequest): Promise<LLMResponse> => {
    const token = localStorage.getItem('token');
    if (!token) throw new Error('Authentication required');

    // Ensure we have a session ID
    const sessionId = request.session_id || getOrCreateSessionId();
    const requestWithSession = {
      ...request,
      session_id: sessionId
    };

    const response = await axios.post<LLMResponse>(
      `${PYTHON_API_URL}/ai/process`,
      requestWithSession,
      { 
        headers: { 
          Authorization: `Bearer ${token}`,
          Cookie: `session_id=${sessionId}`
        }
      }
    );
    
    // If we got a new session ID back, update our storage
    if (response.data.session_id && response.data.session_id !== sessionId) {
      localStorage.setItem(SESSION_ID_KEY, response.data.session_id);
    }
    
    return response.data;
  },

  // Stream response from the LLM
  streamResponse: async function* (prompt: string, previousMessages?: Array<{sender: string; text: string}>) {
    const token = localStorage.getItem('token');
    if (!token) throw new Error('Authentication required');
    
    // Get the current session ID
    const sessionId = getOrCreateSessionId();

    try {
      const response = await fetch(`${PYTHON_API_URL}/ai/process/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
          'Cookie': `session_id=${sessionId}`
        },
        body: JSON.stringify({ 
          prompt,
          previous_messages: previousMessages,
          session_id: sessionId
        }),
      });

      if (!response.ok) {
        const errorText = await response.text();
        console.error('LLM API Error:', errorText);
        yield JSON.stringify({ error: `Stream request failed: ${response.status} ${response.statusText}` });
        return;
      }

      const reader = response.body?.getReader();
      if (!reader) {
        yield JSON.stringify({ error: 'Response body is not readable' });
        return;
      }

      const decoder = new TextDecoder();
      
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        
        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split('\n\n');
        
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.substring(6).trim();
            
            if (data === '[DONE]') {
              console.log('Stream complete');
              break;
            }
            
            if (data.startsWith('Error:') || data.includes('"error"')) {
              console.error('Stream error:', data);
              yield JSON.stringify({ error: data.includes('{') ? JSON.parse(data).error : data });
              return;
            }
            
            if (data) yield data;
          }
        }
      }
    } catch (error) {
      console.error('Error in stream response:', error);
      yield JSON.stringify({ error: error instanceof Error ? error.message : 'Unknown error' });
    }
  }
};

// React Query Hooks
export const useGenerateLLMResponse = () => {
  return useMutation({
    mutationFn: (request: LLMRequest) => llmService.generateResponse(request),
  });
};

// Custom hook for streaming responses
export const useStreamingLLMResponse = () => {
  return {
    streamResponse: (prompt: string, previousMessages?: Array<{sender: string; text: string}>) => {
      return llmService.streamResponse(prompt, previousMessages);
    },
  };
};

// Hook to manage conversation sessions
export const useConversationSession = () => {
  return {
    getSessionId: llmService.getSessionId,
    createNewSession: llmService.createNewSession,
    clearSession: llmService.clearSession
  };
};

export default llmService;
