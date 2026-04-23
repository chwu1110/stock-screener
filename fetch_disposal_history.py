"""
補抓近兩個月的處置股歷史資料
只需要跑一次！
"""

import requests
import json
import os
import time
from datetime import date, timedelta

HISTORY_FILE = r"C:\Users\chaow\stock_project\disposal_history.json"
headers = {"User-Agent": "Mozilla/5.0"}

def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_history(history):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

def fetch_disposal_by_date(query_date):
    """用日期查詢當天的處置股"""
    date_str = query_date.strftime("%Y%m%d")
    url = f"https://www.twse.com.tw/rwd/zh/announcement/punish?response=json&startDate={date_str}&endDate={date_str}"
    try:
        r = requests.get(url, headers=headers, timeout=15, verify=False)
        data = r.json()
        stocks = {}
        if data.get("stat") == "OK":
            for row in data.get("data", []):
                try:
                    stock_id   = row[2].strip()
                    stock_name = row[3].strip()
                    period     = row[6].strip() if len(row) > 6 else ""
                    if stock_id and stock_id not in stocks:
                        stocks[stock_id] = {"name": stock_name, "period": period}
                except:
                    continue
        return stocks
    except Exception as e:
        print(f"  失敗: {e}")
        return None

def main():
    history = load_history()
    today = date.today()

    # 抓近 65 天
    print("開始補抓近兩個月的處置股歷史資料...")
    for i in range(65, 0, -1):
        target = today - timedelta(days=i)
        # 跳過週末
        if target.weekday() >= 5:
            continue
        date_key = target.strftime("%Y-%m-%d")
        if date_key in history:
            print(f"  {date_key} 已有資料，跳過")
            continue

        print(f"  抓取 {date_key}...", end=" ")
        stocks = fetch_disposal_by_date(target)
        if stocks is None:
            print("失敗，跳過")
            continue
        if stocks:
            history[date_key] = stocks
            print(f"找到 {len(stocks)} 檔")
        else:
            print("無資料（當天可能無處置）")
            history[date_key] = {}

        time.sleep(0.5)  # 避免太頻繁

    save_history(history)
    print(f"\n✅ 完成！共 {len(history)} 天的資料")

    # 顯示有哪幾天找到 7721
    print("\n7721 出現的日期：")
    for d, stocks in sorted(history.items()):
        if "7721" in stocks:
            print(f"  {d}: {stocks['7721']}")

if __name__ == "__main__":
    main()
