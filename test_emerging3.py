import requests
import pandas as pd
from datetime import datetime, timedelta
import time

def get_emerging_prices():
    """抓取近一個月興櫃每日收盤價 - 使用TPEx OpenAPI"""
    all_data = {}
    
    end_date = datetime.today()
    start_date = end_date - timedelta(days=30)
    
    current = start_date
    while current <= end_date:
        if current.weekday() >= 5:
            current += timedelta(days=1)
            continue
        
        date_str = current.strftime("%Y%m%d")
        
        try:
            # 使用TPEx新版API
            url = f"https://www.tpex.org.tw/openapi/v1/tpex_esb_latest_statistics"
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                "Accept": "application/json"
            }
            res = requests.get(url, headers=headers, timeout=10)
            
            if res.status_code == 200:
                data = res.json()
                count = 0
                for row in data:
                    stock_id = row.get("SecuritiesCompanyCode", "").strip()
                    stock_name = row.get("CompanyName", "").strip()
                    try:
                        close_price = float(str(row.get("ClosingPrice", "0")).replace(",", ""))
                    except:
                        continue
                    if close_price <= 0:
                        continue
                    
                    if stock_id not in all_data:
                        all_data[stock_id] = {"name": stock_name, "prices": {}}
                    all_data[stock_id]["prices"][current.strftime("%Y-%m-%d")] = close_price
                    count += 1
                    
                print(f"✅ {current.strftime('%Y-%m-%d')} 抓到 {count} 支")
                break  # 這個API只有最新一天，先測試
            else:
                print(f"❌ HTTP {res.status_code}")
                
        except Exception as e:
            print(f"❌ {current.strftime('%Y-%m-%d')} 失敗: {e}")
        
        current += timedelta(days=1)
        time.sleep(0.3)
    
    return all_data

if __name__ == "__main__":
    print("測試TPEx OpenAPI...")
    
    # 先測試最新資料
    url = "https://www.tpex.org.tw/openapi/v1/tpex_esb_latest_statistics"
    headers = {"User-Agent": "Mozilla/5.0"}
    
    try:
        res = requests.get(url, headers=headers, timeout=10)
        print(f"HTTP Status: {res.status_code}")
        print(f"Content-Type: {res.headers.get('Content-Type')}")
        print(f"前200字: {res.text[:200]}")
    except Exception as e:
        print(f"失敗: {e}")
