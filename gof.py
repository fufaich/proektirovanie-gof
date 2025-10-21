from abc import ABC, abstractmethod
from enum import Enum
from typing import List, Any, Dict
import time

# ========== События ==========
class EventSubject(ABC):
    def __init__(self):
        self._observers: List['EventObserver'] = []

    def attach(self, observer: 'EventObserver'):
        self._observers.append(observer)

    def detach(self, observer: 'EventObserver'):
        self._observers.remove(observer)

    def notify(self, event: 'Event'):
        for observer in self._observers:
            observer.update(event)

class ActionStrategy(ABC):
    @abstractmethod
    def execute(self, event: 'Event'):
        pass

class Event:
    def __init__(self, event_id: str, timestamp: float, event_type: str, zona: str, severity: int,
                 action_strategy: ActionStrategy = None):
        super().__init__()
        self.id = event_id
        self.timestamp = timestamp
        self.type = event_type
        self.zona = zona
        self.severity = severity
        self._action_strategy = action_strategy or NotificationStrategy()

    def logEvent(self):
        print(f"[LOG] {self.type} in {self.zona} at {self.timestamp}")

    def executeAction(self):
        self._action_strategy.execute(self)

    def set_action_strategy(self, strategy: ActionStrategy):
        self._action_strategy = strategy

class DetectionEvent(Event):
    def __init__(self, *, detectionResultID: str, modelID: str, **kwargs):
        super().__init__(**kwargs)
        self.detectionResultID = detectionResultID
        self.modelID = modelID

    def toRuleTrigger(self):
        print(f"[RULE TRIGGER] Detection {self.id} from model {self.modelID}")

class SystemEvent(Event):
    def __init__(self, *, component: str, message: str, **kwargs):
        super().__init__(**kwargs, action_strategy=AdminAlertStrategy())
        self.component = component
        self.message = message

    def alertAdmin(self):
        self.executeAction()

# ========== Стратегии действий ==========
class NotificationStrategy(ActionStrategy):
    def execute(self, event: Event):
        print(f"[NOTIFY] Alert: {event.type} in zone '{event.zona}'")

class DeviceControlStrategy(ActionStrategy):
    def __init__(self, command: 'Command', executor):
        self.command = command
        self.executor = executor  # ← внедрение зависимости

    def execute(self, event: Event):
        print(f"[DEVICE CTRL] Scheduling action for {event.zona}")
        self.executor.add_command(self.command)

class AdminAlertStrategy(ActionStrategy):
    def execute(self, event: Event):
        if isinstance(event, SystemEvent):
            print(f"[ADMIN ALERT] {event.component}: {event.message}")
        else:
            print("[ADMIN ALERT] Unknown system issue")

# ========== Команды ==========
class Command(ABC):
    @abstractmethod
    def execute(self):
        pass

class OpenBarrierCommand(Command):
    def __init__(self, barrier_id: str):
        self.barrier_id = barrier_id

    def execute(self):
        print(f"[EXEC] Opening barrier {self.barrier_id}")

class TurnOnLightCommand(Command):
    def __init__(self, light_id: str):
        self.light_id = light_id

    def execute(self):
        print(f"[EXEC] Turning on light {self.light_id}")

# ========== EventManager интерфейс ==========

class EventObserver(ABC):
    @abstractmethod
    def update(self, event: 'Event'):
        pass

class EventManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._observers: List[EventObserver] = [] # pyright: ignore[reportInvalidTypeForm]
        return cls._instance

    def subscribe(self, observer: EventObserver):
        self._observers.append(observer)

    def unsubscribe(self, observer: EventObserver):
        self._observers.remove(observer)

    def publish(self, event: 'Event'):
        for observer in self._observers:
            observer.update(event)
        


# ========= Factory ==============
# Базовый фабричный интерфейс
class EventFactory(ABC):
    @abstractmethod
    def create_event(self, **kwargs) -> 'Event':
        pass

# Фабрика для событий детекции
class DetectionEventFactory(EventFactory):
    def __init__(self, model_id: str):
        self.model_id = model_id

    def create_event(self, **kwargs) -> 'DetectionEvent':
        return DetectionEvent(
            event_id=kwargs['event_id'],
            timestamp=kwargs['timestamp'],
            event_type=kwargs['event_type'],
            zona=kwargs['zona'],
            severity=kwargs['severity'],
            detectionResultID=kwargs['detectionResultID'],
            modelID=self.model_id
        )

# Фабрика для системных событий
class SystemEventFactory(EventFactory):
    def create_event(self, **kwargs) -> 'SystemEvent':
        return SystemEvent(
            event_id=kwargs['event_id'],
            timestamp=kwargs['timestamp'],
            event_type=kwargs['event_type'],
            zona=kwargs['zona'],
            severity=kwargs['severity'],
            component=kwargs['component'],
            message=kwargs['message']
        )