package handlers

import (
	"net/http"
	"strconv"

	"github.com/ahmedelhadi17776/Compass/Backend_go/internal/api/dto"
	"github.com/ahmedelhadi17776/Compass/Backend_go/internal/domain/task"
	"github.com/gin-gonic/gin"
	"github.com/google/uuid"
)

// TaskHandler handles HTTP requests for task operations
type TaskHandler struct {
	service task.Service
}

// NewTaskHandler creates a new TaskHandler instance
func NewTaskHandler(service task.Service) *TaskHandler {
	return &TaskHandler{service: service}
}

// CreateTask godoc
// @Summary Create a new task
// @Description Create a new task with the provided information
// @Tags tasks
// @Accept json
// @Produce json
// @Security BearerAuth
// @Param task body dto.CreateTaskRequest true "Task creation request"
// @Success 201 {object} dto.TaskResponse "Task created successfully"
// @Failure 400 {object} map[string]string "Invalid request"
// @Failure 401 {object} map[string]string "Unauthorized"
// @Failure 500 {object} map[string]string "Internal server error"
// @Router /api/tasks [post]
func (h *TaskHandler) CreateTask(c *gin.Context) {
	var req dto.CreateTaskRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	// Get creator ID from context (set by auth middleware)
	creatorID, exists := c.Get("user_id")
	if !exists {
		c.JSON(http.StatusUnauthorized, gin.H{"error": "user not authenticated"})
		return
	}

	input := task.CreateTaskInput{
		Title:          req.Title,
		Description:    req.Description,
		Status:         req.Status,
		Priority:       req.Priority,
		ProjectID:      req.ProjectID,
		OrganizationID: req.OrganizationID,
		AssigneeID:     req.AssigneeID,
		ReviewerID:     req.ReviewerID,
		CategoryID:     req.CategoryID,
		ParentTaskID:   req.ParentTaskID,
		EstimatedHours: req.EstimatedHours,
		StartDate:      req.StartDate,
		Duration:       req.Duration,
		DueDate:        req.DueDate,
		Dependencies:   req.Dependencies,
		CreatorID:      creatorID.(uuid.UUID),
	}

	createdTask, err := h.service.CreateTask(c.Request.Context(), input)
	if err != nil {
		statuscode := http.StatusInternalServerError
		if err == task.ErrInvalidInput {
			statuscode = http.StatusBadRequest
		}
		c.JSON(statuscode, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusCreated, gin.H{"data": dto.TaskToResponse(createdTask)})
}

// GetTask godoc
// @Summary Get a task by ID
// @Description Get detailed information about a specific task
// @Tags tasks
// @Accept json
// @Produce json
// @Security BearerAuth
// @Param id path string true "Task ID" format(uuid)
// @Success 200 {object} dto.TaskResponse "Task details retrieved successfully"
// @Failure 400 {object} map[string]string "Invalid task ID"
// @Failure 401 {object} map[string]string "Unauthorized"
// @Failure 404 {object} map[string]string "Task not found"
// @Failure 500 {object} map[string]string "Internal server error"
// @Router /api/tasks/{id} [get]
func (h *TaskHandler) GetTask(c *gin.Context) {
	id, err := uuid.Parse(c.Param("id"))
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid task ID"})
		return
	}

	tsk, err := h.service.GetTask(c.Request.Context(), id)
	if err != nil {
		statuscode := http.StatusInternalServerError
		if err == task.ErrTaskNotFound {
			statuscode = http.StatusNotFound
		}
		c.JSON(statuscode, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{"data": dto.TaskToResponse(tsk)})
}

// ListTasks godoc
// @Summary List all tasks
// @Description Get a paginated list of tasks with optional filters
// @Tags tasks
// @Accept json
// @Produce json
// @Security BearerAuth
// @Param page query int false "Page number (default: 0)"
// @Param pageSize query int false "Number of items per page (default: 10)"
// @Success 200 {object} dto.TaskListResponse "List of tasks retrieved successfully"
// @Failure 400 {object} map[string]string "Invalid pagination parameters"
// @Failure 401 {object} map[string]string "Unauthorized"
// @Failure 500 {object} map[string]string "Internal server error"
// @Router /api/tasks [get]
func (h *TaskHandler) ListTasks(c *gin.Context) {
	pageStr := c.DefaultQuery("page", "0")
	pageSizeStr := c.DefaultQuery("pageSize", "10")

	page, err := strconv.Atoi(pageStr)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid page number"})
		return
	}
	pageSize, err := strconv.Atoi(pageSizeStr)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid page size"})
		return
	}

	filter := task.TaskFilter{
		Page:     page,
		PageSize: pageSize,
	}

	tasks, total, err := h.service.ListTasks(c.Request.Context(), filter)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	// Convert tasks to response DTOs
	taskResponses := make([]dto.TaskResponse, len(tasks))
	for i, t := range tasks {
		response := dto.TaskToResponse(&t)
		taskResponses[i] = *response
	}

	response := dto.TaskListResponse{
		Tasks:      taskResponses,
		TotalCount: total,
		Page:       page,
		PageSize:   pageSize,
	}

	c.JSON(http.StatusOK, gin.H{"data": response})
}

// UpdateTask godoc
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
// @Failure 404 {object} map[string]string "Task not found"
// @Failure 500 {object} map[string]string "Internal server error"
// @Router /api/tasks/{id} [put]
func (h *TaskHandler) UpdateTask(c *gin.Context) {
	id, err := uuid.Parse(c.Param("id"))
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid task ID"})
		return
	}

	var req dto.UpdateTaskRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	input := task.UpdateTaskInput{
		Title:          req.Title,
		Description:    req.Description,
		Status:         req.Status,
		Priority:       req.Priority,
		AssigneeID:     req.AssigneeID,
		ReviewerID:     req.ReviewerID,
		CategoryID:     req.CategoryID,
		EstimatedHours: req.EstimatedHours,
		StartDate:      req.StartDate,
		Duration:       req.Duration,
		DueDate:        req.DueDate,
		Dependencies:   req.Dependencies,
	}

	updatedTask, err := h.service.UpdateTask(c.Request.Context(), id, input)
	if err != nil {
		statuscode := http.StatusInternalServerError
		if err == task.ErrTaskNotFound {
			statuscode = http.StatusNotFound
		} else if err == task.ErrInvalidInput {
			statuscode = http.StatusBadRequest
		}
		c.JSON(statuscode, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{"data": dto.TaskToResponse(updatedTask)})
}

// DeleteTask godoc
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
// @Failure 404 {object} map[string]string "Task not found"
// @Failure 500 {object} map[string]string "Internal server error"
// @Router /api/tasks/{id} [delete]
func (h *TaskHandler) DeleteTask(c *gin.Context) {
	id, err := uuid.Parse(c.Param("id"))
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid task ID"})
		return
	}

	err = h.service.DeleteTask(c.Request.Context(), id)
	if err != nil {
		statuscode := http.StatusInternalServerError
		if err == task.ErrTaskNotFound {
			statuscode = http.StatusNotFound
		}
		c.JSON(statuscode, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusNoContent, nil)
}
