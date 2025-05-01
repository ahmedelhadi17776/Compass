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
	Name         string
	Version      string
	tools        map[string]mcp.Tool
	handlers     map[string]ToolHandler
	capabilities ServerCapabilities
	mu           sync.RWMutex
}

// ServerCapabilities represents the capabilities of the MCP server
type ServerCapabilities struct {
	Tools   bool `json:"tools"`
	Logging bool `json:"logging"`
}

// SetCapabilities sets the server capabilities
func (s *MCPServer) SetCapabilities(caps ServerCapabilities) {
	s.mu.Lock()
	defer s.mu.Unlock()
	s.capabilities = caps
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

	// Convert Parameters to InputSchema for client compatibility
	paramsJSON, _ := json.Marshal(tool.Parameters)
	tool.InputSchema = paramsJSON

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

	// Write initialization response in the format expected by Python MCP client
	initResponse := map[string]interface{}{
		"jsonrpc": "2.0",
		"id":      0,
		"result": map[string]interface{}{
			"implementation": map[string]string{
				"name":    s.Name,
				"version": s.Version,
			},
			"toolsVersion": 1,
		},
	}
	if err := encoder.Encode(initResponse); err != nil {
		return fmt.Errorf("failed to encode init response: %w", err)
	}

	for {
		// Decode the incoming request
		var request map[string]interface{}
		if err := decoder.Decode(&request); err != nil {
			if err == io.EOF {
				return nil
			}
			return fmt.Errorf("failed to decode request: %w", err)
		}

		// Extract request ID and method
		id, _ := request["id"].(float64)
		method, _ := request["method"].(string)

		// Handle different methods
		switch method {
		case "listTools":
			tools := s.GetTools()
			response := map[string]interface{}{
				"jsonrpc": "2.0",
				"id":      id,
				"result": map[string]interface{}{
					"tools": tools,
				},
			}
			if err := encoder.Encode(response); err != nil {
				return fmt.Errorf("failed to encode listTools response: %w", err)
			}

		case "callTool":
			// Extract params from the request
			paramsRaw, _ := request["params"].(map[string]interface{})
			name, _ := paramsRaw["name"].(string)
			paramsObj, _ := paramsRaw["params"].(map[string]interface{})
			arguments, _ := paramsObj["arguments"].(map[string]interface{})

			// Create a tool call request
			req := mcp.CallToolRequest{
				Name: name,
				Params: mcp.ToolParameters{
					Arguments: arguments,
				},
			}

			// Handle the request
			result, err := s.HandleRequest(context.Background(), req)
			if err != nil {
				result = mcp.NewToolResultError(err.Error())
			}

			// Send the response
			response := map[string]interface{}{
				"jsonrpc": "2.0",
				"id":      id,
				"result":  result,
			}
			if err := encoder.Encode(response); err != nil {
				return fmt.Errorf("failed to encode callTool response: %w", err)
			}

		default:
			// Handle unknown methods
			response := map[string]interface{}{
				"jsonrpc": "2.0",
				"id":      id,
				"error": map[string]interface{}{
					"code":    -32601,
					"message": fmt.Sprintf("method %q not found", method),
				},
			}
			if err := encoder.Encode(response); err != nil {
				return fmt.Errorf("failed to encode error response: %w", err)
			}
		}
	}
}

// ServeHTTP serves the MCP server over HTTP
func ServeHTTP(s *MCPServer, addr string) error {
	// TODO: Implement HTTP server
	return nil
}
