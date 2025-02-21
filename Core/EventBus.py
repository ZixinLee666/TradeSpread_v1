from dataclasses import dataclass
from typing import Callable, Dict
from queue import Queue, Empty
import threading


@dataclass
class Event:
    """基础事件类"""
    pass


class EventBus:
    def __init__(self):
        self.subscriptions: Dict[type, list] = {}
        self.queue = Queue()
        self.dispatcher = threading.Thread(target=self._dispatch, daemon=True)
        self.running = False

    def subscribe(self, event_type: type, callback: Callable):
        """订阅事件类型"""
        self.subscriptions.setdefault(event_type, []).append(callback)

    def publish(self, event: Event):
        """发布事件"""
        self.queue.put(event)

    def start(self):
        """启动事件总线"""
        self.running = True
        self.dispatcher.start()

    def stop(self):
        """停止事件总线"""
        self.running = False
        self.dispatcher.join()

    def _dispatch(self):
        while self.running:
            try:
                event = self.queue.get(timeout=0.1)
                for handler in self.subscriptions.get(type(event), []):
                    handler(event)
            except Empty:
                continue




# ===== 调试代码 =====
if __name__ == "__main__":
    # 测试事件系统
    bus = EventBus()


    # 测试订阅者
    def test_handler(event: Event):
        print(f"[Debug] Received event: {event}")


    bus.subscribe(Event, test_handler)

    # 启动总线
    bus.start()

    # 手动发送测试事件
    try:
        while True:  # 保持运行
            user_input = input("输入测试事件内容（输入q退出）: ")
            if user_input.lower() == 'q':
                break
            bus.publish(Event())
    finally:
        bus.stop()