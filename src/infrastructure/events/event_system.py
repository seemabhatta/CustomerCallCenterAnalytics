"""
Blinker-based Event System for Knowledge Graph 2.0.

Lightweight pub/sub using Blinker signals for event-driven architecture.
NO FALLBACK PRINCIPLE: Events must be delivered or system fails fast.
"""
import logging
from typing import Dict, Any, Callable, List, Optional
from datetime import datetime
from dataclasses import asdict

from blinker import Namespace

from .event_types import Event, EventType

logger = logging.getLogger(__name__)

# Global namespace for all event signals
_event_namespace = Namespace()


class EventSystemError(Exception):
    """Exception raised for event system errors."""
    pass


class EventSystem:
    """
    Blinker-based event system for pub/sub architecture.

    Features:
    - Lightweight signal-based events using Blinker
    - Type-safe event publishing and subscription
    - Event delivery guarantees
    - Error handling with fail-fast behavior
    - Event statistics and monitoring
    """

    def __init__(self):
        """Initialize the event system."""
        self._subscribers: Dict[str, Dict] = {}
        self._wrapped_handlers: Dict[str, List[Callable]] = {}  # Keep references to prevent GC
        self._stats = {
            'events_published': 0,
            'events_processed': 0,
            'events_failed': 0,
            'subscribers_count': 0
        }
        self._event_history: List[Event] = []
        self._max_history = 1000

        logger.info("✅ EventSystem initialized with Blinker")

    def _get_signal(self, event_type: EventType):
        """Get or create signal for event type."""
        return _event_namespace.signal(event_type.value)

    def publish(self, event: Event) -> bool:
        """
        Publish event to all subscribers.

        Args:
            event: Event to publish

        Returns:
            True if successfully published to all subscribers

        Raises:
            EventSystemError: If event publishing fails (NO FALLBACK)
        """
        if not isinstance(event, Event):
            raise EventSystemError("Invalid event object")

        try:
            # Add to history
            self._event_history.append(event)
            if len(self._event_history) > self._max_history:
                self._event_history.pop(0)

            self._stats['events_published'] += 1

            # Get signal for this event type
            event_signal = self._get_signal(event.event_type)

            # Debug: Check connected receivers
            all_receivers = getattr(event_signal, 'receivers', {})
            sender_receivers = all_receivers.get(id(self), set()) if all_receivers else set()
            any_receivers = getattr(event_signal, '_by_receiver', {})
            logger.debug(f"Signal {event.event_type} (id: {id(event_signal)}) has {len(all_receivers)} total receivers, {len(sender_receivers)} for this sender, {len(any_receivers)} any receivers")

            # Send signal with event data
            responses = event_signal.send(
                self,
                event=event,
                event_type=event.event_type,
                payload=event.payload,
                timestamp=event.timestamp,
                source_service=event.source_service
            )

            # Debug: Check responses
            logger.debug(f"Signal {event.event_type} got {len(responses)} responses")

            # Check for handler failures
            success_count = 0
            for receiver, response in responses:
                if isinstance(response, str) and response.startswith("HANDLER_ERROR:"):
                    # This is an error message from our wrapper
                    error_msg = f"Handler failed for event {event.event_type}: {response}"
                    logger.error(error_msg)
                    self._stats['events_failed'] += 1

                    # NO FALLBACK: Fail fast on critical event processing errors
                    raise EventSystemError(error_msg)
                else:
                    # Handler succeeded (any return value except error strings)
                    success_count += 1
                    self._stats['events_processed'] += 1

            subscriber_count = len(responses)
            if subscriber_count == 0:
                logger.warning(f"No subscribers for event type: {event.event_type}")
            else:
                logger.info(f"📢 Event {event.event_type} published to {subscriber_count} subscribers")

            return True

        except Exception as e:
            logger.error(f"Failed to publish event {event.event_type}: {e}")
            raise EventSystemError(f"Event publishing failed: {e}")

    def subscribe(self, event_types: List[EventType], handler: Callable,
                  subscriber_name: str) -> bool:
        """
        Subscribe to specific event types.

        Args:
            event_types: List of event types to subscribe to
            handler: Function to handle events
            subscriber_name: Unique name for this subscriber

        Returns:
            True if subscription successful

        Raises:
            EventSystemError: If subscription fails (NO FALLBACK)
        """
        if not event_types:
            raise EventSystemError("event_types cannot be empty")

        if not callable(handler):
            raise EventSystemError("handler must be callable")

        if not subscriber_name:
            raise EventSystemError("subscriber_name is required")

        try:
            # Store subscriber info
            self._subscribers[subscriber_name] = {
                'event_types': event_types,
                'handler': handler,
                'events_processed': 0,
                'last_error': None,
                'created_at': datetime.utcnow()
            }

            # Initialize wrapped handlers list for this subscriber
            self._wrapped_handlers[subscriber_name] = []

            # Connect to all requested event type signals
            for event_type in event_types:
                event_signal = self._get_signal(event_type)

                # Create a wrapper that tracks subscriber stats
                def create_wrapped_handler(handler_func, sub_name):
                    def wrapped_handler(*args, **kwargs):
                        try:
                            result = handler_func(*args, **kwargs)
                            self._subscribers[sub_name]['events_processed'] += 1
                            return result
                        except Exception as e:
                            error_msg = f"HANDLER_ERROR:{sub_name}:{str(e)}"
                            self._subscribers[sub_name]['last_error'] = str(e)
                            logger.error(f"Handler {sub_name} failed: {str(e)}")
                            return error_msg  # Return error to trigger fail-fast
                    return wrapped_handler

                # Connect handler to signal
                wrapped = create_wrapped_handler(handler, subscriber_name)

                # Store reference to prevent garbage collection
                self._wrapped_handlers[subscriber_name].append(wrapped)

                event_signal.connect(wrapped)  # Connect without sender filtering
                logger.debug(f"Connected handler {subscriber_name} to signal {event_type} (signal id: {id(event_signal)}, receivers: {len(event_signal.receivers)})")

            self._stats['subscribers_count'] = len(self._subscribers)

            logger.info(f"✅ Subscriber '{subscriber_name}' registered for {len(event_types)} event types")
            return True

        except Exception as e:
            raise EventSystemError(f"Subscription failed: {e}")

    def unsubscribe(self, subscriber_name: str, event_types: Optional[List[EventType]] = None) -> bool:
        """
        Unsubscribe from event types.

        Args:
            subscriber_name: Name of subscriber to remove
            event_types: Specific event types to unsubscribe from (None = all)

        Returns:
            True if unsubscription successful
        """
        try:
            if subscriber_name not in self._subscribers:
                logger.warning(f"Subscriber '{subscriber_name}' not found")
                return False

            subscriber_info = self._subscribers[subscriber_name]

            if event_types is None:
                # Remove from all event types
                event_types = subscriber_info['event_types']

            # Disconnect from signals
            for event_type in event_types:
                event_signal = self._get_signal(event_type)
                # Note: Blinker doesn't have direct way to disconnect specific handlers
                # This is a limitation - in practice, we'd need to track connections

            # Remove subscriber info if no more event types
            remaining_types = [et for et in subscriber_info['event_types'] if et not in event_types]
            if not remaining_types:
                del self._subscribers[subscriber_name]
                # Clean up wrapped handlers to allow garbage collection
                if subscriber_name in self._wrapped_handlers:
                    del self._wrapped_handlers[subscriber_name]
            else:
                self._subscribers[subscriber_name]['event_types'] = remaining_types

            self._stats['subscribers_count'] = len(self._subscribers)

            logger.info(f"✅ Subscriber '{subscriber_name}' unsubscribed from {len(event_types)} event types")
            return True

        except Exception as e:
            logger.error(f"Unsubscription failed: {e}")
            return False

    def get_stats(self) -> Dict[str, Any]:
        """Get event system statistics."""
        stats = self._stats.copy()
        stats['event_types_count'] = len(_event_namespace)
        stats['recent_events'] = [
            {
                'event_type': e.event_type.value,
                'timestamp': e.timestamp.isoformat(),
                'source_service': e.source_service
            }
            for e in self._event_history[-10:]  # Last 10 events
        ]
        return stats

    def get_subscribers(self) -> Dict[str, Any]:
        """Get current subscribers information."""
        return {
            name: {
                'event_types': [et.value for et in info['event_types']],
                'events_processed': info['events_processed'],
                'last_error': info['last_error'],
                'created_at': info['created_at'].isoformat()
            }
            for name, info in self._subscribers.items()
        }

    def health_check(self) -> Dict[str, Any]:
        """Health check for event system."""
        stats = self.get_stats()

        # Simple health criteria
        is_healthy = (
            stats['events_failed'] == 0 or
            (stats['events_processed'] > 0 and
             stats['events_failed'] / stats['events_processed'] < 0.1)  # < 10% failure rate
        )

        return {
            'status': 'healthy' if is_healthy else 'unhealthy',
            'stats': stats,
            'timestamp': datetime.utcnow().isoformat()
        }


# Global event system instance
_global_event_system: Optional[EventSystem] = None


def get_event_system() -> EventSystem:
    """Get the global event system instance (singleton)."""
    global _global_event_system

    if _global_event_system is None:
        _global_event_system = EventSystem()
        logger.debug(f"Created new EventSystem instance: {id(_global_event_system)}")
    else:
        logger.debug(f"Returning existing EventSystem instance: {id(_global_event_system)}")

    return _global_event_system


# Convenience functions
def publish_event(event: Event) -> bool:
    """Publish event using global event system."""
    return get_event_system().publish(event)


def subscribe_to_events(event_types: List[EventType], handler: Callable,
                       subscriber_name: str) -> bool:
    """Subscribe to events using global event system."""
    return get_event_system().subscribe(event_types, handler, subscriber_name)


# Decorator for easy event subscription
def event_handler(*event_types: EventType):
    """
    Decorator for creating event handlers.

    Usage:
        @event_handler(EventType.TRANSCRIPT_CREATED, EventType.ANALYSIS_COMPLETED)
        def handle_transcript_events(sender, **kwargs):
            event = kwargs['event']
            # Process event
    """
    def decorator(func):
        # Register the handler automatically when decorator is applied
        handler_name = f"{func.__module__}.{func.__name__}"
        subscribe_to_events(list(event_types), func, handler_name)
        return func
    return decorator