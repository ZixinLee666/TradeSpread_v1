# -*- coding: utf-8 -*-
# Core/__init__.py
from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
from Core.EventBus import Event, EventBus
from dataclasses import dataclass
import threading
from datetime import datetime, timezone
import time
from collections import deque  # 新增导入

# 新增deque双端队列用于缓存价格和时间戳数据
# 在tickString中仅处理tickType=88的延时时间戳
# 使用cache_lock保证线程安全
# 通过本地时间差（1秒窗口）匹配价格和时间戳
# 发布事件时使用服务器原始时间戳


# 双层缓存的设计目标
#该代码的核心挑战在于：价格数据（tickPrice）和时间戳数据（tickString）通过不同的回调函数异步到达，且可能存在网络延迟或乱序。双层缓存的作用是：

#缓存原始数据：临时存储价格和时间戳。
#时间对齐匹配：确保发布的事件中价格和时间戳来自同一时刻的行情。
@dataclass
class MarketDataEvent(Event):
    symbol: str
    price: float
    time: str  # 使用服务器时间戳
    tickType: int


class MarketDataService(EWrapper, EClient):
    def __init__(self, bus: EventBus):
        EClient.__init__(self, self)
        self.bus = bus
        self.symbol_map = {
            1: "GCJ5",
            2: "GCM5"
        }
        self._connected = False
        self._connect_lock = threading.Lock()
        self.thread = None
        #第一层缓存：原始数据队列————代码通过两个 ** 双端队列（deque） ** 分别缓存价格和时间戳：
        # 线程安全：通过 cache_lock 保证多线程操作的原子性。
        # 容量控制：maxlen=100 防止内存溢出，自动丢弃旧数据。
        self.data_cache = {
            1: {"prices": deque(maxlen=100), "times": deque(maxlen=100)},
            2: {"prices": deque(maxlen=100), "times": deque(maxlen=100)}
        }
        self.cache_lock = threading.Lock()

    def connect_ib(self):
        """连接IB"""
        try:
            self.connect("127.0.0.1", 7497, clientId=0)
            self.thread = threading.Thread(target=self.run, daemon=True)
            self.thread.start()
            time.sleep(1)
            return True
        except Exception as e:
            print(f"连接失败: {e}")
            return False

    def error(self, reqId, errorCode, errorString, advancedOrderRejectJson=None):
        if errorCode == 504 and not self._connected:
            return
        print(f"行情错误: reqId={reqId}, code={errorCode}, msg={errorString}")

    def connectAck(self):
        self._connected = True

    def connectionClosed(self):
        self._connected = False

    def reqMarketDataType(self, dataType):
        super().reqMarketDataType(dataType)
        print(f"[Debug] 请求市场数据类型: {dataType}")

    def subscribe(self):
        if not self._connected:
            print("未连接IB")
            return

        contract1 = self._create_contract(self.symbol_map[1])
        contract2 = self._create_contract(self.symbol_map[2])

        self.reqMarketDataType(3)
        self.reqMktData(1, contract1, "", False, False, [])
        self.reqMktData(2, contract2, "", False, False, [])
        print("已发送订阅请求")

    def _create_contract(self, localSymbol):
        contract = Contract()
        contract.symbol = "GC"
        contract.localSymbol = localSymbol
        contract.secType = "FUT"
        contract.exchange = "COMEX"
        contract.currency = "USD"
        return contract

    def tickString(self, reqId: int, tickType: int, value: str):
        super().tickString(reqId, tickType, value)
        if tickType == 88:  # 仅处理延时时间戳
            try:
                server_timestamp = int(value)
                with self.cache_lock:
                    self.data_cache[reqId]["times"].append((
                        server_timestamp,
                        time.time()   # 本地接收时间戳
                    ))
                    self._try_emit_event(reqId)
            except ValueError:
                pass

    def tickPrice(self, reqId, tickType, price, attrib):
        super().tickPrice(reqId, tickType, price, attrib)
        symbol = self.symbol_map.get(reqId)
        if symbol and price > 0:
            with self.cache_lock:
                self.data_cache[reqId]["prices"].append((
                    price,
                    time.time()  # 本地接收时间戳
                ))
                self._try_emit_event(reqId)

    def format_timestamp(self,timestamp_ms):
        dt_utc =datetime.fromtimestamp(int(timestamp_ms) , tz=timezone.utc)
        return dt_utc.strftime("%Y-%m-%d %H:%M:%S.%f")

    #  第二层缓存：时间窗口匹配。匹配逻辑：
    #  比较队列头部元素的本地接收时间差。
    #  若时间差 ≤ 阈值（代码中为2秒），则认为属于同一时刻的数据。
    #  发布事件时使用服务器时间戳（time_entry[0]）保证时间准确性。
    #  容错处理：当时间差过大时，丢弃更旧的一侧数据（价格或时间戳），避免队列阻塞。
    def _try_emit_event(self, reqId):
        """时间-价格匹配核心逻辑"""
        cache = self.data_cache[reqId]
        while len(cache["prices"]) > 0 and len(cache["times"]) > 0:
            price_entry = cache["prices"][0]
            time_entry = cache["times"][0]

            # 计算本地接收时间差（毫秒）
            local_diff = abs(price_entry[1] - time_entry[1])

            if local_diff <= 2:  # 时间窗口阈值
                symbol = self.symbol_map[reqId]
                # 发布事件并移除数据
                self.bus.publish(MarketDataEvent(
                    symbol=symbol,
                    price=price_entry[0],
                    time=str(time_entry[0]),  # 使用服务器时间戳
                    tickType=88
                ))
                # 移除已匹配数据
                cache["prices"].popleft()
                cache["times"].popleft()
            else:
                # 丢弃较旧的数据
                if price_entry[1] < time_entry[1]:
                    cache["prices"].popleft()
                else:
                    cache["times"].popleft()

    def disconnect(self):
        """正确断开连接"""
        if self._connected:
            try:
                # 调用EClient的disconnect方法
                super().disconnect()
                # 停止消息处理线程
                if self.thread and self.thread.is_alive():
                    self.thread.join(timeout=5)
            finally:
                self._connected = False
                print("[IB] 连接已断开")

if __name__ == "__main__":
    bus = EventBus()
    md = MarketDataService(bus)


    def print_price(event: MarketDataEvent):
        print(f"[Debug] {event.symbol} Price: {event.price} tickType:{event.tickType} time={event.time} = {md.format_timestamp(event.time)}")



    bus.subscribe(MarketDataEvent, print_price)
    bus.start()

    if md.connect_ib():
        print("成功连接IB")
        md.subscribe()
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            md.disconnect()
    else:
        print("连接IB失败")