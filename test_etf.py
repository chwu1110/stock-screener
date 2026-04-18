import requests
import json

headers = {"User-Agent": "Mozilla/5.0"}

# 測試證交所ETF申購贖回清單API
print("測試1：證交所ETF API")
url1 = "https://www.twse.com.tw/fund/ETF_LARGE?response=json"
res1 = requests.get(url1, headers=headers, timeout=10)
print(f"HTTP: {res1.status_code}")
print(f"前300字: {res1.text[:300]}")

print("\n測試2：主動型ETF持股")
url2 = "https://www.twse.com.tw/exchangeReport/STOCK_DAY?response=json&stockNo=00987A"
res2 = requests.get(url2, headers=headers, timeout=10)
print(f"HTTP: {res2.status_code}")
print(f"前300字: {res2.text[:300]}")
