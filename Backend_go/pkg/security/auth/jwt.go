package auth

import (
    "errors"
    "fmt"
    "time"

    "github.com/golang-jwt/jwt/v5"
    "github.com/ahmedelhadi17776/Compass/Backend_go/pkg/config"
)

// Custom claims structure
type Claims struct {
    jwt.RegisteredClaims
    UserID    uint     `json:"user_id"`
    Email     string   `json:"email"`
    Roles     []string `json:"roles"`
    OrgID     uint     `json:"org_id"`
    Permissions []string `json:"permissions"`
}

// JWTService handles JWT operations
type JWTService struct {
    secretKey     []byte
    tokenDuration time.Duration
    issuer        string
}

// NewJWTService creates a new JWT service
func NewJWTService(config *config.Config) *JWTService {
    return &JWTService{
        secretKey:     []byte(config.Auth.JWTSecret),
        tokenDuration: time.Duration(config.Auth.TokenExpiryHours) * time.Hour,
        issuer:        config.Auth.Issuer,
    }
}

// GenerateToken generates a new JWT token
func (s *JWTService) GenerateToken(userID uint, email string, roles []string, orgID uint, permissions []string) (string, error) {
    now := time.Now()
    claims := Claims{
        RegisteredClaims: jwt.RegisteredClaims{
            ExpiresAt: jwt.NewNumericDate(now.Add(s.tokenDuration)),
            IssuedAt:  jwt.NewNumericDate(now),
            Issuer:    s.issuer,
        },
        UserID:    userID,
        Email:     email,
        Roles:     roles,
        OrgID:     orgID,
        Permissions: permissions,
    }

    token := jwt.NewWithClaims(jwt.SigningMethodHS256, claims)
    return token.SignedString(s.secretKey)
}

// ValidateToken validates a JWT token
func (s *JWTService) ValidateToken(tokenString string) (*Claims, error) {
    token, err := jwt.ParseWithClaims(tokenString, &Claims{}, func(token *jwt.Token) (interface{}, error) {
        // Validate signing method
        if _, ok := token.Method.(*jwt.SigningMethodHMAC); !ok {
            return nil, fmt.Errorf("unexpected signing method: %v", token.Header["alg"])
        }
        return s.secretKey, nil
    })

    if err != nil {
        return nil, err
    }

    claims, ok := token.Claims.(*Claims)
    if !ok || !token.Valid {
        return nil, errors.New("invalid token")
    }

    return claims, nil
}

// RefreshToken refreshes a JWT token
func (s *JWTService) RefreshToken(tokenString string) (string, error) {
    claims, err := s.ValidateToken(tokenString)
    if err != nil {
        return "", err
    }

    // Check if token is about to expire
    now := time.Now()
    expiry := claims.ExpiresAt.Time
    threshold := expiry.Add(-6 * time.Hour) // Refresh if less than 6 hours left

    if now.Before(threshold) {
        return tokenString, nil // Token still valid for more than threshold
    }

    // Generate new token with same claims but new expiry
    return s.GenerateToken(
        claims.UserID,
        claims.Email,
        claims.Roles,
        claims.OrgID,
        claims.Permissions,
    )
}