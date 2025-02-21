# View/sub_BuySell.py
import threading
import time
from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
from ibapi.order import Order
import tkinter as tk  # 新增导入
from tkinter import ttk

class TradingService(EWrapper, EClient):
    def __init__(self, leg1, leg2):
        EClient.__init__(self, self)
        self.leg1 = leg1
        self.leg2 = leg2
        self.next_order_id = None
        self.order_id_lock = threading.Lock()
        self.connected = False

    def error(self, reqId, errorCode, errorString, advancedOrderRejectJson):
        print(f"交易错误: {errorCode} - {errorString}")

    def nextValidId(self, orderId: int):
        with self.order_id_lock:
            self.next_order_id = orderId
            print(f"可用订单ID更新: {self.next_order_id}")

    def connect_trading(self):
        try:
            self.connect("127.0.0.1", 7497, clientId=1)  # 使用不同clientId
            self.thread = threading.Thread(target=self.run, daemon=True)
            self.thread.start()
            time.sleep(1)
            return True
        except Exception as e:
            print(f"交易连接失败: {e}")
            return False

    def create_contract(self, localSymbol):
        contract = Contract()
        contract.symbol = "GC"
        contract.localSymbol = localSymbol
        contract.secType = "FUT"
        contract.exchange = "COMEX"
        contract.currency = "USD"
        return contract

    def create_order(self, action, quantity=1):
        order = Order()
        order.action = action
        order.orderType = "MKT"
        order.totalQuantity = quantity
        order.transmit = True
        order.account = "DUE542842"  # 替换为真实账户
        return order

    def submit_pair_order(self, leg1_action, leg2_action):
        if not self.connected:
            print("交易服务未连接")
            return

        leg1_contract = self.create_contract(self.leg1)
        leg2_contract = self.create_contract(self.leg2)

        with self.order_id_lock:
            leg1_order_id = self.next_order_id
            self.next_order_id += 1
            leg2_order_id = self.next_order_id
            self.next_order_id += 1

        # 发送第一条腿订单
        self.placeOrder(leg1_order_id, leg1_contract,
                        self.create_order(leg1_action))

        # 发送第二条腿订单
        self.placeOrder(leg2_order_id, leg2_contract,
                        self.create_order(leg2_action))


class TradeButtonsView(ttk.Frame):
    def __init__(self, parent, leg1="GCJ5", leg2="GCM5"):
        super().__init__(parent)
        self.leg1 = leg1
        self.leg2 = leg2
        self.trading_service = TradingService(leg1, leg2)
        self._configure_styles()
        self._setup_ui()
        self._connect_trading()

    def _connect_trading(self):
        if self.trading_service.connect_trading():
            self.trading_service.connected = True
            print("交易服务连接成功")
        else:
            print("交易服务连接失败")

    def _setup_ui(self):
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill=tk.X, pady=10)

        self.buy_btn = ttk.Button(
            btn_frame,
            text="BUY",
            command=lambda: self._submit_order("BUY"),
            style="Buy.TButton"
        )
        self.buy_btn.pack(side=tk.LEFT, expand=True, padx=5)

        self.sell_btn = ttk.Button(
            btn_frame,
            text="SELL",
            command=lambda: self._submit_order("SELL"),
            style="Sell.TButton"
        )
        self.sell_btn.pack(side=tk.LEFT, expand=True, padx=5)

    def _submit_order(self, direction):
        if direction == "BUY":
            self.trading_service.submit_pair_order("BUY", "SELL")
        elif direction == "SELL":
            self.trading_service.submit_pair_order("SELL", "BUY")
        print(f"已发送{direction}指令")

    # 保留原有的样式配置代码...



    def _configure_styles(self):
        style = ttk.Style()
        style.theme_use("clam")

        # 买入按钮样式配置
        style.configure("Buy.TButton",
                        foreground="black",  # 默认文字颜色
                        background="#FFA500",
                        bordercolor="#CC8800",
                        lightcolor="#FFB347",
                        darkcolor="#CC8800",
                        padding=10,
                        font=('Helvetica', 12, 'bold'))

        # 卖出按钮样式配置
        style.configure("Sell.TButton",
                        foreground="black",  # 默认文字颜色
                        background="#007BFF",
                        bordercolor="#0056B3",
                        lightcolor="#5AA9FF",
                        darkcolor="#0056B3",
                        padding=10,
                        font=('Helvetica', 12, 'bold'))

        # 配置悬停状态映射
        style.map("Buy.TButton",
                  foreground=[('active', 'black')],  # 保持黑色文字
                  background=[('active', '#FFB347')],  # 更亮的橙色
                  lightcolor=[('active', '#FFD699')],  # 顶部高亮
                  darkcolor=[('active', '#FFA500')])  # 底部阴影

        style.map("Sell.TButton",
                  foreground=[('active', 'black')],  # 保持黑色文字
                  background=[('active', '#5AA9FF')],  # 更亮的蓝色
                  lightcolor=[('active', '#B3D7FF')],  # 顶部高亮
                  darkcolor=[('active', '#007BFF')])  # 底部阴影

if __name__ == "__main__":
    import tkinter as tk
    from tkinter import ttk


    class TradingTest:
        def __init__(self):
            self.root = tk.Tk()
            self.trade_view = TradeButtonsView(self.root, "GCJ5", "GCM5")
            self.trade_view.pack(padx=20, pady=20)

        def run(self):
            self.root.mainloop()


    test = TradingTest()
    test.run()