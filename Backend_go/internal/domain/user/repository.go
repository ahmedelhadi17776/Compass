package user

import (
	"context"
	"errors"

	"github.com/ahmedelhadi17776/Compass/Backend_go/internal/infrastructure/persistence/postgres/connection"
	"github.com/google/uuid"
	"gorm.io/gorm"
)

var (
	ErrUserNotFound = errors.New("user not found")
	ErrInvalidInput = errors.New("invalid input")
)

// UserFilter defines the filtering options for users
type UserFilter struct {
	IsActive    *bool
	Email       *string
	Username    *string
	FirstName   *string
	LastName    *string
	PhoneNumber *string
	Timezone    *string
	Locale      *string
	Page        int
	PageSize    int
}

type Repository interface {
	Create(ctx context.Context, user *User) error
	FindByID(ctx context.Context, id uuid.UUID) (*User, error)
	FindByEmail(ctx context.Context, email string) (*User, error)
	FindByUsername(ctx context.Context, username string) (*User, error)
	FindByProviderID(ctx context.Context, providerID, provider string) (*User, error)
	FindAll(ctx context.Context, filter UserFilter) ([]User, int64, error)
	Update(ctx context.Context, user *User) error
	Delete(ctx context.Context, id uuid.UUID) error
}

type repository struct {
	db *connection.Database
}

func NewRepository(db *connection.Database) Repository {
	return &repository{db: db}
}

func (r *repository) Create(ctx context.Context, user *User) error {
	return r.db.WithContext(ctx).Create(user).Error
}

func (r *repository) FindByID(ctx context.Context, id uuid.UUID) (*User, error) {
	var user User
	result := r.db.WithContext(ctx).First(&user, id)
	if result.Error != nil {
		if errors.Is(result.Error, gorm.ErrRecordNotFound) {
			return nil, ErrUserNotFound
		}
		return nil, result.Error
	}
	return &user, nil
}

func (r *repository) FindAll(ctx context.Context, filter UserFilter) ([]User, int64, error) {
	var users []User
	var total int64
	query := r.db.WithContext(ctx).Model(&User{})

	if filter.IsActive != nil {
		query = query.Where("is_active = ?", *filter.IsActive)
	}
	if filter.Email != nil {
		query = query.Where("email LIKE ?", "%"+*filter.Email+"%")
	}
	if filter.Username != nil {
		query = query.Where("username LIKE ?", "%"+*filter.Username+"%")
	}
	if filter.FirstName != nil {
		query = query.Where("first_name LIKE ?", "%"+*filter.FirstName+"%")
	}
	if filter.LastName != nil {
		query = query.Where("last_name LIKE ?", "%"+*filter.LastName+"%")
	}
	if filter.PhoneNumber != nil {
		query = query.Where("phone_number LIKE ?", "%"+*filter.PhoneNumber+"%")
	}
	if filter.Timezone != nil {
		query = query.Where("timezone = ?", *filter.Timezone)
	}
	if filter.Locale != nil {
		query = query.Where("locale = ?", *filter.Locale)
	}

	err := query.Count(&total).Error
	if err != nil {
		return nil, 0, err
	}

	err = query.Offset(filter.Page * filter.PageSize).
		Limit(filter.PageSize).
		Find(&users).Error
	if err != nil {
		return nil, 0, err
	}

	return users, total, nil
}

func (r *repository) Update(ctx context.Context, user *User) error {
	result := r.db.WithContext(ctx).Save(user)
	if result.Error != nil {
		return result.Error
	}
	if result.RowsAffected == 0 {
		return ErrUserNotFound
	}
	return nil
}

func (r *repository) Delete(ctx context.Context, id uuid.UUID) error {
	result := r.db.WithContext(ctx).Delete(&User{}, id)
	if result.Error != nil {
		return result.Error
	}
	if result.RowsAffected == 0 {
		return ErrUserNotFound
	}
	return nil
}

func (r *repository) FindByEmail(ctx context.Context, email string) (*User, error) {
	var user User
	result := r.db.WithContext(ctx).Where("email = ?", email).First(&user)
	if result.Error != nil {
		if errors.Is(result.Error, gorm.ErrRecordNotFound) {
			return nil, nil
		}
		return nil, result.Error
	}
	return &user, nil
}

func (r *repository) FindByUsername(ctx context.Context, username string) (*User, error) {
	var user User
	result := r.db.WithContext(ctx).Where("username = ?", username).First(&user)
	if result.Error != nil {
		if errors.Is(result.Error, gorm.ErrRecordNotFound) {
			return nil, nil
		}
		return nil, result.Error
	}
	return &user, nil
}

func (r *repository) FindByProviderID(ctx context.Context, providerID, provider string) (*User, error) {
	var user User
	result := r.db.WithContext(ctx).Where("provider_id = ? AND provider = ?", providerID, provider).First(&user)
	if result.Error != nil {
		if errors.Is(result.Error, gorm.ErrRecordNotFound) {
			return nil, ErrUserNotFound
		}
		return nil, result.Error
	}
	return &user, nil
}
