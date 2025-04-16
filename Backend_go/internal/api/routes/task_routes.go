package routes

import (
	"net/http"

	"github.com/ahmedelhadi17776/Compass/Backend_go/internal/domain/task"
	"github.com/gin-gonic/gin"
	"github.com/google/uuid"
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
		var req task.CreateTaskRequest
		if err := c.ShouldBindJSON(&req); err != nil {
			c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
			return
		}

		// Convert request to service input
		input := task.CreateTaskInput{
			Title:          req.Title,
			Description:    req.Description,
			Status:         task.TaskStatus(req.Status),
			StartDate:      req.DueDate, // Using DueDate as StartDate for now
			CreatorID:      uuid.New(),  // Should come from authenticated user
			ProjectID:      uuid.New(),  // Should come from request context
			OrganizationID: uuid.New(),  // Should come from request context
		}

		createdTask, err := taskService.CreateTask(c.Request.Context(), input)
		if err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
			return
		}

		c.JSON(http.StatusCreated, createdTask)
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
		filter := task.TaskFilter{
			Page:     0,
			PageSize: 10,
		}

		tasks, total, err := taskService.ListTasks(c.Request.Context(), filter)
		if err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
			return
		}

		c.JSON(http.StatusOK, gin.H{
			"tasks": tasks,
			"total": total,
		})
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
		id, err := uuid.Parse(c.Param("id"))
		if err != nil {
			c.JSON(http.StatusBadRequest, gin.H{"error": "invalid task ID"})
			return
		}

		foundTask, err := taskService.GetTask(c.Request.Context(), id)
		if err != nil {
			if err == task.ErrTaskNotFound {
				c.JSON(http.StatusNotFound, gin.H{"error": "task not found"})
				return
			}
			c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
			return
		}

		c.JSON(http.StatusOK, foundTask)
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
		id, err := uuid.Parse(c.Param("id"))
		if err != nil {
			c.JSON(http.StatusBadRequest, gin.H{"error": "invalid task ID"})
			return
		}

		var req task.UpdateTaskRequest
		if err := c.ShouldBindJSON(&req); err != nil {
			c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
			return
		}

		// Convert request to service input
		input := task.UpdateTaskInput{
			Title:       &req.Title,
			Description: &req.Description,
			Status:      (*task.TaskStatus)(&req.Status),
		}

		updatedTask, err := taskService.UpdateTask(c.Request.Context(), id, input)
		if err != nil {
			if err == task.ErrTaskNotFound {
				c.JSON(http.StatusNotFound, gin.H{"error": "task not found"})
				return
			}
			c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
			return
		}

		c.JSON(http.StatusOK, updatedTask)
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
		id, err := uuid.Parse(c.Param("id"))
		if err != nil {
			c.JSON(http.StatusBadRequest, gin.H{"error": "invalid task ID"})
			return
		}

		err = taskService.DeleteTask(c.Request.Context(), id)
		if err != nil {
			if err == task.ErrTaskNotFound {
				c.JSON(http.StatusNotFound, gin.H{"error": "task not found"})
				return
			}
			c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
			return
		}

		c.Status(http.StatusNoContent)
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
