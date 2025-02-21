# Model/SpreadCalculator.py
from Core.EventBus import Event
from Model.MarketData import MarketDataEvent  # 新增关键导入
from dataclasses import dataclass
import threading
from datetime import datetime
from typing import Tuple
import time  # 添加这行到代码文件顶部

@dataclass
class SpreadEvent(Event):
    spread: float
    timestamp: datetime
    symbol_pair: Tuple[str, str]  # 例如 ("GCJ5", "GCZ5")
    prices: Tuple[float, float]  # 对应symbol_pair的价格


class SpreadCalculator:
    def __init__(self, bus, symbol_pair=("GCJ5", "GCZ5"), max_time_diff=10):
        self.bus = bus
        self.symbol_pair = symbol_pair
        self.max_time_diff = max_time_diff  # 允许的最大时间差（秒）

        # 使用有序字典存储最新数据
        # 第一层缓存：品种最新数据存储
        self.market_data = {
            symbol_pair[0]: {"price": None, "timestamp": None},
            symbol_pair[1]: {"price": None, "timestamp": None}
        }
        self.lock = threading.Lock()

        # 明确指定事件类型（关键修正）
        bus.subscribe(MarketDataEvent, self.handle_market_data)

    def handle_market_data(self, event: MarketDataEvent):
        """处理行情事件（带类型注解）"""
        print("DEBUG")
        with self.lock:
            # 只处理目标品种
            if event.symbol not in self.symbol_pair:
                return

            # 更新数据并转换时间戳

            try:
                timestamp = datetime.fromtimestamp(int(event.time) / 1000)  # 毫秒转秒
            except:
                timestamp = None

            self.market_data[event.symbol] = {
                "price": event.price,
                "timestamp": timestamp
            }

            # 当两个合约都有有效数据时
            if all(v["timestamp"] for v in self.market_data.values()):
                self._calculate_spread()

    def _calculate_spread(self):
        """带时间有效性验证的价差计算"""
        data1 = self.market_data[self.symbol_pair[0]]
        data2 = self.market_data[self.symbol_pair[1]]

        time_diff = abs((data1["timestamp"] - data2["timestamp"]).total_seconds())

        if time_diff <= self.max_time_diff:
            spread = data1["price"] - data2["price"]
            self.bus.publish(SpreadEvent(
                spread=spread,
                timestamp=datetime.now(),
                symbol_pair=self.symbol_pair,
                prices=(data1["price"], data2["price"])
            ))
        else:
            print(f"[Spread] 时间差 {time_diff:.2f}s 超过阈值 {self.max_time_diff}s，跳过计算")


# ===== 调试代码 =====
if __name__ == "__main__":
    from Core.EventBus import EventBus
    from datetime import timedelta

    bus = EventBus()
    calculator = SpreadCalculator(bus)


    def print_spread(event: SpreadEvent):
        # 使用正确的属性symbol_pair和prices
        price1, price2 = event.prices
        time_diff = (datetime.now() - event.timestamp).total_seconds()

        print(f"[价差] {event.symbol_pair[0]}-{event.symbol_pair[1]} = {event.spread:.2f} "
              f"(计算延迟: {time_diff:.3f}s)")


    bus.subscribe(SpreadEvent, print_spread)
    bus.start()

    # 生成测试数据
    test_time = datetime.now()
    test_events = [
        MarketDataEvent("GCJ5", 2000.0, str(int(test_time.timestamp() * 1000)), 88),
        MarketDataEvent("GCZ5", 2010.0, str(int((test_time + timedelta(seconds=5)).timestamp() * 1000)), 88),
        MarketDataEvent("GCJ5", 2020.0, str(int((test_time + timedelta(seconds=15)).timestamp() * 1000)), 88),
        MarketDataEvent("GCZ5", 2030.0, str(int((test_time + timedelta(seconds=20)).timestamp() * 1000)), 88),
    ]

    for event in test_events:
        bus.publish(event)
        time.sleep(0.5)