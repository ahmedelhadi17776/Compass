package routes

import (
	"github.com/ahmedelhadi17776/Compass/Backend_go/internal/api/handlers"
	"github.com/ahmedelhadi17776/Compass/Backend_go/internal/api/middleware"
	"github.com/ahmedelhadi17776/Compass/Backend_go/pkg/logger"
	"github.com/ahmedelhadi17776/Compass/Backend_go/pkg/security/auth"
	"github.com/gin-gonic/gin"
)

var log = logger.NewLogger()

type UserRoutes struct {
	userHandler *handlers.UserHandler
	jwtSecret   string
	rateLimiter *auth.RedisRateLimiter
}

func NewUserRoutes(userHandler *handlers.UserHandler, jwtSecret string, rateLimiter *auth.RedisRateLimiter) *UserRoutes {
	return &UserRoutes{
		userHandler: userHandler,
		jwtSecret:   jwtSecret,
		rateLimiter: rateLimiter,
	}
}

// RegisterRoutes sets up all user-related routes
func (ur *UserRoutes) RegisterRoutes(router *gin.Engine) {
	userGroup := router.Group("/api/users")
	{
		// Public routes with stricter rate limiting
		public := userGroup.Group("")
		public.Use(middleware.RateLimitMiddleware(ur.rateLimiter))
		{
			public.POST("/register", ur.userHandler.CreateUser)
			public.POST("/login", ur.userHandler.Login)
		}

		// Protected routes with general API rate limiting
		protected := userGroup.Group("")
		protected.Use(
			middleware.NewAuthMiddleware(ur.jwtSecret),
			middleware.RateLimitMiddleware(ur.rateLimiter),
		)
		{
			// Profile management
			protected.GET("/profile", ur.userHandler.GetUser)
			protected.PUT("/profile", ur.userHandler.UpdateUser)
			protected.DELETE("/profile", ur.userHandler.DeleteUser)

			// Session management
			protected.GET("/sessions", ur.userHandler.GetUserSessions)
			protected.POST("/sessions/:id/revoke", ur.userHandler.RevokeSession)
			protected.POST("/logout", ur.userHandler.Logout)
		}
	}
}

func (ur *UserRoutes) Register(c *gin.Context) {
	ur.userHandler.CreateUser(c)
}

func (ur *UserRoutes) Login(c *gin.Context) {
	var loginRequest dto.LoginRequest

	if err := c.ShouldBindJSON(&loginRequest); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	user, err := ur.userHandler.AuthenticateUser(c, loginRequest.Email, loginRequest.Password)
	if err != nil {
		log.Error("Authentication failed", zap.Error(err))
		c.JSON(http.StatusUnauthorized, gin.H{"error": "Invalid credentials"})
		return
	}

	// Get user's roles and permissions
	roles, permissions, err := ur.userHandler.GetUserRolesAndPermissions(c, user.ID)
	if err != nil {
		log.Error("Failed to get user roles and permissions", zap.Error(err))
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to get user permissions"})
		return
	}

	// Generate JWT token with 24 hours expiry
	token, err := auth.GenerateToken(
		user.ID,
		user.Email,
		roles,       // Include user's roles
		uuid.Nil,    // No org ID for now
		permissions, // Include user's permissions
		ur.jwtSecret,
		24,
	)

	if err != nil {
		log.Error("Failed to generate token", zap.Error(err))
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to generate token"})
		return
	}

	response := dto.LoginResponse{
		Token: token,
		User: dto.UserResponse{
			ID:          user.ID,
			Email:       user.Email,
			Username:    user.Username,
			FirstName:   user.FirstName,
			LastName:    user.LastName,
			PhoneNumber: user.PhoneNumber,
			AvatarURL:   user.AvatarURL,
			Bio:         user.Bio,
			Timezone:    user.Timezone,
			Locale:      user.Locale,
			IsActive:    user.IsActive,
			IsSuperuser: user.IsSuperuser,
			CreatedAt:   user.CreatedAt,
			UpdatedAt:   user.UpdatedAt,
			DeletedAt:   user.DeletedAt,
		},
		ExpiresAt: time.Now().Add(24 * time.Hour),
	}

	c.JSON(http.StatusOK, gin.H{"data": response})
}

func (ur *UserRoutes) GetProfile(c *gin.Context) {
	ur.userHandler.GetUser(c)
}

func (ur *UserRoutes) UpdateProfile(c *gin.Context) {
	ur.userHandler.UpdateUser(c)
}

func (ur *UserRoutes) DeleteProfile(c *gin.Context) {
	ur.userHandler.DeleteUser(c)
}
