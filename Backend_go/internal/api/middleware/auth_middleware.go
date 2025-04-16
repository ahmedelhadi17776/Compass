package middleware

import (
    "net/http"
    "strings"

    "github.com/gin-gonic/gin"
    "github.com/ahmedelhadi17776/Compass/Backend_go/pkg/security/auth"
    "github.com/ahmedelhadi17776/Compass/Backend_go/pkg/logger"
    "go.uber.org/zap"
)

var log = logger.NewLogger()

// AuthMiddleware is a middleware for JWT authentication
type AuthMiddleware struct {
    jwtService *auth.JWTService
}

// NewAuthMiddleware creates a new auth middleware
func NewAuthMiddleware(jwtService *auth.JWTService) *AuthMiddleware {
    return &AuthMiddleware{jwtService: jwtService}
}

// Authenticate authenticates a request using JWT
func (m *AuthMiddleware) Authenticate() gin.HandlerFunc {
    return func(c *gin.Context) {
        authHeader := c.GetHeader("Authorization")
        if authHeader == "" {
            c.JSON(http.StatusUnauthorized, gin.H{"error": "authorization header required"})
            c.Abort()
            return
        }

        parts := strings.Split(authHeader, " ")
        if len(parts) != 2 || parts[0] != "Bearer" {
            c.JSON(http.StatusUnauthorized, gin.H{"error": "invalid authorization header format"})
            c.Abort()
            return
        }

        tokenString := parts[1]
        claims, err := m.jwtService.ValidateToken(tokenString)
        if err != nil {
            log.Error("Token validation failed", zap.Error(err))
            c.JSON(http.StatusUnauthorized, gin.H{"error": "invalid or expired token"})
            c.Abort()
            return
        }

        // Store claims in context for later use
        c.Set("user_id", claims.UserID)
        c.Set("email", claims.Email)
        c.Set("roles", claims.Roles)
        c.Set("org_id", claims.OrgID)
        c.Set("permissions", claims.Permissions)

        c.Next()
    }
}

// RequireRoles middleware checks if user has required roles
func (m *AuthMiddleware) RequireRoles(roles ...string) gin.HandlerFunc {
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
func (m *AuthMiddleware) RequirePermissions(permissions ...string) gin.HandlerFunc {
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