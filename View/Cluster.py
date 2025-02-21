import tkinter as tk
from tkinter import ttk
from View.sub_MD import MarketDataView
from View.sub_BuySell import TradeButtonsView
from Core.EventBus import EventBus
from Model.MarketData import MarketDataService,MarketDataEvent

class TradingCluster(tk.Tk):
    def __init__(self, bus: EventBus, leg1, leg2):
        super().__init__()
        self.bus = bus
        self.title("Pair Trading Monitor")
        self.geometry("600x400")
        self._setup_layout(leg1, leg2)

    def _setup_layout(self, leg1, leg2):
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)


        # 行情显示
        self.md_view = MarketDataView(main_frame, self.bus, leg1, leg2)
        self.md_view.pack(fill=tk.BOTH, expand=True)

        # 交易按钮
        self.trade_view = TradeButtonsView(main_frame, leg1, leg2)
        self.trade_view.pack(fill=tk.X, pady=5)

# 测试代码
# 这个东西就不需要测试，它只是个布局的问题