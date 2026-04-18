import requests
import json

headers = {"User-Agent": "Mozilla/5.0"}

# 印出完整欄位
url = "https://www.tpex.org.tw/openapi/v1/tpex_esb_latest_statistics"
res = requests.get(url, headers=headers, timeout=10)
data = res.json()
print("完整欄位:", list(data[0].keys()))
print("\n第一筆資料:")
print(json.dumps(data[0], ensure_ascii=False, indent=2))

# 試試歷史資料API
print("\n\n測試歷史資料API...")
url2 = "https://www.tpex.org.tw/openapi/v1/tpex_esb_daily_statistics"
res2 = requests.get(url2, headers=headers, timeout=10)
print(f"HTTP: {res2.status_code}")
print(f"前300字: {res2.text[:300]}")
