"""
每天收盤後自動抓處置股資料，存到 disposal_history.json，然後 push 到 GitHub
建議設定 Windows 排程每天 14:00 執行
"""

import requests
import json
import os
import subprocess
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
from datetime import datetime, date, timedelta

# 自動偵測路徑（家裡 or 辦公室）
_possible_dirs = [
    r"C:\Users\wu\stock-screener",
    r"C:\Users\chaow\stock_project",
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
    """抓取上市處置股清單（含20分鐘標記）"""
    url = "https://www.twse.com.tw/rwd/zh/announcement/punish?response=json"
    headers = {"User-Agent": "Mozilla/5.0"}
    stocks = {}
    try:
        resp = requests.get(url, headers=headers, timeout=15, verify=False)
        data = resp.json()
        if data.get("stat") == "OK":
            for row in data.get("data", []):
                try:
                    stock_id   = row[2].strip()
                    stock_name = row[3].strip()
                    period     = row[6].strip() if len(row) > 6 else ""
                    content    = row[8].strip() if len(row) > 8 else ""
                    is_20min   = "二十分鐘" in content
                    if stock_id and stock_id not in stocks:
                        stocks[stock_id] = {
                            "name": stock_name,
                            "period": period,
                            "is_20min": is_20min,
                            "market": "上市"
                        }
                except:
                    continue
        print(f"  上市：共 {len(stocks)} 檔，其中20分鐘 {sum(1 for v in stocks.values() if v['is_20min'])} 檔")
    except Exception as e:
        print(f"  上市抓取失敗: {e}")
    return stocks

def fetch_otc():
    """抓取上櫃處置股清單（含20分鐘標記）"""
    # 嘗試多個可能的 TPEX 網址
    urls = [
        "https://www.tpex.org.tw/web/bulletin/disposal/disposal_result.php?l=zh-tw&o=json",
        "https://www.tpex.org.tw/rwd/zh/announcement/punish?response=json",
    ]
    headers = {"User-Agent": "Mozilla/5.0"}
    stocks = {}
    for url in urls:
        try:
            resp = requests.get(url, headers=headers, timeout=15, verify=False)
            if resp.status_code != 200:
                continue
            data = resp.json()
            rows = data.get("aaData", data.get("data", []))
            if not rows:
                continue
            for row in rows:
                try:
                    stock_id   = str(row[2]).strip()
                    stock_name = str(row[3]).strip()
                    period     = str(row[6]).strip() if len(row) > 6 else ""
                    content    = str(row[8]).strip() if len(row) > 8 else ""
                    is_20min   = "二十分鐘" in content
                    if stock_id and stock_id not in stocks:
                        stocks[stock_id] = {
                            "name": stock_name,
                            "period": period,
                            "is_20min": is_20min,
                            "market": "上櫃"
                        }
                except:
                    continue
            if stocks:
                print(f"  上櫃：共 {len(stocks)} 檔，其中20分鐘 {sum(1 for v in stocks.values() if v['is_20min'])} 檔")
                break
        except Exception as e:
            print(f"  上櫃 {url} 失敗: {e}")
            continue
    if not stocks:
        print("  上櫃：無法抓取")
    return stocks

def git_push():
    """把更新後的 JSON push 到 GitHub"""
    try:
        subprocess.run(["git", "add", "disposal_history.json"], cwd=REPO_DIR, check=True)
        subprocess.run(["git", "commit", "-m", f"data: 更新處置股資料 {date.today()}"], cwd=REPO_DIR, check=True)
        subprocess.run(["git", "push"], cwd=REPO_DIR, check=True)
        print("✅ 已推送到 GitHub")
    except subprocess.CalledProcessError as e:
        if "nothing to commit" in str(e):
            print("⚠️ 今天的資料已存在，不需要 push")
        else:
            print(f"❌ Push 失敗: {e}")

def main():
    today_str = date.today().strftime("%Y-%m-%d")
    print(f"[{datetime.now().strftime('%H:%M')}] 開始抓取處置股資料...")

    # 載入歷史
    history = load_history()

    # 抓今天的資料（上市＋上櫃合併）
    print("抓取上市...")
    twse_stocks = fetch_twse()
    print("抓取上櫃...")
    otc_stocks = fetch_otc()

    stocks = {**twse_stocks, **otc_stocks}  # 上市優先，上櫃補充

    if not stocks:
        print("❌ 今天沒有抓到資料，中止")
        return

    # 存入歷史（以日期為key）
    history[today_str] = stocks
    count_20 = sum(1 for v in stocks.values() if v.get("is_20min"))
    print(f"✅ 今天共 {len(stocks)} 檔處置股，其中20分鐘 {count_20} 檔")

    # 清除超過 65 天的資料
    cutoff = (date.today() - timedelta(days=65)).strftime("%Y-%m-%d")
    old_count = len(history)
    history = {d: v for d, v in history.items() if d >= cutoff}
    print(f"🧹 清除舊資料：{old_count - len(history)} 筆，剩餘 {len(history)} 天")

    # 存檔
    save_history(history)
    print(f"💾 已儲存到 {HISTORY_FILE}")

    # Push 到 GitHub
    git_push()

if __name__ == "__main__":
    main()
