package scheduler

import (
	"context"
	"time"

	"github.com/ahmedelhadi17776/Compass/Backend_go/internal/domain/habits"
	"github.com/ahmedelhadi17776/Compass/Backend_go/pkg/logger"
	"go.uber.org/zap"
)

type Scheduler struct {
	habitService habits.Service
	logger       *logger.Logger
}

func NewScheduler(habitService habits.Service, logger *logger.Logger) *Scheduler {
	return &Scheduler{
		habitService: habitService,
		logger:       logger,
	}
}

func (s *Scheduler) Start() {
	// Run immediately at startup
	s.runResetTasks()

	// Calculate time until next midnight
	now := time.Now()
	nextMidnight := time.Date(now.Year(), now.Month(), now.Day()+1, 0, 0, 0, 0, now.Location())
	timeUntilMidnight := nextMidnight.Sub(now)

	s.logger.Info("Habit scheduler initialized",
		zap.Time("current_time", now),
		zap.Time("next_run", nextMidnight),
		zap.Duration("time_until_next_run", timeUntilMidnight),
	)

	// Start the scheduler
	go func() {
		// Wait until first midnight
		time.Sleep(timeUntilMidnight)

		// Then run every 24 hours
		ticker := time.NewTicker(24 * time.Hour)
		for range ticker.C {
			s.runResetTasks()
		}
	}()
}

func (s *Scheduler) runResetTasks() {
	ctx := context.Background()
	startTime := time.Now()

	s.logger.Info("Starting daily habit reset tasks", zap.Time("start_time", startTime))

	// Reset daily completions for habits completed in past days
	resetCount, err := s.habitService.ResetDailyCompletions(ctx)
	if err != nil {
		s.logger.Error("Failed to reset daily completions",
			zap.Error(err),
		)
	} else {
		s.logger.Info("Successfully reset daily completions",
			zap.Int64("reset_count", resetCount),
			zap.String("reset_criteria", "Habits completed before today"),
		)
	}

	// Then check and reset broken streaks
	// This will automatically log streak history before resetting
	streakResetCount, err := s.habitService.CheckAndResetBrokenStreaks(ctx)
	if err != nil {
		s.logger.Error("Failed to reset broken streaks",
			zap.Error(err),
		)
	} else {
		s.logger.Info("Successfully processed broken streaks",
			zap.Int64("streak_reset_count", streakResetCount),
			zap.String("reset_criteria", "Habits not completed since yesterday"),
		)
	}

	s.logger.Info("Completed daily habit reset tasks",
		zap.Time("end_time", time.Now()),
		zap.Duration("duration", time.Since(startTime)),
	)
}
