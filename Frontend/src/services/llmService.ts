import axios from 'axios';
import { useMutation, useQuery } from '@tanstack/react-query';
import { API_URL } from '@/config';

// Types
export interface LLMRequest {
  prompt: string;
  context?: Record<string, any>;
  model_parameters?: Record<string, any>;
}

export interface LLMResponse {
  text: string;
  usage?: {
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
  };
}

export interface LLMModelInfo {
  model: string;
  capabilities: {
    streaming: boolean;
    function_calling: boolean;
    context_window: number;
    temperature_range: [number, number];
  };
  configuration: {
    temperature: number;
    max_tokens: number;
    top_p: number;
    min_p: number;
    top_k: number;
  };
}

export interface TaskEnhancement {
  enhanced_description: string;
  suggestions: string[];
  keywords: string[];
}

export interface WorkflowAnalysis {
  efficiency_score: number;
  bottlenecks: string[];
  recommendations: string[];
}

export interface MeetingSummary {
  summary: string;
  action_items: string[];
  key_points: string[];
}

// Add TodoRAG interfaces
export interface TodoSuggestion {
  title: string;
  description?: string;
  priority: string;
  ai_generated: boolean;
}

export interface TodoSearchResult {
  todo_id: number;
  title: string;
  status?: string;
  priority?: string;
  similarity_score: number;
  metadata?: Record<string, any>;
}

export interface TodoAnalytics {
  metrics: Record<string, any>;
  insights: string[];
  recommendations: string[];
  productivity_score: number;
}

export interface TodoQueryContext {
  previousQuery?: string;
  relevantTodoIds?: number[];
}

// LLM Service
export const llmService = {
  // Generate a response from the LLM
  generateResponse: async (request: LLMRequest): Promise<LLMResponse> => {
    const token = localStorage.getItem('token');
    if (!token) throw new Error('Authentication required');

    const response = await axios.post<LLMResponse>(
      `${API_URL}/ai/llm/generate`,
      request,
      { headers: { Authorization: `Bearer ${token}` } }
    );
    return response.data;
  },

  // Stream response from the LLM - this is an async generator function
  streamResponse: async function* (prompt: string) {
    const token = localStorage.getItem('token');
    if (!token) throw new Error('Authentication required');

    try {
      console.log('Starting stream request with prompt:', prompt);
      
      // Create the request with the proper format
      const response = await fetch(`${API_URL}/ai/llm/generate/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ 
          prompt,
          // Add default context and model parameters to match GitHub API example
          context: {
            system_message: ""
          },
          model_parameters: {
            temperature: 1,
            max_tokens: 4096,
            top_p: 1
          }
        }),
      });

      if (!response.ok) {
        const errorText = await response.text();
        console.error('LLM API Error:', errorText);
        yield JSON.stringify({ error: `Stream request failed: ${response.status} ${response.statusText}` });
        return;
      }

      // Get the reader from the response body
      const reader = response.body?.getReader();
      if (!reader) {
        yield JSON.stringify({ error: 'Response body is not readable' });
        return;
      }

      const decoder = new TextDecoder();
      
      // Read chunks from the stream
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        
        // Decode the chunk and split by SSE format
        const chunk = decoder.decode(value, { stream: true });
        console.log('Raw chunk received:', chunk);
        const lines = chunk.split('\n\n');
        
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.substring(6).trim();
            console.log('Parsed data:', data);
            
            // Check if this is the end of the stream
            if (data === '[DONE]') {
              console.log('Stream complete');
              break;
            }
            
            // Check if this is an error message
            if (data.startsWith('Error:') || data.includes('"error"')) {
              console.error('Stream error:', data);
              
              // Try to parse as JSON if it looks like JSON
              if (data.includes('{') && data.includes('}')) {
                try {
                  const jsonData = JSON.parse(data);
                  yield JSON.stringify({ error: jsonData.error || 'Unknown error' });
                } catch (e) {
                  yield JSON.stringify({ error: data });
                }
              } else {
                yield JSON.stringify({ error: data });
              }
              return;
            }
            
            // Yield the data if it's not empty
            if (data) {
              yield data;
            }
          }
        }
      }
    } catch (error) {
      console.error('Error in stream response:', error);
      yield JSON.stringify({ error: error instanceof Error ? error.message : 'Unknown error' });
    }
  },

  // Get model information
  getModelInfo: async (): Promise<LLMModelInfo> => {
    const token = localStorage.getItem('token');
    if (!token) throw new Error('Authentication required');

    const response = await axios.get<LLMModelInfo>(
      `${API_URL}/ai/llm/model-info`,
      { headers: { Authorization: `Bearer ${token}` } }
    );
    return response.data;
  },

  // Enhance task description
  enhanceTaskDescription: async (task: { title: string; description: string }): Promise<TaskEnhancement> => {
    const token = localStorage.getItem('token');
    if (!token) throw new Error('Authentication required');

    const response = await axios.post<TaskEnhancement>(
      `${API_URL}/ai/llm/enhance-task`,
      task,
      { headers: { Authorization: `Bearer ${token}` } }
    );
    return response.data;
  },

  // Analyze workflow
  analyzeWorkflow: async (workflowId: number, historicalData: any[]): Promise<WorkflowAnalysis> => {
    const token = localStorage.getItem('token');
    if (!token) throw new Error('Authentication required');

    const response = await axios.post<WorkflowAnalysis>(
      `${API_URL}/ai/llm/analyze-workflow`,
      { workflow_id: workflowId, historical_data: historicalData },
      { headers: { Authorization: `Bearer ${token}` } }
    );
    return response.data;
  },

  // Summarize meeting
  summarizeMeeting: async (transcript: string, participants: string[], duration: number): Promise<MeetingSummary> => {
    const token = localStorage.getItem('token');
    if (!token) throw new Error('Authentication required');

    const response = await axios.post<MeetingSummary>(
      `${API_URL}/ai/llm/summarize-meeting`,
      { transcript, participants, duration },
      { headers: { Authorization: `Bearer ${token}` } }
    );
    return response.data;
  },

  // Todo RAG methods
  processTodoQuery: async (prompt: string): Promise<LLMResponse> => {
    const token = localStorage.getItem('token');
    if (!token) throw new Error('Authentication required');

    const response = await axios.post<LLMResponse>(
      `${API_URL}/ai/llm/todo-rag`,
      { prompt, context: null, model_parameters: null },
      { headers: { Authorization: `Bearer ${token}` } }
    );
    return response.data;
  },

  async *streamTodoQuery(prompt: string, context?: TodoQueryContext): AsyncGenerator<string> {
    try {
      const response = await fetch(`${API_URL}/ai/llm/todo-rag/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          prompt,
          context: {
            system_message: "You are a helpful AI assistant specialized in productivity and task management.",
            previous_query: context?.previousQuery,
            relevant_todo_ids: context?.relevantTodoIds,
            conversation_mode: "follow_up"
          },
          model_parameters: {
            temperature: 1,
            max_tokens: 4096,
            top_p: 1
          }
        }),
      });

      if (!response.ok) {
        throw new Error('Network response was not ok');
      }

      const reader = response.body?.getReader();
      if (!reader) {
        throw new Error('Failed to get response reader');
      }

      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.trim() === '') continue;
          if (line.trim() === 'data: [DONE]') return;

          const message = line.replace(/^data: /, '');
          yield message;
        }
      }
    } catch (error) {
      console.error('Error in streamTodoQuery:', error);
      throw error;
    }
  },
};

// React Query Hooks
export const useGenerateLLMResponse = () => {
  return useMutation({
    mutationFn: (request: LLMRequest) => llmService.generateResponse(request),
  });
};

export const useModelInfo = () => {
  return useQuery({
    queryKey: ['llm', 'model-info'],
    queryFn: () => llmService.getModelInfo(),
    staleTime: 1000 * 60 * 60, // 1 hour
  });
};

export const useEnhanceTaskDescription = () => {
  return useMutation({
    mutationFn: (task: { title: string; description: string }) => 
      llmService.enhanceTaskDescription(task),
  });
};

export const useAnalyzeWorkflow = () => {
  return useMutation({
    mutationFn: ({ workflowId, historicalData }: { workflowId: number; historicalData: any[] }) => 
      llmService.analyzeWorkflow(workflowId, historicalData),
  });
};

export const useSummarizeMeeting = () => {
  return useMutation({
    mutationFn: ({ transcript, participants, duration }: 
      { transcript: string; participants: string[]; duration: number }) => 
      llmService.summarizeMeeting(transcript, participants, duration),
  });
};

export const useTodoRagQuery = () => {
  return useMutation({
    mutationFn: (prompt: string) => llmService.processTodoQuery(prompt),
  });
};

// Custom hook for streaming responses
export const useStreamingLLMResponse = () => {
  return {
    streamResponse: (prompt: string) => {
      return llmService.streamResponse(prompt);
    },
  };
};

export default llmService;
