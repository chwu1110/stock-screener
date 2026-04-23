import finlab
from finlab import data

finlab.login("LBmwu3n0/lor77y1Z0aBH/Q0WBI6+bLJrA2TlchZAM1jb6jJaURRbaQRZRWjozwP#vip_m")

# 測試有沒有處置股資料
try:
    disposal = data.get("etf:處置股票")
    print("找到:", disposal)
except:
    pass

try:
    disposal = data.get("institutional_investors:處置")
    print("找到:", disposal)
except:
    pass

# 用證交所API試試
import requests
url = "https://www.twse.com.tw/rwd/zh/announcement/punish?response=json"
headers = {"User-Agent": "Mozilla/5.0"}
res = requests.get(url, headers=headers, timeout=10)
print(f"證交所處置股API: HTTP {res.status_code}")
print(f"內容: {res.text[:300]}")
