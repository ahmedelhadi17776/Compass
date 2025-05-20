package notification

import (
	"context"
	"errors"
	"time"

	"github.com/ahmedelhadi17776/Compass/Backend_go/internal/infrastructure/persistence/postgres/connection"
	"github.com/google/uuid"
	"github.com/sirupsen/logrus"
	"gorm.io/gorm"
)

// postgresRepository implements the Repository interface for PostgreSQL
type postgresRepository struct {
	db     *connection.Database
	logger *logrus.Logger
}

// NewRepository creates a new PostgreSQL notification repository
func NewRepository(db *connection.Database, logger *logrus.Logger) Repository {
	return &postgresRepository{
		db:     db,
		logger: logger,
	}
}

// Create creates a new notification
func (r *postgresRepository) Create(ctx context.Context, notification *Notification) error {
	if err := r.db.WithContext(ctx).Create(notification).Error; err != nil {
		r.logger.WithError(err).Error("Failed to create notification")
		return err
	}
	return nil
}

// GetByID retrieves a notification by its ID
func (r *postgresRepository) GetByID(ctx context.Context, id uuid.UUID) (*Notification, error) {
	var notification Notification
	if err := r.db.WithContext(ctx).Where("id = ?", id).First(&notification).Error; err != nil {
		if errors.Is(err, gorm.ErrRecordNotFound) {
			return nil, &ErrNotFoundType{Message: "notification not found"}
		}
		r.logger.WithError(err).Error("Failed to get notification by ID")
		return nil, err
	}
	return &notification, nil
}

// GetByUserID retrieves all notifications for a user
func (r *postgresRepository) GetByUserID(ctx context.Context, userID uuid.UUID, limit, offset int) ([]*Notification, error) {
	var notifications []*Notification

	query := r.db.WithContext(ctx).
		Where("user_id = ?", userID).
		Order("created_at DESC")

	if limit > 0 {
		query = query.Limit(limit)
	}

	if offset > 0 {
		query = query.Offset(offset)
	}

	if err := query.Find(&notifications).Error; err != nil {
		r.logger.WithError(err).Error("Failed to get notifications by user ID")
		return nil, err
	}

	return notifications, nil
}

// GetUnreadByUserID retrieves unread notifications for a user
func (r *postgresRepository) GetUnreadByUserID(ctx context.Context, userID uuid.UUID, limit, offset int) ([]*Notification, error) {
	var notifications []*Notification

	query := r.db.WithContext(ctx).
		Where("user_id = ? AND status = ?", userID, Unread).
		Order("created_at DESC")

	if limit > 0 {
		query = query.Limit(limit)
	}

	if offset > 0 {
		query = query.Offset(offset)
	}

	if err := query.Find(&notifications).Error; err != nil {
		r.logger.WithError(err).Error("Failed to get unread notifications")
		return nil, err
	}

	return notifications, nil
}

// UpdateStatus updates the status of a notification
func (r *postgresRepository) UpdateStatus(ctx context.Context, id uuid.UUID, status Status) error {
	result := r.db.WithContext(ctx).
		Model(&Notification{}).
		Where("id = ?", id).
		Updates(map[string]interface{}{
			"status":     status,
			"updated_at": time.Now(),
		})

	if result.Error != nil {
		r.logger.WithError(result.Error).Error("Failed to update notification status")
		return result.Error
	}

	if result.RowsAffected == 0 {
		return ErrNotFound
	}

	return nil
}

// MarkAsRead marks a notification as read
func (r *postgresRepository) MarkAsRead(ctx context.Context, id uuid.UUID) error {
	now := time.Now()
	result := r.db.WithContext(ctx).
		Model(&Notification{}).
		Where("id = ?", id).
		Updates(map[string]interface{}{
			"status":     Read,
			"read_at":    now,
			"updated_at": now,
		})

	if result.Error != nil {
		r.logger.WithError(result.Error).Error("Failed to mark notification as read")
		return result.Error
	}

	if result.RowsAffected == 0 {
		return ErrNotFound
	}

	return nil
}

// MarkAllAsRead marks all notifications as read for a user
func (r *postgresRepository) MarkAllAsRead(ctx context.Context, userID uuid.UUID) error {
	now := time.Now()
	if err := r.db.WithContext(ctx).
		Model(&Notification{}).
		Where("user_id = ? AND status = ?", userID, Unread).
		Updates(map[string]interface{}{
			"status":     Read,
			"read_at":    now,
			"updated_at": now,
		}).Error; err != nil {
		r.logger.WithError(err).Error("Failed to mark all notifications as read")
		return err
	}
	return nil
}

// Delete removes a notification
func (r *postgresRepository) Delete(ctx context.Context, id uuid.UUID) error {
	result := r.db.WithContext(ctx).
		Delete(&Notification{}, "id = ?", id)

	if result.Error != nil {
		r.logger.WithError(result.Error).Error("Failed to delete notification")
		return result.Error
	}

	if result.RowsAffected == 0 {
		return ErrNotFound
	}

	return nil
}

// CountUnread counts unread notifications for a user
func (r *postgresRepository) CountUnread(ctx context.Context, userID uuid.UUID) (int, error) {
	var count int64
	if err := r.db.WithContext(ctx).
		Model(&Notification{}).
		Where("user_id = ? AND status = ?", userID, Unread).
		Count(&count).Error; err != nil {
		r.logger.WithError(err).Error("Failed to count unread notifications")
		return 0, err
	}
	return int(count), nil
}

// DeleteExpired removes all expired notifications
func (r *postgresRepository) DeleteExpired(ctx context.Context) error {
	now := time.Now()
	if err := r.db.WithContext(ctx).
		Where("expires_at IS NOT NULL AND expires_at < ?", now).
		Delete(&Notification{}).Error; err != nil {
		r.logger.WithError(err).Error("Failed to delete expired notifications")
		return err
	}
	return nil
}
