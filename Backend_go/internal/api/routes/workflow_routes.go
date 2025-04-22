package routes

import (
	"github.com/ahmedelhadi17776/Compass/Backend_go/internal/api/handlers"
	"github.com/ahmedelhadi17776/Compass/Backend_go/internal/api/middleware"
	"github.com/gin-gonic/gin"
)

// WorkflowRoutes handles the setup of workflow-related routes
type WorkflowRoutes struct {
	handler   *handlers.WorkflowHandler
	jwtSecret string
}

// NewWorkflowRoutes creates a new WorkflowRoutes instance
func NewWorkflowRoutes(handler *handlers.WorkflowHandler, jwtSecret string) *WorkflowRoutes {
	return &WorkflowRoutes{
		handler:   handler,
		jwtSecret: jwtSecret,
	}
}

// RegisterRoutes registers all workflow-related routes
func (wr *WorkflowRoutes) RegisterRoutes(router *gin.Engine) {
	// Create a workflow group with authentication middleware
	workflowGroup := router.Group("/api/workflows")
	workflowGroup.Use(middleware.NewAuthMiddleware(wr.jwtSecret))

	// Core workflow operations
	workflowGroup.POST("", wr.handler.CreateWorkflow)
	workflowGroup.GET("", wr.handler.ListWorkflows)
	workflowGroup.GET("/:id", wr.handler.GetWorkflow)
	workflowGroup.PUT("/:id", wr.handler.UpdateWorkflow)
	workflowGroup.DELETE("/:id", wr.handler.DeleteWorkflow)

	// Workflow execution operations
	workflowGroup.POST("/:id/execute", wr.handler.ExecuteWorkflow)
	workflowGroup.POST("/:id/cancel", wr.handler.CancelWorkflowExecution)

	// Workflow analysis and optimization
	workflowGroup.GET("/:id/analyze", wr.handler.AnalyzeWorkflow)
	workflowGroup.POST("/:id/optimize", wr.handler.OptimizeWorkflow)
}
