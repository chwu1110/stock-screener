"""
測試興櫃即時報價 - 印出所有回應
市場代碼：4 = 興櫃（TWEMERGING）
"""
import sys
import time
from pathlib import Path

DLL_DIR  = r"C:\Users\chaow\Downloads\Compressed\YuantaOneAPI_Python\YuantaOneAPI_Python"
ACCOUNT  = "A123363332"
PASSWORD = "Alex0722$$"

sys.path.append(DLL_DIR)
sys.path.append(str(Path(DLL_DIR).parent))

import clr
clr.AddReference('System.Collections')
clr.AddReference('YuantaOneAPI')

from YuantaOneAPI import (
    YuantaOneAPITrader, enumEnvironmentMode,
    OnResponseEventHandler, YuantaDataHelper,
    enumLangType, enumLogType, WatchlistAll
)
from System.Collections.Generic import List

count = [0]

def on_response(intMark, dwIndex, strIndex, objHandle, objValue):
    count[0] += 1
    # 印出所有回應
    print(f"[回應{count[0]}] intMark={intMark} strIndex='{strIndex}'")
    
    # 如果是報價回應，嘗試解析
    if intMark == 2:
        try:
            h = YuantaDataHelper(enumLangType.NORMAL)
            h.OutMsgLoad(objValue)
            key    = h.GetStr(22).strip()
            market = h.GetByte()
            sid    = h.GetStr(12).strip()
            seq    = h.GetLong()
            flag   = h.GetByte()
            print(f"  → 市場={market} 股票={sid} 旗標={flag}")
            
            if flag == 29:  # 成交
                t = h.GetTYuantaTime()
                h.GetInt()  # out
                h.GetInt()  # in
                price = h.GetInt() / 10000.0
                vol   = h.GetInt()
                total = h.GetInt()
                print(f"  → 成交價={price} 量={vol} 總量={total}")
        except Exception as e:
            print(f"  → 解析錯誤: {e}")

api = YuantaOneAPITrader()
api.OnResponse += OnResponseEventHandler(on_response)
api.SetLogType(enumLogType.COMMON)

print("連線中...")
api.Open(enumEnvironmentMode.PROD)
time.sleep(3)

print(f"登入 {ACCOUNT}...")
api.Login(ACCOUNT, PASSWORD)
time.sleep(4)

# 訂閱興櫃股票（市場代碼=4）
# 用幾個今天成交量大的興櫃股
stocks = ["4738", "6434", "6407", "5271", "3585", "4582"]
lst = List[WatchlistAll]()
for sid in stocks:
    w = WatchlistAll()
    w.MarketNo  = 4   # 興櫃
    w.StockCode = sid
    lst.Add(w)

api.SubscribeWatchlistAll(lst)
print(f"已訂閱 {len(stocks)} 檔興櫃股票，等待報價 60 秒...")

time.sleep(60)
print(f"\n總共收到 {count[0]} 則回應")
