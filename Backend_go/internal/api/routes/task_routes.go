package routes

import (
	"github.com/ahmedelhadi17776/Compass/Backend_go/internal/domain/task"
	"github.com/gin-gonic/gin"
)

// @Summary Create a new task
// @Description Create a new task for the authenticated user
// @Tags tasks
// @Accept json
// @Produce json
// @Security BearerAuth
// @Param task body task.CreateTaskRequest true "Task creation information"
// @Success 201 {object} task.Task "Task created successfully"
// @Failure 400 {object} map[string]string "Invalid request"
// @Failure 401 {object} map[string]string "Unauthorized"
// @Failure 500 {object} map[string]string "Internal server error"
// @Router /tasks [post]
func createTaskHandler(taskService task.Service) gin.HandlerFunc {
	return func(c *gin.Context) {
		// ... existing implementation ...
	}
}

// @Summary Get all tasks
// @Description Get all tasks for the authenticated user
// @Tags tasks
// @Accept json
// @Produce json
// @Security BearerAuth
// @Success 200 {array} task.Task "List of tasks"
// @Failure 401 {object} map[string]string "Unauthorized"
// @Failure 500 {object} map[string]string "Internal server error"
// @Router /tasks [get]
func listTasksHandler(taskService task.Service) gin.HandlerFunc {
	return func(c *gin.Context) {
		// ... existing implementation ...
	}
}

// @Summary Get a task by ID
// @Description Get a specific task by its ID
// @Tags tasks
// @Accept json
// @Produce json
// @Security BearerAuth
// @Param id path string true "Task ID"
// @Success 200 {object} task.Task "Task details"
// @Failure 401 {object} map[string]string "Unauthorized"
// @Failure 404 {object} map[string]string "Task not found"
// @Failure 500 {object} map[string]string "Internal server error"
// @Router /tasks/{id} [get]
func getTaskHandler(taskService task.Service) gin.HandlerFunc {
	return func(c *gin.Context) {
		// ... existing implementation ...
	}
}

// @Summary Update a task
// @Description Update an existing task
// @Tags tasks
// @Accept json
// @Produce json
// @Security BearerAuth
// @Param id path string true "Task ID"
// @Param task body task.UpdateTaskRequest true "Task update information"
// @Success 200 {object} task.Task "Task updated successfully"
// @Failure 400 {object} map[string]string "Invalid request"
// @Failure 401 {object} map[string]string "Unauthorized"
// @Failure 404 {object} map[string]string "Task not found"
// @Failure 500 {object} map[string]string "Internal server error"
// @Router /tasks/{id} [put]
func updateTaskHandler(taskService task.Service) gin.HandlerFunc {
	return func(c *gin.Context) {
		// ... existing implementation ...
	}
}

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
// @Router /tasks/{id} [delete]
func deleteTaskHandler(taskService task.Service) gin.HandlerFunc {
	return func(c *gin.Context) {
		// ... existing implementation ...
	}
}

func SetupTaskRoutes(router *gin.RouterGroup, taskService task.Service) {
	tasks := router.Group("/tasks")
	{
		tasks.POST("", createTaskHandler(taskService))
		tasks.GET("", listTasksHandler(taskService))
		tasks.GET("/:id", getTaskHandler(taskService))
		tasks.PUT("/:id", updateTaskHandler(taskService))
		tasks.DELETE("/:id", deleteTaskHandler(taskService))
	}
}
