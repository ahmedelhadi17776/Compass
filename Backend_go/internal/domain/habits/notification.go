package habits

import (
	"context"
	"fmt"

	"github.com/ahmedelhadi17776/Compass/Backend_go/internal/domain/notification"
	"github.com/google/uuid"
)

// HabitNotificationService handles notifications for habits
type HabitNotificationService struct {
	notificationService notification.Service
}

// NewHabitNotificationService creates a new habit notification service
func NewHabitNotificationService(notificationService notification.Service) *HabitNotificationService {
	return &HabitNotificationService{
		notificationService: notificationService,
	}
}

// NotifyHabitCompleted sends a notification when a habit is completed
func (s *HabitNotificationService) NotifyHabitCompleted(ctx context.Context, userID uuid.UUID, habit *Habit) error {
	title := "Habit Completed"
	content := fmt.Sprintf("You've completed your habit: %s", habit.Title)

	return s.notificationService.CreateForUser(
		ctx,
		userID,
		notification.HabitCompleted,
		title,
		content,
		map[string]string{
			"habitID": habit.ID.String(),
			"title":   habit.Title,
		},
		"habits",
		habit.ID,
	)
}

// NotifyHabitStreak sends a notification when a habit streak reaches a milestone
func (s *HabitNotificationService) NotifyHabitStreak(ctx context.Context, userID uuid.UUID, habit *Habit) error {
	title := "Habit Streak"
	content := fmt.Sprintf("Amazing! You've maintained a %d day streak for your habit: %s", habit.CurrentStreak, habit.Title)

	return s.notificationService.CreateForUser(
		ctx,
		userID,
		notification.HabitStreak,
		title,
		content,
		map[string]string{
			"habitID":       habit.ID.String(),
			"title":         habit.Title,
			"currentStreak": fmt.Sprintf("%d", habit.CurrentStreak),
		},
		"habits",
		habit.ID,
	)
}

// NotifyHabitStreakBroken sends a notification when a habit streak is broken
func (s *HabitNotificationService) NotifyHabitStreakBroken(ctx context.Context, userID uuid.UUID, habit *Habit, streakLength int) error {
	title := "Habit Streak Broken"
	content := fmt.Sprintf("Your %d day streak for habit \"%s\" has been broken. Don't worry, you can start a new streak today!", streakLength, habit.Title)

	return s.notificationService.CreateForUser(
		ctx,
		userID,
		notification.HabitBroken,
		title,
		content,
		map[string]string{
			"habitID":      habit.ID.String(),
			"title":        habit.Title,
			"streakLength": fmt.Sprintf("%d", streakLength),
		},
		"habits",
		habit.ID,
	)
}

// NotifyHabitReminder sends a reminder notification for a habit
func (s *HabitNotificationService) NotifyHabitReminder(ctx context.Context, userID uuid.UUID, habit *Habit) error {
	title := "Habit Reminder"
	content := fmt.Sprintf("Don't forget to complete your habit: %s", habit.Title)

	return s.notificationService.CreateForUser(
		ctx,
		userID,
		notification.HabitReminder,
		title,
		content,
		map[string]string{
			"habitID": habit.ID.String(),
			"title":   habit.Title,
		},
		"habits",
		habit.ID,
	)
}

// NotifyHabitMilestone sends a notification when a habit reaches a significant milestone
func (s *HabitNotificationService) NotifyHabitMilestone(ctx context.Context, userID uuid.UUID, habit *Habit, milestone string, achievementDesc string) error {
	title := fmt.Sprintf("Habit Milestone: %s", milestone)
	content := fmt.Sprintf("Congratulations! %s for habit \"%s\"", achievementDesc, habit.Title)

	return s.notificationService.CreateForUser(
		ctx,
		userID,
		notification.HabitMilestone,
		title,
		content,
		map[string]string{
			"habitID":   habit.ID.String(),
			"title":     habit.Title,
			"milestone": milestone,
		},
		"habits",
		habit.ID,
	)
}

// ShouldSendStreakNotification determines if a streak notification should be sent
// sent for milestones (3 days, 7 days, 14 days, 30 days, etc)
func (s *HabitNotificationService) ShouldSendStreakNotification(streak int) bool {
	milestones := []int{3, 7, 14, 21, 30, 60, 90, 100, 180, 365}

	for _, milestone := range milestones {
		if streak == milestone {
			return true
		}
	}

	return false
}
