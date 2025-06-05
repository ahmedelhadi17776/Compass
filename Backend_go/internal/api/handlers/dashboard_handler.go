package handlers

import (
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"time"

	"github.com/ahmedelhadi17776/Compass/Backend_go/internal/api/dto"
	"github.com/ahmedelhadi17776/Compass/Backend_go/internal/api/middleware"
	"github.com/ahmedelhadi17776/Compass/Backend_go/internal/domain/calendar"
	"github.com/ahmedelhadi17776/Compass/Backend_go/internal/domain/events"
	"github.com/ahmedelhadi17776/Compass/Backend_go/internal/domain/habits"
	"github.com/ahmedelhadi17776/Compass/Backend_go/internal/domain/task"
	"github.com/ahmedelhadi17776/Compass/Backend_go/internal/domain/todos"
	"github.com/ahmedelhadi17776/Compass/Backend_go/internal/domain/user"
	"github.com/ahmedelhadi17776/Compass/Backend_go/internal/infrastructure/cache"
	"github.com/gin-gonic/gin"
	"go.uber.org/zap"
)

type DashboardHandler struct {
	habitsService   habits.Service
	tasksService    task.Service
	todosService    todos.Service
	calendarService calendar.Service
	userService     user.Service
	redisClient     *cache.RedisClient
	logger          *zap.Logger
}

func NewDashboardHandler(
	habitsService habits.Service,
	tasksService task.Service,
	todosService todos.Service,
	calendarService calendar.Service,
	userService user.Service,
	redisClient *cache.RedisClient,
	logger *zap.Logger,
) *DashboardHandler {
	return &DashboardHandler{
		habitsService:   habitsService,
		tasksService:    tasksService,
		todosService:    todosService,
		calendarService: calendarService,
		userService:     userService,
		redisClient:     redisClient,
		logger:          logger,
	}
}

// Conversion functions from domain metrics to DTO metrics
func HabitsDashboardMetricsToDTO(m habits.HabitsDashboardMetrics) dto.HabitsDashboardMetrics {
	return dto.HabitsDashboardMetrics{
		Total:     m.Total,
		Active:    m.Active,
		Completed: m.Completed,
		Streak:    m.Streak,
	}
}

func TasksDashboardMetricsToDTO(m task.TasksDashboardMetrics) dto.TasksDashboardMetrics {
	return dto.TasksDashboardMetrics{
		Total:     m.Total,
		Completed: m.Completed,
		Overdue:   m.Overdue,
	}
}

func TodosDashboardMetricsToDTO(m todos.TodosDashboardMetrics) dto.TodosDashboardMetrics {
	return dto.TodosDashboardMetrics{
		Total:     m.Total,
		Completed: m.Completed,
		Overdue:   m.Overdue,
	}
}

func CalendarDashboardMetricsToDTO(m calendar.CalendarDashboardMetrics) dto.CalendarDashboardMetrics {
	return dto.CalendarDashboardMetrics{
		Upcoming: m.Upcoming,
		Total:    m.Total,
	}
}

func UserDashboardMetricsToDTO(m user.UserDashboardMetrics) dto.UserDashboardMetrics {
	return dto.UserDashboardMetrics{
		ActivitySummary: m.ActivitySummary,
	}
}

func (h *DashboardHandler) GetDashboardMetrics(c *gin.Context) {
	userID, exists := middleware.GetUserID(c)
	if !exists {
		c.JSON(http.StatusUnauthorized, gin.H{"error": "user not authenticated"})
		return
	}

	// Use the standardized cache key
	cacheKey := fmt.Sprintf("dashboard:metrics:%v", userID)
	cachedData, err := h.redisClient.Get(c.Request.Context(), cacheKey)
	if err == nil && cachedData != "" {
		var response dto.DashboardMetricsResponse
		if err := json.Unmarshal([]byte(cachedData), &response); err == nil {
			c.JSON(http.StatusOK, gin.H{"data": response})
			return
		}
	}

	// Collect metrics from all services
	habitsMetrics, err := h.habitsService.GetDashboardMetrics(userID)
	if err != nil {
		h.logger.Error("Failed to get habits metrics", zap.Error(err))
	}

	tasksMetrics, err := h.tasksService.GetDashboardMetrics(userID)
	if err != nil {
		h.logger.Error("Failed to get tasks metrics", zap.Error(err))
	}

	todosMetrics, err := h.todosService.GetDashboardMetrics(userID)
	if err != nil {
		h.logger.Error("Failed to get todos metrics", zap.Error(err))
	}

	calendarMetrics, err := h.calendarService.GetDashboardMetrics(userID)
	if err != nil {
		h.logger.Error("Failed to get calendar metrics", zap.Error(err))
	}

	userMetrics, err := h.userService.GetDashboardMetrics(userID)
	if err != nil {
		h.logger.Error("Failed to get user metrics", zap.Error(err))
	}

	response := dto.DashboardMetricsResponse{
		Habits:    HabitsDashboardMetricsToDTO(habitsMetrics),
		Tasks:     TasksDashboardMetricsToDTO(tasksMetrics),
		Todos:     TodosDashboardMetricsToDTO(todosMetrics),
		Calendar:  CalendarDashboardMetricsToDTO(calendarMetrics),
		User:      UserDashboardMetricsToDTO(userMetrics),
		Timestamp: time.Now().UTC(),
	}

	// Cache the response using the new key
	if data, err := json.Marshal(response); err == nil {
		if err := h.redisClient.Set(c.Request.Context(), cacheKey, string(data), 5*time.Minute); err != nil {
			h.logger.Error("Failed to cache dashboard metrics", zap.Error(err))
		}
	}

	c.JSON(http.StatusOK, gin.H{"data": response})
}

// StartDashboardEventListener starts listening for dashboard events
func (h *DashboardHandler) StartDashboardEventListener(ctx context.Context) {
	go func() {
		err := h.redisClient.SubscribeToDashboardEvents(ctx, func(event *events.DashboardEvent) error {
			h.logger.Info("Received dashboard event",
				zap.String("event_type", event.EventType),
				zap.String("user_id", event.UserID.String()))

			// Invalidate all dashboard cache keys for the affected user (handles double prefix)
			pattern := fmt.Sprintf("compass:dashboard:*:%s", event.UserID.String())
			if err := h.redisClient.ClearByPattern(ctx, pattern); err != nil {
				h.logger.Error("Failed to invalidate dashboard cache",
					zap.Error(err),
					zap.String("event_type", event.EventType),
					zap.String("user_id", event.UserID.String()))
			} else {
				h.logger.Info("Successfully invalidated dashboard cache",
					zap.String("user_id", event.UserID.String()))
			}
			return nil
		})
		if err != nil {
			h.logger.Error("Dashboard event listener error", zap.Error(err))
		}
	}()
}
