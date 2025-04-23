package routes

import (
	"net/http"
	"time"

	"github.com/ahmedelhadi17776/Compass/Backend_go/internal/api/dto"
	"github.com/ahmedelhadi17776/Compass/Backend_go/internal/api/handlers"
	"github.com/ahmedelhadi17776/Compass/Backend_go/internal/api/middleware"
	"github.com/ahmedelhadi17776/Compass/Backend_go/pkg/logger"
	"github.com/ahmedelhadi17776/Compass/Backend_go/pkg/security/auth"
	"github.com/gin-gonic/gin"
	"github.com/google/uuid"
	"go.uber.org/zap"
)

var log = logger.NewLogger()

type UserRoutes struct {
	userHandler *handlers.UserHandler
	jwtSecret   string
}

func NewUserRoutes(userHandler *handlers.UserHandler, jwtSecret string) *UserRoutes {
	return &UserRoutes{
		userHandler: userHandler,
		jwtSecret:   jwtSecret,
	}
}

// RegisterRoutes sets up all user-related routes
func (ur *UserRoutes) RegisterRoutes(router *gin.Engine) {
	userGroup := router.Group("/api/users")
	{
		// @Summary Register a new user
		// @Description Create a new user account
		// @Tags users
		// @Accept json
		// @Produce json
		// @Param user body dto.CreateUserRequest true "User registration information"
		// @Success 201 {object} dto.UserResponse
		// @Failure 400 {object} map[string]string "Invalid request"
		// @Failure 500 {object} map[string]string "Internal server error"
		// @Router /api/users/register [post]
		userGroup.POST("/register", ur.Register)

		// @Summary Login user
		// @Description Authenticate user and return JWT token
		// @Tags users
		// @Accept json
		// @Produce json
		// @Param credentials body dto.LoginRequest true "Login credentials"
		// @Success 200 {object} dto.LoginResponse
		// @Failure 400 {object} map[string]string "Invalid request"
		// @Failure 401 {object} map[string]string "Invalid credentials"
		// @Failure 500 {object} map[string]string "Internal server error"
		// @Router /api/users/login [post]
		userGroup.POST("/login", ur.Login)

		// Protected routes
		protected := userGroup.Use(middleware.NewAuthMiddleware(ur.jwtSecret))
		{
			// @Summary Get user profile
			// @Description Get the current user's profile
			// @Tags users
			// @Produce json
			// @Security BearerAuth
			// @Success 200 {object} dto.UserResponse
			// @Failure 401 {object} map[string]string "Unauthorized"
			// @Failure 404 {object} map[string]string "User not found"
			// @Router /api/users/profile [get]
			protected.GET("/profile", ur.GetProfile)

			// @Summary Update user profile
			// @Description Update the current user's profile
			// @Tags users
			// @Accept json
			// @Produce json
			// @Security BearerAuth
			// @Param user body dto.UpdateUserRequest true "User update information"
			// @Success 200 {object} dto.UserResponse
			// @Failure 400 {object} map[string]string "Invalid request"
			// @Failure 401 {object} map[string]string "Unauthorized"
			// @Failure 404 {object} map[string]string "User not found"
			// @Router /api/users/profile [put]
			protected.PUT("/profile", ur.UpdateProfile)

			// @Summary Delete user profile
			// @Description Delete the current user's account
			// @Tags users
			// @Produce json
			// @Security BearerAuth
			// @Success 204 "User deleted successfully"
			// @Failure 401 {object} map[string]string "Unauthorized"
			// @Failure 404 {object} map[string]string "User not found"
			// @Router /api/users/profile [delete]
			protected.DELETE("/profile", ur.DeleteProfile)
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
