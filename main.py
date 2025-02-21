# main.py
from tkinter import messagebox
import sys
import os
import threading
from Core.EventBus import EventBus
from Model.MarketData import MarketDataService
from Model.SpreadCalculator import SpreadCalculator
from View.Cluster import TradingCluster
import time


class PairTradingSystem:
    def __init__(self, leg1, leg2):
        self.bus = EventBus()
        self.md_service = MarketDataService(self.bus)
        self.spread_calculator = SpreadCalculator(
            self.bus,
            symbol_pair=(leg1, leg2),
            max_time_diff=2
        )
        self.gui = TradingCluster(self.bus, leg1, leg2)

        # 绑定窗口关闭事件（关键修改点[4,5](@ref)）
        self.gui.protocol("WM_DELETE_WINDOW", self.on_window_close)

    def on_window_close(self):
        """窗口关闭事件处理（新增线程检查）"""
        if messagebox.askokcancel("退出", "确定要断开连接并退出系统吗？"):
            self.safe_shutdown()
            # 强制终止所有线程（关键修改[7](@ref)）
            os._exit(0)

    def start(self):
        """启动交易系统"""
        try:
            self.bus.start()
            print("事件总线已启动")

            if self._connect_ib_with_retry(retries=3):
                self.gui.mainloop()
        finally:
            self.safe_shutdown()

    def safe_shutdown(self):
        """安全关闭所有资源（新增线程监控）"""
        print("\n正在关闭系统...")

        # 断开IB连接（关键资源释放[1](@ref)）
        if self.md_service._connected:
            self.md_service.disconnect()
            print("已断开IB连接")

        # 停止事件总线（关键线程终止[7](@ref)）
        self.bus.stop()
        print("所有资源已释放")

        # 线程状态检查（新增调试信息）
        active_threads = threading.enumerate()
        print(f"残留线程: {[t.name for t in active_threads if t != threading.main_thread()]}")

    def _connect_ib_with_retry(self, retries=3):
        """带重试机制的IB连接"""
        for attempt in range(1, retries + 1):
            if self.md_service.connect_ib():
                print(f"第{attempt}次连接IB成功")
                time.sleep(2)
                self.md_service.subscribe()
                return True
            print(f"第{attempt}次连接失败，{'' if attempt == retries else '5秒后重试...'}")
            time.sleep(5)
        return False


if __name__ == "__main__":
    system = PairTradingSystem("GCJ5", "GCM5")
    system.start()