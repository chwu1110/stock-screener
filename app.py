import os
import finlab
from finlab import data
import pandas as pd
from datetime import datetime, timedelta
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
    </style>
</head>
<body>
    <h1>📊 台股選股平台</h1>
    <p class="subtitle">更新時間：{{ update_time }}｜點擊策略卡片查看詳細結果</p>

    <div class="grid">
        <a href="/strategy/1" class="card">
            <div class="card-icon">🔥</div>
            <div class="card-title">連續兩天漲停</div>
            <div class="card-desc">2026/1/1起，連續兩個交易日漲停的股票</div>
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
            <div class="card-desc">一年內任意5日漲幅≥30%，且目前從高點修正≥25%</div>
            <div class="card-count">{{ counts[2] }}</div>
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

def get_all_data():
    finlab.login(FINLAB_API_KEY)

    today = datetime.today()
    start_2026 = "2026-01-01"
    start_1yr = (today - timedelta(days=365)).strftime("%Y-%m-%d")
    end_date = today.strftime("%Y-%m-%d")

    data.date_range = (start_1yr, end_date)

    close = data.get("price:收盤價")
    open_ = data.get("price:開盤價")
    stock_info = data.get("company_basic_info")
    name_dict = stock_info.set_index("stock_id")["公司簡稱"].to_dict()

    close_df = pd.DataFrame(close.values, index=pd.to_datetime(close.index.astype(str)), columns=close.columns)
    open_df = pd.DataFrame(open_.values, index=pd.to_datetime(open_.index.astype(str)), columns=open_.columns)

    close_1yr = close_df[close_df.index >= pd.to_datetime(start_1yr)]
    close_2026 = close_df[close_df.index >= pd.to_datetime(start_2026)]
    open_2026 = open_df[open_df.index >= pd.to_datetime(start_2026)]

    # 策略一：連續兩天漲停
    daily_return_2026 = close_2026.pct_change()
    is_limit_up = daily_return_2026 >= 0.095
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
                "第一天收盤": round(close_2026[stock].loc[prev_date], 2),
                "第二天收盤": round(close_2026[stock].loc[date], 2),
            })
    s1.sort(key=lambda x: x["第二天漲停日"], reverse=True)

    # 策略二：跌停開→漲停收
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

    # 策略三：強勢股回檔
    daily_return_1yr = close_1yr.pct_change()
    s3 = []
    for stock in daily_return_1yr.columns:
        series = daily_return_1yr[stock].dropna()
        if len(series) < 5:
            continue
        rolling_5 = (1 + series).rolling(5).apply(lambda x: x.prod(), raw=True) - 1
        max_gain = rolling_5.max()
        if max_gain < 0.30:
            continue
        best_end_date = rolling_5.idxmax()
        idx = series.index.get_loc(best_end_date)
        segment = close_1yr[stock].iloc[max(0, idx-4):idx+1]
        actual_gain = (segment.iloc[-1] / segment.iloc[0]) - 1
        if actual_gain < 0.30 or segment.index[0] < pd.to_datetime(start_1yr):
            continue
        peak_price = segment.max()
        current_price = close_1yr[stock].dropna().iloc[-1]
        drawdown = (current_price - peak_price) / peak_price
        if drawdown <= -0.25:
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

    return s1, s2, s3

# 快取資料
_cache = {"data": None, "time": None}

def get_cached_data():
    now = datetime.now()
    if _cache["data"] is None or (now - _cache["time"]).seconds > 1800:
        _cache["data"] = get_all_data()
        _cache["time"] = now
    return _cache["data"]

@app.route("/")
def home():
    s1, s2, s3 = get_cached_data()
    update_time = datetime.now().strftime("%Y-%m-%d %H:%M")
    return render_template_string(HOME_TEMPLATE, counts=[len(s1), len(s2), len(s3)], update_time=update_time)

@app.route("/strategy/<int:sid>")
def strategy(sid):
    s1, s2, s3 = get_cached_data()
    update_time = datetime.now().strftime("%Y-%m-%d %H:%M")

    strategies = {
        1: {"title": "連續兩天漲停", "icon": "🔥", "desc": "2026/1/1起，連續兩個交易日漲停的股票，依日期由新到舊排列",
            "stocks": s1, "columns": ["股票代號", "股票名稱", "第一天漲停日", "第二天漲停日", "第一天收盤", "第二天收盤"]},
        2: {"title": "跌停翻漲停", "icon": "⚡", "desc": "2026/1/1起，單日開盤跌停、收盤漲停的股票",
            "stocks": s2, "columns": ["股票代號", "股票名稱", "發生日期", "開盤價", "收盤價", "前日收盤"]},
        3: {"title": "強勢股回檔", "icon": "📉", "desc": "一年內任意5日漲幅≥30%，且目前從高點修正≥25%，修正最多的在前",
            "stocks": s3, "columns": ["股票代號", "股票名稱", "5日最大漲幅", "漲幅起始日", "漲幅結束日", "當時最高價", "目前股價", "從高點修正"]},
    }

    if sid not in strategies:
        return "找不到此策略", 404

    s = strategies[sid]
    return render_template_string(DETAIL_TEMPLATE, update_time=update_time, **s)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"🚀 啟動中，請用瀏覽器開啟 http://127.0.0.1:{port}")
    app.run(host="0.0.0.0", port=port, debug=False)
