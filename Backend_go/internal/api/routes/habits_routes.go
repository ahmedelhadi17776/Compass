package routes

import (
	"github.com/ahmedelhadi17776/Compass/Backend_go/internal/api/handlers"
	"github.com/ahmedelhadi17776/Compass/Backend_go/internal/api/middleware"
	"github.com/gin-gonic/gin"
)

type HabitsRoutes struct {
	handler   *handlers.HabitsHandler
	jwtSecret string
}

func NewHabitsRoutes(handler *handlers.HabitsHandler, jwtSecret string) *HabitsRoutes {
	return &HabitsRoutes{
		handler:   handler,
		jwtSecret: jwtSecret,
	}
}

// RegisterHabitsRoutes registers all habit-related routes
// @Summary Register habits routes
// @Description Register all habit-related routes with their handlers
// @Tags habits
// @Security BearerAuth
func (h *HabitsRoutes) RegisterRoutes(router *gin.Engine) {
	habits := router.Group("/api/habits")
	habits.Use(middleware.NewAuthMiddleware(h.jwtSecret))

	// CRUD operations
	// @Summary Create a new habit
	// @Description Create a new habit for the authenticated user
	// @Tags habits
	// @Accept json
	// @Produce json
	// @Security BearerAuth
	// @Router / [post]
	habits.POST("", h.handler.CreateHabit)

	// @Summary Get a habit by ID
	// @Description Get a specific habit by its ID
	// @Tags habits
	// @Accept json
	// @Produce json
	// @Param id path string true "Habit ID"
	// @Security BearerAuth
	// @Router /{id} [get]
	habits.GET("/:id", h.handler.GetHabit)

	// @Summary Update a habit
	// @Description Update an existing habit
	// @Tags habits
	// @Accept json
	// @Produce json
	// @Param id path string true "Habit ID"
	// @Security BearerAuth
	// @Router /{id} [put]
	habits.PUT("/:id", h.handler.UpdateHabit)

	// @Summary Delete a habit
	// @Description Delete an existing habit
	// @Tags habits
	// @Accept json
	// @Produce json
	// @Param id path string true "Habit ID"
	// @Security BearerAuth
	// @Router /{id} [delete]
	habits.DELETE("/:id", h.handler.DeleteHabit)

	// List and filter
	// @Summary List all habits
	// @Description Get all habits for the authenticated user
	// @Tags habits
	// @Accept json
	// @Produce json
	// @Security BearerAuth
	// @Router / [get]
	habits.GET("", h.handler.ListHabits)

	// @Summary Get habits due today
	// @Description Get all habits that are due today
	// @Tags habits
	// @Accept json
	// @Produce json
	// @Security BearerAuth
	// @Router /due-today [get]
	habits.GET("/due-today", h.handler.GetHabitsDueToday)

	// Habit completion
	// @Summary Mark habit as completed
	// @Description Mark a specific habit as completed
	// @Tags habits
	// @Accept json
	// @Produce json
	// @Param id path string true "Habit ID"
	// @Security BearerAuth
	// @Router /{id}/complete [post]
	habits.POST("/:id/complete", h.handler.MarkHabitCompleted)

	// @Summary Unmark habit completion
	// @Description Remove completion mark from a habit
	// @Tags habits
	// @Accept json
	// @Produce json
	// @Param id path string true "Habit ID"
	// @Security BearerAuth
	// @Router /{id}/uncomplete [post]
	habits.POST("/:id/uncomplete", h.handler.UnmarkHabitCompleted)

	// Stats and history
	// @Summary Get habit statistics
	// @Description Get statistics for a specific habit
	// @Tags habits
	// @Accept json
	// @Produce json
	// @Param id path string true "Habit ID"
	// @Security BearerAuth
	// @Router /{id}/stats [get]
	habits.GET("/:id/stats", h.handler.GetHabitStats)

	// @Summary Get streak history
	// @Description Get the streak history for a specific habit
	// @Tags habits
	// @Accept json
	// @Produce json
	// @Param id path string true "Habit ID"
	// @Security BearerAuth
	// @Router /{id}/streak-history [get]
	habits.GET("/:id/streak-history", h.handler.GetStreakHistory)
}
