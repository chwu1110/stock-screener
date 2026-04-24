import os
import finlab
from finlab import data
import pandas as pd
from datetime import datetime, timedelta
import json
import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
from flask import Flask, render_template_string

app = Flask(__name__)

FINLAB_API_KEY = os.environ.get("FINLAB_API_KEY", "LBmwu3n0/lor77y1Z0aBH/Q0WBI6+bLJrA2TlchZAM1jb6jJaURRbaQRZRWjozwP#vip_m")

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
        <a href="/strategy/2" class="card">
            <div class="card-icon">⚡</div>
            <div class="card-title">跌停翻漲停</div>
            <div class="card-desc">2026/1/1起，單日開盤跌停、收盤漲停的股票</div>
            <div class="card-count">{{ counts[1] }}</div>
            <div class="card-count-label">符合股票數</div>
        </a>
        <a href="/strategy/3" class="card">
            <div class="card-icon">📉</div>
            <div class="card-title">強勢股回檔</div>
            <div class="card-desc">最近3個月內任意5日漲幅≥30%，且目前從高點修正≥20%</div>
            <div class="card-count">{{ counts[2] }}</div>
            <div class="card-count-label">符合股票數</div>
        </a>
        <a href="/strategy/4" class="card">
            <div class="card-icon">🀄</div>
            <div class="card-title">三手紅盤</div>
            <div class="card-desc">最近一個月內，連續三天漲停 或 連續三天累積漲幅≥30%</div>
            <div class="card-count">{{ counts[3] }}</div>
            <div class="card-count-label">符合股票數</div>
        </a>
        <a href="/strategy/5" class="card">
            <div class="card-icon">🎰</div>
            <div class="card-title">四手紅盤</div>
            <div class="card-desc">最近一個月內，連續四天漲停 或 連續四天累積漲幅≥40%</div>
            <div class="card-count">{{ counts[4] }}</div>
            <div class="card-count-label">符合股票數</div>
        </a>
        <a href="/strategy/6" class="card">
            <div class="card-icon">🔴</div>
            <div class="card-title">五手紅盤</div>
            <div class="card-desc">最近一個月內，連續五天累積漲幅≥50%</div>
            <div class="card-count">{{ counts[5] }}</div>
            <div class="card-count-label">符合股票數</div>
        </a>
        <a href="/strategy/7" class="card">
            <div class="card-icon">⚠️</div>
            <div class="card-title">處置股跌破10日線</div>
            <div class="card-desc">目前正在被處置的股票，且收盤價跌破10日均線</div>
            <div class="card-count">{{ counts[6] }}</div>
            <div class="card-count-label">符合股票數</div>
        </a>
        <a href="/strategy/10" class="card">
            <div class="card-icon">🔻</div>
            <div class="card-title">處置股拉回</div>
            <div class="card-desc">兩個月內曾被處置的股票，連續下跌5天</div>
            <div class="card-count">{{ counts[9] }}</div>
            <div class="card-count-label">符合股票數</div>
        </a>
        <a href="/strategy/12" class="card">
            <div class="card-icon">📊</div>
            <div class="card-title">處置股來到月線</div>
            <div class="card-desc">兩個月內曾被處置的股票，股價在20日均線上下3%以內</div>
            <div class="card-count">{{ counts[11] }}</div>
            <div class="card-count-label">符合股票數</div>
            <div style="margin-top:10px;font-size:12px;color:#38bdf8;">🔴 <a href="/strategy/12/realtime" style="color:#38bdf8;">即時版（盤中）</a></div>
        </a>
    </div>

    <div class="section-title">🏪 興櫃專區</div>
    <div class="grid">
        <a href="/strategy/8" class="card card-emerging">
            <div class="card-icon">🚀</div>
            <div class="card-title">興櫃爆量強漲</div>
            <div class="card-desc">興櫃股票當日成交量≥5日均量10倍、成交≥500張、漲幅≥30%</div>
            <div class="card-count">{{ counts[7] }}</div>
            <div class="card-count-label">符合股票數</div>
        </a>
        <a href="/strategy/9" class="card card-emerging">
            <div class="card-icon">📉</div>
            <div class="card-title">興櫃當天拉回</div>
            <div class="card-desc">興櫃股票當天從最高點拉回幅度≥25%</div>
            <div class="card-count">{{ counts[8] }}</div>
            <div class="card-count-label">符合股票數</div>
        </a>
        <a href="/strategy/11" class="card card-emerging">
            <div class="card-icon">💥</div>
            <div class="card-title">興櫃突破平台</div>
            <div class="card-desc">今天漲幅≥10%、突破前兩天高點、前30天盤整區間≤5%</div>
            <div class="card-count">{{ counts[10] }}</div>
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
        .stat-box { display: inline-block; background: #1e293b; border-radius: 10px; padding: 8px 20px; margin-bottom: 20px; }
        .stat-box .num { font-size: 22px; font-weight: bold; color: #38bdf8; }
        .stat-box .label { font-size: 12px; color: #94a3b8; }
        table { width: 100%; border-collapse: collapse; background: #1e293b; border-radius: 12px; overflow: hidden; }
        thead tr { background: #0f172a; }
        th { padding: 12px 16px; text-align: left; font-size: 13px; color: #94a3b8; font-weight: 600; }
        td { padding: 11px 16px; font-size: 14px; border-top: 1px solid #334155; }
        tr:hover td { background: #263548; }
        .gain { color: #4ade80; font-weight: bold; }
        .loss { color: #f87171; font-weight: bold; }
        .stock-id { color: #38bdf8; font-weight: bold; }
        .empty { text-align: center; color: #94a3b8; padding: 40px; background: #1e293b; border-radius: 12px; }
        .updated { text-align: center; color: #475569; font-size: 12px; margin-top: 20px; }
    </style>
</head>
<body>
    <a href="/" class="back">← 返回首頁</a>
    <h1>{{ icon }} {{ title }}</h1>
    <p class="subtitle">{{ desc }}</p>

    <div class="stat-box">
        <div class="num">{{ stocks|length }}</div>
        <div class="label">符合股票數</div>
    </div>

    {% if stocks %}
    <table>
        <thead>
            <tr>
                {% for col in columns %}
                <th>{{ col }}</th>
                {% endfor %}
            </tr>
        </thead>
        <tbody>
            {% for s in stocks %}
            <tr>
                {% for col in columns %}
                <td class="
                    {% if col == '股票代號' %}stock-id
                    {% elif '漲幅' in col or '收盤' in col or '漲停' in col %}gain
                    {% elif '修正' in col or '開盤' in col %}loss
                    {% endif %}
                ">{{ s[col] }}</td>
                {% endfor %}
            </tr>
            {% endfor %}
        </tbody>
    </table>
    {% else %}
    <div class="empty">❌ 沒有找到符合條件的股票</div>
    {% endif %}

    <p class="updated">資料來源：FinLab｜更新時間：{{ update_time }}</p>
</body>
</html>
"""

REALTIME_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>📊 處置股來到月線（即時）</title>
    <meta http-equiv="refresh" content="300">
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: 'Microsoft JhengHei', sans-serif; background: #0f172a; color: #e2e8f0; padding: 30px; }
        .back { display: inline-block; margin-bottom: 20px; color: #38bdf8; text-decoration: none; font-size: 14px; }
        .back:hover { text-decoration: underline; }
        h1 { font-size: 22px; margin-bottom: 6px; color: #f8fafc; }
        .subtitle { color: #94a3b8; font-size: 13px; margin-bottom: 8px; }
        .badge { display: inline-block; background: #1e3a5f; color: #38bdf8; border-radius: 6px; padding: 3px 10px; font-size: 12px; margin-bottom: 20px; }
        .stat-box { display: inline-block; background: #1e293b; border-radius: 10px; padding: 8px 20px; margin-bottom: 20px; }
        .stat-box .num { font-size: 22px; font-weight: bold; color: #38bdf8; }
        .stat-box .label { font-size: 12px; color: #94a3b8; }
        table { width: 100%; border-collapse: collapse; background: #1e293b; border-radius: 12px; overflow: hidden; }
        thead tr { background: #0f172a; }
        th { padding: 12px 16px; text-align: left; font-size: 13px; color: #94a3b8; font-weight: 600; }
        td { padding: 11px 16px; font-size: 14px; border-top: 1px solid #334155; }
        tr:hover td { background: #263548; }
        .stock-id { color: #38bdf8; font-weight: bold; }
        .gain { color: #4ade80; font-weight: bold; }
        .loss { color: #f87171; font-weight: bold; }
        .empty { text-align: center; color: #94a3b8; padding: 40px; background: #1e293b; border-radius: 12px; }
        .updated { text-align: center; color: #475569; font-size: 12px; margin-top: 20px; }
        .countdown { text-align: center; color: #64748b; font-size: 12px; margin-top: 6px; }
    </style>
    <script>
        let secs = 300;
        setInterval(() => {
            secs--;
            const el = document.getElementById('cd');
            if (el) el.textContent = secs + ' 秒後自動刷新';
            if (secs <= 0) location.reload();
        }, 1000);
    </script>
</head>
<body>
    <a href="/" class="back">← 返回首頁</a>
    <h1>📊 處置股來到月線</h1>
    <p class="subtitle">兩個月內曾被處置的股票，即時股價在20日均線上下3%以內，偏離最小的在前</p>
    <div class="badge">🔴 即時模式｜每5分鐘自動更新</div><br>

    <div class="stat-box">
        <div class="num">{{ stocks|length }}</div>
        <div class="label">符合股票數</div>
    </div>

    {% if stocks %}
    <table>
        <thead>
            <tr>
                <th>股票代號</th><th>股票名稱</th><th>產業別</th><th>處置期間</th>
                <th>即時股價</th><th>20日均線</th><th>偏離幅度</th><th>資料時間</th>
            </tr>
        </thead>
        <tbody>
            {% for s in stocks %}
            <tr>
                <td class="stock-id">{{ s['股票代號'] }}</td>
                <td>{{ s['股票名稱'] }}</td>
                <td>{{ s['產業別'] }}</td>
                <td>{{ s['處置期間'] }}</td>
                <td class="{{ 'gain' if s['偏離幅度'][0] != '-' else 'loss' }}">{{ s['即時股價'] }}</td>
                <td>{{ s['20日均線'] }}</td>
                <td class="{{ 'gain' if s['偏離幅度'][0] != '-' else 'loss' }}">{{ s['偏離幅度'] }}</td>
                <td>{{ s['資料時間'] }}</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
    {% else %}
    <div class="empty">❌ 目前沒有處置股來到月線（即時股價更新中...）</div>
    {% endif %}

    <p class="updated">MA20 來源：FinLab｜即時股價：證交所／櫃買｜更新時間：{{ update_time }}</p>
    <p class="countdown" id="cd">300 秒後自動刷新</p>
</body>
</html>
"""

# ========== 即時股價快取 ==========
_realtime_cache = {"prices": {}, "time": None}
_ma20_cache = {"data": {}, "time": None}  # {stock_id: ma20_value}

def get_twse_realtime(stock_ids):
    """從證交所抓上市即時股價，一次最多50檔"""
    prices = {}
    try:
        ids_str = "|".join(stock_ids)
        url = f"https://mis.twse.com.tw/stock/api/getStockInfo.jsp?ex_ch={ids_str}&json=1&delay=0"
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(url, headers=headers, timeout=10)
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
        resp = requests.get(url, headers=headers, timeout=10)
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

def get_realtime_prices(stock_ids):
    """抓所有處置股的即時股價（自動判斷上市/上櫃）"""
    now = datetime.now()
    # 非交易時間直接回傳空
    if now.weekday() >= 5:
        return {}
    if not (9 <= now.hour < 13 or (now.hour == 13 and now.minute <= 30)):
        return {}

    # 5分鐘快取
    if _realtime_cache["time"] and (now - _realtime_cache["time"]).seconds < 300:
        return _realtime_cache["prices"]

    prices = {}
    # 全部先試上市，再試上櫃（同一個API，用 tse_ 或 otc_ 前綴）
    # 分批處理（每批50檔）
    twse_ids = [f"tse_{sid}.tw" for sid in stock_ids]
    tpex_ids = [f"otc_{sid}.tw" for sid in stock_ids]

    batch_size = 50
    now_str = datetime.now().strftime("%H:%M")

    for batch in [twse_ids[i:i+batch_size] for i in range(0, len(twse_ids), batch_size)]:
        try:
            ids_str = "|".join(batch)
            url = f"https://mis.twse.com.tw/stock/api/getStockInfo.jsp?ex_ch={ids_str}&json=1&delay=0"
            resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
            for item in resp.json().get("msgArray", []):
                sid = item.get("c", "")
                p = item.get("z", "-")
                if p and p != "-":
                    try:
                        prices[sid] = {"price": float(p), "time": now_str}
                    except:
                        pass
        except:
            pass

    # 沒抓到的再試上櫃
    missing = [sid for sid in stock_ids if sid not in prices]
    for batch in [missing[i:i+batch_size] for i in range(0, len(missing), batch_size)]:
        try:
            ids_str = "|".join([f"otc_{sid}.tw" for sid in batch])
            url = f"https://mis.twse.com.tw/stock/api/getStockInfo.jsp?ex_ch={ids_str}&json=1&delay=0"
            resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
            for item in resp.json().get("msgArray", []):
                sid = item.get("c", "")
                p = item.get("z", "-")
                if p and p != "-":
                    try:
                        prices[sid] = {"price": float(p), "time": now_str}
                    except:
                        pass
        except:
            pass

    _realtime_cache["prices"] = prices
    _realtime_cache["time"] = now
    print(f"即時股價: 抓到 {len(prices)}/{len(stock_ids)} 檔")
    return prices

def get_ma20_cache(disposal_stocks_2m, close_3m):
    """計算並快取所有處置股的 MA20，30分鐘更新一次"""
    now = datetime.now()
    if _ma20_cache["time"] and (now - _ma20_cache["time"]).seconds < 1800:
        return _ma20_cache["data"]

    ma20_dict = {}
    for stock_id in disposal_stocks_2m:
        try:
            if stock_id not in close_3m.columns:
                continue
            prices = close_3m[stock_id].dropna()
            if len(prices) < 20:
                continue
            ma20 = prices.rolling(20).mean().iloc[-1]
            if pd.isna(ma20) or ma20 <= 0:
                continue
            ma20_dict[stock_id] = round(ma20, 2)
        except:
            continue

    _ma20_cache["data"] = ma20_dict
    _ma20_cache["time"] = now
    print(f"MA20 快取更新: {len(ma20_dict)} 檔")
    return ma20_dict


def get_all_data():
    finlab.login(FINLAB_API_KEY)

    today = datetime.today()
    start_2026 = "2026-01-01"
    start_1yr = (today - timedelta(days=90)).strftime("%Y-%m-%d")  # 改為3個月，加快速度
    start_3m = (today - timedelta(days=90)).strftime("%Y-%m-%d")

    # 載入處置股歷史資料（由 save_disposal.py 每天更新）
    disposal_history = {}
    try:
        history_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "disposal_history.json")
        print(f"處置股歷史路徑: {history_path}, 存在: {os.path.exists(history_path)}")
        if os.path.exists(history_path):
            with open(history_path, "r", encoding="utf-8") as f:
                disposal_history = json.load(f)
            print(f"處置股歷史天數: {len(disposal_history)}, 含7721: {'7721' in str(disposal_history)}")
    except Exception as e:
        print(f"讀取處置股歷史失敗: {e}")

    # 整合兩個月內的歷史處置股
    two_months_ago = (today - timedelta(days=60)).strftime("%Y-%m-%d")
    disposal_stocks_2m = {}
    for date_str, stocks in disposal_history.items():
        if date_str >= two_months_ago:
            for sid, info in stocks.items():
                if sid not in disposal_stocks_2m:
                    disposal_stocks_2m[sid] = info
    print(f"兩個月內處置股數: {len(disposal_stocks_2m)}, 含7721: {'7721' in disposal_stocks_2m}")

    # 存進全域，供即時策略12使用
    global _global_disposal_2m
    _global_disposal_2m = disposal_stocks_2m

    start_1m = (today - timedelta(days=30)).strftime("%Y-%m-%d")
    end_date = today.strftime("%Y-%m-%d")

    data.date_range = (start_3m, end_date)

    close = data.get("price:收盤價")
    open_ = data.get("price:開盤價")
    stock_info = data.get("company_basic_info")
    name_dict = stock_info.set_index("stock_id")["公司簡稱"].to_dict()
    industry_dict = stock_info.set_index("stock_id")["產業類別"].to_dict()

    global _global_industry_dict
    _global_industry_dict = industry_dict

    close_df = pd.DataFrame(close.values, index=pd.to_datetime(close.index.astype(str)), columns=close.columns)
    open_df = pd.DataFrame(open_.values, index=pd.to_datetime(open_.index.astype(str)), columns=open_.columns)

    close_1yr = close_df[close_df.index >= pd.to_datetime(start_1yr)]
    close_3m = close_df[close_df.index >= pd.to_datetime(start_3m)]

    # 存進全域，供即時策略12使用
    global _global_close_3m
    _global_close_3m = close_3m

    close_1m = close_df[close_df.index >= pd.to_datetime(start_1m)]
    close_2026 = close_df[close_df.index >= pd.to_datetime(start_2026)]
    open_2026 = open_df[open_df.index >= pd.to_datetime(start_2026)]

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
                "第一天漲停日": str(prev_date)[:10], "第二天漲停日": str(date)[:10],
                "第一天收盤": round(close_1m[stock].loc[prev_date], 2),
                "第二天收盤": round(close_1m[stock].loc[date], 2),
            })
    s1.sort(key=lambda x: x["第二天漲停日"], reverse=True)

    # 策略二：跌停開→漲停收
    daily_return_2026 = close_2026.pct_change()
    prev_close = close_2026.shift(1)
    open_change = (open_2026 - prev_close) / prev_close
    reversal = (open_change <= -0.095) & (daily_return_2026 >= 0.095)

    s2 = []
    for stock in reversal.columns:
        dates = reversal.index[reversal[stock]]
        for date in dates:
            prev_idx = close_2026.index.get_loc(date) - 1
            prev_close_price = close_2026[stock].iloc[prev_idx] if prev_idx >= 0 else None
            s2.append({
                "股票代號": stock, "股票名稱": name_dict.get(stock, ""),
                "發生日期": str(date)[:10],
                "開盤價": round(open_2026[stock].loc[date], 2),
                "收盤價": round(close_2026[stock].loc[date], 2),
                "前日收盤": round(prev_close_price, 2) if prev_close_price else "-",
            })
    s2.sort(key=lambda x: x["發生日期"], reverse=True)

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
                    "觸發條件": cond,
                    "第一天": str(d1)[:10], "第二天": str(d2)[:10], "第三天": str(d3)[:10],
                    "第一天收盤": round(close_1m[stock].loc[d1], 2),
                    "第二天收盤": round(close_1m[stock].loc[d2], 2),
                    "第三天收盤": round(close_1m[stock].loc[d3], 2),
                    "三日累積漲幅": f"{gain*100:.1f}%",
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
                    "觸發條件": cond,
                    "第一天": str(d1)[:10], "第二天": str(d2)[:10], "第三天": str(d3)[:10], "第四天": str(d4)[:10],
                    "第一天收盤": round(close_1m[stock].loc[d1], 2),
                    "第四天收盤": round(close_1m[stock].loc[d4], 2),
                    "四日累積漲幅": f"{gain*100:.1f}%",
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
                    "第一天": str(d1)[:10], "第五天": str(d5)[:10],
                    "第一天收盤": round(close_1m[stock].loc[d1], 2),
                    "第五天收盤": round(close_1m[stock].loc[d5], 2),
                    "五日累積漲幅": f"{gain*100:.1f}%",
                }

    s6 = list(s6_dict.values())
    s6.sort(key=lambda x: x["第五天"], reverse=True)

    # 策略七：處置股跌破10日線（每次跌破列一筆）
    s7 = []
    try:
        # 抓取目前處置股清單
        disposal_url = "https://www.twse.com.tw/rwd/zh/announcement/punish?response=json"
        disposal_res = requests.get(disposal_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10, verify=False)
        disposal_data = disposal_res.json()

        disposal_stocks = {}
        if disposal_data.get("stat") == "OK":
            for row in disposal_data.get("data", []):
                try:
                    stock_id = row[2].strip()
                    stock_name = row[3].strip()
                    period = row[5].strip() if len(row) > 5 else ""
                    disposal_stocks[stock_id] = {"name": stock_name, "period": period}
                except:
                    continue

        def roc_to_date(s):
            y, m, d = s.split("/")
            return pd.Timestamp(int(y)+1911, int(m), int(d))

        # 每次跌破都列一筆
        for stock_id, info in disposal_stocks.items():
            try:
                if stock_id not in close_3m.columns:
                    continue
                prices = close_3m[stock_id].dropna()
                if len(prices) < 10:
                    continue

                ma10 = prices.rolling(10).mean()

                # 解析處置期間（民國年轉西元年）
                period = info.get("period", "")
                disposal_start = None
                disposal_end = None
                try:
                    parts = period.replace(" ", "").split("~")
                    if len(parts) == 2:
                        disposal_start = roc_to_date(parts[0])
                        disposal_end = roc_to_date(parts[1])
                except:
                    pass

                # 找處置期間內每一天跌破10日線的紀錄
                for date, price in prices.items():
                    ma = ma10.get(date)
                    if pd.isna(ma):
                        continue
                    # 只看處置期間內
                    if disposal_start and disposal_end:
                        if not (disposal_start <= date <= disposal_end):
                            continue
                    if price < ma:
                        diff_pct = (price - ma) / ma
                        s7.append({
                            "股票代號": stock_id,
                            "股票名稱": info["name"],
                            "處置期間": period,
                            "跌破日期": str(date)[:10],
                            "收盤價": round(price, 2),
                            "10日均線": round(ma, 2),
                            "跌破幅度": f"{diff_pct*100:.1f}%",
                        })
            except:
                continue

        # 依股票代號、日期排序
        s7.sort(key=lambda x: (x["股票代號"], x["跌破日期"]))

    except Exception as e:
        print(f"處置股API失敗: {e}")
        s7 = []


    # 策略八：興櫃爆量強漲（用公開API抓今日資料）
    s8 = []
    try:
        def _esb_float(val):
            s = str(val).replace(",", "").strip()
            return float(s) if s and s not in ["-", "--", ""] else 0.0

        # 抓今日即時資料
        esb_url = "https://www.tpex.org.tw/openapi/v1/tpex_esb_latest_statistics"
        esb_h = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}
        r8 = requests.get(esb_url, headers=esb_h, timeout=15, verify=False)
        esb_today = {}
        for item in r8.json():
            sid = str(item.get("SecuritiesCompanyCode","")).strip()
            if not sid or not sid.isdigit(): continue
            prev = _esb_float(item.get("PreviousAveragePrice",0))
            latest = _esb_float(item.get("LatestPrice",0))
            high = _esb_float(item.get("Highest",0))
            vol = _esb_float(item.get("TransactionVolume",0))
            name8 = str(item.get("CompanyName","")).strip()
            change = (latest - prev) / prev if prev > 0 and latest > 0 else 0.0
            esb_today[sid] = {"name":name8,"latest":latest,"prev":prev,"vol":vol,"change":change,"high":high}

        # 抓近期歷史成交量（用月資料算5日均量）
        avg5_dict = {}
        today_dt = datetime.now()
        for delta in [0, -1]:
            m = today_dt.month + delta
            y = today_dt.year
            if m <= 0: m += 12; y -= 1
            hist_url = f"https://www.tpex.org.tw/openapi/v1/tpex_esb_every_day_statistics?date={y}{m:02d}"
            hr8 = requests.get(hist_url, headers=esb_h, timeout=15, verify=False)
            if hr8.status_code != 200: continue
            try:
                hdata = hr8.json()
                if not isinstance(hdata, list): continue
                for row in hdata:
                    sid = str(row.get("SecuritiesCompanyCode","")).strip()
                    vol = _esb_float(row.get("TransactionVolume",0))
                    if sid and sid.isdigit():
                        avg5_dict.setdefault(sid,[]).append(vol / 1000)  # 轉換為張
            except: continue

        for sid, info in esb_today.items():
            vol_k = info["vol"] / 1000  # 轉換為張
            change = info["change"]
            vols = avg5_dict.get(sid, [])
            avg5 = sum(vols[-5:]) / len(vols[-5:]) if vols else 0

            # 爆量條件：成交>=500張、漲幅>=30%
            # 若有均量資料則額外判斷>=10倍均量
            vol_ok = vol_k >= 500
            change_ok = change >= 0.30
            ratio_ok = (avg5 <= 0) or (vol_k >= avg5 * 10)

            if vol_ok and change_ok and ratio_ok:
                ratio_str = f"{vol_k/avg5:.1f}x" if avg5 > 0 else "-"
                avg5_str = f"{int(avg5):,}" if avg5 > 0 else "-"
                s8.append({
                    "股票代號": sid,
                    "股票名稱": info["name"],
                    "收盤價": info["latest"],
                    "前日均價": info["prev"],
                    "漲幅": f"{change*100:.1f}%",
                    "成交張數": f"{int(vol_k):,}",
                    "5日均量(張)": avg5_str,
                    "爆量倍數": ratio_str,
                })

        s8.sort(key=lambda x: float(x["漲幅"].replace("%","")), reverse=True)
    except Exception as e8:
        print(f"興櫃爆量錯誤: {e8}")
        s8 = []


    # 策略九：興櫃當天拉回（用公開API抓今日資料）
    s9 = []
    try:
        # 重用策略八的今日資料
        for sid, info in esb_today.items():
            high = info["high"]
            latest = info["latest"]
            prev = info["prev"]
            if high > 0 and latest > 0:
                pullback = (high - latest) / high
                if pullback >= 0.25:
                    change = info["change"]
                    s9.append({
                        "股票代號": sid,
                        "股票名稱": info["name"],
                        "今日最高": high,
                        "現價": latest,
                        "前日均價": prev,
                        "拉回幅度": f"{pullback*100:.1f}%",
                        "漲跌幅": f"{change*100:.1f}%",
                    })
        s9.sort(key=lambda x: float(x["拉回幅度"].replace("%","")), reverse=True)
    except Exception as e9:
        print(f"興櫃拉回錯誤: {e9}")
        s9 = []


    # 策略十：處置股拉回（兩個月內被處置，且連續下跌5天）
    s10 = []
    try:
        disposal_stocks = disposal_stocks_2m  # 使用歷史處置股資料

        # 計算連續下跌天數
        two_months_ago = (today - timedelta(days=60)).strftime("%Y-%m-%d")
        close_2m = close_df[close_df.index >= pd.to_datetime(two_months_ago)]

        for stock_id, info in disposal_stocks.items():
            try:
                if stock_id not in close_2m.columns:
                    continue
                prices = close_2m[stock_id].dropna()
                if len(prices) < 6:
                    continue

                # 計算每日漲跌
                daily_chg = prices.diff()

                # 檢查最近5天是否連續下跌
                last5 = daily_chg.iloc[-5:]
                if len(last5) < 5:
                    continue

                if all(last5 < 0):
                    # 連續下跌5天
                    current_price = prices.iloc[-1]
                    price_5d_ago  = prices.iloc[-6]
                    drop_pct      = (current_price - price_5d_ago) / price_5d_ago

                    s10.append({
                        "股票代號": stock_id,
                        "股票名稱": info["name"],
                        "處置期間": info["period"],
                        "目前股價": round(current_price, 2),
                        "5日前股價": round(price_5d_ago, 2),
                        "5日跌幅": f"{drop_pct*100:.1f}%",
                        "最近下跌日": str(prices.index[-1])[:10],
                    })
            except:
                continue

        s10.sort(key=lambda x: float(x["5日跌幅"].replace("%", "")))

    except Exception as e:
        print(f"處置股拉回錯誤: {e}")
        s10 = []


    # 策略十一：興櫃突破平台
    # 條件：今天漲幅≥10% + 今天股價>前兩天最高 + 前30天高低差≤5%
    s11 = []
    try:
        def _esb_f(val):
            s = str(val).replace(",", "").strip()
            return float(s) if s and s not in ["-", "--", ""] else 0.0

        esb_url11 = "https://www.tpex.org.tw/openapi/v1/tpex_esb_latest_statistics"
        esb_h11 = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}
        r11 = requests.get(esb_url11, headers=esb_h11, timeout=15, verify=False)
        esb_items11 = r11.json()

        # 整理今日資料
        esb_today11 = {}
        for item in esb_items11:
            sid = str(item.get("SecuritiesCompanyCode","")).strip()
            if not sid or not sid.isdigit(): continue
            prev   = _esb_f(item.get("PreviousAveragePrice", 0))
            latest = _esb_f(item.get("LatestPrice", 0))
            high   = _esb_f(item.get("Highest", 0))
            name11 = str(item.get("CompanyName","")).strip()
            change = (latest - prev) / prev if prev > 0 and latest > 0 else 0.0
            esb_today11[sid] = {
                "name": name11, "latest": latest,
                "prev": prev, "high": high, "change": change
            }

        # 用 close_3m 抓興櫃歷史資料計算平台
        start_30d = (today - timedelta(days=45)).strftime("%Y-%m-%d")
        close_30d = close_df[close_df.index >= pd.to_datetime(start_30d)]

        for sid, info in esb_today11.items():
            try:
                latest = info["latest"]
                change = info["change"]

                # 條件1：今天漲幅≥10%
                if change < 0.10:
                    continue

                # 需要歷史資料
                if sid not in close_30d.columns:
                    continue

                prices_30d = close_30d[sid].dropna()
                if len(prices_30d) < 5:
                    continue

                # 條件2：今天股價 > 前兩天最高
                prev2_high = prices_30d.iloc[-3:-1].max() if len(prices_30d) >= 3 else 0
                if latest <= prev2_high:
                    continue

                # 條件3：前30天（不含今天）高低差≤5%
                hist_prices = prices_30d.iloc[:-1]  # 不含今天
                if len(hist_prices) < 5:
                    continue
                p_max = hist_prices.max()
                p_min = hist_prices.min()
                if p_min <= 0:
                    continue
                range_pct = (p_max - p_min) / p_min
                if range_pct > 0.05:
                    continue

                s11.append({
                    "股票代號": sid,
                    "股票名稱": info["name"],
                    "今日收盤": latest,
                    "今日漲幅": f"{change*100:.1f}%",
                    "前兩天最高": round(prev2_high, 2),
                    "30日高點": round(p_max, 2),
                    "30日低點": round(p_min, 2),
                    "平台區間": f"{range_pct*100:.1f}%",
                })
            except:
                continue

        s11.sort(key=lambda x: float(x["今日漲幅"].replace("%","")), reverse=True)

    except Exception as e:
        print(f"興櫃突破平台錯誤: {e}")
        s11 = []


    # 策略十二：處置股來到月線（兩個月內被處置，股價在20日均線上下3%）
    s12 = []
    try:
        disposal_stocks12 = disposal_stocks_2m  # 使用歷史處置股資料

        for stock_id, info in disposal_stocks12.items():
            try:
                if stock_id not in close_3m.columns:
                    continue
                prices = close_3m[stock_id].dropna()
                if len(prices) < 20:
                    continue

                ma20 = prices.rolling(20).mean()
                current_price = prices.iloc[-1]
                current_ma20  = ma20.iloc[-1]

                if pd.isna(current_ma20) or current_ma20 <= 0:
                    continue

                diff_pct = (current_price - current_ma20) / current_ma20

                if abs(diff_pct) <= 0.03:
                    s12.append({
                        "股票代號": stock_id,
                        "股票名稱": info["name"],
                        "處置期間": info["period"],
                        "目前股價": round(current_price, 2),
                        "20日均線": round(current_ma20, 2),
                        "偏離幅度": f"{diff_pct*100:.1f}%",
                    })
            except:
                continue

        s12.sort(key=lambda x: abs(float(x["偏離幅度"].replace("%", ""))))

    except Exception as e:
        print(f"處置股月線錯誤: {e}")
        s12 = []

    # 存進全域供監控頁面使用
    global _global_s1, _global_s2, _global_s3, _global_s4, _global_s5, _global_s6, _global_s7, _global_s10, _global_s12
    _global_s1  = s1
    _global_s2  = s2
    _global_s3  = s3
    _global_s4  = s4
    _global_s5  = s5
    _global_s6  = s6
    _global_s7  = s7
    _global_s10 = s10
    _global_s12 = s12

    return s1, s2, s3, s4, s5, s6, s7, s8, s9, s10, s11, s12






# 快取資料
_cache = {"data": None, "time": None}
_global_disposal_2m = {}
_global_close_3m = None
_global_industry_dict = {}
_global_s1 = []
_global_s2 = []
_global_s3 = []
_global_s4 = []
_global_s5 = []
_global_s6 = []
_global_s7 = []
_global_s10 = []
_global_s12 = []

MONITOR_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>📡 即時監控總覽</title>
    <meta http-equiv="refresh" content="300">
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: 'Microsoft JhengHei', sans-serif; background: #0f172a; color: #e2e8f0; padding: 24px; }
        .back { display: inline-block; margin-bottom: 16px; color: #38bdf8; text-decoration: none; font-size: 14px; }
        h1 { font-size: 22px; margin-bottom: 4px; }
        .subtitle { color: #94a3b8; font-size: 13px; margin-bottom: 20px; }
        .section { margin-bottom: 32px; }
        .section-title { font-size: 15px; font-weight: bold; color: #f8fafc; margin-bottom: 10px; padding: 6px 12px; background: #1e293b; border-left: 3px solid #38bdf8; border-radius: 4px; }
        table { width: 100%; border-collapse: collapse; background: #1e293b; border-radius: 10px; overflow: hidden; font-size: 13px; }
        thead tr { background: #0f172a; }
        th { padding: 10px 14px; text-align: left; color: #94a3b8; font-weight: 600; white-space: nowrap; }
        td { padding: 9px 14px; border-top: 1px solid #334155; white-space: nowrap; }
        tr:hover td { background: #263548; }
        .sid { color: #38bdf8; font-weight: bold; }
        .up { color: #4ade80; font-weight: bold; }
        .dn { color: #f87171; font-weight: bold; }
        .flat { color: #94a3b8; }
        .empty { color: #475569; padding: 16px; text-align: center; }
        .updated { text-align: center; color: #475569; font-size: 12px; margin-top: 20px; }
        .countdown { text-align: center; color: #64748b; font-size: 12px; margin-top: 4px; }
        .tag { display: inline-block; font-size: 11px; padding: 1px 7px; border-radius: 4px; margin-left: 4px; }
        .tag-s1 { background:#7c3aed22; color:#a78bfa; border:1px solid #7c3aed44; }
        .tag-s2 { background:#0369a122; color:#38bdf8; border:1px solid #0369a144; }
        .tag-s3 { background:#dc262622; color:#f87171; border:1px solid #dc262644; }
        .tag-s4 { background:#92400e22; color:#fbbf24; border:1px solid #92400e44; }
        .tag-s5 { background:#16543022; color:#34d399; border:1px solid #16543044; }
        .tag-s6 { background:#be185d22; color:#f472b6; border:1px solid #be185d44; }
        .tag-s7 { background:#1e3a5f22; color:#93c5fd; border:1px solid #1e3a5f44; }
        .tag-s10 { background:#78350f22; color:#fcd34d; border:1px solid #78350f44; }
        .tag-s12 { background:#14532d22; color:#86efac; border:1px solid #14532d44; }
    </style>
    <script>
        let secs = 300;
        setInterval(() => {
            secs--;
            const el = document.getElementById('cd');
            if (el) el.textContent = secs + ' 秒後自動刷新';
            if (secs <= 0) location.reload();
        }, 1000);
    </script>
</head>
<body>
    <a href="/" class="back">← 返回首頁</a>
    <h1>📡 即時監控總覽</h1>
    <p class="subtitle">整合所有策略股票的即時行情｜每5分鐘自動刷新｜更新時間：{{ update_time }}</p>

    {% if stocks %}
    <table>
        <thead>
            <tr>
                <th>策略來源</th>
                <th>股票代號</th>
                <th>股票名稱</th>
                <th>產業別</th>
                <th>昨收</th>
                <th>即時股價</th>
                <th>漲跌幅</th>
                <th>今日最高</th>
                <th>今日最低</th>
                <th>資料時間</th>
            </tr>
        </thead>
        <tbody>
            {% for s in stocks %}
            <tr>
                <td>{% for tag in s['策略來源'] %}<span class="tag tag-{{ tag.cls }}">{{ tag.name }}</span>{% endfor %}</td>
                <td class="sid">{{ s['股票代號'] }}</td>
                <td>{{ s['股票名稱'] }}</td>
                <td>{{ s['產業別'] }}</td>
                <td>{{ s['昨收'] }}</td>
                <td class="{{ 'up' if s['漲跌幅'][0] != '-' else 'dn' }}">{{ s['即時股價'] }}</td>
                <td class="{{ 'up' if s['漲跌幅'][0] != '-' else ('dn' if s['漲跌幅'][0] == '-' else 'flat') }}">{{ s['漲跌幅'] }}</td>
                <td class="up">{{ s['今日最高'] }}</td>
                <td class="dn">{{ s['今日最低'] }}</td>
                <td>{{ s['資料時間'] }}</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
    {% else %}
    <div class="empty">❌ 目前沒有監控股票，或即時資料尚未載入</div>
    {% endif %}

    <p class="updated">即時股價來源：證交所／櫃買｜策略資料來源：FinLab</p>
    <p class="countdown" id="cd">300 秒後自動刷新</p>
</body>
</html>
"""

def get_cached_data():
    now = datetime.now()
    if _cache["data"] is None or (now - _cache["time"]).seconds > 1800:
        _cache["data"] = get_all_data()
        _cache["time"] = now
    return _cache["data"]

@app.route("/strategy/12/realtime")
def strategy12_realtime():
    """策略12 即時版 - 用證交所即時股價"""
    # 確保主資料已載入（MA20 需要）
    get_cached_data()

    update_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    s12_rt = []

    try:
        if not _global_disposal_2m or _global_close_3m is None:
            return render_template_string(REALTIME_TEMPLATE, stocks=[], update_time=update_time)

        # 取得 MA20（30分鐘快取）
        ma20_dict = get_ma20_cache(_global_disposal_2m, _global_close_3m)

        # 取得即時股價（5分鐘快取）
        stock_ids = list(ma20_dict.keys())
        realtime_prices = get_realtime_prices(stock_ids)

        for stock_id, ma20 in ma20_dict.items():
            info = _global_disposal_2m.get(stock_id, {})

            # 優先用即時價，沒有就用 FinLab 昨收
            if stock_id in realtime_prices:
                current_price = realtime_prices[stock_id]["price"]
                price_time = realtime_prices[stock_id]["time"]
            else:
                # 非交易時間 fallback 用 FinLab 收盤價
                try:
                    prices_hist = _global_close_3m[stock_id].dropna()
                    current_price = prices_hist.iloc[-1]
                    price_time = "昨收"
                except:
                    continue

            diff_pct = (current_price - ma20) / ma20

            if abs(diff_pct) <= 0.03:
                s12_rt.append({
                    "股票代號": stock_id,
                    "股票名稱": info.get("name", ""),
                    "產業別": _global_industry_dict.get(stock_id, ""),
                    "處置期間": info.get("period", ""),
                    "即時股價": round(current_price, 2),
                    "20日均線": ma20,
                    "偏離幅度": f"{diff_pct*100:.1f}%",
                    "資料時間": price_time,
                })

        s12_rt.sort(key=lambda x: abs(float(x["偏離幅度"].replace("%", ""))))

    except Exception as e:
        print(f"即時策略12錯誤: {e}")

    return render_template_string(REALTIME_TEMPLATE, stocks=s12_rt, update_time=update_time)

@app.route("/monitor")
def monitor():
    """即時監控總覽 - 整合所有策略股票"""
    get_cached_data()
    update_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 收集所有策略的股票，去重並記錄來源
    strategy_tags = [
        ("s1",  _global_s1,  "二手紅盤",   "股票代號"),
        ("s2",  _global_s2,  "跌停翻漲停", "股票代號"),
        ("s3",  _global_s3,  "強勢回檔",   "股票代號"),
        ("s4",  _global_s4,  "三手紅盤",   "股票代號"),
        ("s5",  _global_s5,  "四手紅盤",   "股票代號"),
        ("s6",  _global_s6,  "五手紅盤",   "股票代號"),
        ("s7",  _global_s7,  "處置跌破線", "股票代號"),
        ("s10", _global_s10, "處置拉回",   "股票代號"),
        ("s12", _global_s12, "處置月線",   "股票代號"),
    ]

    # 整合：同一支股票合併策略標籤
    stock_map = {}  # {stock_id: {name, tags, prev_close}}
    for cls, slist, label, key in strategy_tags:
        seen = set()
        for item in slist:
            sid = item.get(key, "")
            if not sid or sid in seen:
                continue
            seen.add(sid)
            # 取昨收（各策略欄位名不同，依序找）
            prev = (item.get("第二天收盤") or item.get("收盤價") or
                    item.get("目前股價") or item.get("第五天收盤") or
                    item.get("第四天收盤") or item.get("第三天收盤") or 0)
            if sid not in stock_map:
                stock_map[sid] = {
                    "股票名稱": item.get("股票名稱", ""),
                    "昨收": prev,
                    "tags": []
                }
            stock_map[sid]["tags"].append({"cls": cls, "name": label})

    if not stock_map:
        return render_template_string(MONITOR_TEMPLATE, stocks=[], update_time=update_time)

    # 抓即時股價
    all_ids = list(stock_map.keys())
    realtime = get_realtime_prices(all_ids)

    # 也抓今日最高最低（用 getStockInfo 的 h/l 欄位）
    high_low = {}
    now_dt = datetime.now()
    is_trading = (now_dt.weekday() < 5 and
                  (9 <= now_dt.hour < 13 or (now_dt.hour == 13 and now_dt.minute <= 30)))
    if is_trading:
        for batch in [all_ids[i:i+50] for i in range(0, len(all_ids), 50)]:
            for prefix in ["tse_", "otc_"]:
                try:
                    ids_str = "|".join([f"{prefix}{sid}.tw" for sid in batch])
                    url = f"https://mis.twse.com.tw/stock/api/getStockInfo.jsp?ex_ch={ids_str}&json=1&delay=0"
                    resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
                    for item in resp.json().get("msgArray", []):
                        sid = item.get("c", "")
                        h = item.get("h", "-")
                        l = item.get("l", "-")
                        y = item.get("y", "-")  # 昨收
                        if sid and h != "-" and l != "-":
                            high_low[sid] = {
                                "high": float(h),
                                "low": float(l),
                                "prev": float(y) if y != "-" else 0,
                            }
                except:
                    pass

    # 組合結果
    result = []
    for sid, info in stock_map.items():
        rt = realtime.get(sid, {})
        hl = high_low.get(sid, {})
        price = rt.get("price", 0)
        prev = hl.get("prev") or info["昨收"] or 0
        change_pct = f"{(price - prev)/prev*100:+.1f}%" if price and prev else "-"
        result.append({
            "策略來源": info["tags"],
            "股票代號": sid,
            "股票名稱": info["股票名稱"],
            "產業別": _global_industry_dict.get(sid, ""),
            "昨收": prev if prev else "-",
            "即時股價": price if price else "-",
            "漲跌幅": change_pct,
            "今日最高": hl.get("high", "-"),
            "今日最低": hl.get("low", "-"),
            "資料時間": rt.get("time", "盤後"),
        })

    # 依漲跌幅排序（漲最多在前）
    def sort_key(x):
        try:
            return -float(x["漲跌幅"].replace("%","").replace("+",""))
        except:
            return 0
    result.sort(key=sort_key)

    return render_template_string(MONITOR_TEMPLATE, stocks=result, update_time=update_time)

@app.route("/")
def home():
    s1, s2, s3, s4, s5, s6, s7, s8, s9, s10, s11, s12 = get_cached_data()
    update_time = datetime.now().strftime("%Y-%m-%d %H:%M")
    return render_template_string(HOME_TEMPLATE, counts=[len(s1), len(s2), len(s3), len(s4), len(s5), len(s6), len(s7), len(s8), len(s9), len(s10), len(s11), len(s12)], update_time=update_time)

@app.route("/strategy/<int:sid>")
def strategy(sid):
    s1, s2, s3, s4, s5, s6, s7, s8, s9, s10, s11, s12 = get_cached_data()
    update_time = datetime.now().strftime("%Y-%m-%d %H:%M")

    strategies = {
        1: {"title": "二手紅盤", "icon": "🔥", "desc": "最近一個月內，連續兩個交易日漲停的股票，依日期由新到舊排列",
            "stocks": s1, "columns": ["股票代號", "股票名稱", "第一天漲停日", "第二天漲停日", "第一天收盤", "第二天收盤"]},
        2: {"title": "跌停翻漲停", "icon": "⚡", "desc": "2026/1/1起，單日開盤跌停、收盤漲停的股票",
            "stocks": s2, "columns": ["股票代號", "股票名稱", "發生日期", "開盤價", "收盤價", "前日收盤"]},
        3: {"title": "強勢股回檔", "icon": "📉", "desc": "最近3個月內任意5日漲幅≥30%，且目前從高點修正≥20%，修正最多的在前",
            "stocks": s3, "columns": ["股票代號", "股票名稱", "5日最大漲幅", "漲幅起始日", "漲幅結束日", "當時最高價", "目前股價", "從高點修正"]},
        4: {"title": "三手紅盤", "icon": "🀄", "desc": "最近一個月內，連續三天漲停 或 連續三天累積漲幅≥30%，依日期由新到舊排列",
            "stocks": s4, "columns": ["股票代號", "股票名稱", "觸發條件", "第一天", "第二天", "第三天", "第一天收盤", "第二天收盤", "第三天收盤", "三日累積漲幅"]},
        5: {"title": "四手紅盤", "icon": "🎰", "desc": "最近一個月內，連續四天漲停 或 連續四天累積漲幅≥40%，依日期由新到舊排列",
            "stocks": s5, "columns": ["股票代號", "股票名稱", "觸發條件", "第一天", "第二天", "第三天", "第四天", "第一天收盤", "第四天收盤", "四日累積漲幅"]},
        6: {"title": "五手紅盤", "icon": "🔴", "desc": "最近一個月內，連續五天累積漲幅≥50%，依日期由新到舊排列",
            "stocks": s6, "columns": ["股票代號", "股票名稱", "第一天", "第五天", "第一天收盤", "第五天收盤", "五日累積漲幅"]},
        7: {"title": "處置股跌破10日線", "icon": "⚠️", "desc": "目前正在被處置的股票，處置期間內每次收盤價跌破10日均線皆列出，依股票代號與日期排序",
            "stocks": s7, "columns": ["股票代號", "股票名稱", "處置期間", "跌破日期", "收盤價", "10日均線", "跌破幅度"]},
        8: {"title": "興櫃爆量強漲", "icon": "🚀", "desc": "興櫃股票當日成交量≥5日均量10倍、成交≥500張、漲幅≥30%，依漲幅由高到低排列",
            "stocks": s8, "columns": ["股票代號", "股票名稱", "收盤價", "前日均價", "漲幅", "成交張數", "5日均量(張)", "爆量倍數"]},
        9: {"title": "興櫃當天拉回", "icon": "📉", "desc": "興櫃股票當天從最高點拉回幅度≥25%，拉回最多的在前",
            "stocks": s9, "columns": ["股票代號", "股票名稱", "今日最高", "現價", "前日均價", "拉回幅度", "漲跌幅"]},
        10: {"title": "處置股拉回", "icon": "🔻", "desc": "兩個月內曾被處置的股票，連續下跌5天，跌最多的在前",
            "stocks": s10, "columns": ["股票代號", "股票名稱", "處置期間", "目前股價", "5日前股價", "5日跌幅", "最近下跌日"]},
        11: {"title": "興櫃突破平台", "icon": "🚀", "desc": "今天漲幅≥10%、突破前兩天高點、前30天盤整區間≤5%，依漲幅排序",
            "stocks": s11, "columns": ["股票代號", "股票名稱", "今日收盤", "今日漲幅", "前兩天最高", "30日高點", "30日低點", "平台區間"]},
        12: {"title": "處置股來到月線", "icon": "📊", "desc": "兩個月內曾被處置的股票，股價在20日均線上下3%以內，偏離最小的在前",
            "stocks": s12, "columns": ["股票代號", "股票名稱", "處置期間", "目前股價", "20日均線", "偏離幅度"]},
    }

    if sid not in strategies:
        return "找不到此策略", 404

    s = strategies[sid]
    return render_template_string(DETAIL_TEMPLATE, update_time=update_time, **s)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"🚀 啟動中，請用瀏覽器開啟 http://127.0.0.1:{port}")
    app.run(host="0.0.0.0", port=port, debug=False)
