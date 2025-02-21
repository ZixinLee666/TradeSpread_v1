from Core.EventBus import Event
from Services import SpreadCalculator


@dataclass
class TradingSignal(Event):
    direction: str


class PairTradingStrategy:
    def __init__(self, bus):
        self.bus = bus
        bus.subscribe(SpreadCalculator.SpreadEvent, self.on_spread)

    def on_spread(self, event):
        if abs(event.spread) > 2.0:
            signal = TradingSignal("BUY" if event.spread < 0 else "SELL")
            self.bus.publish(signal)