package mcp

import "encoding/json"

// Tool represents an MCP tool definition
type Tool struct {
	Name        string     `json:"name"`
	Description string     `json:"description"`
	Parameters  Parameters `json:"parameters"`
}

// Parameters defines the structure of tool parameters
type Parameters struct {
	Properties map[string]Property `json:"properties"`
	Required   []string            `json:"required"`
	Type       string              `json:"type"`
}

// Property defines a parameter property
type Property struct {
	Description string    `json:"description"`
	Type        string    `json:"type"`
	Items       *Property `json:"items,omitempty"`
}

// CallToolRequest represents a request to call a tool
type CallToolRequest struct {
	Name   string         `json:"name"`
	Params ToolParameters `json:"params"`
}

// ToolParameters contains the arguments for a tool call
type ToolParameters struct {
	Arguments map[string]interface{} `json:"arguments"`
}

// CallToolResult represents the result of a tool call
type CallToolResult struct {
	Type    string          `json:"type"`
	Content json.RawMessage `json:"content"`
}

// NewToolResultText creates a new text result
func NewToolResultText(text string) *CallToolResult {
	content, _ := json.Marshal(text)
	return &CallToolResult{
		Type:    "text",
		Content: content,
	}
}

// NewToolResultError creates a new error result
func NewToolResultError(err string) *CallToolResult {
	content, _ := json.Marshal(err)
	return &CallToolResult{
		Type:    "error",
		Content: content,
	}
}

// ToolOption is a function that configures a Tool
type ToolOption func(*Tool)

// WithDescription sets the tool description
func WithDescription(desc string) ToolOption {
	return func(t *Tool) {
		t.Description = desc
	}
}

// WithString adds a string parameter to the tool
func WithString(name string, opts ...ParamOption) ToolOption {
	return func(t *Tool) {
		if t.Parameters.Properties == nil {
			t.Parameters.Properties = make(map[string]Property)
		}
		prop := Property{
			Type: "string",
		}
		for _, opt := range opts {
			opt(&prop, t, name)
		}
		t.Parameters.Properties[name] = prop
	}
}

// ParamOption configures a parameter
type ParamOption func(*Property, *Tool, string)

// Required marks a parameter as required
func Required() ParamOption {
	return func(_ *Property, t *Tool, name string) {
		t.Parameters.Required = append(t.Parameters.Required, name)
	}
}

// Description sets the parameter description
func Description(desc string) ParamOption {
	return func(p *Property, _ *Tool, _ string) {
		p.Description = desc
	}
}
