# a.py
USE_MODULE = "3"  # 改这里切换模块：a1/a2/a3

if USE_MODULE == "1":
    from Model.MarketData1 import MarketDataEvent,MarketDataService
elif USE_MODULE == "2":
    from Model.MarketData2 import MarketDataEvent,MarketDataService
elif USE_MODULE == "3":
    from Model.MarketData3 import MarketDataEvent,MarketDataService
else:
    raise ValueError("Invalid module")