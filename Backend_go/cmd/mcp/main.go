package main

import (
	"context"
	"fmt"
	"io"
	"log"
	"net/http"
	"os"

	"github.com/ahmedelhadi17776/Compass/Backend_go/internal/mcp"
	"github.com/ahmedelhadi17776/Compass/Backend_go/internal/mcp/server"
)

func main() {
	// Create MCP server
	s := server.NewMCPServer(
		"Compass MCP Server",
		"1.0.0",
	)

	// Set server capabilities
	s.SetCapabilities(server.ServerCapabilities{
		Tools:   true,
		Logging: true,
	})

	// Add browser tools
	browserLogs := mcp.Tool{
		Name:        "getConsoleLogs",
		Description: "Check our browser logs",
		Parameters: mcp.Parameters{
			Properties: map[string]mcp.Property{
				"random_string": {
					Description: "Dummy parameter for no-parameter tools",
					Type:        "string",
				},
			},
			Required: []string{"random_string"},
			Type:     "object",
		},
	}
	s.AddTool(browserLogs, handleBrowserLogs)

	browserErrors := mcp.Tool{
		Name:        "getConsoleErrors",
		Description: "Check our browsers console errors",
		Parameters: mcp.Parameters{
			Properties: map[string]mcp.Property{
				"random_string": {
					Description: "Dummy parameter for no-parameter tools",
					Type:        "string",
				},
			},
			Required: []string{"random_string"},
			Type:     "object",
		},
	}
	s.AddTool(browserErrors, handleBrowserErrors)

	networkErrors := mcp.Tool{
		Name:        "getNetworkErrorLogs",
		Description: "Check our network ERROR logs",
		Parameters: mcp.Parameters{
			Properties: map[string]mcp.Property{
				"random_string": {
					Description: "Dummy parameter for no-parameter tools",
					Type:        "string",
				},
			},
			Required: []string{"random_string"},
			Type:     "object",
		},
	}
	s.AddTool(networkErrors, handleNetworkErrors)

	networkSuccess := mcp.Tool{
		Name:        "getNetworkSuccessLogs",
		Description: "Check our network SUCCESS logs",
		Parameters: mcp.Parameters{
			Properties: map[string]mcp.Property{
				"random_string": {
					Description: "Dummy parameter for no-parameter tools",
					Type:        "string",
				},
			},
			Required: []string{"random_string"},
			Type:     "object",
		},
	}
	s.AddTool(networkSuccess, handleNetworkSuccess)

	screenshot := mcp.Tool{
		Name:        "takeScreenshot",
		Description: "Take a screenshot of the current browser tab",
		Parameters: mcp.Parameters{
			Properties: map[string]mcp.Property{
				"random_string": {
					Description: "Dummy parameter for no-parameter tools",
					Type:        "string",
				},
			},
			Required: []string{"random_string"},
			Type:     "object",
		},
	}
	s.AddTool(screenshot, handleScreenshot)

	selectedElement := mcp.Tool{
		Name:        "getSelectedElement",
		Description: "Get the selected element from the browser",
		Parameters: mcp.Parameters{
			Properties: map[string]mcp.Property{
				"random_string": {
					Description: "Dummy parameter for no-parameter tools",
					Type:        "string",
				},
			},
			Required: []string{"random_string"},
			Type:     "object",
		},
	}
	s.AddTool(selectedElement, handleSelectedElement)

	wipeLogs := mcp.Tool{
		Name:        "wipeLogs",
		Description: "Wipe all browser logs from memory",
		Parameters: mcp.Parameters{
			Properties: map[string]mcp.Property{
				"random_string": {
					Description: "Dummy parameter for no-parameter tools",
					Type:        "string",
				},
			},
			Required: []string{"random_string"},
			Type:     "object",
		},
	}
	s.AddTool(wipeLogs, handleWipeLogs)

	// Add retrieve todos tool
	retrieveTodos := mcp.Tool{
		Name:        "retrieveTodosByUser",
		Description: "Retrieve todos for a specific user",
		Parameters: mcp.Parameters{
			Properties: map[string]mcp.Property{
				"type": {
					Description: "Resource type (todos or habits)",
					Type:        "string",
				},
				"user_id": {
					Description: "User UUID",
					Type:        "string",
				},
				"auth_token": {
					Description: "Auth token",
					Type:        "string",
				},
			},
			Required: []string{"type", "user_id", "auth_token"},
			Type:     "object",
		},
	}
	s.AddTool(getResource, handleGetResource)

	// Start the server
	log.Println("Starting MCP server...")
	if err := server.ServeStdio(s); err != nil {
		fmt.Fprintf(os.Stderr, "Server error: %v\n", err)
		os.Exit(1)
	}
}

func handleGetResource(ctx context.Context, req mcp.CallToolRequest) (*mcp.CallToolResult, error) {
	resourceType, ok := req.Params.Arguments["type"].(string)
	if !ok || (resourceType != "todos" && resourceType != "habits") {
		return mcp.NewToolResultError("type must be 'todos' or 'habits'"), nil
	}

	userID, ok := req.Params.Arguments["user_id"].(string)
	if !ok {
		return mcp.NewToolResultError("user_id required"), nil
	}

	authToken, ok := req.Params.Arguments["auth_token"].(string)
	if !ok {
		return mcp.NewToolResultError("auth_token required"), nil
	}

	// Create HTTP client
	client := &http.Client{}

	// Create request to API endpoint
	apiURL := fmt.Sprintf("http://localhost:8000/api/%s/user/%s", resourceType, userID)
	request, err := http.NewRequest("GET", apiURL, nil)
	if err != nil {
		return mcp.NewToolResultError(fmt.Sprintf("Request error: %v", err)), nil
	}

	// Add authorization header
	request.Header.Add("Authorization", "Bearer "+authToken)

	// Make the request
	response, err := client.Do(request)
	if err != nil {
		return mcp.NewToolResultError(fmt.Sprintf("Request failed: %v", err)), nil
	}
	defer response.Body.Close()

	// Read response body
	body, err := io.ReadAll(response.Body)
	if err != nil {
		return mcp.NewToolResultError(fmt.Sprintf("Read error: %v", err)), nil
	}

	// Check response status
	if response.StatusCode != http.StatusOK {
		return mcp.NewToolResultError(fmt.Sprintf("API error %d: %s", response.StatusCode, string(body))), nil
	}

	// Return the response
	return mcp.NewToolResultText(string(body)), nil
}
