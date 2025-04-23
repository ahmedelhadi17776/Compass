package calendar

import (
	"context"
	"fmt"
	"strings"
	"time"

	"github.com/google/uuid"
)

// Service defines the business logic interface for calendar events
type Service interface {
	// Event operations
	CreateEvent(ctx context.Context, req CreateCalendarEventRequest, userID uuid.UUID) (*CalendarEvent, error)
	UpdateEvent(ctx context.Context, id uuid.UUID, req UpdateCalendarEventRequest) (*CalendarEvent, error)
	DeleteEvent(ctx context.Context, id uuid.UUID) error
	GetEventByID(ctx context.Context, id uuid.UUID) (*CalendarEvent, error)
	ListEvents(ctx context.Context, userID uuid.UUID, startTime, endTime time.Time, eventType *EventType, page, pageSize int) (*CalendarEventListResponse, error)

	// Occurrence operations
	UpdateOccurrence(ctx context.Context, eventID uuid.UUID, originalTime time.Time, req UpdateCalendarEventRequest) error
	DeleteOccurrence(ctx context.Context, eventID uuid.UUID, originalTime time.Time) error
	ListOccurrences(ctx context.Context, eventID uuid.UUID, startTime, endTime time.Time) ([]EventOccurrence, error)

	// Reminder operations
	AddReminder(ctx context.Context, eventID uuid.UUID, req CreateEventReminderRequest) error
	UpdateReminder(ctx context.Context, id uuid.UUID, req CreateEventReminderRequest) error
	DeleteReminder(ctx context.Context, id uuid.UUID) error
}

type service struct {
	repo Repository
}

// NewService creates a new calendar service instance
func NewService(repo Repository) Service {
	return &service{repo: repo}
}

func (s *service) CreateEvent(ctx context.Context, req CreateCalendarEventRequest, userID uuid.UUID) (*CalendarEvent, error) {
	// Start a transaction
	tx := s.repo.BeginTransaction(ctx)
	if tx == nil {
		return nil, fmt.Errorf("failed to start transaction")
	}
	defer tx.Rollback()

	// Create the main event
	event := &CalendarEvent{
		UserID:       userID,
		Title:        req.Title,
		Description:  req.Description,
		EventType:    req.EventType,
		StartTime:    req.StartTime,
		EndTime:      req.EndTime,
		IsAllDay:     req.IsAllDay,
		Location:     req.Location,
		Color:        req.Color,
		Transparency: req.Transparency,
	}

	// Validate the event
	if err := event.Validate(); err != nil {
		return nil, err
	}

	// Create the event
	if err := tx.CreateEvent(event); err != nil {
		return nil, err
	}

	// Add recurrence rule if specified
	var rule *RecurrenceRule
	if req.RecurrenceRule != nil {
		rule = &RecurrenceRule{
			EventID:    event.ID,
			Freq:       req.RecurrenceRule.Freq,
			Interval:   req.RecurrenceRule.Interval,
			ByDay:      StringArray(req.RecurrenceRule.ByDay),
			ByMonth:    Int64Array(convertToInt64(req.RecurrenceRule.ByMonth)),
			ByMonthDay: Int64Array(convertToInt64(req.RecurrenceRule.ByMonthDay)),
			Count:      req.RecurrenceRule.Count,
			Until:      req.RecurrenceRule.Until,
		}
		if err := rule.Validate(); err != nil {
			return nil, err
		}
		if err := tx.CreateRecurrenceRule(rule); err != nil {
			return nil, err
		}

		// Generate and store initial occurrences
		occurrences := s.generateOccurrences(event, rule)
		for _, occ := range occurrences {
			if err := tx.CreateOccurrence(occ); err != nil {
				return nil, err
			}
		}
	}

	// Add reminders if specified
	for _, reminderReq := range req.Reminders {
		reminder := &EventReminder{
			EventID:       event.ID,
			MinutesBefore: reminderReq.MinutesBefore,
			Method:        reminderReq.Method,
		}
		if err := reminder.Validate(); err != nil {
			return nil, err
		}
		if err := tx.CreateReminder(reminder); err != nil {
			return nil, err
		}
	}

	if err := tx.Commit(); err != nil {
		return nil, err
	}

	// Fetch the complete event with all relationships
	return s.GetEventByID(ctx, event.ID)
}

// generateOccurrences generates event occurrences based on the recurrence rule
func (s *service) generateOccurrences(event *CalendarEvent, rule *RecurrenceRule) []*EventOccurrence {
	var occurrences []*EventOccurrence
	currentTime := event.StartTime

	// Determine the end date for occurrence generation
	var endDate time.Time
	if rule.Until != nil {
		endDate = *rule.Until
	} else if rule.Count != nil {
		// If count is specified, we'll generate that many occurrences
		endDate = event.StartTime.AddDate(10, 0, 0) // Use 10 years as a reasonable maximum
	} else {
		// If neither until nor count is specified, generate occurrences for 1 year
		endDate = event.StartTime.AddDate(1, 0, 0)
	}

	count := 0
	for currentTime.Before(endDate) {
		if rule.Count != nil && count >= *rule.Count {
			break
		}

		// Check if this occurrence matches the recurrence pattern
		if s.isValidOccurrence(currentTime, rule) {
			occurrence := &EventOccurrence{
				EventID:        event.ID,
				OccurrenceTime: currentTime,
				Status:         OccurrenceStatusUpcoming,
			}
			occurrences = append(occurrences, occurrence)
			count++
		}

		// Advance to next potential occurrence
		switch rule.Freq {
		case RecurrenceTypeDaily:
			currentTime = currentTime.AddDate(0, 0, rule.Interval)
		case RecurrenceTypeWeekly:
			currentTime = currentTime.AddDate(0, 0, 7*rule.Interval)
		case RecurrenceTypeBiweekly:
			currentTime = currentTime.AddDate(0, 0, 14*rule.Interval)
		case RecurrenceTypeMonthly:
			currentTime = currentTime.AddDate(0, rule.Interval, 0)
		case RecurrenceTypeYearly:
			currentTime = currentTime.AddDate(rule.Interval, 0, 0)
		}
	}

	return occurrences
}

// isValidOccurrence checks if a given date matches the recurrence rule
func (s *service) isValidOccurrence(date time.Time, rule *RecurrenceRule) bool {
	// Check ByDay (if specified)
	if len(rule.ByDay) > 0 {
		weekday := strings.ToUpper(date.Weekday().String()[:2])
		found := false
		for _, day := range rule.ByDay {
			if string(day) == weekday {
				found = true
				break
			}
		}
		if !found {
			return false
		}
	}

	// Check ByMonth (if specified)
	if len(rule.ByMonth) > 0 {
		month := int64(date.Month())
		found := false
		for _, m := range rule.ByMonth {
			if m == month {
				found = true
				break
			}
		}
		if !found {
			return false
		}
	}

	// Check ByMonthDay (if specified)
	if len(rule.ByMonthDay) > 0 {
		day := int64(date.Day())
		found := false
		for _, d := range rule.ByMonthDay {
			if d == day {
				found = true
				break
			}
		}
		if !found {
			return false
		}
	}

	return true
}

// Helper function to convert []int to []int64
func convertToInt64(input []int) []int64 {
	if input == nil {
		return nil
	}
	result := make([]int64, len(input))
	for i, v := range input {
		result[i] = int64(v)
	}
	return result
}

func (s *service) UpdateEvent(ctx context.Context, id uuid.UUID, req UpdateCalendarEventRequest) (*CalendarEvent, error) {
	event, err := s.repo.GetEventByID(ctx, id)
	if err != nil {
		return nil, err
	}

	// Start a transaction for updating the event and related data
	tx := s.repo.BeginTransaction(ctx)
	if tx == nil {
		return nil, fmt.Errorf("failed to start transaction")
	}
	defer tx.Rollback()

	// Calculate time difference if start time is being updated
	var timeDiff time.Duration
	if req.StartTime != nil {
		timeDiff = req.StartTime.Sub(event.StartTime)
	}

	// Update fields if provided
	if req.Title != nil {
		event.Title = *req.Title
	}
	if req.Description != nil {
		event.Description = *req.Description
	}
	if req.EventType != nil {
		event.EventType = *req.EventType
	}
	if req.StartTime != nil {
		event.StartTime = *req.StartTime
	}
	if req.EndTime != nil {
		event.EndTime = *req.EndTime
	}
	if req.IsAllDay != nil {
		event.IsAllDay = *req.IsAllDay
	}
	if req.Location != nil {
		event.Location = *req.Location
	}
	if req.Color != nil {
		event.Color = *req.Color
	}
	if req.Transparency != nil {
		event.Transparency = *req.Transparency
	}

	// Validate and update the main event
	if err := event.Validate(); err != nil {
		return nil, err
	}
	if err := tx.UpdateEvent(event); err != nil {
		return nil, err
	}

	// If this is a recurring event and time was updated
	if len(event.RecurrenceRules) > 0 && (req.StartTime != nil || req.EndTime != nil) {
		// Get all future exceptions
		now := time.Now()
		exceptions, err := tx.GetExceptions(event.ID, now, now.AddDate(10, 0, 0))
		if err != nil {
			return nil, err
		}

		// Update time in exceptions while preserving other overrides
		for _, exception := range exceptions {
			if exception.OverrideStartTime != nil {
				newTime := exception.OverrideStartTime.Add(timeDiff)
				exception.OverrideStartTime = &newTime
			}
			if exception.OverrideEndTime != nil {
				newTime := exception.OverrideEndTime.Add(timeDiff)
				exception.OverrideEndTime = &newTime
			}
			if err := tx.UpdateException(&exception); err != nil {
				return nil, err
			}
		}
	}

	if err := tx.Commit(); err != nil {
		return nil, err
	}

	return s.GetEventByID(ctx, event.ID)
}

func (s *service) DeleteEvent(ctx context.Context, id uuid.UUID) error {
	return s.repo.DeleteEvent(ctx, id)
}

func (s *service) GetEventByID(ctx context.Context, id uuid.UUID) (*CalendarEvent, error) {
	return s.repo.GetEventByID(ctx, id)
}

func (s *service) ListEvents(ctx context.Context, userID uuid.UUID, startTime, endTime time.Time, eventType *EventType, page, pageSize int) (*CalendarEventListResponse, error) {
	filter := EventFilter{
		UserID:    userID,
		StartTime: &startTime,
		EndTime:   &endTime,
		EventType: eventType,
		Page:      page,
		PageSize:  pageSize,
	}

	events, total, err := s.repo.ListEvents(ctx, filter)
	if err != nil {
		return nil, err
	}

	// For each recurring event, generate and apply exceptions
	for i, event := range events {
		if len(event.RecurrenceRules) > 0 {
			// Generate occurrences based on recurrence rules
			occurrences := s.generateOccurrences(&event, &event.RecurrenceRules[0])

			// Filter occurrences to the requested date range
			var validOccurrences []*EventOccurrence
			for _, occ := range occurrences {
				if (occ.OccurrenceTime.Equal(startTime) || occ.OccurrenceTime.After(startTime)) &&
					(occ.OccurrenceTime.Equal(endTime) || occ.OccurrenceTime.Before(endTime)) {
					validOccurrences = append(validOccurrences, occ)
				}
			}

			// Get exceptions for this event
			exceptions, err := s.repo.GetExceptions(ctx, event.ID, startTime, endTime)
			if err != nil {
				return nil, err
			}

			// Create a map of exceptions by original time for quick lookup
			exceptionMap := make(map[time.Time]*EventException)
			for i := range exceptions {
				exceptionMap[exceptions[i].OriginalTime] = &exceptions[i]
			}

			// Apply exceptions to occurrences
			var finalOccurrences []EventOccurrence
			for _, occ := range validOccurrences {
				if exception, exists := exceptionMap[occ.OccurrenceTime]; exists {
					if exception.IsDeleted {
						continue // Skip deleted occurrences
					}
					// Apply overrides
					if exception.OverrideStartTime != nil {
						occ.OccurrenceTime = *exception.OverrideStartTime
					}
				}
				finalOccurrences = append(finalOccurrences, *occ)
			}

			events[i].Occurrences = finalOccurrences
		}
	}

	return &CalendarEventListResponse{
		Events: events,
		Total:  total,
	}, nil
}

func (s *service) UpdateOccurrence(ctx context.Context, eventID uuid.UUID, originalTime time.Time, req UpdateCalendarEventRequest) error {
	// Verify the event exists and is recurring
	event, err := s.repo.GetEventByID(ctx, eventID)
	if err != nil {
		return err
	}
	if len(event.RecurrenceRules) == 0 {
		return fmt.Errorf("cannot update occurrence of non-recurring event")
	}

	// Start a transaction
	tx := s.repo.BeginTransaction(ctx)
	if tx == nil {
		return fmt.Errorf("failed to start transaction")
	}
	defer tx.Rollback()

	// Check if an exception already exists
	exceptions, err := tx.GetExceptions(eventID, originalTime, originalTime)
	if err != nil {
		return err
	}

	var exception *EventException
	if len(exceptions) > 0 {
		// Update existing exception
		exception = &exceptions[0]
	} else {
		// Create new exception
		exception = &EventException{
			EventID:      eventID,
			OriginalTime: originalTime,
		}
	}

	// Update exception fields based on the request
	if req.StartTime != nil {
		exception.OverrideStartTime = req.StartTime
	}
	if req.EndTime != nil {
		exception.OverrideEndTime = req.EndTime
	}
	if req.Title != nil {
		exception.OverrideTitle = req.Title
	}
	if req.Description != nil {
		exception.OverrideDescription = req.Description
	}
	if req.Location != nil {
		exception.OverrideLocation = req.Location
	}
	if req.Color != nil {
		exception.OverrideColor = req.Color
	}
	if req.Transparency != nil {
		exception.OverrideTransparency = req.Transparency
	}

	// Save the exception
	if len(exceptions) > 0 {
		if err := tx.UpdateException(exception); err != nil {
			return err
		}
	} else {
		if err := tx.CreateException(exception); err != nil {
			return err
		}
	}

	return tx.Commit()
}

func (s *service) DeleteOccurrence(ctx context.Context, eventID uuid.UUID, originalTime time.Time) error {
	// Create an exception that marks this occurrence as deleted
	exception := &EventException{
		EventID:      eventID,
		OriginalTime: originalTime,
		IsDeleted:    true,
	}

	// Check if an exception already exists
	exceptions, err := s.repo.GetExceptions(ctx, eventID, originalTime, originalTime)
	if err != nil {
		return err
	}

	if len(exceptions) > 0 {
		// Update existing exception to mark as deleted
		exceptions[0].IsDeleted = true
		return s.repo.UpdateException(ctx, &exceptions[0])
	}

	// Create new exception
	return s.repo.CreateException(ctx, exception)
}

func (s *service) ListOccurrences(ctx context.Context, eventID uuid.UUID, startTime, endTime time.Time) ([]EventOccurrence, error) {
	// Get base occurrences
	occurrences, err := s.repo.GetOccurrences(ctx, eventID, startTime, endTime)
	if err != nil {
		return nil, err
	}

	// Get exceptions for this time range
	exceptions, err := s.repo.GetExceptions(ctx, eventID, startTime, endTime)
	if err != nil {
		return nil, err
	}

	// Create a map of exceptions by original time for quick lookup
	exceptionMap := make(map[time.Time]*EventException)
	for i := range exceptions {
		exceptionMap[exceptions[i].OriginalTime] = &exceptions[i]
	}

	// Filter out deleted occurrences and apply modifications
	var result []EventOccurrence
	for _, occ := range occurrences {
		if exception, exists := exceptionMap[occ.OccurrenceTime]; exists {
			if exception.IsDeleted {
				continue // Skip deleted occurrences
			}
			// Apply exception modifications if they exist
			if exception.OverrideStartTime != nil {
				occ.OccurrenceTime = *exception.OverrideStartTime
			}
		}
		result = append(result, occ)
	}

	return result, nil
}

func (s *service) AddReminder(ctx context.Context, eventID uuid.UUID, req CreateEventReminderRequest) error {
	reminder := &EventReminder{
		EventID:       eventID,
		MinutesBefore: req.MinutesBefore,
		Method:        req.Method,
	}
	if err := reminder.Validate(); err != nil {
		return err
	}
	return s.repo.AddReminder(ctx, reminder)
}

func (s *service) UpdateReminder(ctx context.Context, id uuid.UUID, req CreateEventReminderRequest) error {
	reminder := &EventReminder{
		ID:            id,
		MinutesBefore: req.MinutesBefore,
		Method:        req.Method,
	}
	if err := reminder.Validate(); err != nil {
		return err
	}
	return s.repo.UpdateReminder(ctx, reminder)
}

func (s *service) DeleteReminder(ctx context.Context, id uuid.UUID) error {
	return s.repo.DeleteReminder(ctx, id)
}
