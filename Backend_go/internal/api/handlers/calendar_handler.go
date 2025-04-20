package handlers

import (
	"net/http"
	"time"

	"github.com/ahmedelhadi17776/Compass/Backend_go/internal/api/middleware"
	"github.com/ahmedelhadi17776/Compass/Backend_go/internal/domain/calendar"
	"github.com/gin-gonic/gin"
	"github.com/google/uuid"
)

// CalendarHandler handles HTTP requests for calendar events
type CalendarHandler struct {
	service calendar.Service
}

// NewCalendarHandler creates a new calendar handler instance
func NewCalendarHandler(service calendar.Service) *CalendarHandler {
	return &CalendarHandler{service: service}
}

// CreateEvent godoc
// @Summary Create a new calendar event
// @Description Create a new calendar event with optional recurrence rules and reminders
// @Tags calendar
// @Accept json
// @Produce json
// @Security BearerAuth
// @Param event body calendar.CreateCalendarEventRequest true "Event creation information"
// @Success 201 {object} calendar.CalendarEventResponse "Event created successfully"
// @Failure 400 {object} map[string]string "Invalid request"
// @Failure 401 {object} map[string]string "Unauthorized"
// @Failure 500 {object} map[string]string "Internal server error"
// @Router /api/calendar/events [post]
func (h *CalendarHandler) CreateEvent(c *gin.Context) {
	var req calendar.CreateCalendarEventRequest
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

	event, err := h.service.CreateEvent(c.Request.Context(), req, userID)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusCreated, calendar.CalendarEventResponse{Event: *event})
}

// ListEvents godoc
// @Summary List calendar events
// @Description Get a list of calendar events with pagination and filtering
// @Tags calendar
// @Accept json
// @Produce json
// @Security BearerAuth
// @Param start_time query string true "Start time (RFC3339)" format(date-time)
// @Param end_time query string true "End time (RFC3339)" format(date-time)
// @Param event_type query string false "Event type filter"
// @Param page query int false "Page number (default: 1)"
// @Param page_size query int false "Page size (default: 10)"
// @Param search query string false "Search term"
// @Success 200 {object} calendar.CalendarEventListResponse "List of events"
// @Failure 400 {object} map[string]string "Invalid request"
// @Failure 401 {object} map[string]string "Unauthorized"
// @Failure 500 {object} map[string]string "Internal server error"
// @Router /api/calendar/events [get]
func (h *CalendarHandler) ListEvents(c *gin.Context) {
	var params struct {
		StartTime time.Time           `form:"start_time" binding:"required"`
		EndTime   time.Time           `form:"end_time" binding:"required"`
		EventType *calendar.EventType `form:"event_type"`
		Page      int                 `form:"page,default=1" binding:"min=1"`
		PageSize  int                 `form:"page_size,default=10" binding:"min=1,max=100"`
		Search    string              `form:"search"`
	}
	if err := c.ShouldBindQuery(&params); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	// Get user ID from context (set by auth middleware)
	userID, exists := middleware.GetUserID(c)
	if !exists {
		c.JSON(http.StatusUnauthorized, gin.H{"error": "user not authenticated"})
		return
	}

	response, err := h.service.ListEvents(
		c.Request.Context(),
		userID,
		params.StartTime,
		params.EndTime,
		params.EventType,
		params.Page,
		params.PageSize,
	)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, response)
}

// GetEvent godoc
// @Summary Get a calendar event by ID
// @Description Get detailed information about a specific calendar event
// @Tags calendar
// @Accept json
// @Produce json
// @Security BearerAuth
// @Param id path string true "Event ID" format(uuid)
// @Success 200 {object} calendar.CalendarEventResponse "Event details"
// @Failure 400 {object} map[string]string "Invalid event ID"
// @Failure 401 {object} map[string]string "Unauthorized"
// @Failure 404 {object} map[string]string "Event not found"
// @Failure 500 {object} map[string]string "Internal server error"
// @Router /api/calendar/events/{id} [get]
func (h *CalendarHandler) GetEvent(c *gin.Context) {
	id, err := uuid.Parse(c.Param("id"))
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid event ID"})
		return
	}

	event, err := h.service.GetEventByID(c.Request.Context(), id)
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "event not found"})
		return
	}

	c.JSON(http.StatusOK, calendar.CalendarEventResponse{Event: *event})
}

// UpdateEvent godoc
// @Summary Update a calendar event
// @Description Update an existing calendar event
// @Tags calendar
// @Accept json
// @Produce json
// @Security BearerAuth
// @Param id path string true "Event ID" format(uuid)
// @Param event body calendar.UpdateCalendarEventRequest true "Event update information"
// @Success 200 {object} calendar.CalendarEventResponse "Event updated successfully"
// @Failure 400 {object} map[string]string "Invalid request"
// @Failure 401 {object} map[string]string "Unauthorized"
// @Failure 404 {object} map[string]string "Event not found"
// @Failure 500 {object} map[string]string "Internal server error"
// @Router /api/calendar/events/{id} [put]
func (h *CalendarHandler) UpdateEvent(c *gin.Context) {
	id, err := uuid.Parse(c.Param("id"))
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid event ID"})
		return
	}

	var req calendar.UpdateCalendarEventRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	event, err := h.service.UpdateEvent(c.Request.Context(), id, req)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, calendar.CalendarEventResponse{Event: *event})
}

// DeleteEvent godoc
// @Summary Delete a calendar event
// @Description Delete an existing calendar event and all its related data
// @Tags calendar
// @Accept json
// @Produce json
// @Security BearerAuth
// @Param id path string true "Event ID" format(uuid)
// @Success 204 "Event deleted successfully"
// @Failure 400 {object} map[string]string "Invalid event ID"
// @Failure 401 {object} map[string]string "Unauthorized"
// @Failure 500 {object} map[string]string "Internal server error"
// @Router /api/calendar/events/{id} [delete]
func (h *CalendarHandler) DeleteEvent(c *gin.Context) {
	id, err := uuid.Parse(c.Param("id"))
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid event ID"})
		return
	}

	if err := h.service.DeleteEvent(c.Request.Context(), id); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.Status(http.StatusNoContent)
}

// UpdateOccurrence godoc
// @Summary Update a specific occurrence of a recurring event
// @Description Modify a single occurrence of a recurring event
// @Tags calendar
// @Accept json
// @Produce json
// @Security BearerAuth
// @Param request body calendar.UpdateCalendarEventRequest true "Occurrence update information"
// @Success 200 "Occurrence updated successfully"
// @Failure 400 {object} map[string]string "Invalid request"
// @Failure 401 {object} map[string]string "Unauthorized"
// @Failure 500 {object} map[string]string "Internal server error"
// @Router /api/calendar/events/occurrence [put]
func (h *CalendarHandler) UpdateOccurrence(c *gin.Context) {
	var req struct {
		EventID      uuid.UUID                           `json:"event_id" binding:"required"`
		OriginalTime time.Time                           `json:"original_time" binding:"required"`
		Updates      calendar.UpdateCalendarEventRequest `json:"updates" binding:"required"`
	}
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	err := h.service.UpdateOccurrence(
		c.Request.Context(),
		req.EventID,
		req.OriginalTime,
		req.Updates,
	)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.Status(http.StatusOK)
}

// DeleteOccurrence godoc
// @Summary Delete a specific occurrence of a recurring event
// @Description Mark a single occurrence of a recurring event as deleted
// @Tags calendar
// @Accept json
// @Produce json
// @Security BearerAuth
// @Param event_id query string true "Event ID" format(uuid)
// @Param original_time query string true "Original occurrence time" format(date-time)
// @Success 204 "Occurrence deleted successfully"
// @Failure 400 {object} map[string]string "Invalid request"
// @Failure 401 {object} map[string]string "Unauthorized"
// @Failure 500 {object} map[string]string "Internal server error"
// @Router /api/calendar/events/occurrence [delete]
func (h *CalendarHandler) DeleteOccurrence(c *gin.Context) {
	eventID, err := uuid.Parse(c.Query("event_id"))
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid event ID"})
		return
	}

	originalTime, err := time.Parse(time.RFC3339, c.Query("original_time"))
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid time format"})
		return
	}

	if err := h.service.DeleteOccurrence(c.Request.Context(), eventID, originalTime); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.Status(http.StatusNoContent)
}

// AddReminder godoc
// @Summary Add a reminder to an event
// @Description Add a new reminder to an existing calendar event
// @Tags calendar
// @Accept json
// @Produce json
// @Security BearerAuth
// @Param event_id path string true "Event ID" format(uuid)
// @Param reminder body calendar.CreateEventReminderRequest true "Reminder information"
// @Success 201 "Reminder added successfully"
// @Failure 400 {object} map[string]string "Invalid request"
// @Failure 401 {object} map[string]string "Unauthorized"
// @Failure 500 {object} map[string]string "Internal server error"
// @Router /api/calendar/events/{event_id}/reminders [post]
func (h *CalendarHandler) AddReminder(c *gin.Context) {
	eventID, err := uuid.Parse(c.Param("event_id"))
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid event ID"})
		return
	}

	var req calendar.CreateEventReminderRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	if err := h.service.AddReminder(c.Request.Context(), eventID, req); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.Status(http.StatusCreated)
}
