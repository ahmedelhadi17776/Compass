package calendar

import (
	"context"
	"time"

	"github.com/google/uuid"
	"gorm.io/gorm"
)

// Repository interface defines the data access methods for calendar events
type Repository interface {
	BeginTransaction(ctx context.Context) Transaction
	// Core event operations
	CreateEvent(ctx context.Context, event *CalendarEvent) error
	GetEventByID(ctx context.Context, id uuid.UUID) (*CalendarEvent, error)
	UpdateEvent(ctx context.Context, event *CalendarEvent) error
	DeleteEvent(ctx context.Context, id uuid.UUID) error
	ListEvents(ctx context.Context, filter EventFilter) ([]CalendarEvent, int64, error)

	// Recurrence rule operations
	AddRecurrenceRule(ctx context.Context, rule *RecurrenceRule) error
	UpdateRecurrenceRule(ctx context.Context, rule *RecurrenceRule) error
	DeleteRecurrenceRule(ctx context.Context, id uuid.UUID) error

	// Exception operations
	CreateException(ctx context.Context, exception *EventException) error
	UpdateException(ctx context.Context, exception *EventException) error
	GetExceptions(ctx context.Context, eventID uuid.UUID, startTime, endTime time.Time) ([]EventException, error)

	// Occurrence operations
	CreateOccurrence(ctx context.Context, occurrence *EventOccurrence) error
	UpdateOccurrenceStatus(ctx context.Context, id uuid.UUID, status OccurrenceStatus) error
	GetOccurrences(ctx context.Context, eventID uuid.UUID, startTime, endTime time.Time) ([]EventOccurrence, error)

	// Reminder operations
	AddReminder(ctx context.Context, reminder *EventReminder) error
	UpdateReminder(ctx context.Context, reminder *EventReminder) error
	DeleteReminder(ctx context.Context, id uuid.UUID) error
	GetUpcomingReminders(ctx context.Context, startTime, endTime time.Time) ([]EventReminder, error)
}

// Transaction represents a database transaction
type Transaction interface {
	Commit() error
	Rollback() error
	CreateEvent(event *CalendarEvent) error
	CreateRecurrenceRule(rule *RecurrenceRule) error
	CreateOccurrence(occurrence *EventOccurrence) error
	CreateReminder(reminder *EventReminder) error
	UpdateEvent(event *CalendarEvent) error
	CreateException(exception *EventException) error
	UpdateException(exception *EventException) error
	GetExceptions(eventID uuid.UUID, startTime, endTime time.Time) ([]EventException, error)
}

// EventFilter defines the filtering options for listing events
type EventFilter struct {
	UserID    uuid.UUID
	StartTime *time.Time
	EndTime   *time.Time
	EventType *EventType
	Search    string
	Page      int
	PageSize  int
}

// repository implements the Repository interface
type repository struct {
	db *gorm.DB
}

// NewRepository creates a new calendar repository instance
func NewRepository(db *gorm.DB) Repository {
	return &repository{db: db}
}

// Implementation of Repository interface
func (r *repository) CreateEvent(ctx context.Context, event *CalendarEvent) error {
	return r.db.WithContext(ctx).Create(event).Error
}

func (r *repository) GetEventByID(ctx context.Context, id uuid.UUID) (*CalendarEvent, error) {
	var event CalendarEvent
	err := r.db.WithContext(ctx).
		Preload("RecurrenceRules").
		Preload("Reminders").
		First(&event, "id = ?", id).Error
	if err != nil {
		return nil, err
	}
	return &event, nil
}

func (r *repository) UpdateEvent(ctx context.Context, event *CalendarEvent) error {
	return r.db.WithContext(ctx).Save(event).Error
}

func (r *repository) DeleteEvent(ctx context.Context, id uuid.UUID) error {
	return r.db.WithContext(ctx).Transaction(func(tx *gorm.DB) error {
		// Delete associated records first
		if err := tx.Where("event_id = ?", id).Delete(&RecurrenceRule{}).Error; err != nil {
			return err
		}
		if err := tx.Where("event_id = ?", id).Delete(&EventException{}).Error; err != nil {
			return err
		}
		if err := tx.Where("event_id = ?", id).Delete(&EventOccurrence{}).Error; err != nil {
			return err
		}
		if err := tx.Where("event_id = ?", id).Delete(&EventReminder{}).Error; err != nil {
			return err
		}
		// Delete the event itself
		return tx.Delete(&CalendarEvent{}, id).Error
	})
}

func (r *repository) ListEvents(ctx context.Context, filter EventFilter) ([]CalendarEvent, int64, error) {
	var events []CalendarEvent
	var total int64

	query := r.db.WithContext(ctx).Model(&CalendarEvent{})

	// Apply filters
	query = query.Where("user_id = ?", filter.UserID)

	// Handle date range filtering for both single and recurring events
	if filter.StartTime != nil && filter.EndTime != nil {
		// Events that overlap with the date range:
		// 1. Events that start within the range
		// 2. Events that end within the range
		// 3. Events that span across the range
		query = query.Where(
			"(start_time BETWEEN ? AND ?) OR "+
				"(end_time BETWEEN ? AND ?) OR "+
				"(start_time <= ? AND end_time >= ?)",
			filter.StartTime, filter.EndTime,
			filter.StartTime, filter.EndTime,
			filter.StartTime, filter.EndTime,
		)
	}

	if filter.EventType != nil {
		query = query.Where("event_type = ?", filter.EventType)
	}
	if filter.Search != "" {
		query = query.Where("title ILIKE ? OR description ILIKE ?",
			"%"+filter.Search+"%", "%"+filter.Search+"%")
	}

	// Get total count
	if err := query.Count(&total).Error; err != nil {
		return nil, 0, err
	}

	// Apply pagination
	if filter.Page > 0 && filter.PageSize > 0 {
		offset := (filter.Page - 1) * filter.PageSize
		query = query.Offset(offset).Limit(filter.PageSize)
	}

	// Execute query with preloads
	err := query.
		Preload("RecurrenceRules").
		Preload("Reminders").
		Find(&events).Error

	return events, total, err
}

func (r *repository) AddRecurrenceRule(ctx context.Context, rule *RecurrenceRule) error {
	return r.db.WithContext(ctx).Create(rule).Error
}

func (r *repository) UpdateRecurrenceRule(ctx context.Context, rule *RecurrenceRule) error {
	return r.db.WithContext(ctx).Save(rule).Error
}

func (r *repository) DeleteRecurrenceRule(ctx context.Context, id uuid.UUID) error {
	return r.db.WithContext(ctx).Delete(&RecurrenceRule{}, id).Error
}

func (r *repository) CreateException(ctx context.Context, exception *EventException) error {
	return r.db.WithContext(ctx).Create(exception).Error
}

func (r *repository) UpdateException(ctx context.Context, exception *EventException) error {
	return r.db.WithContext(ctx).Save(exception).Error
}

func (r *repository) GetExceptions(ctx context.Context, eventID uuid.UUID, startTime, endTime time.Time) ([]EventException, error) {
	var exceptions []EventException
	err := r.db.WithContext(ctx).
		Where("event_id = ? AND original_time BETWEEN ? AND ?", eventID, startTime, endTime).
		Find(&exceptions).Error
	return exceptions, err
}

func (r *repository) CreateOccurrence(ctx context.Context, occurrence *EventOccurrence) error {
	return r.db.WithContext(ctx).Create(occurrence).Error
}

func (r *repository) UpdateOccurrenceStatus(ctx context.Context, id uuid.UUID, status OccurrenceStatus) error {
	return r.db.WithContext(ctx).
		Model(&EventOccurrence{}).
		Where("id = ?", id).
		Update("status", status).Error
}

func (r *repository) GetOccurrences(ctx context.Context, eventID uuid.UUID, startTime, endTime time.Time) ([]EventOccurrence, error) {
	var occurrences []EventOccurrence
	err := r.db.WithContext(ctx).
		Where("event_id = ? AND occurrence_time BETWEEN ? AND ?", eventID, startTime, endTime).
		Find(&occurrences).Error
	return occurrences, err
}

func (r *repository) AddReminder(ctx context.Context, reminder *EventReminder) error {
	return r.db.WithContext(ctx).Create(reminder).Error
}

func (r *repository) UpdateReminder(ctx context.Context, reminder *EventReminder) error {
	return r.db.WithContext(ctx).Save(reminder).Error
}

func (r *repository) DeleteReminder(ctx context.Context, id uuid.UUID) error {
	return r.db.WithContext(ctx).Delete(&EventReminder{}, id).Error
}

func (r *repository) GetUpcomingReminders(ctx context.Context, startTime, endTime time.Time) ([]EventReminder, error) {
	var reminders []EventReminder
	err := r.db.WithContext(ctx).
		Joins("JOIN calendar_events ON calendar_events.id = event_reminders.event_id").
		Where("calendar_events.start_time BETWEEN ? AND ?", startTime, endTime).
		Find(&reminders).Error
	return reminders, err
}

func (r *repository) BeginTransaction(ctx context.Context) Transaction {
	tx := r.db.WithContext(ctx).Begin()
	if tx.Error != nil {
		return nil
	}
	return &transaction{tx: tx}
}

type transaction struct {
	tx *gorm.DB
}

func (t *transaction) Commit() error {
	return t.tx.Commit().Error
}

func (t *transaction) Rollback() error {
	return t.tx.Rollback().Error
}

func (t *transaction) CreateEvent(event *CalendarEvent) error {
	return t.tx.Create(event).Error
}

func (t *transaction) CreateRecurrenceRule(rule *RecurrenceRule) error {
	return t.tx.Create(rule).Error
}

func (t *transaction) CreateOccurrence(occurrence *EventOccurrence) error {
	return t.tx.Create(occurrence).Error
}

func (t *transaction) CreateReminder(reminder *EventReminder) error {
	return t.tx.Create(reminder).Error
}

func (t *transaction) UpdateEvent(event *CalendarEvent) error {
	return t.tx.Save(event).Error
}

func (t *transaction) CreateException(exception *EventException) error {
	return t.tx.Create(exception).Error
}

func (t *transaction) UpdateException(exception *EventException) error {
	return t.tx.Save(exception).Error
}

func (t *transaction) GetExceptions(eventID uuid.UUID, startTime, endTime time.Time) ([]EventException, error) {
	var exceptions []EventException
	err := t.tx.Where("event_id = ? AND original_time BETWEEN ? AND ?", eventID, startTime, endTime).
		Find(&exceptions).Error
	return exceptions, err
}
