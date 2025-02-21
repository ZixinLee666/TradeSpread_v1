# Core/__init__.py
from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
from Core.EventBus import Event, EventBus
from dataclasses import dataclass
import threading
from datetime import datetime, timezone
import time

# 这个管时间戳，但没有双重缓存，时间未必同步的
@dataclass
class MarketDataEvent(Event):
    symbol: str
    price: float
    time: str
    tickType: int


class MarketDataService(EWrapper, EClient):
    def __init__(self, bus: EventBus):
        EClient.__init__(self, self)
        self.bus = bus
        self.symbol_map = {
            1: "GCJ5",  # 第一个合约【xxxx改xxxx这xxxx里xxxx哦xxxx】
            2: "GCZ5"  # 第二个合约【xxxx改xxxx这xxxx里xxxx哦xxxx】
        }
        self._connected = False
        self._connect_lock = threading.Lock()
        self.thread=None
        self.timestamps = {1: None, 2: None}  # 存储各reqId的最新时间戳

    def connect_ib(self):
        """连接IB"""
        try:
            self.connect("127.0.0.1", 7497, clientId=0)
            # 启动独立线程处理消息
            self.thread = threading.Thread(target=self.run, daemon=True)
            self.thread.start()
            time.sleep(1)  # 等待连接建立
            return True
        except Exception as e:
            print(f"连接失败: {e}")
            return False

    def error(self, reqId, errorCode, errorString, advancedOrderRejectJson=None):
        if errorCode == 504 and not self._connected:
            return  # 静默处理断开后的504错误
        print(f"行情错误: reqId={reqId}, code={errorCode}, msg={errorString}")

    def connectAck(self):
        self._connected = True

    def connectionClosed(self):
        self._connected = False

    def reqMarketDataType(self, dataType):
        super().reqMarketDataType(dataType)
        print(f"[Debug] 请求市场数据类型: {dataType}")  # 新增

    def subscribe(self):
        """订阅两个相同合约"""
        if not self._connected:
            print("未连接IB")
            return

        # 创建相同合约（示例用GC期货）
        contract1 = self._create_contract(self.symbol_map[1])
        contract2 = self._create_contract(self.symbol_map[2])

        # 订阅两个相同合约（不同reqId）
        self.reqMarketDataType(3)
        self.reqMktData(1, contract1, "", False, False, [])
        self.reqMktData(2, contract2, "", False, False, [])
        print("已发送订阅请求")

    def _create_contract(self,localSymbol):
        """创建合约（与调试示例相同）"""
        print(localSymbol)
        contract = Contract()
        contract.symbol = "GC"
        contract.localSymbol = localSymbol  # 请根据实际合约修改
        contract.secType = "FUT"
        contract.exchange = "COMEX"
        contract.currency = "USD"
        return contract

    def nextValidId(self, orderId):
        super().nextValidId(orderId)
        print(f"[Debug] 下一个有效ID: {orderId}")  # 新增

    def format_timestamp(self,timestamp_ms):
        dt_utc =datetime.fromtimestamp(int(timestamp_ms) , tz=timezone.utc)
        print(f"时间={dt_utc.strftime("%Y-%m-%d %H:%M:%S.%f")}")
        return dt_utc.strftime("%Y-%m-%d %H:%M:%S.%f")


    def tickString(self, reqId: int, tickType: int, value: str):
        """处理时间戳行情"""
        super().tickString(reqId, tickType, value)
        #print(f"[看看收到什么了] tickString: reqId={reqId}, type={tickType}, value={value}")  # 新增
        tmpd=self.format_timestamp(value)
        print(f"{tmpd}")
        if tickType == 45 or 88:  # LAST_TIMESTAMP
            try:
                timestamp = int(value)
                self.timestamps[reqId] = timestamp
                print(f"[Debug] 更新时间戳 reqId={reqId}, timestamp={timestamp}")
            except ValueError:
                pass

    def tickPrice(self, reqId, tickType, price, attrib):
        super().tickPrice(reqId, tickType, price, attrib)
        #if tickType == 1:  # 最新价
        symbol = self.symbol_map.get(reqId)
        if symbol and price > 0:
            current_time = str(self.timestamps.get(reqId, None))
            self.bus.publish(MarketDataEvent(symbol, price, current_time, tickType))


# ===== 调试代码 =====
if __name__ == "__main__":
    bus = EventBus()
    md = MarketDataService(bus)


    # 注册测试处理器
    def print_price(event: MarketDataEvent):
        print(f"[Debug] {event.symbol} Price: {event.price} tickType:{event.tickType} time{event.time}")


    bus.subscribe(MarketDataEvent, print_price)
    bus.start()

    # 连接IB
    if md.connect_ib():
        print("成功连接IB")
        md.subscribe()  # 开始订阅

        # 保持运行
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            md.disconnect()
    else:
        print("连接IB失败")