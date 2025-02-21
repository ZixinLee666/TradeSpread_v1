# main.py
from Core.EventBus import EventBus
from Model.MarketData import MarketDataService
from Model.SpreadCalculator import SpreadCalculator
from View.TradingGUI import TradingGUI
import threading
import time


class TradingSystem:
    def __init__(self):
        self.bus = EventBus()
        self.md = MarketDataService(self.bus)
        self.spread_calculator = SpreadCalculator(
            self.bus,
            symbol_pair=("GCJ5", "GCM5"),
            max_time_diff=2
        )
        self.gui = TradingGUI(self.bus)

    def start(self):
        """启动交易系统"""
        # 先启动事件总线
        self.bus.start()

        # 连接IB
        if self._connect_ib():
            # 启动GUI主循环
            self.gui.mainloop()
        else:
            print("系统启动失败")

        # 清理资源
        self.bus.stop()

    def _connect_ib(self):
        """连接IB的带重试机制"""
        retries = 3
        for i in range(retries):
            if self.md.connect_ib():
                print("IB连接成功")
                time.sleep(2)  # 等待初始化
                self.md.subscribe()
                return True
            print(f"连接失败，剩余重试次数: {retries - i - 1}")
            time.sleep(5)
        return False


if __name__ == "__main__":
    system = TradingSystem()
    system.start()