from typing import Callable, Dict, List
from enum import Enum


class EventType(str, Enum):
    """Runtime event types."""
    TASK_CREATED = "TASK_CREATED"
    TASK_QUEUED = "TASK_QUEUED"
    TASK_STARTED = "TASK_STARTED"
    TASK_COMPLETED = "TASK_COMPLETED"
    TASK_FAILED = "TASK_FAILED"
    TASK_RETRIED = "TASK_RETRIED"
    MANUAL_REVIEW_REQUIRED = "MANUAL_REVIEW_REQUIRED"
    WORKER_ASSIGNED = "WORKER_ASSIGNED"
    WORKER_RELEASED = "WORKER_RELEASED"


class Event:
    """Immutable event record."""

    def __init__(self, event_type: str, data: dict):
        """
        Initialize event.

        Args:
            event_type: Type of event
            data: Event payload
        """
        self.event_type = event_type
        self.data = data

    def to_dict(self) -> dict:
        """Convert event to dictionary."""
        return {
            "event_type": self.event_type,
            "data": self.data,
        }


class EventBus:
    """Lightweight event bus for runtime events."""

    def __init__(self):
        """Initialize event bus."""
        self._subscribers: Dict[str, List[Callable]] = {}
        self._event_history: List[Event] = []

    def subscribe(self, event_type: str, handler: Callable) -> None:
        """
        Subscribe to event type.

        Args:
            event_type: Event type to subscribe to
            handler: Callable that receives event data
        """
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(handler)

    def unsubscribe(self, event_type: str, handler: Callable) -> None:
        """
        Unsubscribe from event type.

        Args:
            event_type: Event type to unsubscribe from
            handler: Handler to remove
        """
        if event_type in self._subscribers:
            self._subscribers[event_type] = [
                h for h in self._subscribers[event_type] if h != handler
            ]

    def emit(self, event_type: str, data: dict) -> None:
        """
        Emit event to all subscribers.

        Args:
            event_type: Type of event
            data: Event payload
        """
        event = Event(event_type, data)
        self._event_history.append(event)

        if event_type in self._subscribers:
            for handler in self._subscribers[event_type]:
                try:
                    handler(data)
                except Exception as e:
                    # Log but don't propagate handler errors
                    print(f"Error in event handler for {event_type}: {e}")

    def get_history(self, event_type: str = None, limit: int = 100) -> List[Event]:
        """
        Retrieve event history.

        Args:
            event_type: Filter by event type (None = all)
            limit: Maximum number of events

        Returns:
            List of events
        """
        if event_type:
            events = [e for e in self._event_history if e.event_type == event_type]
        else:
            events = self._event_history
        return events[-limit:]

    def clear_history(self) -> None:
        """Clear event history."""
        self._event_history = []

    def get_subscriber_count(self, event_type: str = None) -> int:
        """
        Get number of subscribers.

        Args:
            event_type: Specific event type (None = all)

        Returns:
            Number of subscribers
        """
        if event_type:
            return len(self._subscribers.get(event_type, []))
        return sum(len(handlers) for handlers in self._subscribers.values())
