"""
每天收盤後自動抓處置股資料，存到 disposal_history.json，然後 push 到 GitHub
建議設定 Windows 排程每天 14:00 執行
"""

import requests
import json
import os
import subprocess
from datetime import datetime, date, timedelta

HISTORY_FILE = r"C:\Users\chaow\stock_project\disposal_history.json"
REPO_DIR     = r"C:\Users\chaow\stock_project"

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

def fetch_disposal():
    """抓取目前處置股清單"""
    url = "https://www.twse.com.tw/rwd/zh/announcement/punish?response=json"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        resp = requests.get(url, headers=headers, timeout=15, verify=False)
        data = resp.json()
        stocks = {}
        if data.get("stat") == "OK":
            for row in data.get("data", []):
                try:
                    stock_id   = row[2].strip()
                    stock_name = row[3].strip()
                    period     = row[6].strip() if len(row) > 6 else ""
                    if stock_id and stock_id not in stocks:
                        stocks[stock_id] = {
                            "name": stock_name,
                            "period": period
                        }
                except:
                    continue
        return stocks
    except Exception as e:
        print(f"抓取失敗: {e}")
        return {}

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

    # 抓今天的資料
    stocks = fetch_disposal()
    if not stocks:
        print("❌ 今天沒有抓到資料，中止")
        return

    # 存入歷史（以日期為key）
    history[today_str] = stocks
    print(f"✅ 今天共 {len(stocks)} 檔處置股：{list(stocks.keys())}")

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
