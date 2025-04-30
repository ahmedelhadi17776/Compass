package server

import (
	"context"
	"encoding/json"
	"fmt"
	"io"
	"os"
	"sync"

	"github.com/ahmedelhadi17776/Compass/Backend_go/internal/mcp"
)

// ToolHandler is a function that handles a tool call
type ToolHandler func(context.Context, mcp.CallToolRequest) (*mcp.CallToolResult, error)

// MCPServer represents an MCP server
type MCPServer struct {
	Name     string
	Version  string
	tools    map[string]mcp.Tool
	handlers map[string]ToolHandler
	mu       sync.RWMutex
}

// NewMCPServer creates a new MCP server
func NewMCPServer(name, version string) *MCPServer {
	return &MCPServer{
		Name:     name,
		Version:  version,
		tools:    make(map[string]mcp.Tool),
		handlers: make(map[string]ToolHandler),
	}
}

// AddTool adds a tool to the server
func (s *MCPServer) AddTool(tool mcp.Tool, handler ToolHandler) {
	s.mu.Lock()
	defer s.mu.Unlock()

	s.tools[tool.Name] = tool
	s.handlers[tool.Name] = handler
}

// GetTools returns all registered tools
func (s *MCPServer) GetTools() []mcp.Tool {
	s.mu.RLock()
	defer s.mu.RUnlock()

	tools := make([]mcp.Tool, 0, len(s.tools))
	for _, tool := range s.tools {
		tools = append(tools, tool)
	}
	return tools
}

// HandleRequest handles an incoming MCP request
func (s *MCPServer) HandleRequest(ctx context.Context, req mcp.CallToolRequest) (*mcp.CallToolResult, error) {
	s.mu.RLock()
	handler, exists := s.handlers[req.Name]
	s.mu.RUnlock()

	if !exists {
		return mcp.NewToolResultError(fmt.Sprintf("tool %q not found", req.Name)), nil
	}

	return handler(ctx, req)
}

// HandleBatchRequest handles multiple tool calls in a single request
func (s *MCPServer) HandleBatchRequest(ctx context.Context, req mcp.BatchToolRequest) (*mcp.BatchToolResult, error) {
	results := make([]mcp.CallToolResult, len(req.Requests))

	// Process each request in sequence
	for i, request := range req.Requests {
		result, err := s.HandleRequest(ctx, request)
		if err != nil {
			results[i] = *mcp.NewToolResultError(err.Error())
		} else {
			results[i] = *result
		}
	}

	return mcp.NewBatchToolResult(results), nil
}

// ServeStdio serves the MCP server over standard IO
func ServeStdio(s *MCPServer) error {
	decoder := json.NewDecoder(os.Stdin)
	encoder := json.NewEncoder(os.Stdout)

	// Write server info
	if err := encoder.Encode(map[string]interface{}{
		"name":    s.Name,
		"version": s.Version,
		"tools":   s.GetTools(),
	}); err != nil {
		return fmt.Errorf("failed to encode server info: %w", err)
	}

	for {
		// Try to decode as batch request first
		var batchReq mcp.BatchToolRequest
		if err := decoder.Decode(&batchReq); err != nil {
			if err == io.EOF {
				return nil
			}
			// If it's not a batch request, try single request
			var req mcp.CallToolRequest
			if err := decoder.Decode(&req); err != nil {
				if err == io.EOF {
					return nil
				}
				return fmt.Errorf("failed to decode request: %w", err)
			}

			result, err := s.HandleRequest(context.Background(), req)
			if err != nil {
				result = mcp.NewToolResultError(err.Error())
			}

			if err := encoder.Encode(result); err != nil {
				return fmt.Errorf("failed to encode response: %w", err)
			}
			continue
		}

		// Handle batch request
		if len(batchReq.Requests) > 0 {
			result, err := s.HandleBatchRequest(context.Background(), batchReq)
			if err != nil {
				return fmt.Errorf("failed to handle batch request: %w", err)
			}

			if err := encoder.Encode(result); err != nil {
				return fmt.Errorf("failed to encode batch response: %w", err)
			}
		}
	}
}

// ServeHTTP serves the MCP server over HTTP
func ServeHTTP(s *MCPServer, addr string) error {
	// TODO: Implement HTTP server
	return nil
}
