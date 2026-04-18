import requests
import pandas as pd
from datetime import datetime, timedelta

def get_emerging_prices():
    """抓取近一個月興櫃每日收盤價"""
    all_data = {}
    
    end_date = datetime.today()
    start_date = end_date - timedelta(days=30)
    
    current = start_date
    while current <= end_date:
        if current.weekday() >= 5:
            current += timedelta(days=1)
            continue
        
        # 換成民國年格式
        roc_year = current.year - 1911
        date_str = f"{roc_year}/{current.month:02d}/{current.day:02d}"
        
        try:
            url = "https://www.tpex.org.tw/web/emergingstock/single_all/emergingstk_all.php"
            params = {
                "l": "zh-tw",
                "d": date_str,
                "se": "EW",
                "o": "json"
            }
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Referer": "https://www.tpex.org.tw/"
            }
            res = requests.get(url, params=params, headers=headers, timeout=10)
            data = res.json()
            
            if "aaData" in data and data["aaData"]:
                for row in data["aaData"]:
                    stock_id = row[0].strip()
                    stock_name = row[1].strip()
                    try:
                        close_price = float(row[4].replace(",", ""))
                    except:
                        continue
                    
                    if stock_id not in all_data:
                        all_data[stock_id] = {"name": stock_name, "prices": {}}
                    all_data[stock_id]["prices"][current.strftime("%Y-%m-%d")] = close_price
                    
            print(f"✅ {date_str} 抓到 {len(data.get('aaData', []))} 支")
        except Exception as e:
            print(f"❌ {date_str} 失敗: {e}")
        
        current += timedelta(days=1)
    
    return all_data

if __name__ == "__main__":
    print("開始抓取興櫃資料...")
    data = get_emerging_prices()
    print(f"\n共抓到 {len(data)} 支興櫃股票")
    
    result = []
    for stock_id, info in data.items():
        prices = sorted(info["prices"].items())
        if len(prices) < 3:
            continue
        
        best_gain = 0
        best_row = None
        
        for i in range(2, len(prices)):
            d1, p1 = prices[i-2]
            d2, p2 = prices[i-1]
            d3, p3 = prices[i]
            if p1 <= 0:
                continue
            gain = (p3 / p1) - 1
            if gain > best_gain:
                best_gain = gain
                best_row = (d1, d2, d3, p1, p2, p3)
        
        if best_gain >= 0.30 and best_row:
            d1, d2, d3, p1, p2, p3 = best_row
            result.append({
                "股票代號": stock_id,
                "股票名稱": info["name"],
                "起始日": d1,
                "中間日": d2,
                "結束日": d3,
                "起始收盤": p1,
                "結束收盤": p3,
                "漲幅": f"{best_gain*100:.1f}%"
            })
    
    result.sort(key=lambda x: x["結束日"], reverse=True)
    print(f"\n符合條件（3天內漲30%）的興櫃股票：{len(result)} 支")
    for r in result:
        print(r)
