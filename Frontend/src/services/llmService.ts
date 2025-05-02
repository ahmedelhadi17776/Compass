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
}

// LLM Service
export const llmService = {
  // Generate a response from the LLM
  generateResponse: async (request: LLMRequest): Promise<LLMResponse> => {
    const token = localStorage.getItem('token');
    if (!token) throw new Error('Authentication required');

    const response = await axios.post<LLMResponse>(
      `${PYTHON_API_URL}/ai/process`,
      request,
      { headers: { Authorization: `Bearer ${token}` } }
    );
    
    return response.data;
  },

  // Stream response from the LLM
  streamResponse: async function* (prompt: string, previousMessages?: Array<{sender: string; text: string}>) {
    const token = localStorage.getItem('token');
    if (!token) throw new Error('Authentication required');

    try {
      const response = await fetch(`${PYTHON_API_URL}/ai/process/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ 
          prompt,
          previous_messages: previousMessages 
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

export default llmService;
