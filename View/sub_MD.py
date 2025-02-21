# View/sub_MD.py
import tkinter as tk
from tkinter import ttk
from Core.EventBus import EventBus
from Model.MarketData import MarketDataEvent
from Model.SpreadCalculator import SpreadEvent
import time
from datetime import datetime, timezone


class MarketDataView(ttk.Frame):
    def __init__(self, master, bus: EventBus, leg1="GCJ5", leg2="GCM5"):
        super().__init__(master)
        self.bus = bus
        self.leg1 = leg1
        self.leg2 = leg2
        self._init_state()
        self._setup_ui()
        self._register_events()

    def _init_state(self):
        self.last_update = {
            self.leg1: {"price": 0.0, "time": ""},
            self.leg2: {"price": 0.0, "time": ""}
        }
        self.spread_value = 0.0

    def _setup_ui(self):
        self.configure(padding=10)

        # 价格显示区域
        price_frame = ttk.LabelFrame(self, text="实时价格")
        price_frame.pack(fill=tk.X, pady=5)

        # 第一条腿
        ttk.Label(price_frame, text=f"{self.leg1}:").grid(row=0, column=0, sticky=tk.W)
        self.leg1_price = ttk.Label(price_frame, text="0.00", font=('Arial', 12, 'bold'))
        self.leg1_price.grid(row=0, column=1, sticky=tk.E)
        self.leg1_time = ttk.Label(price_frame, text="", foreground="gray")
        self.leg1_time.grid(row=1, column=0, columnspan=2, sticky=tk.W)

        # 分隔线
        ttk.Separator(price_frame, orient=tk.HORIZONTAL).grid(row=2, column=0, columnspan=2, sticky=tk.EW, pady=5)

        # 第二条腿
        ttk.Label(price_frame, text=f"{self.leg2}:").grid(row=3, column=0, sticky=tk.W)
        self.leg2_price = ttk.Label(price_frame, text="0.00", font=('Arial', 12, 'bold'))
        self.leg2_price.grid(row=3, column=1, sticky=tk.E)
        self.leg2_time = ttk.Label(price_frame, text="", foreground="gray")
        self.leg2_time.grid(row=4, column=0, columnspan=2, sticky=tk.W)

        # 价差显示
        spread_frame = ttk.LabelFrame(self, text="价差监控")
        spread_frame.pack(fill=tk.X, pady=5)
        self.spread_value_label = ttk.Label(
            spread_frame,
            text="0.00",
            font=('Arial', 14, 'bold'),
            foreground=self._get_spread_color(0)
        )
        self.spread_value_label.pack(side=tk.LEFT, padx=5)



    def handle_market_data(self, event: MarketDataEvent):
        self.after(0, self._update_price_ui, event)

    def handle_spread(self, event: SpreadEvent):
        self.after(0, self._update_spread_ui, event)

    def _register_events(self):
        if self.bus is None:
            raise ValueError("Event bus未正确初始化")
        self.bus.subscribe(MarketDataEvent, self.handle_market_data)
        self.bus.subscribe(SpreadEvent, self.handle_spread)

    def _update_price_ui(self, event: MarketDataEvent):

        try:
            symbol = event.symbol
            if symbol not in [self.leg1, self.leg2]:
                return

            timestamp = int(event.time) // 1000  # 转换为秒


            dt_utc = datetime.fromtimestamp(int(event.time), tz=timezone.utc)
            readable_time = dt_utc.strftime("%Y-%m-%d %H:%M:%S")
            self.last_update[symbol].update({
                "price": event.price,
                "time": readable_time
            })

            if symbol == self.leg1:
                self.leg1_price.config(text=f"{event.price:.2f}")
                self.leg1_time.config(text=f"最后更新: {readable_time}")
            else:
                self.leg2_price.config(text=f"{event.price:.2f}")
                self.leg2_time.config(text=f"最后更新: {readable_time}")

        except Exception as e:
            print(f"更新价格UI异常: {str(e)}")

    def _update_spread_ui(self, event: SpreadEvent):
        print(f"[DEBUG] _update_spread_ui:")  # 确认计算逻辑执行
        print(f"[DEBUG] _update_spread_ui: {event.spread}")  # 确认计算逻辑执行
        self.spread_value = event.spread
        self.spread_value_label.config(
            text=f"{event.spread:.2f}",
            foreground=self._get_spread_color(event.spread)
        )

    def _get_spread_color(self, spread):
        if spread > 0:
            return "#28a745"
        elif spread < 0:
            return "#dc3545"
        return "black"


# 测试代码
# View/sub_MD.py 测试部分修正
if __name__ == "__main__":
    from Core.EventBus import EventBus
    from Model.MarketData import MarketDataService
    from Model.SpreadCalculator import SpreadCalculator  # 新增关键导入
    import time

    class CorrectTestSystem:
        def __init__(self):
            self.bus = EventBus()
            # 必须按顺序初始化所有组件
            self.md = MarketDataService(self.bus)
            self.spread_calculator = SpreadCalculator(  # 新增关键组件
                self.bus,
                symbol_pair=("GCJ5", "GCM5"),
                max_time_diff=2
            )
            self.root = tk.Tk()
            self.md_view = MarketDataView(self.root, self.bus)
            self.md_view.pack()

        def start(self):
            self.bus.start()  # 先启动总线
            if self._connect_ib():
                self.root.mainloop()
            self.bus.stop()

        def _connect_ib(self):
            if self.md.connect_ib():
                time.sleep(2)
                self.md.subscribe()
                return True
            return False

    CorrectTestSystem().start()  # 使用修正后的测试类