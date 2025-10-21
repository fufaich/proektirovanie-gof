# main.py
from Components import *
from gof import *

def main():
    # Инициализация
    video = VideoModule(camera_id="CAM_01")
    cv_engine = ComputerVisionEngine()
    executor = ExecutionModule()
    rule_engine = RuleEngine(execution_module=executor)
    storage = StorageService()
    api = APIGateway()

    # Подписки на события
    event_manager = EventManager()
    event_manager.subscribe(rule_engine)
    event_manager.subscribe(storage)

    # Симуляция события
    frame_meta = video.receive_frame(frame_data=b"fake_video_bytes")
    detection_event = cv_engine.detect(frame_meta)

    # Публикация события
    event_manager.publish(detection_event)

    # Выполнение команд
    executor.process_all()

    # Системное событие
    print("\n--- Simulating system event via API ---")
    sys_event = api.create_event_from_request({
        "type": "system",
        "component": "VideoModule",
        "message": "Camera disconnected",
        "zona": "Perimeter",
        "severity": 4
    })
    event_manager.publish(sys_event)

if __name__ == "__main__":
    main()