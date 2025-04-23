package middleware

import (
	"net/http"
	"strings"

	"github.com/ahmedelhadi17776/Compass/Backend_go/pkg/logger"
	"github.com/ahmedelhadi17776/Compass/Backend_go/pkg/security/auth"
	"github.com/gin-gonic/gin"
	"github.com/google/uuid"
	"go.uber.org/zap"
)

var log = logger.NewLogger()

const (
	bearerSchema = "Bearer "
)

// AuthMiddleware is a middleware for JWT authentication
type AuthMiddleware struct {
	jwtSecret string
}

// NewAuthMiddleware creates a new auth middleware
func NewAuthMiddleware(jwtSecret string) gin.HandlerFunc {
	return func(c *gin.Context) {
		authHeader := c.GetHeader("Authorization")
		if authHeader == "" {
			log.Error("Missing authorization header")
			c.JSON(http.StatusUnauthorized, gin.H{"error": "authorization header is required"})
			c.Abort()
			return
		}

		if !strings.HasPrefix(authHeader, bearerSchema) {
			log.Error("Invalid authorization header format")
			c.JSON(http.StatusUnauthorized, gin.H{"error": "invalid authorization header format"})
			c.Abort()
			return
		}

		tokenString := authHeader[len(bearerSchema):]

		// Check if token is blacklisted
		if auth.GetTokenBlacklist().IsBlacklisted(tokenString) {
			log.Error("Token is blacklisted")
			c.JSON(http.StatusUnauthorized, gin.H{"error": "token has been invalidated"})
			c.Abort()
			return
		}

		claims, err := auth.ValidateToken(tokenString, jwtSecret)
		if err != nil {
			log.Error("Token validation failed", zap.Error(err))
			c.JSON(http.StatusUnauthorized, gin.H{"error": "invalid token"})
			c.Abort()
			return
		}

		// Store claims and token in context for later use
		c.Set("user_id", claims.UserID)
		c.Set("email", claims.Email)
		c.Set("roles", claims.Roles)
		c.Set("org_id", claims.OrgID)
		c.Set("permissions", claims.Permissions)
		c.Set("token", tokenString)

		c.Next()
	}
}

// GetUserID retrieves the authenticated user's ID from the context
func GetUserID(c *gin.Context) (uuid.UUID, bool) {
	userID, exists := c.Get("user_id")
	if !exists {
		return uuid.Nil, false
	}
	return userID.(uuid.UUID), true
}

// RequireRoles middleware checks if user has required roles
func RequireRoles(roles ...string) gin.HandlerFunc {
	return func(c *gin.Context) {
		userRoles, exists := c.Get("roles")
		if !exists {
			c.JSON(http.StatusUnauthorized, gin.H{"error": "user not authenticated"})
			c.Abort()
			return
		}

		userRolesList := userRoles.([]string)
		hasRole := false

		for _, role := range roles {
			for _, userRole := range userRolesList {
				if userRole == role {
					hasRole = true
					break
				}
			}
			if hasRole {
				break
			}
		}

		if !hasRole {
			c.JSON(http.StatusForbidden, gin.H{"error": "insufficient permissions"})
			c.Abort()
			return
		}

		c.Next()
	}
}

// RequirePermissions middleware checks if user has required permissions
func RequirePermissions(permissions ...string) gin.HandlerFunc {
	return func(c *gin.Context) {
		userPermissions, exists := c.Get("permissions")
		if !exists {
			c.JSON(http.StatusUnauthorized, gin.H{"error": "user not authenticated"})
			c.Abort()
			return
		}

		userPermissionsList := userPermissions.([]string)
		hasPermission := false

		for _, permission := range permissions {
			for _, userPermission := range userPermissionsList {
				if userPermission == permission {
					hasPermission = true
					break
				}
			}
			if hasPermission {
				break
			}
		}

		if !hasPermission {
			c.JSON(http.StatusForbidden, gin.H{"error": "insufficient permissions"})
			c.Abort()
			return
		}

		c.Next()
	}
}
