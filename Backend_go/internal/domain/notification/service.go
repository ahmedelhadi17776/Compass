package notification

import (
	"context"
	"time"

	"github.com/google/uuid"
	"github.com/sirupsen/logrus"
)

// Service defines the notification service interface
type Service interface {
	Create(ctx context.Context, notification *Notification) error

	CreateForUser(ctx context.Context, userID uuid.UUID, notificationType Type, title, content string, data map[string]string, reference string, referenceID uuid.UUID) error

	GetByID(ctx context.Context, id uuid.UUID) (*Notification, error)

	GetByUserID(ctx context.Context, userID uuid.UUID, limit, offset int) ([]*Notification, error)

	GetUnreadByUserID(ctx context.Context, userID uuid.UUID, limit, offset int) ([]*Notification, error)

	MarkAsRead(ctx context.Context, id uuid.UUID) error

	MarkAllAsRead(ctx context.Context, userID uuid.UUID) error

	Delete(ctx context.Context, id uuid.UUID) error

	CountUnread(ctx context.Context, userID uuid.UUID) (int, error)

	SubscribeToNotifications(userID uuid.UUID) (<-chan *Notification, func(), error)
}

// ServiceConfig holds the configuration for the notification service
type ServiceConfig struct {
	Repository Repository
	Logger     *logrus.Logger
	SignalRepo SignalRepository
}

// serviceImpl implements the notification Service interface
type serviceImpl struct {
	repo       Repository
	logger     *logrus.Logger
	signalRepo SignalRepository
}

// NewService creates a new notification service
func NewService(config ServiceConfig) Service {
	return &serviceImpl{
		repo:       config.Repository,
		logger:     config.Logger,
		signalRepo: config.SignalRepo,
	}
}

// Create creates a new notification
func (s *serviceImpl) Create(ctx context.Context, notification *Notification) error {
	if err := s.repo.Create(ctx, notification); err != nil {
		s.logger.WithError(err).Error("Failed to create notification")
		return err
	}
	// Publish notification to subscribers
	s.signalRepo.Publish(notification.UserID.String(), notification)
	return nil
}

// CreateForUser creates a notification for a specific user
func (s *serviceImpl) CreateForUser(ctx context.Context, userID uuid.UUID, notificationType Type, title, content string, data map[string]string, reference string, referenceID uuid.UUID) error {
	notification := &Notification{
		ID:          uuid.New(),
		UserID:      userID,
		Type:        notificationType,
		Title:       title,
		Content:     content,
		Status:      Unread,
		Data:        data,
		Reference:   reference,
		ReferenceID: referenceID,
		CreatedAt:   time.Now(),
		UpdatedAt:   time.Now(),
	}

	return s.Create(ctx, notification)
}

// GetByID retrieves a notification by its ID
func (s *serviceImpl) GetByID(ctx context.Context, id uuid.UUID) (*Notification, error) {
	return s.repo.GetByID(ctx, id)
}

// GetByUserID retrieves all notifications for a user
func (s *serviceImpl) GetByUserID(ctx context.Context, userID uuid.UUID, limit, offset int) ([]*Notification, error) {
	return s.repo.GetByUserID(ctx, userID, limit, offset)
}

// GetUnreadByUserID retrieves unread notifications for a user
func (s *serviceImpl) GetUnreadByUserID(ctx context.Context, userID uuid.UUID, limit, offset int) ([]*Notification, error) {
	return s.repo.GetUnreadByUserID(ctx, userID, limit, offset)
}

// MarkAsRead marks a notification as read
func (s *serviceImpl) MarkAsRead(ctx context.Context, id uuid.UUID) error {
	return s.repo.MarkAsRead(ctx, id)
}

// MarkAllAsRead marks all notifications as read for a user
func (s *serviceImpl) MarkAllAsRead(ctx context.Context, userID uuid.UUID) error {
	return s.repo.MarkAllAsRead(ctx, userID)
}

// Delete deletes a notification
func (s *serviceImpl) Delete(ctx context.Context, id uuid.UUID) error {
	return s.repo.Delete(ctx, id)
}

// CountUnread counts unread notifications for a user
func (s *serviceImpl) CountUnread(ctx context.Context, userID uuid.UUID) (int, error) {
	return s.repo.CountUnread(ctx, userID)
}

// SubscribeToNotifications subscribes to receive notifications
func (s *serviceImpl) SubscribeToNotifications(userID uuid.UUID) (<-chan *Notification, func(), error) {
	return s.signalRepo.Subscribe(userID.String())
}
