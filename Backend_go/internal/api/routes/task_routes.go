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
	// @Description Create a new task for the authenticated user
	// @Tags tasks
	// @Accept json
	// @Produce json
	// @Security BearerAuth
	// @Param task body dto.CreateTaskRequest true "Task creation information"
	// @Success 201 {object} dto.TaskResponse "Task created successfully"
	// @Failure 400 {object} map[string]string "Invalid request"
	// @Failure 401 {object} map[string]string "Unauthorized"
	// @Failure 500 {object} map[string]string "Internal server error"
	// @Router /api/tasks [post]
	taskGroup.POST("", tr.handler.CreateTask)

	// @Summary Get all tasks
	// @Description Get all tasks for the authenticated user with pagination
	// @Tags tasks
	// @Accept json
	// @Produce json
	// @Security BearerAuth
	// @Param page query int false "Page number (default: 0)"
	// @Param pageSize query int false "Page size (default: 10)"
	// @Success 200 {object} dto.TaskListResponse "List of tasks"
	// @Failure 401 {object} map[string]string "Unauthorized"
	// @Failure 500 {object} map[string]string "Internal server error"
	// @Router /api/tasks [get]
	taskGroup.GET("", tr.handler.ListTasks)

	// @Summary Get a task by ID
	// @Description Get a specific task by its ID
	// @Tags tasks
	// @Accept json
	// @Produce json
	// @Security BearerAuth
	// @Param id path string true "Task ID"
	// @Success 200 {object} dto.TaskResponse "Task details"
	// @Failure 401 {object} map[string]string "Unauthorized"
	// @Failure 404 {object} map[string]string "Task not found"
	// @Failure 500 {object} map[string]string "Internal server error"
	// @Router /api/tasks/{id} [get]
	taskGroup.GET("/:id", tr.handler.GetTask)

	// @Summary Update a task
	// @Description Update an existing task
	// @Tags tasks
	// @Accept json
	// @Produce json
	// @Security BearerAuth
	// @Param id path string true "Task ID"
	// @Param task body dto.UpdateTaskRequest true "Task update information"
	// @Success 200 {object} dto.TaskResponse "Task updated successfully"
	// @Failure 400 {object} map[string]string "Invalid request"
	// @Failure 401 {object} map[string]string "Unauthorized"
	// @Failure 404 {object} map[string]string "Task not found"
	// @Failure 500 {object} map[string]string "Internal server error"
	// @Router /api/tasks/{id} [put]
	taskGroup.PUT("/:id", tr.handler.UpdateTask)

	// @Summary Delete a task
	// @Description Delete an existing task
	// @Tags tasks
	// @Accept json
	// @Produce json
	// @Security BearerAuth
	// @Param id path string true "Task ID"
	// @Success 204 "Task deleted successfully"
	// @Failure 401 {object} map[string]string "Unauthorized"
	// @Failure 404 {object} map[string]string "Task not found"
	// @Failure 500 {object} map[string]string "Internal server error"
	// @Router /api/tasks/{id} [delete]
	taskGroup.DELETE("/:id", tr.handler.DeleteTask)
}
