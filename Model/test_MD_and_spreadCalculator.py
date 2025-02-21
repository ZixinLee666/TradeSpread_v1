# Model/MarketSpread_Debug.py
from Core.EventBus import Event, EventBus
from datetime import datetime
import threading
import time
from Model.MarketData3 import MarketDataService, MarketDataEvent
from Model.SpreadCalculator import SpreadCalculator,SpreadEvent

# ===== 以下是合并后的MarketData和SpreadCalculator代码 =====
# （代码较长，这里展示关键整合部分）

class DebugMarketSpread:
    def __init__(self):
        self.bus = EventBus()

        # 初始化行情服务
        self.md = MarketDataService(self.bus)

        # 初始化价差计算器（调整为实际symbol）
        self.spread_calculator = SpreadCalculator(
            self.bus,
            symbol_pair=("GCJ5", "GCM5"),  # 确保与MarketData的symbol_map一致
            max_time_diff=2
        )

        # 注册事件处理器
        self._register_handlers()

    def _register_handlers(self):
        """注册调试用事件处理器"""
        # 行情打印
        self.bus.subscribe(MarketDataEvent, lambda e: print(
            f"[行情] {e.symbol} 价格: {e.price} 时间: {self.md.format_timestamp(e.time)}"
        ))

        # 价差打印
        self.bus.subscribe(SpreadEvent, lambda e: print(
            f"[价差] {e.symbol_pair[0]}-{e.symbol_pair[1]} = {e.spread:.2f} "
            f"价格: {e.prices[0]:.2f}/{e.prices[1]:.2f} "
            f"时间差: {(datetime.now() - e.timestamp).total_seconds():.3f}s"
        ))

    def run(self):
        """启动调试"""
        self.bus.start()

        if self.md.connect_ib():
            print("成功连接IB，等待3秒初始化...")
            time.sleep(3)
            self.md.subscribe()

            try:
                while True:  # 保持主线程运行
                    time.sleep(1)
            except KeyboardInterrupt:
                self.md.disconnect()
                self.bus.stop()
        else:
            print("连接IB失败")
            self.bus.stop()


# ===== 调试执行 =====
if __name__ == "__main__":
    debugger = DebugMarketSpread()
    debugger.run()