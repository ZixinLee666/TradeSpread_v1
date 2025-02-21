from Core.EventBus import Event
from dataclasses import dataclass
from Model.SpreadCalculator import SpreadEvent


@dataclass
class TradingSignal(Event):
    direction: str  # BUY/SELL


class PairTradingStrategy:
    def __init__(self, bus, threshold=2.0):
        self.threshold = threshold
        bus.subscribe(SpreadEvent, self.on_spread)

    def on_spread(self, event: SpreadEvent):
        if abs(event.spread) > self.threshold:
            direction = "BUY" if event.spread < 0 else "SELL"
            print(f"[Stg Debug] 触发交易信号: {direction}")
            # 实际应通过bus发布信号
            # bus.publish(TradingSignal(direction))


# ===== 调试代码 =====
if __name__ == "__main__":
    from Core.EventBus import EventBus
    from Model.SpreadCalculator import SpreadEvent

    bus = EventBus()
    strategy = PairTradingStrategy(bus, threshold=1.5)

    # 手动测试
    bus.start()
    try:
        while True:
            spread = float(input("输入测试价差: "))
            bus.publish(SpreadEvent(spread))
    except KeyboardInterrupt:
        bus.stop()