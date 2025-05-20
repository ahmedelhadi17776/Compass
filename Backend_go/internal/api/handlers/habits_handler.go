package handlers

import (
	"net/http"
	"strconv"
	"time"

	"github.com/ahmedelhadi17776/Compass/Backend_go/internal/api/dto"
	"github.com/ahmedelhadi17776/Compass/Backend_go/internal/api/middleware"
	"github.com/ahmedelhadi17776/Compass/Backend_go/internal/domain/habits"
	"github.com/gin-gonic/gin"
	"github.com/google/uuid"
)

// HabitsHandler handles HTTP requests for habits operations
type HabitsHandler struct {
	service habits.Service
}

// NewHabitsHandler creates a new HabitsHandler instance
func NewHabitsHandler(service habits.Service) *HabitsHandler {
	return &HabitsHandler{service: service}
}

// CreateHabit godoc
// @Summary Create a new habit
// @Description Create a new habit with the provided information
// @Tags habits
// @Accept json
// @Produce json
// @Security BearerAuth
// @Param habit body dto.CreateHabitRequest true "Habit creation request"
// @Success 201 {object} dto.HabitResponse "Habit created successfully"
// @Failure 400 {object} map[string]string "Invalid request"
// @Failure 401 {object} map[string]string "Unauthorized"
// @Failure 500 {object} map[string]string "Internal server error"
// @Router /api/habits [post]
func (h *HabitsHandler) CreateHabit(c *gin.Context) {
	var req dto.CreateHabitRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	// Get user ID from context (set by auth middleware)
	userID, exists := middleware.GetUserID(c)
	if !exists {
		c.JSON(http.StatusUnauthorized, gin.H{"error": "user not authenticated"})
		return
	}

	input := habits.CreateHabitInput{
		Title:       req.Title,
		Description: req.Description,
		StartDay:    req.StartDay,
		EndDay:      req.EndDay,
		UserID:      userID,
	}

	createdHabit, err := h.service.CreateHabit(c.Request.Context(), input)
	if err != nil {
		statusCode := http.StatusInternalServerError
		if err == habits.ErrInvalidInput {
			statusCode = http.StatusBadRequest
		}
		c.JSON(statusCode, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusCreated, gin.H{"data": dto.HabitToResponse(createdHabit)})
}

// GetHabit godoc
// @Summary Get a habit by ID
// @Description Get detailed information about a specific habit
// @Tags habits
// @Accept json
// @Produce json
// @Security BearerAuth
// @Param id path string true "Habit ID" format(uuid)
// @Success 200 {object} dto.HabitResponse "Habit details retrieved successfully"
// @Failure 400 {object} map[string]string "Invalid habit ID"
// @Failure 401 {object} map[string]string "Unauthorized"
// @Failure 404 {object} map[string]string "Habit not found"
// @Failure 500 {object} map[string]string "Internal server error"
// @Router /api/habits/{id} [get]
func (h *HabitsHandler) GetHabit(c *gin.Context) {
	id, err := uuid.Parse(c.Param("id"))
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid habit ID"})
		return
	}

	habit, err := h.service.GetHabit(c.Request.Context(), id)
	if err != nil {
		statusCode := http.StatusInternalServerError
		if err == habits.ErrHabitNotFound {
			statusCode = http.StatusNotFound
		}
		c.JSON(statusCode, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{"data": dto.HabitToResponse(habit)})
}

// ListHabits godoc
// @Description Get a list of all habits for the authenticated user
// @Tags habits
// @Accept json
// @Produce json
// @Security BearerAuth
// @Param page query int false "Page number" default(1)
// @Param page_size query int false "Number of habits per page" default(10)
// @Success 200 {object} dto.HabitListResponse "List of habits retrieved successfully"
// @Failure 400 {object} map[string]string "Invalid request parameters"
// @Failure 401 {object} map[string]string "Unauthorized"
// @Failure 500 {object} map[string]string "Internal server error"
// @Router /api/habits [get]
func (h *HabitsHandler) ListHabits(c *gin.Context) {
	pageStr := c.DefaultQuery("page", "0")
	pageSizeStr := c.DefaultQuery("page_size", "10")

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

	filter := habits.HabitFilter{
		Page:     page,
		PageSize: pageSize,
	}

	habits, total, err := h.service.ListHabits(c.Request.Context(), filter)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	responses := make([]dto.HabitResponse, len(habits))
	for i, habit := range habits {
		response := dto.HabitToResponse(&habit)
		responses[i] = *response
	}

	c.JSON(http.StatusOK, gin.H{"data": dto.HabitListResponse{
		Habits:     responses,
		TotalCount: total,
		Page:       page,
		PageSize:   pageSize,
	}})
}

// UpdateHabit godoc
// @Summary Update a habit
// @Description Update an existing habit's information
// @Tags habits
// @Accept json
// @Produce json
// @Security BearerAuth
// @Param id path string true "Habit ID" format(uuid)
// @Param habit body dto.UpdateHabitRequest true "Habit update information"
// @Success 200 {object} dto.HabitResponse "Habit updated successfully"
// @Failure 400 {object} map[string]string "Invalid request or habit ID"
// @Failure 401 {object} map[string]string "Unauthorized"
// @Failure 404 {object} map[string]string "Habit not found"
// @Failure 500 {object} map[string]string "Internal server error"
// @Router /api/habits/{id} [put]
func (h *HabitsHandler) UpdateHabit(c *gin.Context) {
	id, err := uuid.Parse(c.Param("id"))
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid habit ID"})
		return
	}

	var req dto.UpdateHabitRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	input := habits.UpdateHabitInput{
		Title:       req.Title,
		Description: req.Description,
		StartDay:    req.StartDay,
		EndDay:      req.EndDay,
	}

	updatedHabit, err := h.service.UpdateHabit(c.Request.Context(), id, input)
	if err != nil {
		statusCode := http.StatusInternalServerError
		if err == habits.ErrHabitNotFound {
			statusCode = http.StatusNotFound
		}
		c.JSON(statusCode, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{"data": dto.HabitToResponse(updatedHabit)})
}

// DeleteHabit godoc
// @Summary Delete a habit
// @Description Delete a habit by ID
// @Tags habits
// @Accept json
// @Produce json
// @Security BearerAuth
// @Param id path string true "Habit ID" format(uuid)
// @Success 204 "Habit deleted successfully"
// @Failure 400 {object} map[string]string "Invalid habit ID"
// @Failure 401 {object} map[string]string "Unauthorized"
// @Failure 404 {object} map[string]string "Habit not found"
// @Failure 500 {object} map[string]string "Internal server error"
// @Router /api/habits/{id} [delete]
func (h *HabitsHandler) DeleteHabit(c *gin.Context) {
	id, err := uuid.Parse(c.Param("id"))
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid habit ID"})
		return
	}

	err = h.service.DeleteHabit(c.Request.Context(), id)
	if err != nil {
		statusCode := http.StatusInternalServerError
		if err == habits.ErrHabitNotFound {
			statusCode = http.StatusNotFound
		}
		c.JSON(statusCode, gin.H{"error": err.Error()})
		return
	}

	c.Status(http.StatusNoContent)
}

// GetStreakHistory godoc
// @Summary Get streak history for a habit
// @Description Get the streak history for a specific habit
// @Tags habits
// @Accept json
// @Produce json
// @Security BearerAuth
// @Param id path string true "Habit ID" format(uuid)
// @Success 200 {array} dto.StreakHistoryResponse "Streak history retrieved successfully"
// @Failure 400 {object} map[string]string "Invalid habit ID"
// @Failure 401 {object} map[string]string "Unauthorized"
// @Failure 404 {object} map[string]string "Habit not found"
// @Failure 500 {object} map[string]string "Internal server error"
// @Router /api/habits/{id}/streak-history [get]
func (h *HabitsHandler) GetStreakHistory(c *gin.Context) {
	id, err := uuid.Parse(c.Param("id"))
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid habit ID"})
		return
	}

	history, err := h.service.GetStreakHistory(c.Request.Context(), id)
	if err != nil {
		statusCode := http.StatusInternalServerError
		if err == habits.ErrHabitNotFound {
			statusCode = http.StatusNotFound
		}
		c.JSON(statusCode, gin.H{"error": err.Error()})
		return
	}

	responses := make([]dto.StreakHistoryResponse, len(history))
	for i, h := range history {
		responses[i] = *dto.StreakHistoryToResponse(&h)
	}

	c.JSON(http.StatusOK, gin.H{"data": responses})
}

// GetHabitsDueToday godoc
// @Summary Get habits due today
// @Description Get all habits that are due for completion today
// @Tags habits
// @Accept json
// @Produce json
// @Security BearerAuth
// @Success 200 {array} dto.HabitResponse "Habits due today retrieved successfully"
// @Failure 401 {object} map[string]string "Unauthorized"
// @Failure 500 {object} map[string]string "Internal server error"
// @Router /api/habits/due-today [get]
func (h *HabitsHandler) GetHabitsDueToday(c *gin.Context) {
	userID, exists := c.Get("user_id")
	if !exists {
		c.JSON(http.StatusUnauthorized, gin.H{"error": "user not authenticated"})
		return
	}

	habits, err := h.service.GetHabitsDueToday(c.Request.Context(), userID.(uuid.UUID))
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	responses := make([]dto.HabitResponse, len(habits))
	for i, habit := range habits {
		responses[i] = *dto.HabitToResponse(&habit)
	}

	c.JSON(http.StatusOK, gin.H{"data": responses})
}

// GetHabitStats godoc
// @Summary Get habit statistics
// @Description Get statistics for a specific habit
// @Tags habits
// @Accept json
// @Produce json
// @Security BearerAuth
// @Param id path string true "Habit ID" format(uuid)
// @Success 200 {object} dto.HabitStatsResponse "Habit statistics retrieved successfully"
// @Failure 400 {object} map[string]string "Invalid habit ID"
// @Failure 401 {object} map[string]string "Unauthorized"
// @Failure 404 {object} map[string]string "Habit not found"
// @Failure 500 {object} map[string]string "Internal server error"
// @Router /api/habits/{id}/stats [get]
func (h *HabitsHandler) GetHabitStats(c *gin.Context) {
	id, err := uuid.Parse(c.Param("id"))
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid habit ID"})
		return
	}

	habit, err := h.service.GetHabit(c.Request.Context(), id)
	if err != nil {
		statusCode := http.StatusInternalServerError
		if err == habits.ErrHabitNotFound {
			statusCode = http.StatusNotFound
		}
		c.JSON(statusCode, gin.H{"error": err.Error()})
		return
	}

	stats := dto.HabitStatsResponse{
		TotalHabits:     1,
		ActiveHabits:    1,
		CompletedHabits: 0,
	}

	if habit.IsCompleted {
		stats.CompletedHabits = 1
		stats.ActiveHabits = 0
	}

	c.JSON(http.StatusOK, gin.H{"data": stats})
}

// MarkHabitCompleted godoc
// @Summary Mark a habit as completed
// @Description Mark a specific habit as completed for today or a specific date
// @Tags habits
// @Accept json
// @Produce json
// @Security BearerAuth
// @Param id path string true "Habit ID" format(uuid)
// @Param completion_date query string false "Completion date (YYYY-MM-DD)" format(date)
// @Success 200 {object} map[string]string "Habit marked as completed"
// @Failure 400 {object} map[string]string "Invalid habit ID or date"
// @Failure 401 {object} map[string]string "Unauthorized"
// @Failure 404 {object} map[string]string "Habit not found"
// @Failure 500 {object} map[string]string "Internal server error"
// @Router /api/habits/{id}/complete [post]
func (h *HabitsHandler) MarkHabitCompleted(c *gin.Context) {
	id, err := uuid.Parse(c.Param("id"))
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid habit ID"})
		return
	}

	userID, exists := c.Get("user_id")
	if !exists {
		c.JSON(http.StatusUnauthorized, gin.H{"error": "user not authenticated"})
		return
	}

	var completionDate *time.Time
	if dateStr := c.Query("completion_date"); dateStr != "" {
		date, err := time.Parse("2006-01-02", dateStr)
		if err != nil {
			c.JSON(http.StatusBadRequest, gin.H{"error": "invalid completion date format"})
			return
		}
		completionDate = &date
	}

	err = h.service.MarkCompleted(c.Request.Context(), id, userID.(uuid.UUID), completionDate)
	if err != nil {
		statusCode := http.StatusInternalServerError
		if err == habits.ErrHabitNotFound {
			statusCode = http.StatusNotFound
		}
		c.JSON(statusCode, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{"message": "habit marked as completed"})
}

// UnmarkHabitCompleted godoc
// @Summary Unmark a habit as completed
// @Description Remove the completion status of a habit for today
// @Tags habits
// @Accept json
// @Produce json
// @Security BearerAuth
// @Param id path string true "Habit ID" format(uuid)
// @Success 200 {object} map[string]string "Habit unmarked as completed"
// @Failure 400 {object} map[string]string "Invalid habit ID"
// @Failure 401 {object} map[string]string "Unauthorized"
// @Failure 404 {object} map[string]string "Habit not found"
// @Failure 500 {object} map[string]string "Internal server error"
// @Router /api/habits/{id}/uncomplete [post]
func (h *HabitsHandler) UnmarkHabitCompleted(c *gin.Context) {
	id, err := uuid.Parse(c.Param("id"))
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid habit ID"})
		return
	}

	userID, exists := c.Get("user_id")
	if !exists {
		c.JSON(http.StatusUnauthorized, gin.H{"error": "user not authenticated"})
		return
	}

	err = h.service.UnmarkCompleted(c.Request.Context(), id, userID.(uuid.UUID))
	if err != nil {
		statusCode := http.StatusInternalServerError
		if err == habits.ErrHabitNotFound {
			statusCode = http.StatusNotFound
		}
		c.JSON(statusCode, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{"message": "habit unmarked as completed"})
}

// GetUserHabits godoc
// @Summary Get habits by user ID
// @Description Get all habits for a specific user with optional active_only filter
// @Tags habits
// @Accept json
// @Produce json
// @Param user_id path string true "User ID"
// @Security BearerAuth
// @Success 200 {array} dto.HabitResponse "List of user habits"
// @Failure 400 {object} map[string]string "Invalid user ID"
// @Failure 500 {object} map[string]string "Internal server error"
// @Router /api/habits/user/{user_id} [get]
func (h *HabitsHandler) GetUserHabits(c *gin.Context) {
	userID, err := uuid.Parse(c.Param("user_id"))
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid user ID"})
		return
	}

	filter := habits.HabitFilter{
		UserID:   &userID,
		Page:     0,
		PageSize: 100, // You might want to make this configurable
	}

	habits, _, err := h.service.ListHabits(c.Request.Context(), filter)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	responses := make([]dto.HabitResponse, len(habits))
	for i, habit := range habits {
		responses[i] = *dto.HabitToResponse(&habit)
	}

	c.JSON(http.StatusOK, gin.H{"data": responses})
}

// GetHabitHeatmap godoc
// @Summary Get habit completion heatmap data
// @Description Get aggregated habit completion data for visualization as a heatmap
// @Tags habits
// @Accept json
// @Produce json
// @Security BearerAuth
// @Param period query string false "Time period for heatmap data (week, month, year)" Enums(week, month, year) default(year)
// @Success 200 {object} dto.HeatmapResponse "Heatmap data retrieved successfully"
// @Failure 401 {object} map[string]string "Unauthorized"
// @Failure 500 {object} map[string]string "Internal server error"
// @Router /api/habits/heatmap [get]
func (h *HabitsHandler) GetHabitHeatmap(c *gin.Context) {
	// Get user ID from context (set by auth middleware)
	userID, exists := middleware.GetUserID(c)
	if !exists {
		c.JSON(http.StatusUnauthorized, gin.H{"error": "user not authenticated"})
		return
	}

	// Get period from query parameters, default to year if not specified
	period := c.DefaultQuery("period", "year")
	if period != "week" && period != "month" && period != "year" {
		period = "year" // Default to year for invalid values
	}

	// Get heatmap data from service
	heatmapData, err := h.service.GetHeatmapData(c.Request.Context(), userID, period)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	// Find min and max values for the heatmap scale
	minValue := 0 // Minimum is always 0 for habit completions
	maxValue := 0
	for _, count := range heatmapData {
		if count > maxValue {
			maxValue = count
		}
	}

	// Return the response
	c.JSON(http.StatusOK, gin.H{"data": dto.HeatmapResponse{
		Data:     heatmapData,
		Period:   period,
		MinValue: minValue,
		MaxValue: maxValue,
	}})
}
