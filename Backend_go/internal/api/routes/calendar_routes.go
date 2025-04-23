package routes

import (
	"github.com/ahmedelhadi17776/Compass/Backend_go/internal/api/handlers"
	"github.com/ahmedelhadi17776/Compass/Backend_go/internal/api/middleware"
	"github.com/gin-gonic/gin"
)

// CalendarRoutes handles the setup of calendar-related routes
type CalendarRoutes struct {
	handler   *handlers.CalendarHandler
	jwtSecret string
}

// NewCalendarRoutes creates a new CalendarRoutes instance
func NewCalendarRoutes(handler *handlers.CalendarHandler, jwtSecret string) *CalendarRoutes {
	return &CalendarRoutes{
		handler:   handler,
		jwtSecret: jwtSecret,
	}
}

// RegisterRoutes registers all calendar-related routes
func (cr *CalendarRoutes) RegisterRoutes(router *gin.Engine) {
	// Create a calendar group with authentication middleware
	calendarGroup := router.Group("/api/calendar")
	calendarGroup.Use(middleware.NewAuthMiddleware(cr.jwtSecret))
	//calendarGroup.Use(middleware.OrganizationMiddleware())

	// Event routes
	events := calendarGroup.Group("/events")
	{
		// Core event operations
		events.POST("", cr.handler.CreateEvent)
		events.GET("", cr.handler.ListEvents)
		events.GET("/:id", cr.handler.GetEvent)
		events.PUT("/:id", cr.handler.UpdateEvent)
		events.DELETE("/:id", cr.handler.DeleteEvent)

		// Occurrence operations
		events.PUT("/occurrence", cr.handler.UpdateOccurrence)
		events.DELETE("/occurrence", cr.handler.DeleteOccurrence)

		// Reminder operations
		events.POST("/:event_id/reminders", cr.handler.AddReminder)
	}
}
