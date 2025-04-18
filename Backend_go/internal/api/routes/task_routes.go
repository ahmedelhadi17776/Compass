package routes

import (
	"github.com/ahmedelhadi17776/Compass/Backend_go/internal/api/handlers"
	"github.com/ahmedelhadi17776/Compass/Backend_go/internal/api/middleware"
	"github.com/gin-gonic/gin"
)

// TaskRoutes handles the setup of task-related routes
type TaskRoutes struct {
	handler   *handlers.TaskHandler
	jwtSecret string
}

// NewTaskRoutes creates a new TaskRoutes instance
func NewTaskRoutes(handler *handlers.TaskHandler, jwtSecret string) *TaskRoutes {
	return &TaskRoutes{
		handler:   handler,
		jwtSecret: jwtSecret,
	}
}

// RegisterRoutes registers all task-related routes
func (tr *TaskRoutes) RegisterRoutes(router *gin.Engine) {
	// Create a task group with authentication middleware
	taskGroup := router.Group("/api/tasks")
	taskGroup.Use(middleware.NewAuthMiddleware(tr.jwtSecret))

	// @Summary Create a new task
	// @Description Create a new task with the provided information
	// @Tags tasks
	// @Accept json
	// @Produce json
	// @Security BearerAuth
	// @Param task body dto.CreateTaskRequest true "Task creation information"
	// @Success 201 {object} dto.TaskResponse "Task created successfully"
	// @Failure 400 {object} map[string]string "Invalid request"
	// @Failure 401 {object} map[string]string "Unauthorized"
	// @Failure 403 {object} map[string]string "Insufficient permissions"
	// @Failure 500 {object} map[string]string "Internal server error"
	// @Router /api/tasks [post]
	taskGroup.POST("", middleware.RequirePermissions("tasks:create"), tr.handler.CreateTask)

	// @Summary Get all tasks
	// @Description Get all tasks for the authenticated user with pagination and filtering
	// @Tags tasks
	// @Accept json
	// @Produce json
	// @Security BearerAuth
	// @Param organization_id query string false "Filter by organization ID"
	// @Param project_id query string false "Filter by project ID"
	// @Param status query string false "Filter by status (Upcoming, In Progress, Completed, etc.)"
	// @Param priority query string false "Filter by priority (Low, Medium, High, Urgent)"
	// @Param assignee_id query string false "Filter by assignee ID"
	// @Param creator_id query string false "Filter by creator ID"
	// @Param reviewer_id query string false "Filter by reviewer ID"
	// @Param page query int false "Page number (default: 0)"
	// @Param pageSize query int false "Page size (default: 10)"
	// @Success 200 {object} dto.TaskListResponse "List of tasks"
	// @Failure 401 {object} map[string]string "Unauthorized"
	// @Failure 403 {object} map[string]string "Insufficient permissions"
	// @Failure 500 {object} map[string]string "Internal server error"
	// @Router /api/tasks [get]
	taskGroup.GET("", middleware.RequirePermissions("tasks:read"), tr.handler.ListTasks)

	// @Summary Get a task by ID
	// @Description Get detailed information about a specific task
	// @Tags tasks
	// @Accept json
	// @Produce json
	// @Security BearerAuth
	// @Param id path string true "Task ID" format(uuid)
	// @Success 200 {object} dto.TaskResponse "Task details"
	// @Failure 400 {object} map[string]string "Invalid task ID"
	// @Failure 401 {object} map[string]string "Unauthorized"
	// @Failure 403 {object} map[string]string "Insufficient permissions"
	// @Failure 404 {object} map[string]string "Task not found"
	// @Failure 500 {object} map[string]string "Internal server error"
	// @Router /api/tasks/{id} [get]
	taskGroup.GET("/:id", middleware.RequirePermissions("tasks:read"), tr.handler.GetTask)

	// @Summary Update a task
	// @Description Update an existing task's information
	// @Tags tasks
	// @Accept json
	// @Produce json
	// @Security BearerAuth
	// @Param id path string true "Task ID" format(uuid)
	// @Param task body dto.UpdateTaskRequest true "Task update information"
	// @Success 200 {object} dto.TaskResponse "Task updated successfully"
	// @Failure 400 {object} map[string]string "Invalid request or task ID"
	// @Failure 401 {object} map[string]string "Unauthorized"
	// @Failure 403 {object} map[string]string "Insufficient permissions"
	// @Failure 404 {object} map[string]string "Task not found"
	// @Failure 500 {object} map[string]string "Internal server error"
	// @Router /api/tasks/{id} [put]
	taskGroup.PUT("/:id", middleware.RequirePermissions("tasks:update"), tr.handler.UpdateTask)

	// @Summary Delete a task
	// @Description Delete an existing task
	// @Tags tasks
	// @Accept json
	// @Produce json
	// @Security BearerAuth
	// @Param id path string true "Task ID" format(uuid)
	// @Success 204 "Task deleted successfully"
	// @Failure 400 {object} map[string]string "Invalid task ID"
	// @Failure 401 {object} map[string]string "Unauthorized"
	// @Failure 403 {object} map[string]string "Insufficient permissions"
	// @Failure 404 {object} map[string]string "Task not found"
	// @Failure 500 {object} map[string]string "Internal server error"
	// @Router /api/tasks/{id} [delete]
	taskGroup.DELETE("/:id", middleware.RequirePermissions("tasks:delete"), tr.handler.DeleteTask)
}
