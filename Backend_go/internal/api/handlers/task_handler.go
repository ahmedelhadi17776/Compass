package handlers

import (
	"net/http"
	"strconv"

	"github.com/ahmedelhadi17776/Compass/Backend_go/internal/api/dto"
	"github.com/ahmedelhadi17776/Compass/Backend_go/internal/api/middleware"
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
// @Failure 403 {object} map[string]string "Insufficient permissions"
// @Failure 500 {object} map[string]string "Internal server error"
// @Router /api/tasks [post]
func (h *TaskHandler) CreateTask(c *gin.Context) {
	var req dto.CreateTaskRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	// Get creator ID from context (set by auth middleware)
	creatorID, exists := middleware.GetUserID(c)
	if !exists {
		c.JSON(http.StatusUnauthorized, gin.H{"error": "user not authenticated"})
		return
	}

	// Convert and validate status
	status := task.TaskStatus(req.Status)
	if !status.IsValid() {
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid status value"})
		return
	}

	// Convert and validate priority
	priority := task.TaskPriority(req.Priority)
	if !priority.IsValid() {
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid priority value"})
		return
	}

	input := task.CreateTaskInput{
		Title:          req.Title,
		Description:    req.Description,
		Status:         status,
		Priority:       priority,
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
		CreatorID:      creatorID,
	}

	createdTask, err := h.service.CreateTask(c.Request.Context(), input)
	if err != nil {
		statuscode := http.StatusInternalServerError
		if err == task.ErrInvalidInput {
			statuscode = http.StatusBadRequest
		} else if err == task.ErrInvalidCreator {
			statuscode = http.StatusForbidden
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

	// Get organization ID from context
	orgID, exists := c.Get("org_id")
	if !exists {
		c.JSON(http.StatusBadRequest, gin.H{"error": "organization context not found"})
		return
	}

	// Convert orgID to uuid.UUID
	orgUUID, ok := orgID.(uuid.UUID)
	if !ok {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "invalid organization ID format"})
		return
	}

	// Verify task belongs to organization
	tsk, err := h.service.GetTask(c.Request.Context(), id)
	if err != nil {
		statuscode := http.StatusInternalServerError
		if err == task.ErrTaskNotFound {
			statuscode = http.StatusNotFound
		}
		c.JSON(statuscode, gin.H{"error": err.Error()})
		return
	}

	// Check if task belongs to the organization
	if tsk.OrganizationID != orgUUID {
		c.JSON(http.StatusForbidden, gin.H{"error": "task does not belong to the organization"})
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
// @Param organization_id query string false "Filter by organization ID"
// @Param project_id query string false "Filter by project ID"
// @Param status query string false "Filter by status"
// @Param priority query string false "Filter by priority"
// @Param assignee_id query string false "Filter by assignee ID"
// @Param creator_id query string false "Filter by creator ID"
// @Param reviewer_id query string false "Filter by reviewer ID"
// @Success 200 {object} dto.TaskListResponse "List of tasks retrieved successfully"
// @Failure 400 {object} map[string]string "Invalid pagination parameters"
// @Failure 401 {object} map[string]string "Unauthorized"
// @Failure 403 {object} map[string]string "Insufficient permissions"
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

	// Get organization ID from context
	orgID, exists := c.Get("org_id")
	if !exists {
		c.JSON(http.StatusBadRequest, gin.H{"error": "organization context not found"})
		return
	}

	// Convert orgID to uuid.UUID
	orgUUID, ok := orgID.(uuid.UUID)
	if !ok {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "invalid organization ID format"})
		return
	}

	filter := task.TaskFilter{
		Page:           page,
		PageSize:       pageSize,
		OrganizationID: &orgUUID,
	}

	// Parse optional filters
	if projectIDStr := c.Query("project_id"); projectIDStr != "" {
		if projectID, err := uuid.Parse(projectIDStr); err == nil {
			filter.ProjectID = &projectID
		}
	}
	if statusStr := c.Query("status"); statusStr != "" {
		status := task.TaskStatus(statusStr)
		if status.IsValid() {
			filter.Status = &status
		}
	}
	if priorityStr := c.Query("priority"); priorityStr != "" {
		priority := task.TaskPriority(priorityStr)
		if priority.IsValid() {
			filter.Priority = &priority
		}
	}
	if assigneeIDStr := c.Query("assignee_id"); assigneeIDStr != "" {
		if assigneeID, err := uuid.Parse(assigneeIDStr); err == nil {
			filter.AssigneeID = &assigneeID
		}
	}
	if creatorIDStr := c.Query("creator_id"); creatorIDStr != "" {
		if creatorID, err := uuid.Parse(creatorIDStr); err == nil {
			filter.CreatorID = &creatorID
		}
	}
	if reviewerIDStr := c.Query("reviewer_id"); reviewerIDStr != "" {
		if reviewerID, err := uuid.Parse(reviewerIDStr); err == nil {
			filter.ReviewerID = &reviewerID
		}
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

	// Get organization ID from context
	orgID, exists := c.Get("org_id")
	if !exists {
		c.JSON(http.StatusBadRequest, gin.H{"error": "organization context not found"})
		return
	}

	// Convert orgID to uuid.UUID
	orgUUID, ok := orgID.(uuid.UUID)
	if !ok {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "invalid organization ID format"})
		return
	}

	// Verify task belongs to organization
	existingTask, err := h.service.GetTask(c.Request.Context(), id)
	if err != nil {
		statuscode := http.StatusInternalServerError
		if err == task.ErrTaskNotFound {
			statuscode = http.StatusNotFound
		}
		c.JSON(statuscode, gin.H{"error": err.Error()})
		return
	}

	// Check if task belongs to the organization
	if existingTask.OrganizationID != orgUUID {
		c.JSON(http.StatusForbidden, gin.H{"error": "task does not belong to the organization"})
		return
	}

	input := task.UpdateTaskInput{
		Title:          req.Title,
		Description:    req.Description,
		AssigneeID:     req.AssigneeID,
		ReviewerID:     req.ReviewerID,
		CategoryID:     req.CategoryID,
		EstimatedHours: req.EstimatedHours,
		StartDate:      req.StartDate,
		Duration:       req.Duration,
		DueDate:        req.DueDate,
		Dependencies:   req.Dependencies,
	}

	// Convert status if provided
	if req.Status != nil {
		status := task.TaskStatus(*req.Status)
		if !status.IsValid() {
			c.JSON(http.StatusBadRequest, gin.H{"error": "invalid status value"})
			return
		}
		input.Status = &status
	}

	// Convert priority if provided
	if req.Priority != nil {
		priority := task.TaskPriority(*req.Priority)
		if !priority.IsValid() {
			c.JSON(http.StatusBadRequest, gin.H{"error": "invalid priority value"})
			return
		}
		input.Priority = &priority
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

	// Get organization ID from context
	orgID, exists := c.Get("org_id")
	if !exists {
		c.JSON(http.StatusBadRequest, gin.H{"error": "organization context not found"})
		return
	}

	// Convert orgID to uuid.UUID
	orgUUID, ok := orgID.(uuid.UUID)
	if !ok {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "invalid organization ID format"})
		return
	}

	// Verify task belongs to organization
	existingTask, err := h.service.GetTask(c.Request.Context(), id)
	if err != nil {
		statuscode := http.StatusInternalServerError
		if err == task.ErrTaskNotFound {
			statuscode = http.StatusNotFound
		}
		c.JSON(statuscode, gin.H{"error": err.Error()})
		return
	}

	// Check if task belongs to the organization
	if existingTask.OrganizationID != orgUUID {
		c.JSON(http.StatusForbidden, gin.H{"error": "task does not belong to the organization"})
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

	c.Status(http.StatusNoContent)
}
