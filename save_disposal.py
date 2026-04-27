"""
瘥予?嗥敺???蔭?∟???摮 disposal_history.json嚗敺?push ??GitHub
撱箄降閮剖? Windows ??瘥予 14:00 ?瑁?
"""

import requests
import json
import os
import subprocess
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
from datetime import datetime, date, timedelta

# ?芸??菜葫頝臬?嚗振鋆?or 颲血摰歹?
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
    """??銝??蔭?⊥??殷???0??璅?嚗?""
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
                    is_20min   = "鈭???" in content
                    if stock_id and stock_id not in stocks:
                        stocks[stock_id] = {
                            "name": stock_name,
                            "period": period,
                            "is_20min": is_20min,
                            "market": "銝?"
                        }
                except:
                    continue
        print(f"  銝?嚗 {len(stocks)} 瑼??嗡葉20?? {sum(1 for v in stocks.values() if v['is_20min'])} 瑼?)
    except Exception as e:
        print(f"  銝???憭望?: {e}")
    return stocks

def fetch_otc():
    """??銝??蔭?⊥??殷???0??璅?嚗?""
    # ?岫憭?賜? TPEX 蝬脣?
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
                    is_20min   = "鈭???" in content
                    if stock_id and stock_id not in stocks:
                        stocks[stock_id] = {
                            "name": stock_name,
                            "period": period,
                            "is_20min": is_20min,
                            "market": "銝?"
                        }
                except:
                    continue
            if stocks:
                print(f"  銝?嚗 {len(stocks)} 瑼??嗡葉20?? {sum(1 for v in stocks.values() if v['is_20min'])} 瑼?)
                break
        except Exception as e:
            print(f"  銝? {url} 憭望?: {e}")
            continue
    if not stocks:
        print("  銝?嚗瘜???)
    return stocks

def git_push():
    """??啣???JSON push ??GitHub"""
    try:
        subprocess.run(["git", "add", "disposal_history.json"], cwd=REPO_DIR, check=True)
        subprocess.run(["git", "commit", "-m", f"data: ?湔?蔭?∟???{date.today()}"], cwd=REPO_DIR, check=True)
        subprocess.run(["git", "push"], cwd=REPO_DIR, check=True)
        print("??撌脫? GitHub")
    except subprocess.CalledProcessError as e:
        if "nothing to commit" in str(e):
            print("?? 隞予???歇摮嚗??閬?push")
        else:
            print(f"??Push 憭望?: {e}")

def main():
    today_str = date.today().strftime("%Y-%m-%d")
    print(f"[{datetime.now().strftime('%H:%M')}] ?????蔭?∟???..")

    # 頛甇瑕
    history = load_history()

    # ??憭拍?鞈?嚗?撣?銝??蔥嚗?
    print("??銝?...")
    twse_stocks = fetch_twse()
    print("??銝?...")
    otc_stocks = fetch_otc()

    stocks = {**twse_stocks, **otc_stocks}  # 銝??芸?嚗?瑹???

    if not stocks:
        print("??隞予瘝??鞈?嚗葉甇?)
        return

    # 摮甇瑕嚗誑?交??榭ey嚗?
    history[today_str] = stocks
    count_20 = sum(1 for v in stocks.values() if v.get("is_20min"))
    print(f"??隞予??{len(stocks)} 瑼?蝵株嚗銝?0?? {count_20} 瑼?)

    # 皜頞? 65 憭拍?鞈?
    cutoff = (date.today() - timedelta(days=65)).strftime("%Y-%m-%d")
    old_count = len(history)
    history = {d: v for d, v in history.items() if d >= cutoff}
    print(f"?完 皜????{old_count - len(history)} 蝑??拚? {len(history)} 憭?)

    # 摮?
    save_history(history)
    print(f"? 撌脣摮 {HISTORY_FILE}")

    # Push ??GitHub
    git_push()

if __name__ == "__main__":
    main()

