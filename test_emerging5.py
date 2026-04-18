import requests

url = "https://www.tpex.org.tw/openapi/v1/tpex_esb_latest_statistics"
headers = {"User-Agent": "Mozilla/5.0"}
res = requests.get(url, headers=headers, timeout=10)
data = res.json()

print(f"總共 {len(data)} 筆資料")
print(f"\n第一筆完整資料:")
import json
print(json.dumps(data[0], ensure_ascii=False, indent=2))

# 模擬篩選條件
result = []
for row in data:
    try:
        stock_id = row.get("SecuritiesCompanyCode", "").strip()
        stock_name = row.get("CompanyName", "").strip()
        prev_price = float(str(row.get("PreviousAveragePrice", "0")).replace(",", ""))
        latest_price = float(str(row.get("LatestPrice", "0")).replace(",", ""))
        volume = int(str(row.get("TransactionVolume", "0")).replace(",", ""))
        
        if prev_price <= 0 or latest_price <= 0:
            continue
        
        gain = (latest_price / prev_price) - 1
        print(f"{stock_id} {stock_name} 昨均:{prev_price} 今:{latest_price} 量:{volume} 漲幅:{gain*100:.1f}%")
        
        if gain >= 0.30 and volume > 500:
            result.append(f"{stock_id} {stock_name} 漲幅:{gain*100:.1f}% 量:{volume}")
    except Exception as e:
        continue

print(f"\n符合條件（漲30%+量>500）：{len(result)} 支")
for r in result:
    print(r)
