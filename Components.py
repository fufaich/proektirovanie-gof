from gof import *
# ========== VideoModule ==========
class VideoModule:
    def __init__(self, camera_id: str):
        self.camera_id = camera_id

    def receive_frame(self, frame_data: Any) -> Dict[str, Any]:
        print(f"[VIDEO] Receiving frame from camera {self.camera_id}")
        return {
            "camera_id": self.camera_id,
            "timestamp": time.time(),
            "frame": frame_data
        }

# ========== ComputerVisionEngine ==========
class ComputerVisionEngine:
    def __init__(self, model_id: str = "person_detector_v1"):
        self.model_id = model_id
        # Фабрика создаётся
        self._event_factory = DetectionEventFactory(model_id=self.model_id)

    def detect(self, frame_meta: Dict[str, Any]) -> 'DetectionEvent':
        timestamp = frame_meta["timestamp"]
        event_id = f"det_{int(timestamp * 1000)}"
        detection_result_id = f"res_{event_id}"

        # Создание через фабрику
        return self._event_factory.create_event(
            event_id=event_id,
            timestamp=timestamp,
            event_type="person_detected",
            zona="Zone_A",
            severity=2,
            detectionResultID=detection_result_id
        )

# ========== RuleEngine ==========
class RuleEngine(EventObserver):
    def __init__(self, execution_module: 'ExecutionModule'):
        self.rules = {
            "person_detected": lambda e: self._handle_person(e),
            "system_failure": lambda e: self._handle_system(e)
        }
        self.execution_module = execution_module

    def update(self, event: Event):
        print(f"[RULE ENGINE] Received event {event.id}")
        handler = self.rules.get(event.type)
        if handler:
            handler(event)

    def _handle_person(self, event: DetectionEvent):
        event.toRuleTrigger()
        # Привязываем команду к стратегии
        command = OpenBarrierCommand(barrier_id="B1")
        strategy = DeviceControlStrategy(command, self.execution_module)
        event.set_action_strategy(strategy)
        event.executeAction()  # запускает выполнение через ExecutionModule

    def _handle_system(self, event: SystemEvent):
        event.alertAdmin()

# ========== StorageService ==========
class StorageService(EventObserver):
    def update(self, event: Event):
        print(f"[STORAGE] Persisting event {event.id} to DB and cloud")

# ========== ExecutionModule (Singleton) ==========
class ExecutionModule:
    _instance = None

    @classmethod
    def instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        self._command_queue: List[Command] = []

    def add_command(self, command: Command):
        self._command_queue.append(command)

    def process_all(self):
        print("[EXECUTION MODULE] Processing command queue...")
        for cmd in self._command_queue:
            cmd.execute()
        self._command_queue.clear()

# ========== APIGateway ==========
class APIGateway:
    def __init__(self):
        self._event_counter = 0
        self._system_event_factory = SystemEventFactory()

    def create_event_from_request(self, payload: Dict[str, Any]) -> 'Event':
        self._event_counter += 1
        if payload.get("type") == "system":
            return self._system_event_factory.create_event(
                event_id=f"sys_{self._event_counter}",
                timestamp=time.time(),
                event_type="system_failure",
                zona=payload.get("zona", "N/A"),
                severity=payload.get("severity", 3),
                component=payload["component"],
                message=payload["message"]
            )
        else:
            raise ValueError("Unsupported event type")