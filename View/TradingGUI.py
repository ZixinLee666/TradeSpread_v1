# View/TradingGUI.py
import tkinter as tk
from tkinter import ttk
from Core.EventBus import EventBus
from Model.MarketData import MarketDataEvent
from Model.SpreadCalculator import SpreadEvent
import time
import threading


class TradingGUI(tk.Tk):
    def __init__(self, bus: EventBus, leg1="GCJ5", leg2="GCM5"):
        super().__init__()
        self.bus = bus
        self.leg1 = leg1
        self.leg2 = leg2
        self._init_state()
        self._setup_ui()
        self._register_events()

        # 窗口关闭协议
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def _init_state(self):
        """初始化显示状态"""
        self.last_update = {
            self.leg1: {"price": 0.0, "time": ""},
            self.leg2: {"price": 0.0, "time": ""}
        }
        self.spread_value = 0.0

    def _setup_ui(self):
        """界面布局"""
        self.title("Pair Trading Monitor")
        self.geometry("400x250")

        # 主容器
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 价格显示区域
        price_frame = ttk.LabelFrame(main_frame, text="实时价格")
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
        spread_frame = ttk.LabelFrame(main_frame, text="价差监控")
        spread_frame.pack(fill=tk.X, pady=5)

        self.spread_value_label = ttk.Label(
            spread_frame,
            text="0.00",
            font=('Arial', 14, 'bold'),
            foreground=self._get_spread_color(0)
        )
        self.spread_value_label.pack(side=tk.LEFT, padx=5)

        # 交易按钮
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=10)

        self.buy_btn = ttk.Button(
            btn_frame,
            text="BUY",
            command=self.on_buy,
            style="Primary.TButton"
        )
        self.buy_btn.pack(side=tk.LEFT, expand=True, padx=5)

        self.sell_btn = ttk.Button(
            btn_frame,
            text="SELL",
            command=self.on_sell,
            style="Danger.TButton"
        )
        self.sell_btn.pack(side=tk.LEFT, expand=True, padx=5)

        # 配置样式
        self.style = ttk.Style()
        self.style.configure("Primary.TButton", foreground="white", background="#28a745")
        self.style.configure("Danger.TButton", foreground="white", background="#dc3545")

    def _register_events(self):
        """事件注册"""
        self.bus.subscribe(MarketDataEvent, self.handle_market_data)
        self.bus.subscribe(SpreadEvent, self.handle_spread)

    def handle_market_data(self, event: MarketDataEvent):
        """处理行情事件"""
        self.after(0, self._update_price_ui, event)

    def handle_spread(self, event: SpreadEvent):
        """处理价差事件"""
        self.after(0, self._update_spread_ui, event)

    def _update_price_ui(self, event: MarketDataEvent):
        """更新价格显示"""
        try:
            symbol = event.symbol
            if symbol not in [self.leg1, self.leg2]:
                return

            # 转换时间戳
            timestamp = int(event.time) // 1000  # 转换为秒
            readable_time = time.strftime("%H:%M:%S", time.localtime(timestamp))

            # 更新数据
            self.last_update[symbol].update({
                "price": event.price,
                "time": readable_time
            })

            # 更新UI
            if symbol == self.leg1:
                self.leg1_price.config(text=f"{event.price:.2f}")
                self.leg1_time.config(text=f"最后更新: {readable_time}")
            else:
                self.leg2_price.config(text=f"{event.price:.2f}")
                self.leg2_time.config(text=f"最后更新: {readable_time}")

        except Exception as e:
            print(f"更新价格UI异常: {str(e)}")

    def _update_spread_ui(self, event: SpreadEvent):
        """更新价差显示"""
        self.spread_value = event.spread
        self.spread_value_label.config(
            text=f"{event.spread:.2f}",
            foreground=self._get_spread_color(event.spread)
        )

    def _get_spread_color(self, spread):
        """根据价差方向设置颜色"""
        if spread > 0:
            return "#28a745"  # 绿色
        elif spread < 0:
            return "#dc3545"  # 红色
        return "black"

    def on_buy(self):
        """买入信号"""
        print(f"[交易信号] BUY {self.leg1} / SELL {self.leg2}")

    def on_sell(self):
        """卖出信号"""
        print(f"[交易信号] SELL {self.leg1} / BUY {self.leg2}")

    def on_close(self):
        """窗口关闭处理"""
        self.bus.stop()
        self.destroy()


# ===== 调试代码 =====
def mock_data(bus):
    """模拟数据生成"""
    symbols = ["GCJ5", "GCM5"]
    count = 0
    while True:
        count += 1
        timestamp = int(time.time() * 1000)
        for i, symbol in enumerate(symbols):
            price = 1800.0 + (count * 2) + (i * 1)
            event = MarketDataEvent(
                symbol=symbol,
                price=price,
                time=str(timestamp),
                tickType=88
            )
            bus.publish(event)
        time.sleep(1)


if __name__ == "__main__":
    bus = EventBus()
    bus.start()

    gui = TradingGUI(bus)

    # 启动模拟数据线程
    threading.Thread(target=mock_data, args=(bus,), daemon=True).start()

    try:
        gui.mainloop()
    finally:
        bus.stop()