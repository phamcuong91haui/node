# -*- coding: utf-8 -*-
from node.interfaces import INodeAddedEvent
from node.interfaces import INodeCreatedEvent
from node.interfaces import INodeDetachedEvent
from node.interfaces import INodeModifiedEvent
from node.interfaces import INodeRemovedEvent
from zope.interface import implementer
from zope.lifecycleevent import ObjectAddedEvent
from zope.lifecycleevent import ObjectCreatedEvent
from zope.lifecycleevent import ObjectModifiedEvent
from zope.lifecycleevent import ObjectRemovedEvent
import threading


###############################################################################
# Lifecycle events for ILifecycle
###############################################################################

@implementer(INodeCreatedEvent)
class NodeCreatedEvent(ObjectCreatedEvent):
    pass


@implementer(INodeAddedEvent)
class NodeAddedEvent(ObjectAddedEvent):
    pass


@implementer(INodeModifiedEvent)
class NodeModifiedEvent(ObjectModifiedEvent):
    pass


@implementer(INodeRemovedEvent)
class NodeRemovedEvent(ObjectRemovedEvent):
    pass


@implementer(INodeDetachedEvent)
class NodeDetachedEvent(ObjectRemovedEvent):
    pass


###############################################################################
# Event dispatcher and event dispatching class attribute descriptor
#
# The API is unabashedly cribbed from Kivy - https://kivy.org
###############################################################################

_local_data = threading.local()
_local_data.suppress = 0
_local_data.events = list()

ALL_EVENTS = object()


class suppress_events(object):
    """Context manager to suppress event notification.

    Dedicated to be used in node implementations to internally modify data
    structures and it's not desired that events are dispached where they
    usually are.

    Suppress all events::

        with suppress_events() as count:
            # count defines the recursion level of ``suppress_event`` calls.
            # do something where normally events are triggered.
            pass

    Suppress specific event::

        with suppress_events('my_event'):
            pass  # do something

    Suppress list of events::

        with suppress_events(['event_1', 'event_2'])
    """

    def __init__(self, events=ALL_EVENTS):
        type_ = type(events)
        if type_ not in (list, tuple):
            events = [events]
        for event in events:
            _local_data.events.append(event)
        self.events = events

    def __enter__(self):
        _local_data.suppress += 1
        return _local_data.suppress

    def __exit__(self, type, value, traceback):
        _local_data.suppress -= 1
        for event in self.events:
            _local_data.events.remove(event)


class UnknownEvent(ValueError):
    """Thrown on attempt to register a subscriber to an unknown event.
    """


class EventDispatcher(object):
    """Object for event dispatching.

    Events are just strings and can be set as class member or registered via
    ``register_event``::

        class ExampleDispatcher(EventDispatcher):
            __events__ = ['event_1']

        dispatcher = ExampleDispatcher()
        dispatcher.register_event('event_2')

    Event subscribers are callables and bound to event name::

        def subscriber(*args, **kw):
            pass  # do something

        dispatcher.bind(event_1=subscriber)

    Events are triggered via ``dispatch``. Given arguments and keyword
    arguments are passed to subscriber::

        dispatcher.dispatch('event_1', 'foo', bar='baz')

    To remove some or all event subscribers from an event dispatcher,
    ``unbind`` is used. Both ``event`` and ``subscriber`` keyword arguments
    are optional::

        dispatcher.unbind(event=event_1, subscriber=subscriber)
    """

    def __init__(self, *args, **kw):
        # XXX: class initialization might go to a metaclass or __new__
        # do not override events defined on class.
        if not hasattr(self, '__events__'):
            self.__events__ = list()
        # mapping between events and subscribers
        self.__subscribers__ = dict()
        # iterate class dict and register events for contained EventAttribute
        # objects
        for attr, val in self.__class__.__dict__.items():
            if isinstance(val, EventAttribute):
                self.register_event(attr)
                val.name = attr

    def register_event(self, event):
        """Register event type.

        :param event: Event name as string.
        """
        if not event in self.__events__:
            self.__events__.append(event)

    def bind(self, **kw):
        """Bind subscribers to events.

        :param kw: Each keyword argument is the event name and the argument
            value is the subscriber callable.
        """
        for event, subscriber in kw.items():
            if not event in self.__events__:
                raise UnknownEvent(event)
            subscribers = self.__subscribers__.setdefault(event, list())
            if not subscriber in subscribers:
                subscribers.append(subscriber)

    def unbind(self, event=None, subscriber=None):
        """Unbind subscribers.

        :param event: Event name. If not given, all events are affected.
        :param subscriber: Subscriber callable. If not given, all subscribers
            are affected.
        """
        if event is None and subscriber is None:
            self.__subscribers__ = dict()
        elif event is not None and subscriber is None:
            if event in self.__subscribers__:
                del self.__subscribers__[event]
        elif event is None and subscriber is not None:
            for subscribers in self.__subscribers__.values():
                if subscriber in subscribers:
                    subscribers.remove(subscriber)
        elif event is not None and subscriber is not None:
            subscribers = self.__subscribers__.get(event, list())
            if subscriber in subscribers:
                subscribers.remove(subscriber)

    def dispatch(self, event, *args, **kw):
        """Dispatch event.

        :param event: Event name.
        :param args: Arguments passed to subscribers.
        :patam kw: Keyword arguments passed to subscribers.
        """
        if _local_data.suppress > 0:
            if ALL_EVENTS in _local_data.events:
                return
            if event in _local_data.events:
                return
        subscribers = self.__subscribers__.get(event, list())
        for subscriber in subscribers:
            subscriber(*args, **kw)


class EventAttribute(object):
    """Descriptor which can be used on ``EventDispatcher`` objects.

    It's possible to bind subscribers to object attributes of type
    ``EventAttribute`` by attribute name::

        class ExampleDispatcher(EventDispatcher):
            example_attribute = EventAttribute(0)

        def subscriber(value):
            pass  # do something

        dispatcher = ExampleDispatcher()
        dispatcher.bind(example_attribute=subscriber)

        # when setting ``example_attribute`` with a changed value, subscriber
        # is called
        dispatcher.example_attribute = 1
    """
    name = None

    def __init__(self, default):
        """Initialize attribute.
        """
        self.default = default

    def __get__(self, obj, owner=None):
        """Return attribute value.
        """
        if obj is None:
            return self.default
        return obj.__dict__.get(self.name, self.default)

    def __set__(self, obj, value):
        """Set attribute value. Triggers event if value changed.
        """
        old_value = obj.__dict__.get(self.name, self.default)
        obj.__dict__[self.name] = value
        if value != old_value:
            obj.dispatch(self.name, value)

    # def __delete__(self, obj):
    #     """Delete attribute value.
    #     """
    #     del obj.__dict__[self.name]
