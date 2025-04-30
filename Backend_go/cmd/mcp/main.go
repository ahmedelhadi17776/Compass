package main

import (
	"context"
	"fmt"
	"io"
	"log"
	"net/http"
	"os"
	"sync"

	"github.com/ahmedelhadi17776/Compass/Backend_go/internal/mcp"
	"github.com/ahmedelhadi17776/Compass/Backend_go/internal/mcp/server"
	"github.com/chromedp/chromedp"
)

// Global browser context
var (
	browserCtx    context.Context
	browserCancel context.CancelFunc
	browserMu     sync.Mutex
)

func init() {
	// Set up browser
	browserCtx, browserCancel = chromedp.NewContext(context.Background())
}

func main() {
	// Create MCP server
	s := server.NewMCPServer(
		"Compass MCP Server",
		"1.0.0",
	)

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
				"user_id": {
					Description: "The UUID of the user to retrieve todos for",
					Type:        "string",
				},
				"auth_token": {
					Description: "Bearer token for authentication",
					Type:        "string",
				},
			},
			Required: []string{"user_id", "auth_token"},
			Type:     "object",
		},
	}
	s.AddTool(retrieveTodos, handleRetrieveTodos)

	// Add retrieve habits tool
	retrieveHabits := mcp.Tool{
		Name:        "retrieveHabitsByUser",
		Description: "Retrieve habits for a specific user",
		Parameters: mcp.Parameters{
			Properties: map[string]mcp.Property{
				"user_id": {
					Description: "The UUID of the user to retrieve habits for",
					Type:        "string",
				},
				"auth_token": {
					Description: "Bearer token for authentication",
					Type:        "string",
				},
			},
			Required: []string{"user_id", "auth_token"},
			Type:     "object",
		},
	}
	s.AddTool(retrieveHabits, handleRetrieveHabits)

	// Start the server
	log.Println("Starting MCP server...")
	if err := server.ServeStdio(s); err != nil {
		fmt.Fprintf(os.Stderr, "Server error: %v\n", err)
		os.Exit(1)
	}
}

func handleBrowserLogs(ctx context.Context, req mcp.CallToolRequest) (*mcp.CallToolResult, error) {
	// Implement browser logs retrieval
	return mcp.NewToolResultText("[]"), nil
}

func handleBrowserErrors(ctx context.Context, req mcp.CallToolRequest) (*mcp.CallToolResult, error) {
	// Implement browser errors retrieval
	return mcp.NewToolResultText("[]"), nil
}

func handleNetworkErrors(ctx context.Context, req mcp.CallToolRequest) (*mcp.CallToolResult, error) {
	// Implement network errors retrieval
	return mcp.NewToolResultText("[]"), nil
}

func handleNetworkSuccess(ctx context.Context, req mcp.CallToolRequest) (*mcp.CallToolResult, error) {
	// Implement network success logs retrieval
	return mcp.NewToolResultText("[]"), nil
}

func handleScreenshot(ctx context.Context, req mcp.CallToolRequest) (*mcp.CallToolResult, error) {
	// Implement screenshot functionality
	return mcp.NewToolResultText("Screenshot taken"), nil
}

func handleSelectedElement(ctx context.Context, req mcp.CallToolRequest) (*mcp.CallToolResult, error) {
	// Implement selected element retrieval
	return mcp.NewToolResultText("No element selected"), nil
}

func handleWipeLogs(ctx context.Context, req mcp.CallToolRequest) (*mcp.CallToolResult, error) {
	browserMu.Lock()
	defer browserMu.Unlock()

	// Clear browser console
	if err := chromedp.Run(browserCtx, chromedp.Evaluate(`console.clear()`, nil)); err != nil {
		return mcp.NewToolResultError(fmt.Sprintf("Failed to clear logs: %v", err)), nil
	}

	return mcp.NewToolResultText("Logs wiped successfully"), nil
}

func handleRetrieveTodos(ctx context.Context, req mcp.CallToolRequest) (*mcp.CallToolResult, error) {
	userID := req.Params.Arguments["user_id"].(string)
	authToken := req.Params.Arguments["auth_token"].(string)

	// Create HTTP client
	client := &http.Client{}

	// Create request to your API endpoint
	apiURL := "http://localhost:8000/api/todos/user/" + userID
	request, err := http.NewRequest("GET", apiURL, nil)
	if err != nil {
		return mcp.NewToolResultError(fmt.Sprintf("Failed to create request: %v", err)), nil
	}

	// Add authorization header
	request.Header.Add("Authorization", "Bearer "+authToken)

	// Make the request
	response, err := client.Do(request)
	if err != nil {
		return mcp.NewToolResultError(fmt.Sprintf("Failed to make request: %v", err)), nil
	}
	defer response.Body.Close()

	// Read response body
	body, err := io.ReadAll(response.Body)
	if err != nil {
		return mcp.NewToolResultError(fmt.Sprintf("Failed to read response: %v", err)), nil
	}

	// Check response status
	if response.StatusCode != http.StatusOK {
		return mcp.NewToolResultError(fmt.Sprintf("API request failed with status %d: %s", response.StatusCode, string(body))), nil
	}

	// Return the response
	return mcp.NewToolResultText(string(body)), nil
}

func handleRetrieveHabits(ctx context.Context, req mcp.CallToolRequest) (*mcp.CallToolResult, error) {
	userID := req.Params.Arguments["user_id"].(string)
	authToken := req.Params.Arguments["auth_token"].(string)

	// Create HTTP client
	client := &http.Client{}

	// Create request to your API endpoint
	apiURL := "http://localhost:8000/api/habits/user/" + userID
	request, err := http.NewRequest("GET", apiURL, nil)
	if err != nil {
		return mcp.NewToolResultError(fmt.Sprintf("Failed to create request: %v", err)), nil
	}

	// Add authorization header
	request.Header.Add("Authorization", "Bearer "+authToken)

	// Make the request
	response, err := client.Do(request)
	if err != nil {
		return mcp.NewToolResultError(fmt.Sprintf("Failed to make request: %v", err)), nil
	}
	defer response.Body.Close()

	// Read response body
	body, err := io.ReadAll(response.Body)
	if err != nil {
		return mcp.NewToolResultError(fmt.Sprintf("Failed to read response: %v", err)), nil
	}

	// Check response status
	if response.StatusCode != http.StatusOK {
		return mcp.NewToolResultError(fmt.Sprintf("API request failed with status %d: %s", response.StatusCode, string(body))), nil
	}

	// Return the response
	return mcp.NewToolResultText(string(body)), nil
}
