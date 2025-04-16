package handlers

import (
	"net/http"
	"strconv"

	"github.com/ahmedelhadi17776/Compass/Backend_go/internal/api/dto"
	"github.com/ahmedelhadi17776/Compass/Backend_go/internal/domain/task"
	"github.com/gin-gonic/gin"
	"github.com/google/uuid"
)

type TaskHandler struct {
	service task.Service
}

func NewTaskHandler(service task.Service) *TaskHandler {
	return &TaskHandler{service: service}
}

// @Router /tasks [post]
func (h *TaskHandler) CreateTask(c *gin.Context) {
	var req dto.CreateTaskRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	input := task.CreateTaskInput{
		Title:          req.Title,
		Description:    req.Description,
		Status:         task.TaskStatus(req.Status),
		Priority:       task.TaskPriority(req.Priority),
		ProjectID:      req.ProjectID,
		AssigneeID:     req.AssigneeID,
		EstimatedHours: req.EstimatedHours,
		StartDate:      req.StartDate,
		DueDate:        req.DueDate,
		Dependencies:   req.Dependencies,
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

	c.JSON(http.StatusCreated, createdTask)
}

// @Router /tasks/{id} [get]
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

	c.JSON(http.StatusOK, tsk)
}

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

	c.JSON(http.StatusOK, gin.H{
		"tasks": tasks,
		"total": total,
	})
}

// @Router /tasks/{id} [put]
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

	var statusPtr *task.TaskStatus
	if req.Status != nil {
		s := task.TaskStatus(*req.Status)
		statusPtr = &s
	}

	input := task.UpdateTaskInput{
		Title:          req.Title,
		Description:    req.Description,
		Status:         statusPtr,
		Priority:       req.Priority,
		AssigneeID:     req.AssigneeID,
		EstimatedHours: req.EstimatedHours,
		StartDate:      req.StartDate,
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

	c.JSON(http.StatusOK, updatedTask)
}

// @Router /tasks/{id} [delete]
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
