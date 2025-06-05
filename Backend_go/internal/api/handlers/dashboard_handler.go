package handlers

import (
	"net/http"

	"github.com/ahmedelhadi17776/Compass/Backend_go/internal/api/dto"
	"github.com/ahmedelhadi17776/Compass/Backend_go/internal/api/middleware"
	"github.com/ahmedelhadi17776/Compass/Backend_go/internal/domain/calendar"
	"github.com/ahmedelhadi17776/Compass/Backend_go/internal/domain/habits"
	"github.com/ahmedelhadi17776/Compass/Backend_go/internal/domain/task"
	"github.com/ahmedelhadi17776/Compass/Backend_go/internal/domain/todos"
	"github.com/ahmedelhadi17776/Compass/Backend_go/internal/domain/user"
	"github.com/gin-gonic/gin"
)

type DashboardHandler struct {
	habitsService   habits.Service
	tasksService    task.Service
	todosService    todos.Service
	calendarService calendar.Service
	userService     user.Service
}

func NewDashboardHandler(
	habitsService habits.Service,
	tasksService task.Service,
	todosService todos.Service,
	calendarService calendar.Service,
	userService user.Service,
) *DashboardHandler {
	return &DashboardHandler{
		habitsService:   habitsService,
		tasksService:    tasksService,
		todosService:    todosService,
		calendarService: calendarService,
		userService:     userService,
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

	habitsMetrics, _ := h.habitsService.GetDashboardMetrics(userID)
	tasksMetrics, _ := h.tasksService.GetDashboardMetrics(userID)
	todosMetrics, _ := h.todosService.GetDashboardMetrics(userID)
	calendarMetrics, _ := h.calendarService.GetDashboardMetrics(userID)
	userMetrics, _ := h.userService.GetDashboardMetrics(userID)

	response := dto.DashboardMetricsResponse{
		Habits:   HabitsDashboardMetricsToDTO(habitsMetrics),
		Tasks:    TasksDashboardMetricsToDTO(tasksMetrics),
		Todos:    TodosDashboardMetricsToDTO(todosMetrics),
		Calendar: CalendarDashboardMetricsToDTO(calendarMetrics),
		User:     UserDashboardMetricsToDTO(userMetrics),
	}
	c.JSON(http.StatusOK, gin.H{"data": response})
}
