import os
import finlab
from finlab import data
import pandas as pd
from datetime import datetime, timedelta, date
import json
import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
from flask import Flask, render_template_string
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)

FINLAB_API_KEY = "LBmwu3n0/lor77y1Z0aBH/Q0WBI6+bLJrA2TlchZAM1jb6jJaURRbaQRZRWjozwP#vip_m"

# ── 處置股歷史（記憶體版，Railway 啟動時從 JSON 載入，之後每天自動更新）──
_disposal_history = {}

def _fetch_disposal_twse():
    urls = [
        "https://www.twse.com.tw/rwd/zh/announcement/punish?response=json",
        "https://www.twse.com.tw/zh/announcement/punish?response=json",
        "https://www.twse.com.tw/exchangeReport/BWIBBU_d?response=json",
    ]
    stocks = {}
    for url in urls:
        try:
            resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}, timeout=15, verify=False)
            if resp.status_code != 200 or not resp.text.strip():
                print(f"處置股上市 {url} 回應異常: status={resp.status_code}")
                continue
            d = resp.json()
            if d.get("stat") == "OK":
                for row in d.get("data", []):
                    try:
                        sid  = row[2].strip()
                        name = row[3].strip()
                        period  = row[6].strip() if len(row) > 6 else ""
                        content = row[8].strip() if len(row) > 8 else ""
                        if sid and sid not in stocks:
                            stocks[sid] = {"name": name, "period": period,
                                           "is_20min": "二十分鐘" in content, "market": "上市"}
                    except:
                        continue
                if stocks:
                    print(f"處置股上市抓取成功: {len(stocks)} 檔")
                    break
        except Exception as e:
            print(f"處置股上市抓取失敗 {url}: {e}")
    return stocks

def _fetch_disposal_otc():
    """從 TPEX OpenAPI 抓上櫃處置股"""
    headers = {"User-Agent": "Mozilla/5.0"}
    stocks = {}

    # 方法1：TPEX OpenAPI 官方端點
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
                        dp     = str(row.get("DisposalPeriod", "")).strip()
                        def roc_yyyymmdd_to_ad(s):
                            s = s.strip()
                            if len(s) == 7:
                                y = int(s[:3]) + 1911
                                m = s[3:5]
                                d = s[5:7]
                                return f"{y}/{m}/{d}"
                            return s
                        if "~" in dp:
                            pts = dp.split("~")
                            period = f"{roc_yyyymmdd_to_ad(pts[0])}~{roc_yyyymmdd_to_ad(pts[1])}"
                        else:
                            period = dp
                        is_20min = "20分鐘" in str(row.get("DisposalCondition", ""))
                        if sid and sid not in stocks:
                            stocks[sid] = {"name": name, "period": period,
                                           "is_20min": is_20min, "market": "上櫃"}
                    except:
                        continue
                if stocks:
                    print(f"處置股上櫃抓取成功 (OpenAPI): {len(stocks)} 檔")
                    return stocks
    except Exception as e:
        print(f"處置股上櫃 OpenAPI 失敗: {e}")

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
                print(f"處置股上櫃抓取成功 (legacy): {len(stocks)} 檔")
                return stocks
        except Exception as e:
            print(f"處置股上櫃失敗 {url}: {e}")

    print("處置股上櫃：所有方法皆失敗")
    return stocks

def refresh_disposal_from_github():
    """每天從 GitHub 重新載入最新的處置股歷史"""
    global _disposal_history
    try:
        github_url = "https://raw.githubusercontent.com/chwu1110/stock-screener/main/disposal_history.json"
        resp = requests.get(github_url, timeout=15)
        if resp.status_code == 200 and resp.text.strip():
            _disposal_history = resp.json()
            print(f"[排程] 從 GitHub 更新處置股歷史：{len(_disposal_history)} 天")
        else:
            print(f"[排程] GitHub 載入失敗: status={resp.status_code}")
    except Exception as e:
        print(f"[排程] 從 GitHub 讀取處置股失敗: {e}")

def update_disposal_history():
    """每天自動抓處置股資料存入記憶體，並同步到 disposal_history.json"""
    global _disposal_history
    today_str = date.today().strftime("%Y-%m-%d")
    print(f"[排程] 更新處置股資料 {today_str}...")
    twse = _fetch_disposal_twse()
    otc  = _fetch_disposal_otc()
    stocks = {**twse, **otc}
    if stocks:
        _disposal_history[today_str] = stocks
        # 清除65天以前的資料
        cutoff = (date.today() - timedelta(days=65)).strftime("%Y-%m-%d")
        _disposal_history = {d: v for d, v in _disposal_history.items() if d >= cutoff}
        # 同步寫回 JSON（讓重啟後不會遺失）
        try:
            history_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "disposal_history.json")
            with open(history_path, "w", encoding="utf-8") as f:
                json.dump(_disposal_history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"寫入 disposal_history.json 失敗: {e}")
        print(f"[排程] 處置股更新完成，共 {len(stocks)} 檔")
    else:
        print("[排程] 今天沒有抓到處置股資料")

HOME_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>台股選股平台</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: 'Microsoft JhengHei', sans-serif; background: #0f172a; color: #e2e8f0; padding: 40px 30px; }
        h1 { text-align: center; font-size: 28px; margin-bottom: 8px; color: #f8fafc; }
        .subtitle { text-align: center; color: #94a3b8; font-size: 13px; margin-bottom: 40px; }
        .grid { display: flex; flex-wrap: wrap; gap: 20px; justify-content: center; }
        .card { background: #1e293b; border-radius: 16px; padding: 28px 24px; width: 260px; cursor: pointer; text-decoration: none; color: inherit; transition: transform 0.2s, box-shadow 0.2s; border: 1px solid #334155; }
        .card:hover { transform: translateY(-4px); box-shadow: 0 8px 30px rgba(0,0,0,0.4); border-color: #4f6e9f; }
        .card-icon { font-size: 36px; margin-bottom: 14px; }
        .card-title { font-size: 16px; font-weight: bold; margin-bottom: 8px; color: #f1f5f9; }
        .card-desc { font-size: 13px; color: #94a3b8; margin-bottom: 16px; line-height: 1.5; }
        .card-count { font-size: 28px; font-weight: bold; color: #38bdf8; }
        .card-count-label { font-size: 12px; color: #64748b; margin-top: 2px; }
        .updated { text-align: center; color: #475569; font-size: 12px; margin-top: 40px; }
        .section-title { width: 100%; text-align: center; font-size: 18px; font-weight: bold; color: #94a3b8; margin: 30px 0 10px 0; letter-spacing: 2px; border-bottom: 1px solid #334155; padding-bottom: 10px; }
        .card-emerging { border-color: #1e4a6e; }
        .card-emerging:hover { border-color: #38bdf8; box-shadow: 0 8px 30px rgba(56,189,248,0.2); }
        .card-emerging .card-count { color: #f59e0b; }
    </style>
</head>
<body>
    <h1>📊 台股選股平台</h1>
    <p class="subtitle">更新時間：{{ update_time }}｜點擊策略卡片查看詳細結果</p>
    <a href="/monitor" style="display:inline-block;margin-bottom:20px;padding:10px 24px;background:#1e3a5f;color:#38bdf8;border-radius:8px;text-decoration:none;font-size:14px;font-weight:bold;border:1px solid #38bdf844;">📡 即時監控總覽（整合所有策略）</a>

    <div class="section-title">📈 上市櫃策略</div>
    <div class="grid">
        <a href="/strategy/1" class="card">
            <div class="card-icon">🔥</div>
            <div class="card-title">二手紅盤</div>
            <div class="card-desc">最近一個月內，連續兩個交易日漲停的股票</div>
            <div class="card-count">{{ counts[0] }}</div>
            <div class="card-count-label">符合股票數</div>
        </a>
        <a href="/strategy/3" class="card">
            <div class="card-icon">📉</div>
            <div class="card-title">強勢股回檔</div>
            <div class="card-desc">最近3個月內任意5日漲幅≥30%，且目前從高點修正≥20%</div>
            <div class="card-count">{{ counts[1] }}</div>
            <div class="card-count-label">符合股票數</div>
        </a>
        <a href="/strategy/4" class="card">
            <div class="card-icon">🀄</div>
            <div class="card-title">三手紅盤</div>
            <div class="card-desc">最近一個月內，連續三天漲停 或 連續三天累積漲幅≥30%</div>
            <div class="card-count">{{ counts[2] }}</div>
            <div class="card-count-label">符合股票數</div>
        </a>
        <a href="/strategy/5" class="card">
            <div class="card-icon">🎰</div>
            <div class="card-title">四手紅盤</div>
            <div class="card-desc">最近一個月內，連續四天漲停 或 連續四天累積漲幅≥40%</div>
            <div class="card-count">{{ counts[3] }}</div>
            <div class="card-count-label">符合股票數</div>
        </a>
        <a href="/strategy/6" class="card">
            <div class="card-icon">🔴</div>
            <div class="card-title">五手紅盤</div>
            <div class="card-desc">最近一個月內，連續五天累積漲幅≥50%</div>
            <div class="card-count">{{ counts[4] }}</div>
            <div class="card-count-label">符合股票數</div>
        </a>
        <a href="/strategy/7" class="card">
            <div class="card-icon">⚠️</div>
            <div class="card-title">近兩個月處置股</div>
            <div class="card-desc">近兩個月曾被處置的股票，即時股價 vs 兩個月高點、10日線、20日線</div>
            <div class="card-count">{{ counts[5] }}</div>
            <div class="card-count-label">符合股票數</div>
        </a>
        <a href="/strategy/14" class="card">
            <div class="card-icon">📅</div>
            <div class="card-title">處置股</div>
            <div class="card-desc">目前正在被處置的股票，今天是處置後第3到第5個交易日</div>
            <div class="card-count">{{ counts[6] }}</div>
            <div class="card-count-label">符合股票數</div>
        </a>
    </div>

    <p class="updated">資料來源：FinLab｜{{ update_time }}</p>
</body>
</html>
"""

DETAIL_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }}</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: 'Microsoft JhengHei', sans-serif; background: #0f172a; color: #e2e8f0; padding: 30px; }
        .back { display: inline-block; margin-bottom: 20px; color: #38bdf8; text-decoration: none; font-size: 14px; }
        .back:hover { text-decoration: underline; }
        h1 { font-size: 22px; margin-bottom: 6px; color: #f8fafc; }
        .subtitle { color: #94a3b8; font-size: 13px; margin-bottom: 24px; }
        .top-bar { display: flex; align-items: center; gap: 16px; margin-bottom: 16px; flex-wrap: wrap; }
        .stat-box { display: inline-block; background: #1e293b; border-radius: 10px; padding: 8px 20px; }
        .stat-box .num { font-size: 22px; font-weight: bold; color: #38bdf8; }
        .stat-box .label { font-size: 12px; color: #94a3b8; }
        .btn-export { background: #059669; color: white; border: none; border-radius: 8px; padding: 8px 18px; cursor: pointer; font-size: 13px; font-family: inherit; }
        .btn-export:hover { background: #047857; }
        .table-wrap { overflow-x: auto; border-radius: 12px; max-height: calc(100vh - 180px); overflow-y: auto; }
        table { width: 100%; border-collapse: collapse; background: #1e293b; }
        thead { position: sticky; top: 0; z-index: 10; }
        thead tr { background: #0f172a; }
        th { padding: 12px 16px; text-align: left; font-size: 13px; color: #94a3b8; font-weight: 600; white-space: nowrap; border-bottom: 1px solid #334155; }
        td { padding: 11px 16px; font-size: 14px; border-top: 1px solid #334155; white-space: nowrap; }
        tr:hover td { background: #263548; }
        .gain { color: #4ade80; font-weight: bold; }
        .loss { color: #f87171; font-weight: bold; }
        .stock-id { color: #38bdf8; font-weight: bold; }
        .empty { text-align: center; color: #94a3b8; padding: 40px; background: #1e293b; border-radius: 12px; }
        .updated { text-align: center; color: #475569; font-size: 12px; margin-top: 20px; }
        .below-ma10 td { background: rgba(248, 113, 113, 0.08); }
        .below-ma10:hover td { background: rgba(248, 113, 113, 0.15) !important; }
    </style>
</head>
<body>
    <a href="/" class="back">← 返回首頁</a>
    <h1>{{ icon }} {{ title }}</h1>
    <p class="subtitle">{{ desc }}</p>

    <div class="top-bar">
        <div class="stat-box">
            <div class="num">{{ stocks|length }}</div>
            <div class="label">符合股票數</div>
        </div>
        {% if stocks %}
        <button class="btn-export" onclick="exportCSV()">匯出 CSV</button>
        {% endif %}
    </div>

    {% if stocks %}
    <div class="table-wrap">
    <table id="main-table">
        <thead>
            <tr>
                {% for col in columns %}
                <th>{{ col }}</th>
                {% endfor %}
            </tr>
        </thead>
        <tbody>
            {% for s in stocks %}
            <tr {% if below_ma10_ids is defined and s['股票代號'] in below_ma10_ids %}class="below-ma10"{% endif %}>
                {% for col in columns %}
                <td class="
                    {% if col == '股票代號' %}stock-id
                    {% elif col == '即時股價' and below_ma10_ids is defined and s['股票代號'] in below_ma10_ids %}loss
                    {% elif col == '10日均線' and below_ma10_ids is defined and s['股票代號'] in below_ma10_ids %}loss
                    {% elif '漲幅' in col or '漲停' in col %}gain
                    {% elif '修正' in col %}loss
                    {% endif %}
                ">{{ s[col] }}</td>
                {% endfor %}
            </tr>
            {% endfor %}
        </tbody>
    </table>
    </div>
    {% else %}
    <div class="empty">❌ 沒有找到符合條件的股票</div>
    {% endif %}

    <p class="updated">資料來源：FinLab｜更新時間：{{ update_time }}</p>

<script>
function exportCSV() {
    var table = document.getElementById('main-table');
    if (!table) return;
    var rows = table.querySelectorAll('tr');
    var lines = [];
    rows.forEach(function(row) {
        var cells = row.querySelectorAll('th, td');
        var rowData = Array.from(cells).map(function(cell) {
            var text = cell.textContent.trim().replace(/,/g, '，');
            return '"' + text + '"';
        });
        lines.push(rowData.join(','));
    });
    var csv = '﻿' + lines.join('
');
    var blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    var a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = '{{ title }}_' + new Date().toISOString().slice(0,10) + '.csv';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
});
        lines.push(rowData.join(','));
    });
    var csv = '﻿' + lines.join('
');
    var blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    var a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = '{{ title }}_' + new Date().toISOString().slice(0,10) + '.csv';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
}
</script>
</body>
</html>
"""


def get_twse_realtime(stock_ids):
    """從證交所抓上市即時股價，一次最多50檔"""
    prices = {}
    try:
        ids_str = "|".join(stock_ids)
        url = f"https://mis.twse.com.tw/stock/api/getStockInfo.jsp?ex_ch={ids_str}&json=1&delay=0"
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(url, headers=headers, timeout=10, verify=False)
        data = resp.json()
        now_str = datetime.now().strftime("%H:%M")
        for item in data.get("msgArray", []):
            sid = item.get("c", "")
            price_str = item.get("z", "-")  # 最新成交價
            if price_str and price_str != "-":
                try:
                    prices[sid] = {"price": float(price_str), "time": now_str}
                except:
                    pass
    except Exception as e:
        print(f"證交所即時API錯誤: {e}")
    return prices

def get_tpex_realtime(stock_ids):
    """從櫃買中心抓上櫃即時股價"""
    prices = {}
    try:
        ids_str = "|".join([f"otc_{sid}.tw" for sid in stock_ids])
        url = f"https://mis.twse.com.tw/stock/api/getStockInfo.jsp?ex_ch={ids_str}&json=1&delay=0"
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(url, headers=headers, timeout=10, verify=False)
        data = resp.json()
        now_str = datetime.now().strftime("%H:%M")
        for item in data.get("msgArray", []):
            sid = item.get("c", "")
            price_str = item.get("z", "-")
            if price_str and price_str != "-":
                try:
                    prices[sid] = {"price": float(price_str), "time": now_str}
                except:
                    pass
    except Exception as e:
        print(f"櫃買即時API錯誤: {e}")
    return prices

FUGLE_API_KEY = os.environ.get("FUGLE_API_KEY", "")

_realtime_cache = {"prices": {}, "time": None}

def get_realtime_prices(stock_ids):
    """用 Fugle API 抓即時股價（5分鐘快取）"""
    now = datetime.now().replace(tzinfo=None)
    if _realtime_cache["time"] and (now - _realtime_cache["time"]).total_seconds() < 300:
        return _realtime_cache["prices"]

    prices = {}
    headers = {"X-API-KEY": FUGLE_API_KEY}
    for sid in stock_ids:
        try:
            url = f"https://api.fugle.tw/marketdata/v1.0/stock/intraday/quote/{sid}"
            resp = requests.get(url, headers=headers, timeout=5, verify=False)
            if resp.status_code == 200:
                d = resp.json()
                price = d.get("closePrice") or d.get("lastPrice") or d.get("referencePrice")
                t = d.get("lastUpdated", "")
                if price:
                    prices[sid] = {"price": float(price), "time": str(t)[:16]}
        except:
            continue

    _realtime_cache["prices"] = prices
    _realtime_cache["time"] = now
    return prices

def get_all_data():
    finlab.login(api_token=FINLAB_API_KEY)

    today = datetime.today()
    start_2026 = "2026-01-01"
    start_1yr = (today - timedelta(days=90)).strftime("%Y-%m-%d")  # 改為3個月，加快速度
    start_3m = (today - timedelta(days=90)).strftime("%Y-%m-%d")

    # 用 FinLab 取兩個月內處置股歷史（上市+上櫃全包）
    two_months_ago = (today - timedelta(days=60)).strftime("%Y-%m-%d")
    today_date_str = today.strftime("%Y-%m-%d")
    disposal_stocks_2m = {}
    try:
        disp_df = data.get("disposal_information")
        disp_df = data.get("disposal_information")
        for _, row in disp_df.iterrows():
            try:
                sid   = str(row.get("stock_id", "")).strip()
                name  = str(row.get("證券名稱", "")).strip()
                start = str(row.get("處置開始時間", ""))[:10]
                end   = str(row.get("處置結束時間", ""))[:10]
                if not sid or start < two_months_ago:
                    continue
                if not is_valid_stock(sid):
                    continue
                period = f"{start}~{end}" if end else start
                if sid not in disposal_stocks_2m:
                    disposal_stocks_2m[sid] = {"name": name, "period": period}
            except:
                continue
        print(f"FinLab 兩個月內處置股：{len(disposal_stocks_2m)} 檔")
    except Exception as e:
        print(f"FinLab disposal_information 失敗: {e}")

    # 存進全域，供即時策略12使用
    global _global_disposal_2m
    _global_disposal_2m = disposal_stocks_2m

    start_1m = (today - timedelta(days=30)).strftime("%Y-%m-%d")
    end_date = today.strftime("%Y-%m-%d")

    data.date_range = (start_3m, end_date)
    close = data.get("price:收盤價")
    high  = data.get("price:最高價")
    low   = data.get("price:最低價")
    stock_info = data.get("company_basic_info")
    name_dict = stock_info.set_index("stock_id")["公司簡稱"].to_dict()
    industry_dict = stock_info.set_index("stock_id")["產業類別"].to_dict()

    global _global_industry_dict
    _global_industry_dict = industry_dict

    close_df = pd.DataFrame(close.values, index=pd.to_datetime(close.index.astype(str)), columns=close.columns)
    high_df  = pd.DataFrame(high.values,  index=pd.to_datetime(high.index.astype(str)),  columns=high.columns)
    low_df   = pd.DataFrame(low.values,   index=pd.to_datetime(low.index.astype(str)),   columns=low.columns)

    # 釋放原始資料節省記憶體
    del close, high, low, stock_info

    close_3m = close_df[close_df.index >= pd.to_datetime(start_3m)]
    high_3m  = high_df[high_df.index   >= pd.to_datetime(start_3m)]
    low_3m   = low_df[low_df.index     >= pd.to_datetime(start_3m)]

    # 存進全域
    global _global_close_3m, _global_high_3m, _global_low_3m
    _global_close_3m = close_3m
    _global_high_3m  = high_3m
    _global_low_3m   = low_3m

    close_1m = close_df[close_df.index >= pd.to_datetime(start_1m)]

    # 釋放大型 DataFrame 節省記憶體
    del close_df

    def is_strong_day(stock, date, df_close, df_high, df_low, df_open=None):
        """判斷是否為強勢漲停日：一價到底(高低差≤2%) 或 開盤即漲停"""
        try:
            c = df_close[stock].loc[date]
            h = df_high[stock].loc[date]
            l = df_low[stock].loc[date]
            hl_diff = (h - l) / l if l > 0 else 1
            if hl_diff <= 0.02:
                return True
            if df_open is not None:
                o = df_open[stock].loc[date]
                prev_c = df_close[stock].iloc[df_close.index.get_loc(date) - 1]
                if prev_c > 0 and (o - prev_c) / prev_c >= 0.095:
                    return True
        except:
            pass
        return False

    # 策略一：二手紅盤（最近一個月）
    daily_return_1m = close_1m.pct_change()
    is_limit_up = daily_return_1m >= 0.095
    consecutive = is_limit_up & is_limit_up.shift(1)

    s1 = []
    for stock in consecutive.columns:
        dates = consecutive.index[consecutive[stock]]
        for date in dates:
            prev_idx = is_limit_up.index.get_loc(date) - 1
            prev_date = is_limit_up.index[prev_idx]
            s1.append({
                "股票代號": stock, "股票名稱": name_dict.get(stock, ""),
                "產業別": industry_dict.get(stock, ""),
                "第一天漲停日": str(prev_date)[:10], "第二天漲停日": str(date)[:10],
                "第一天收盤": round(close_1m[stock].loc[prev_date], 2),
                "第二天收盤": round(close_1m[stock].loc[date], 2),
                "目前收盤價": round(close_1m[stock].dropna().iloc[-1], 2),
            })
    s1.sort(key=lambda x: x["第二天漲停日"], reverse=True)

    s2 = []  # 策略二已移除

    # 策略三：強勢股回檔（最近3個月內5日漲30%，從高點回檔20%）
    daily_return_3m = close_3m.pct_change()
    s3 = []
    for stock in daily_return_3m.columns:
        series = daily_return_3m[stock].dropna()
        if len(series) < 5:
            continue
        rolling_5 = (1 + series).rolling(5).apply(lambda x: x.prod(), raw=True) - 1
        max_gain = rolling_5.max()
        if max_gain < 0.30:
            continue
        best_end_date = rolling_5.idxmax()
        idx = series.index.get_loc(best_end_date)
        segment = close_3m[stock].iloc[max(0, idx-4):idx+1]
        actual_gain = (segment.iloc[-1] / segment.iloc[0]) - 1
        if actual_gain < 0.30 or segment.index[0] < pd.to_datetime(start_3m):
            continue
        peak_price = segment.max()
        current_price = close_3m[stock].dropna().iloc[-1]
        drawdown = (current_price - peak_price) / peak_price
        if drawdown <= -0.20:
            s3.append({
                "股票代號": stock, "股票名稱": name_dict.get(stock, ""),
                "5日最大漲幅": f"{actual_gain*100:.1f}%",
                "漲幅起始日": str(segment.index[0])[:10],
                "漲幅結束日": str(segment.index[-1])[:10],
                "當時最高價": round(peak_price, 2),
                "目前股價": round(current_price, 2),
                "從高點修正": f"{drawdown*100:.1f}%",
            })
    s3.sort(key=lambda x: float(x["從高點修正"].replace("%", "")))

    # 策略四：三手紅盤（最近一個月，連續三天漲停 或 三天漲幅≥25%，每股只出現一次）
    daily_return_1m = close_1m.pct_change()
    s4_dict = {}
    for stock in daily_return_1m.columns:
        series = daily_return_1m[stock].dropna()
        if len(series) < 3:
            continue
        is_lu = series >= 0.095
        rolling_3 = (1 + series).rolling(3).apply(lambda x: x.prod(), raw=True) - 1
        consec3 = is_lu & is_lu.shift(1) & is_lu.shift(2)

        for date in series.index[rolling_3 >= 0.30]:
            idx = series.index.get_loc(date)
            if idx < 2:
                continue
            d1, d2, d3 = series.index[idx-2], series.index[idx-1], series.index[idx]
            gain = rolling_3.loc[date]
            cond = "連續三天漲停" if (is_lu.loc[d1] and is_lu.loc[d2] and is_lu.loc[d3]) else "三天漲幅≥30%"
            if stock not in s4_dict or gain > float(s4_dict[stock]["三日累積漲幅"].replace("%","")):
                s4_dict[stock] = {
                    "股票代號": stock, "股票名稱": name_dict.get(stock, ""),
                    "產業別": industry_dict.get(stock, ""),
                    "觸發條件": cond,
                    "第一天": str(d1)[:10], "第二天": str(d2)[:10], "第三天": str(d3)[:10],
                    "第一天收盤": round(close_1m[stock].loc[d1], 2),
                    "第二天收盤": round(close_1m[stock].loc[d2], 2),
                    "第三天收盤": round(close_1m[stock].loc[d3], 2),
                    "三日累積漲幅": f"{gain*100:.1f}%",
                    "目前收盤價": round(close_1m[stock].dropna().iloc[-1], 2),
                }

    s4 = list(s4_dict.values())
    s4.sort(key=lambda x: x["第三天"], reverse=True)

    # 策略五：四手紅盤（最近一個月，連續四天漲停 或 四天漲幅≥30%，每股只出現一次）
    s5_dict = {}
    for stock in daily_return_1m.columns:
        series = daily_return_1m[stock].dropna()
        if len(series) < 4:
            continue
        is_lu = series >= 0.095
        rolling_4 = (1 + series).rolling(4).apply(lambda x: x.prod(), raw=True) - 1

        for date in series.index[rolling_4 >= 0.40]:
            idx = series.index.get_loc(date)
            if idx < 3:
                continue
            d1, d2, d3, d4 = series.index[idx-3], series.index[idx-2], series.index[idx-1], series.index[idx]
            gain = rolling_4.loc[date]
            cond = "連續四天漲停" if (is_lu.loc[d1] and is_lu.loc[d2] and is_lu.loc[d3] and is_lu.loc[d4]) else "四天漲幅≥40%"
            if stock not in s5_dict or gain > float(s5_dict[stock]["四日累積漲幅"].replace("%","")):
                s5_dict[stock] = {
                    "股票代號": stock, "股票名稱": name_dict.get(stock, ""),
                    "產業別": industry_dict.get(stock, ""),
                    "觸發條件": cond,
                    "第一天": str(d1)[:10], "第二天": str(d2)[:10], "第三天": str(d3)[:10], "第四天": str(d4)[:10],
                    "第一天收盤": round(close_1m[stock].loc[d1], 2),
                    "第四天收盤": round(close_1m[stock].loc[d4], 2),
                    "四日累積漲幅": f"{gain*100:.1f}%",
                    "目前收盤價": round(close_1m[stock].dropna().iloc[-1], 2),
                }

    s5 = list(s5_dict.values())
    s5.sort(key=lambda x: x["第四天"], reverse=True)

    # 策略六：五手紅盤（最近一個月，五天漲幅≥50%，每支股票只出現一次，保留漲幅最大那段）
    s6_dict = {}
    for stock in daily_return_1m.columns:
        series = daily_return_1m[stock].dropna()
        if len(series) < 5:
            continue

        rolling_5 = (1 + series).rolling(5).apply(lambda x: x.prod(), raw=True) - 1
        dates = series.index[rolling_5 >= 0.50]

        for date in dates:
            idx = series.index.get_loc(date)
            if idx < 4:
                continue
            gain = rolling_5.loc[date]
            # 每支股票只保留漲幅最大的那筆
            if stock not in s6_dict or gain > float(s6_dict[stock]["五日累積漲幅"].replace("%","")):
                d1 = series.index[idx-4]
                d5 = series.index[idx]
                s6_dict[stock] = {
                    "股票代號": stock, "股票名稱": name_dict.get(stock, ""),
                    "產業別": industry_dict.get(stock, ""),
                    "第一天": str(d1)[:10], "第五天": str(d5)[:10],
                    "第一天收盤": round(close_1m[stock].loc[d1], 2),
                    "第五天收盤": round(close_1m[stock].loc[d5], 2),
                    "五日累積漲幅": f"{gain*100:.1f}%",
                    "目前收盤價": round(close_1m[stock].dropna().iloc[-1], 2),
                }

    s6 = list(s6_dict.values())
    s6.sort(key=lambda x: x["第五天"], reverse=True)

    # 去重：股票只出現在最高等級（五手 > 四手 > 三手 > 二手）
    s6_stocks = {x["股票代號"] for x in s6}
    s5_stocks = {x["股票代號"] for x in s5}
    s4_stocks = {x["股票代號"] for x in s4}
    s5 = [x for x in s5 if x["股票代號"] not in s6_stocks]
    s4 = [x for x in s4 if x["股票代號"] not in s6_stocks and x["股票代號"] not in s5_stocks]
    s1 = [x for x in s1 if x["股票代號"] not in s6_stocks and x["股票代號"] not in s5_stocks and x["股票代號"] not in s4_stocks]

    # 策略七：懶載入，點進頁面才計算（避免啟動 timeout）
    s7 = []

    # 策略七B：處置股 — 使用 _disposal_history 今日資料（最完整）
    s7b = []
    try:
        import re
        low_3m = _global_low_3m  # 盤中最低價

        # 用 FinLab 取目前正在處置中的股票（上市+上櫃）
        today_str = date.today().strftime("%Y-%m-%d")
        today_ts  = pd.Timestamp(today_str)
        disposal_today = {}
        try:
            disp_df_now = data.get("disposal_information")
            for _, row in disp_df_now.iterrows():
                try:
                    sid   = str(row.get("stock_id", "")).strip()
                    name  = str(row.get("證券名稱", "")).strip()
                    start = str(row.get("處置開始時間", ""))[:10]
                    end   = str(row.get("處置結束時間", ""))[:10]
                    if not sid or not end or not is_valid_stock(sid):
                        continue
                    if pd.Timestamp(end) < today_ts:
                        continue  # 已出關
                    period = f"{start}~{end}"
                    if sid not in disposal_today:
                        disposal_today[sid] = {"name": name, "period": period}
                except:
                    continue
            print(f"FinLab 即時處置股：{len(disposal_today)} 檔（上市+上櫃）")
        except Exception as e:
            print(f"FinLab disposal_information 失敗: {e}")

        def parse_period(period_str):
            """解析處置期間，支援民國年/西元年、/或-分隔，回傳 (start_ts, end_ts, period_ad)"""
            period_str = period_str.replace(" ", "").replace("～", "~")
            parts = period_str.split("~")
            if len(parts) != 2:
                return None, None, period_str
            def to_ts(s):
                s = s.strip().replace("-", "/")
                p = s.split("/")
                if len(p) != 3:
                    raise ValueError(f"無法解析: {s}")
                y, m, d = p
                if len(y) == 3:  # 民國年
                    return pd.Timestamp(int(y)+1911, int(m), int(d))
                return pd.Timestamp(int(y), int(m), int(d))
            def to_display(s):
                s = s.strip().replace("-", "/")
                p = s.split("/")
                if len(p) == 3 and len(p[0]) == 3:
                    return f"{int(p[0])+1911}/{p[1]}/{p[2]}"
                return s
            try:
                start_ts = to_ts(parts[0])
                end_ts   = to_ts(parts[1])
                period_ad = f"{to_display(parts[0])}~{to_display(parts[1])}"
                return start_ts, end_ts, period_ad
            except Exception as e:
                return None, None, period_str

        for stock_id, info in disposal_today.items():
            try:
                stock_name  = info.get("name", "")
                period_raw  = info.get("period", "")
                start_date, end_date_ts, date_period_ad = parse_period(period_raw)
                if start_date is None or end_date_ts is None:
                    # 嘗試從 stockwarden 補充日期
                    sw_stock = sw_data_shared.get(stock_id, {})
                    if sw_stock:
                        sorted_dates = sorted(sw_stock.keys(), reverse=True)
                        for ann_date in sorted_dates:
                            item = sw_stock[ann_date]
                            k = str(item.get("k", ""))
                            f_date = str(item.get("f", ""))
                            if k and f_date:
                                start_date, end_date_ts, date_period_ad = parse_period(f"{k}～{f_date}")
                                if start_date and end_date_ts:
                                    stock_name = str(item.get("h", stock_name))
                                    break
                    if start_date is None or end_date_ts is None:
                        print(f"  {stock_id} 日期格式錯誤: {repr(period_raw)}")
                        continue
                end_date_str = end_date_ts.strftime("%Y/%m/%d")

                # 過濾已出關的股票（出關日早於今天才過濾）
                if end_date_ts < pd.Timestamp(today.date()):
                    continue

                if stock_id not in close_3m.columns:
                    if stock_id in ["7711", "1591"]:
                        print(f"  [{stock_id}] 不在 close_3m")
                    continue
                prices = close_3m[stock_id].dropna()
                if len(prices) < 20:
                    print(f"  跳過 {stock_id}：資料不足20筆({len(prices)}筆)")
                    continue

                trading_days = prices.index[prices.index >= start_date]
                today_ts = pd.Timestamp(today)
                today_idx = len(trading_days) + 1 if len(trading_days) > 0 and trading_days[-1] < today_ts else len(trading_days)

                print(f"  {stock_id} 開始:{str(start_date)[:10]} 交易天數:{len(trading_days)} 估計今天第{today_idx}天")

                ma10 = prices.rolling(10).mean()
                ma20 = prices.rolling(20).mean()
                hist_price = prices.iloc[-1]
                current_ma10 = ma10.iloc[-1]
                current_ma20 = ma20.iloc[-1]
                # 處置前20日高點（處置開始日不含，取之前最近20個交易日）
                if stock_id in high_3m.columns:
                    h = high_3m[stock_id].dropna()
                    pre_highs = h[h.index < start_date]
                    if len(pre_highs) == 0:
                        # start_date 可能是非交易日，往前找
                        pre_highs = h[h.index <= start_date].iloc[:-1] if len(h[h.index <= start_date]) > 0 else h.iloc[:0]
                    high_10d = pre_highs.iloc[-20:].max() if len(pre_highs) > 0 else h.max()
                else:
                    pre_prices = prices[prices.index < start_date]
                    high_10d = pre_prices.iloc[-20:].max() if len(pre_prices) > 0 else prices.max()

                # 處置期間最低點（用盤中最低價）
                low_day = None
                low_val = None
                if stock_id in low_3m.columns:
                    low_series = low_3m[stock_id].dropna()
                    disposal_lows = low_series[low_series.index >= start_date]
                    if len(disposal_lows) > 0:
                        low_val = round(disposal_lows.min(), 2)
                        low_day_idx = disposal_lows.values.argmin()
                        low_day = low_day_idx + 1  # 第幾天（從1開始）

                low_display = f"{low_val}（第{low_day}天）" if low_val is not None else "-"

                if pd.isna(current_ma10) or pd.isna(current_ma20):
                    continue

                s7b.append({
                    "股票代號": stock_id,
                    "股票名稱": stock_name,
                    "處置期間": date_period_ad,
                    "出關日": end_date_str,
                    "處置第幾天": f"第{today_idx}天",
                    "即時股價": round(hist_price, 2),
                    "昨收": round(hist_price, 2),
                    "處置前高點": round(high_10d, 2),
                    "處置期間最低": low_display,
                    "10日均線": round(current_ma10, 2),
                    "20日均線": round(current_ma20, 2),
                    "_below_ma10": hist_price < current_ma10,
                    "_end_date": end_date_ts,
                    "_stock_id": stock_id,
                })
            except:
                continue

        s7b.sort(key=lambda x: x["_end_date"])

        # 批次抓即時股價（用 TWSE/TPEX 批次 API，速度快）
        s7b_ids = [x["_stock_id"] for x in s7b]
        if s7b_ids:
            # 依市場分組批次抓取
            twse_ids = [f"tse_{sid}.tw" for sid in s7b_ids]
            otc_ids  = [sid for sid in s7b_ids]  # get_tpex_realtime 會自動加 otc_ 前綴
            rt_twse  = get_twse_realtime(twse_ids)
            rt_tpex  = get_tpex_realtime(otc_ids)
            rt_prices = {**rt_twse, **rt_tpex}
            # fallback: 抓不到的用 Fugle
            missing = [sid for sid in s7b_ids if sid not in rt_prices]
            if missing:
                rt_fugle = get_realtime_prices(missing)
                rt_prices.update(rt_fugle)
            for item in s7b:
                item.pop("_end_date", None)
                sid = item.pop("_stock_id")
                rt = rt_prices.get(sid, {})
                rt_price = rt.get("price", None)
                item["即時股價"] = rt_price if rt_price else item["昨收"]

                # 用即時股價重新計算10/20日均線（把今天即時價接在歷史序列後面）
                if rt_price and sid in close_3m.columns:
                    try:
                        hist = close_3m[sid].dropna()
                        today_ts = pd.Timestamp(datetime.today().date())
                        if hist.index[-1] < today_ts:
                            new_row = pd.Series([rt_price], index=[today_ts])
                            prices_with_today = pd.concat([hist, new_row])
                        else:
                            prices_with_today = hist.copy()
                            prices_with_today.iloc[-1] = rt_price
                        new_ma10 = round(prices_with_today.rolling(10).mean().iloc[-1], 2)
                        new_ma20 = round(prices_with_today.rolling(20).mean().iloc[-1], 2)
                        if sid in high_3m.columns:
                            h = high_3m[sid].dropna()
                            hist_high = h.iloc[-20:].max() if len(h) >= 20 else h.max()
                        else:
                            hist_high = prices_with_today.iloc[-20:].max()
                        high_10d = round(max(hist_high, rt_price), 2)
                        item["10日均線"] = new_ma10
                        item["20日均線"] = new_ma20
                        item["處置前高點"] = high_10d
                        # 處置期間最低：即時更新當天最低（保留原有格式不變）
                        pass  # 處置期間最低已在初始計算時設定，即時不重算
                        item["_below_ma10"] = rt_price < new_ma10
                    except Exception as e:
                        print(f"重新計算均線失敗 {sid}: {e}")

        print(f"處置第五天: {len(s7b)}筆")
    except Exception as e:
        print(f"處置第五天錯誤: {e}")
        s7b = []

    # 存進全域供監控頁面使用
    global _global_s1, _global_s3, _global_s4, _global_s5, _global_s6, _global_s7
    _global_s1  = s1
    _global_s3  = s3
    _global_s4  = s4
    _global_s5  = s5
    _global_s6  = s6
    _global_s7  = s7

    return s1, s2, s3, s4, s5, s6, s7, s7b



# 快取資料
_cache = {"data": None, "time": None}
_global_disposal_2m = {}
_global_close_3m = None
_global_high_3m = None
_global_low_3m = None
_global_s1 = []
_global_s3 = []
_global_s4 = []
_global_s5 = []
_global_s6 = []
_global_s7 = []

def get_cached_data():
    now = datetime.now()
    if _cache["data"] is None or (now - _cache["time"]).total_seconds() > 1800:
        _cache["data"] = get_all_data()
        _cache["time"] = now
    return _cache["data"]

@app.route("/")
def home():
    s1, s2, s3, s4, s5, s6, s7, s7b = get_cached_data()
    update_time = datetime.now().strftime("%Y-%m-%d %H:%M")
    return render_template_string(HOME_TEMPLATE, counts=[len(s1), len(s3), len(s4), len(s5), len(s6), len(s7), len(s7b)], update_time=update_time)


# 策略七獨立快取（懶載入，只有點進去才算）
_s7_cache = {"data": None, "time": None}

def get_s7_data():
    """懶載入策略七：近兩個月處置股"""
    now = datetime.now()
    if _s7_cache["data"] is not None and (now - _s7_cache["time"]).total_seconds() < 1800:
        return _s7_cache["data"]

    s7 = []
    try:
        disposal_stocks_2m = _global_disposal_2m
        close_3m = _global_close_3m
        high_3m  = _global_high_3m

        if not disposal_stocks_2m or close_3m is None:
            return s7

        for stock_id, info in disposal_stocks_2m.items():
            try:
                if stock_id not in close_3m.columns:
                    continue
                prices = close_3m[stock_id].dropna()
                if len(prices) < 20:
                    continue

                ma10 = prices.rolling(10).mean()
                ma20 = prices.rolling(20).mean()
                hist_price = prices.iloc[-1]
                current_ma10 = ma10.iloc[-1]
                current_ma20 = ma20.iloc[-1]
                two_m_ago = pd.Timestamp(datetime.today().date()) - pd.Timedelta(days=60)
                if high_3m is not None and stock_id in high_3m.columns:
                    highs = high_3m[stock_id].dropna()
                    high_2m = highs[highs.index >= two_m_ago].max()
                else:
                    high_2m = prices[prices.index >= two_m_ago].max()

                if pd.isna(current_ma10) or pd.isna(current_ma20):
                    continue

                # 過濾20元以下
                if hist_price < 20:
                    continue

                # 處置期間（民國轉西元）
                period_raw = info.get("period", "")
                try:
                    import re as _re
                    period_ad = _re.sub(r'(\d{3})/', lambda m: str(int(m.group(1))+1911)+'/', period_raw)
                except:
                    period_ad = period_raw

                s7.append({
                    "股票代號": stock_id,
                    "股票名稱": info.get("name", ""),
                    "處置期間": period_ad,
                    "昨收": round(hist_price, 2),
                    "2月高點": round(high_2m, 2),
                    "10日均線": round(current_ma10, 2),
                    "20日均線": round(current_ma20, 2),
                    "_below_ma10": hist_price < current_ma10,
                    "_stock_id": stock_id,
                })
            except:
                continue

        s7.sort(key=lambda x: x["股票代號"])

        # 批次抓即時股價，重新計算均線
        s7_ids = [x["_stock_id"] for x in s7]
        if s7_ids:
            rt_prices = get_realtime_prices(s7_ids)
            for item in s7:
                sid = item.pop("_stock_id")
                rt = rt_prices.get(sid, {})
                rt_price = rt.get("price", None)
                item["即時股價"] = rt_price if rt_price else item["昨收"]

                if rt_price and sid in close_3m.columns:
                    try:
                        hist = close_3m[sid].dropna()
                        today_ts = pd.Timestamp(datetime.today().date())
                        if hist.index[-1] < today_ts:
                            new_row = pd.Series([rt_price], index=[today_ts])
                            prices_with_today = pd.concat([hist, new_row])
                        else:
                            prices_with_today = hist.copy()
                            prices_with_today.iloc[-1] = rt_price
                        new_ma10 = round(prices_with_today.rolling(10).mean().iloc[-1], 2)
                        new_ma20 = round(prices_with_today.rolling(20).mean().iloc[-1], 2)
                        two_m_ago = pd.Timestamp(datetime.today().date()) - pd.Timedelta(days=60)
                        if high_3m is not None and sid in high_3m.columns:
                            highs = high_3m[sid].dropna()
                            hist_high = highs[highs.index >= two_m_ago].max()
                        else:
                            hist_high = prices_with_today[prices_with_today.index >= two_m_ago].max()
                        # 和今日即時價比較取最大
                        new_high = round(max(hist_high, rt_price), 2)
                        item["10日均線"] = new_ma10
                        item["20日均線"] = new_ma20
                        item["2月高點"] = new_high
                        item["_below_ma10"] = rt_price < new_ma10
                    except Exception as e:
                        print(f"策略七重新計算均線失敗 {sid}: {e}")

        print(f"近兩個月處置股（懶載入）: {len(s7)}筆")
    except Exception as e:
        print(f"策略七懶載入錯誤: {e}")
        s7 = []

    _s7_cache["data"] = s7
    _s7_cache["time"] = now
    return s7

@app.route("/strategy/<int:sid>")
def strategy(sid):
    s1, s2, s3, s4, s5, s6, s7, s7b = get_cached_data()
    update_time = _cache["time"].strftime("%Y-%m-%d %H:%M") if _cache["time"] else datetime.now().strftime("%Y-%m-%d %H:%M")

    strategies = {
        1: {"title": "二手紅盤", "icon": "🔥", "desc": "最近一個月內，連續兩個交易日漲停的股票，依日期由新到舊排列",
            "stocks": s1, "columns": ["股票代號", "股票名稱", "產業別", "第一天漲停日", "第二天漲停日", "第一天收盤", "第二天收盤", "目前收盤價"]},
        3: {"title": "強勢股回檔", "icon": "📉", "desc": "最近3個月內任意5日漲幅≥30%，且目前從高點修正≥20%，修正最多的在前",
            "stocks": s3, "columns": ["股票代號", "股票名稱", "5日最大漲幅", "漲幅起始日", "漲幅結束日", "當時最高價", "目前股價", "從高點修正"]},
        4: {"title": "三手紅盤", "icon": "🀄", "desc": "最近一個月內，連續三天漲停 或 連續三天累積漲幅≥30%，依日期由新到舊排列",
            "stocks": s4, "columns": ["股票代號", "股票名稱", "產業別", "觸發條件", "第一天", "第二天", "第三天", "第一天收盤", "第二天收盤", "第三天收盤", "三日累積漲幅", "目前收盤價"]},
        5: {"title": "四手紅盤", "icon": "🎰", "desc": "最近一個月內，連續四天漲停 或 連續四天累積漲幅≥40%，依日期由新到舊排列",
            "stocks": s5, "columns": ["股票代號", "股票名稱", "產業別", "觸發條件", "第一天", "第二天", "第三天", "第四天", "第一天收盤", "第四天收盤", "四日累積漲幅", "目前收盤價"]},
        6: {"title": "五手紅盤", "icon": "🔴", "desc": "最近一個月內，連續五天累積漲幅≥50%，依日期由新到舊排列",
            "stocks": s6, "columns": ["股票代號", "股票名稱", "產業別", "第一天", "第五天", "第一天收盤", "第五天收盤", "五日累積漲幅", "目前收盤價"]},
        7: None,  # 懶載入，下方單獨處理
        14: {"title": "處置股", "icon": "📅", "desc": "目前正在被處置的股票，最快出關的在前",
            "stocks": s7b, "columns": ["股票代號", "股票名稱", "處置期間", "出關日", "處置第幾天", "即時股價", "昨收", "處置前高點", "處置期間最低", "10日均線", "20日均線"],
            "below_ma10_ids": {x["股票代號"] for x in s7b if x.get("_below_ma10")}},
    }

    if sid not in strategies:
        return "找不到此策略", 404

    if sid == 7:
        s7_lazy = get_s7_data()
        s = {
            "title": "近兩個月處置股", "icon": "⚠️",
            "desc": "近兩個月曾被處置的股票，顯示即時股價、兩個月高點、10日線、20日線，紅底為跌破10日線",
            "stocks": s7_lazy,
            "columns": ["股票代號", "股票名稱", "處置期間", "即時股價", "昨收", "2月高點", "10日均線", "20日均線"],
            "below_ma10_ids": {x["股票代號"] for x in s7_lazy if x.get("_below_ma10")},
        }
    else:
        s = strategies[sid]

    s.setdefault('below_ma10_ids', set())
    return render_template_string(DETAIL_TEMPLATE, update_time=update_time, **s)

TELEGRAM_TOKEN = "8721511256:AAFVhKoVQgfu43288ivwVaLxgoIVNFRtXKs"
TELEGRAM_CHAT_ID = "7449081850"

def send_telegram(msg):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "HTML"}, timeout=10)
    except Exception as e:
        print(f"Telegram 發送失敗: {e}")

_notified_today = {}  # {股票代號: 日期} 防止重複通知

def check_and_notify_s7():
    """每5分鐘檢查策略7：即時股價 <= 2月高點 * 0.82 就發 Telegram（每天每檔只通知一次）"""
    global _notified_today
    today_str = date.today().strftime("%Y-%m-%d")
    _notified_today = {k: v for k, v in _notified_today.items() if v == today_str}

    now = datetime.now()
    if not (9 <= now.hour < 13 or (now.hour == 13 and now.minute <= 35)):
        return

    try:
        s7 = get_s7_data()
        alerts = []
        for stock in s7:
            sid = stock["股票代號"]
            if _notified_today.get(sid) == today_str:
                continue
            price = stock.get("即時股價", 0)
            high = stock.get("2月高點", 0)
            if high > 0 and price > 0 and price <= high * 0.82:
                drop_pct = (price - high) / high * 100
                name = stock["股票名稱"]
                ma10 = stock.get("10日均線", "-")
                ma20 = stock.get("20日均線", "-")
                # 判斷是否還在處置中（用 disposal_stocks_2m 判斷）
                is_active = sid in _global_disposal_2m
                status = "🔴 處置中" if is_active else "⚪ 已結束"
                line = f"{status} <b>{sid} {name}</b>\n即時價: {price} | 2月高點: {high} | 跌幅: {drop_pct:.1f}%\n10日線: {ma10} | 20日線: {ma20}"
                alerts.append(line)
                _notified_today[sid] = today_str
        if alerts:
            msg = "\U0001F4C9 <b>處置股跌破高點82%警示</b>\n\n" + "\n\n".join(alerts)
            send_telegram(msg)
            print(f"[Telegram] 發送 {len(alerts)} 筆警示")
    except Exception as e:
        print(f"check_and_notify_s7 錯誤: {e}")

# 啟動排程器：每天 14:30 自動更新處置股資料
scheduler = BackgroundScheduler(timezone="Asia/Taipei")
scheduler.add_job(update_disposal_history, "cron", hour=14, minute=30)
scheduler.add_job(refresh_disposal_from_github, "cron", hour=14, minute=35)  # 本機push後Railway自動同步
scheduler.add_job(lambda: (_cache.update({"data": None, "time": None}), _s7_cache.update({"data": None, "time": None})), "cron", hour=15, minute=0)
scheduler.add_job(check_and_notify_s7, "interval", minutes=5)  # 每5分鐘檢查一次
scheduler.start()

# 啟動時立刻從 GitHub 載入最新處置股資料
refresh_disposal_from_github()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"🚀 啟動中，請用瀏覽器開啟 http://127.0.0.1:{port}")
    app.run(host="0.0.0.0", port=port, debug=False)
