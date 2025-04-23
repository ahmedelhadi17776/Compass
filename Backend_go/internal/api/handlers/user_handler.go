package handlers

import (
	"net/http"

	"github.com/ahmedelhadi17776/Compass/Backend_go/internal/api/dto"
	"github.com/ahmedelhadi17776/Compass/Backend_go/pkg/security/auth"
	"github.com/ahmedelhadi17776/Compass/Backend_go/internal/domain/user"
	"github.com/gin-gonic/gin"
	"github.com/google/uuid"
)

type UserHandler struct {
	userService user.Service
	jwtSecret   string
}

func NewUserHandler(userService user.Service, jwtSecret string) *UserHandler {
	return &UserHandler{userService: userService, jwtSecret: jwtSecret}
}

// CreateUser handles user registration
// @Summary Create a new user
// @Description Register a new user in the system
// @Tags users
// @Accept json
// @Produce json
// @Param user body dto.CreateUserRequest true "User registration information"
// @Success 201 {object} dto.UserResponse
// @Failure 400 {object} map[string]string
// @Failure 500 {object} map[string]string
// @Router /api/users/register [post]
func (h *UserHandler) CreateUser(c *gin.Context) {
	var input dto.CreateUserRequest

	if err := c.ShouldBindJSON(&input); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	createInput := user.CreateUserInput{
		Email:    input.Email,
		Username: input.Username,
		Password: input.Password,
	}

	createdUser, err := h.userService.CreateUser(c.Request.Context(), createInput)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	response := dto.UserResponse{
		ID:          createdUser.ID,
		Email:       createdUser.Email,
		Username:    createdUser.Username,
		IsActive:    createdUser.IsActive,
		IsSuperuser: createdUser.IsSuperuser,
		CreatedAt:   createdUser.CreatedAt,
		UpdatedAt:   createdUser.UpdatedAt,
		DeletedAt:   createdUser.DeletedAt,
		FirstName:   input.FirstName,
		LastName:    input.LastName,
		PhoneNumber: input.PhoneNumber,
		Timezone:    input.Timezone,
		Locale:      input.Locale,
	}

	c.JSON(http.StatusCreated, gin.H{"user": response})
}

// AuthenticateUser handles user authentication
func (h *UserHandler) AuthenticateUser(c *gin.Context, email, password string) (*user.User, error) {
	return h.userService.AuthenticateUser(c.Request.Context(), email, password)
}

// GetUser handles fetching a single user by ID
// @Summary Get a user by ID
// @Description Get user details by their ID
// @Tags users
// @Accept json
// @Produce json
// @Success 200 {object} dto.UserResponse
// @Failure 401 {object} map[string]string
// @Failure 500 {object} map[string]string
// @Router /api/users/profile [get]
func (h *UserHandler) GetUser(c *gin.Context) {
	userID, exists := c.Get("user_id")
	if !exists {
		c.JSON(http.StatusUnauthorized, gin.H{"error": "user not authenticated"})
		return
	}

	foundUser, err := h.userService.GetUser(c.Request.Context(), userID.(uuid.UUID))
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	response := dto.UserResponse{
		ID:          foundUser.ID,
		Email:       foundUser.Email,
		Username:    foundUser.Username,
		IsActive:    foundUser.IsActive,
		IsSuperuser: foundUser.IsSuperuser,
		CreatedAt:   foundUser.CreatedAt,
		UpdatedAt:   foundUser.UpdatedAt,
		DeletedAt:   foundUser.DeletedAt,
	}

	c.JSON(http.StatusOK, gin.H{"user": response})
}

// UpdateUser handles updating user information
// @Summary Update a user
// @Description Update user information
// @Tags users
// @Accept json
// @Produce json
// @Success 200 {object} dto.UserResponse
// @Failure 400 {object} map[string]string
// @Failure 401 {object} map[string]string
// @Failure 500 {object} map[string]string
// @Router /api/users/profile [put]
func (h *UserHandler) UpdateUser(c *gin.Context) {
	userID, exists := c.Get("user_id")
	if !exists {
		c.JSON(http.StatusUnauthorized, gin.H{"error": "user not authenticated"})
		return
	}

	var input dto.UpdateUserRequest
	if err := c.ShouldBindJSON(&input); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	updateInput := user.UpdateUserInput{
		Username: input.Username,
		Email:    input.Email,
	}

	updatedUser, err := h.userService.UpdateUser(c.Request.Context(), userID.(uuid.UUID), updateInput)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	response := dto.UserResponse{
		ID:          updatedUser.ID,
		Email:       updatedUser.Email,
		Username:    updatedUser.Username,
		IsActive:    updatedUser.IsActive,
		IsSuperuser: updatedUser.IsSuperuser,
		CreatedAt:   updatedUser.CreatedAt,
		UpdatedAt:   updatedUser.UpdatedAt,
		DeletedAt:   updatedUser.DeletedAt,
		FirstName:   *input.FirstName,
		LastName:    *input.LastName,
		PhoneNumber: *input.PhoneNumber,
		Timezone:    *input.Timezone,
		Locale:      *input.Locale,
	}

	c.JSON(http.StatusOK, gin.H{"user": response})
}

// DeleteUser handles user deletion
// @Summary Delete a user
// @Description Delete a user
// @Tags users
// @Accept json
// @Produce json
// @Success 204 "No Content"
// @Failure 401 {object} map[string]string
// @Failure 500 {object} map[string]string
// @Router /api/users/profile [delete]
func (h *UserHandler) DeleteUser(c *gin.Context) {
	userID, exists := c.Get("user_id")
	if !exists {
		c.JSON(http.StatusUnauthorized, gin.H{"error": "user not authenticated"})
		return
	}

	err := h.userService.DeleteUser(c.Request.Context(), userID.(uuid.UUID))
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.Status(http.StatusNoContent)
}

// GetUserRolesAndPermissions retrieves the roles and permissions for a user
func (h *UserHandler) GetUserRolesAndPermissions(c *gin.Context, userID uuid.UUID) ([]string, []string, error) {
	roles, permissions, err := h.userService.GetUserRolesAndPermissions(c.Request.Context(), userID)
	if err != nil {
		return nil, nil, err
	}
	return roles, permissions, nil
}

// Logout handles user logout
// @Summary Logout user
// @Description Invalidate the user's JWT token
// @Tags users
// @Produce json
// @Security BearerAuth
// @Success 200 {object} map[string]string "Successfully logged out"
// @Failure 401 {object} map[string]string "Unauthorized"
// @Router /api/users/logout [post]
func (h *UserHandler) Logout(c *gin.Context) {
	token, exists := c.Get("token")
	if !exists {
		c.JSON(http.StatusUnauthorized, gin.H{"error": "no token found"})
		return
	}

	// Get token claims to get expiry time
	claims, err := auth.ValidateToken(token.(string), h.jwtSecret)
	if err != nil {
		c.JSON(http.StatusUnauthorized, gin.H{"error": "invalid token"})
		return
	}

	// Add token to blacklist
	auth.GetTokenBlacklist().AddToBlacklist(token.(string), claims.ExpiresAt.Time)

	c.JSON(http.StatusOK, gin.H{"message": "successfully logged out"})
}
