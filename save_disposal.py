"""
Every day after market close, fetch disposal stocks and push to GitHub.
Run at 14:00 daily via Windows Task Scheduler.
"""

import requests
import json
import os
import subprocess
import time
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
from datetime import datetime, date, timedelta

_possible_dirs = [
    r"C:\Users\wu\stock-screener",
    r"C:\Users\chaow\stock-screener",
]
REPO_DIR = next((d for d in _possible_dirs if os.path.exists(d)), os.path.dirname(os.path.abspath(__file__)))
HISTORY_FILE = os.path.join(REPO_DIR, "disposal_history.json")

def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {}

def save_history(history):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

def fetch_twse():
    urls = [
        "https://www.twse.com.tw/rwd/zh/announcement/punish?response=json",
        "https://www.twse.com.tw/zh/announcement/punish?response=json",
        "https://openapi.twse.com.tw/v1/announcement/punish",
    ]
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    stocks = {}
    for url in urls:
        try:
            for attempt in range(3):  # retry 3次
                try:
                    resp = requests.get(url, headers=headers, timeout=15, verify=False)
                    if resp.status_code == 200 and resp.text.strip():
                        break
                except:
                    if attempt == 2:
                        raise
                    time.sleep(1)
            
            # 嘗試 JSON 格式
            data = resp.json()
            
            # OpenAPI 格式（list of dict）
            if isinstance(data, list) and data and isinstance(data[0], dict):
                for row in data:
                    try:
                        sid   = str(row.get("SecuritiesCompanyCode", row.get("stockCode", ""))).strip()
                        name  = str(row.get("CompanyName", row.get("stockName", ""))).strip()
                        period= str(row.get("DisposalPeriod", row.get("period", ""))).strip()
                        if sid and sid not in stocks:
                            stocks[sid] = {"name": name, "period": period, "is_20min": False, "market": "上市"}
                    except:
                        continue
            # 舊版格式
            elif data.get("stat") == "OK":
                for row in data.get("data", []):
                    try:
                        stock_id   = row[2].strip()
                        stock_name = row[3].strip()
                        period     = row[6].strip() if len(row) > 6 else ""
                        content    = row[8].strip() if len(row) > 8 else ""
                        is_20min   = "20" in content or "二十分鐘" in content
                        if stock_id and stock_id not in stocks:
                            stocks[stock_id] = {
                                "name": stock_name,
                                "period": period,
                                "is_20min": is_20min,
                                "market": "上市"
                            }
                    except:
                        continue
            
            if stocks:
                print(f"  TWSE: {len(stocks)} stocks (from {url.split('/')[4]})")
                break
        except Exception as e:
            print(f"  TWSE {url} failed: {e}")
    
    if not stocks:
        print("  TWSE: all methods failed")
    return stocks

def fetch_otc():
    headers = {"User-Agent": "Mozilla/5.0"}
    stocks = {}

    # 方法1：TPEX OpenAPI（官方正式端點）
    try:
        resp = requests.get(
            "https://www.tpex.org.tw/openapi/v1/tpex_disposal_information",
            headers=headers, timeout=15, verify=False
        )
        if resp.status_code == 200:
            data = resp.json()
            if isinstance(data, list) and data:
                for row in data:
                    try:
                        sid    = str(row.get("SecuritiesCompanyCode", "")).strip()
                        name   = str(row.get("CompanyName", "")).strip()
                        # DisposalPeriod 格式: "1150429~1150513" (民國年YYYMMDD)
                        dp = str(row.get("DispositionPeriod", "")).strip()
                        def roc_to_ad(s):
                            s = s.strip().replace("/", "").replace("-", "")
                            if len(s) == 7:  # YYYMMDD
                                y = int(s[:3]) + 1911
                                return f"{y}/{s[3:5]}/{s[5:7]}"
                            return s
                        if "~" in dp:
                            parts = dp.split("~")
                            period = f"{roc_to_ad(parts[0])}～{roc_to_ad(parts[1])}"
                        else:
                            period = dp
                        is_20min = "20分鐘" in str(row.get("DisposalCondition", ""))
                        if sid and sid not in stocks:
                            stocks[sid] = {"name": name, "period": period,
                                           "is_20min": is_20min, "market": "上櫃"}
                    except:
                        continue
                if stocks:
                    print(f"  OTC (OpenAPI): {len(stocks)} stocks")
                    return stocks
    except Exception as e:
        print(f"  OTC OpenAPI failed: {e}")

    # 方法2：舊版 aaData 格式
    for url in [
        "https://www.tpex.org.tw/web/bulletin/disposal/disposal_result.php?l=zh-tw&o=json",
        "https://www.tpex.org.tw/rwd/zh/announcement/punish?response=json",
    ]:
        try:
            resp = requests.get(url, headers=headers, timeout=15, verify=False)
            if resp.status_code != 200:
                continue
            data = resp.json()
            rows = data.get("aaData", data.get("data", []))
            for row in rows:
                try:
                    sid    = str(row[2]).strip()
                    name   = str(row[3]).strip()
                    period = str(row[6]).strip() if len(row) > 6 else ""
                    content= str(row[8]).strip() if len(row) > 8 else ""
                    is_20min = "20" in content or "二十分鐘" in content
                    if sid and sid not in stocks:
                        stocks[sid] = {"name": name, "period": period,
                                       "is_20min": is_20min, "market": "上櫃"}
                except:
                    continue
            if stocks:
                print(f"  OTC (legacy): {len(stocks)} stocks from {url}")
                return stocks
        except Exception as e:
            print(f"  OTC {url} failed: {e}")

    print("  OTC: all methods failed")
    return stocks

def git_push():
    try:
        subprocess.run(["git", "add", "disposal_history.json"], cwd=REPO_DIR, check=True)
        subprocess.run(["git", "commit", "-m", f"data: disposal update {date.today()}"], cwd=REPO_DIR, check=True)
        subprocess.run(["git", "push"], cwd=REPO_DIR, check=True)
        print("Pushed to GitHub")
    except subprocess.CalledProcessError as e:
        if "nothing to commit" in str(e):
            print("Already up to date")
        else:
            print(f"Push failed: {e}")

def main():
    today_str = date.today().strftime("%Y-%m-%d")
    print(f"[{datetime.now().strftime('%H:%M')}] Fetching disposal stocks for {today_str}...")

    history = load_history()

    print("Fetching TWSE...")
    twse_stocks = fetch_twse()
    print("Fetching OTC...")
    otc_stocks = fetch_otc()

    stocks = {**twse_stocks, **otc_stocks}

    if not stocks:
        print("No data fetched, aborting")
        return

    # 過濾已出關的股票
    today_date = date.today()
    def parse_end_date(period):
        try:
            period = period.replace("～", "~").replace(" ", "")
            end = period.split("~")[1].strip()
            parts = end.replace("-", "/").split("/")
            if len(parts) == 3:
                y = int(parts[0])
                if y < 1911: y += 1911
                return date(y, int(parts[1]), int(parts[2]))
        except:
            pass
        return None

    filtered = {}
    for sid, info in stocks.items():
        end_date = parse_end_date(info.get("period", ""))
        if end_date is None or end_date >= today_date:
            filtered[sid] = info
    print(f"過濾已出關後: {len(filtered)} 筆（移除 {len(stocks)-len(filtered)} 筆）")
    stocks = filtered

    history[today_str] = stocks
    print(f"Today total: {len(stocks)} disposal stocks (TWSE:{len(twse_stocks)} OTC:{len(otc_stocks)})")

    cutoff = (date.today() - timedelta(days=65)).strftime("%Y-%m-%d")
    history = {d: v for d, v in history.items() if d >= cutoff}

    save_history(history)
    print(f"Saved to {HISTORY_FILE}")

    git_push()

if __name__ == "__main__":
    main()
