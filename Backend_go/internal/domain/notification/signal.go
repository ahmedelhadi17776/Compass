package notification

import (
	"errors"
	"sync"
)

var (
	// ErrEmptyTopic is returned when no topic is found
	ErrEmptyTopic = errors.New("no topic found")
)

// SignalRepository defines the interface for notification signal management
type SignalRepository interface {
	// Subscribe subscribes to a topic and returns a channel for notifications
	Subscribe(topic string) (<-chan *Notification, func(), error)

	// Publish publishes a notification to a topic
	Publish(topic string, notification *Notification) error
}

// Topic represents a notification topic
type Topic struct {
	Listeners []chan<- *Notification
	Mutex     *sync.Mutex
}

// signalImpl implements the SignalRepository interface
type signalImpl struct {
	Topics    *sync.Map
	TopicSize int
}

// NewSignalRepository creates a new signal repository
func NewSignalRepository(topicSize int) SignalRepository {
	return &signalImpl{
		Topics:    new(sync.Map),
		TopicSize: topicSize,
	}
}

// Subscribe subscribes to notifications for a specific topic
func (s *signalImpl) Subscribe(topic string) (<-chan *Notification, func(), error) {
	topicInf, _ := s.Topics.LoadOrStore(topic, &Topic{Mutex: new(sync.Mutex)})
	t := topicInf.(*Topic)

	t.Mutex.Lock()
	defer t.Mutex.Unlock()

	// Create buffered channel to prevent blocking
	ch := make(chan *Notification, s.TopicSize)
	t.Listeners = append(t.Listeners, ch)

	// Return read-only channel and cleanup function
	return ch, func() {
		t.Mutex.Lock()
		defer t.Mutex.Unlock()

		for i := 0; i < len(t.Listeners); i++ {
			if t.Listeners[i] == ch {
				// Remove channel from listeners
				t.Listeners = append(t.Listeners[:i], t.Listeners[i+1:]...)
				close(ch) // Close the channel
				break
			}
		}
	}, nil
}

// Publish publishes a notification to a topic
func (s *signalImpl) Publish(topic string, notification *Notification) error {
	topicInf, ok := s.Topics.Load(topic)
	if !ok {
		return ErrEmptyTopic
	}

	t := topicInf.(*Topic)
	t.Mutex.Lock()
	defer t.Mutex.Unlock()

	if len(t.Listeners) == 0 {
		return ErrEmptyTopic
	}

	// Send notification to all listeners
	for _, listener := range t.Listeners {
		// Non-blocking send to prevent slowdowns
		select {
		case listener <- notification:
		default:
			// Channel is full, continue to next listener
		}
	}

	return nil
}
