# 测试绝对导入
from Core.EventBus import EventBus
# 测试相对导入（需正确标记源码根）
from Model.MarketData1 import MarketDataService
print("导入成功！")