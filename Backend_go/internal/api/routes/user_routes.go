package routes

import (
	"github.com/ahmedelhadi17776/Compass/Backend_go/internal/api/handlers"
	"github.com/ahmedelhadi17776/Compass/Backend_go/internal/domain/user"
	"github.com/gin-gonic/gin"
)

// @Summary Register a new user
// @Description Register a new user with the provided information
// @Tags users
// @Accept json
// @Produce json
// @Param user body user.CreateUserRequest true "User registration information"
// @Success 201 {object} user.User "User created successfully"
// @Failure 400 {object} map[string]string "Invalid request"
// @Failure 500 {object} map[string]string "Internal server error"
// @Router /users/register [post]
func registerHandler(userService user.Service) gin.HandlerFunc {
	return func(c *gin.Context) {
		// ... existing implementation ...
	}
}

// @Summary Login user
// @Description Authenticate a user and return a JWT token
// @Tags users
// @Accept json
// @Produce json
// @Param credentials body user.LoginRequest true "Login credentials"
// @Success 200 {object} map[string]string "Login successful"
// @Failure 401 {object} map[string]string "Invalid credentials"
// @Failure 500 {object} map[string]string "Internal server error"
// @Router /users/login [post]
func loginHandler(userService user.Service) gin.HandlerFunc {
	return func(c *gin.Context) {
		// ... existing implementation ...
	}
}

// @Summary Get user profile
// @Description Get the profile of the currently authenticated user
// @Tags users
// @Accept json
// @Produce json
// @Security BearerAuth
// @Success 200 {object} user.User "User profile"
// @Failure 401 {object} map[string]string "Unauthorized"
// @Failure 500 {object} map[string]string "Internal server error"
// @Router /users/profile [get]
func profileHandler(userService user.Service) gin.HandlerFunc {
	return func(c *gin.Context) {
		// ... existing implementation ...
	}
}

func SetupUserRoutes(router *gin.RouterGroup, userService user.Service) {
	handler := handlers.NewUserHandler(userService)

	users := router.Group("/users")
	{
		users.POST("/register", registerHandler(userService))
		users.POST("/login", loginHandler(userService))
		users.GET("/profile", profileHandler(userService))
		users.GET("/:id", handler.GetUser)
		users.GET("", handler.ListUsers)
		users.PUT("/:id", handler.UpdateUser)
		users.DELETE("/:id", handler.DeleteUser)
	}
}
