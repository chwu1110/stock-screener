import os
import finlab
from finlab import data
import pandas as pd
from datetime import datetime, timedelta
from flask import Flask, render_template_string

app = Flask(__name__)

FINLAB_API_KEY = os.environ.get("FINLAB_API_KEY", "LBmwu3n0/lor77y1Z0aBH/Q0WBI6+bLJrA2TlchZAM1jb6jJaURRbaQRZRWjozwP#vip_m")

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>選股平台</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: 'Microsoft JhengHei', sans-serif; background: #0f172a; color: #e2e8f0; padding: 30px; }
        h1 { text-align: center; font-size: 26px; margin-bottom: 6px; color: #f8fafc; }
        .subtitle { text-align: center; color: #94a3b8; font-size: 13px; margin-bottom: 36px; }
        .section { margin-bottom: 50px; }
        .section-title { font-size: 18px; font-weight: bold; margin-bottom: 12px; padding: 10px 18px; border-radius: 8px; display: flex; align-items: center; gap: 10px; }
        .title-1 { background: #7c3aed33; color: #a78bfa; }
        .title-2 { background: #dc262633; color: #f87171; }
        .title-3 { background: #0369a133; color: #38bdf8; }
        .stat-box { display: inline-block; background: #1e293b; border-radius: 10px; padding: 8px 20px; margin-bottom: 14px; }
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
        .empty { text-align: center; color: #94a3b8; padding: 30px; background: #1e293b; border-radius: 12px; }
        .divider { border: none; border-top: 1px solid #1e293b; margin: 40px 0; }
        .updated { text-align: center; color: #475569; font-size: 12px; margin-top: 30px; }
    </style>
</head>
<body>
    <h1>📊 台股選股平台</h1>
    <p class="subtitle">更新時間：{{ update_time }}</p>

    <!-- 策略一 -->
    <div class="section">
        <div class="section-title title-1">🔥 策略一：連續兩天漲停（2026/1/1起）</div>
        <div class="stat-box">
            <div class="num">{{ limit_up_count }}</div>
            <div class="label">符合股票數</div>
        </div>
        {% if limit_up_stocks %}
        <table>
            <thead>
                <tr>
                    <th>股票代號</th><th>股票名稱</th><th>第一天漲停日</th><th>第二天漲停日</th><th>第一天收盤</th><th>第二天收盤</th>
                </tr>
            </thead>
            <tbody>
                {% for s in limit_up_stocks %}
                <tr>
                    <td class="stock-id">{{ s['股票代號'] }}</td>
                    <td>{{ s['股票名稱'] }}</td>
                    <td>{{ s['第一天漲停日'] }}</td>
                    <td>{{ s['第二天漲停日'] }}</td>
                    <td class="gain">{{ s['第一天收盤'] }}</td>
                    <td class="gain">{{ s['第二天收盤'] }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
        {% else %}
        <div class="empty">❌ 沒有找到符合條件的股票</div>
        {% endif %}
    </div>

    <hr class="divider">

    <!-- 策略二 -->
    <div class="section">
        <div class="section-title title-2">⚡ 策略二：單日跌停開盤→漲停收盤（2026/1/1起）</div>
        <div class="stat-box">
            <div class="num">{{ reversal_count }}</div>
            <div class="label">符合股票數</div>
        </div>
        {% if reversal_stocks %}
        <table>
            <thead>
                <tr>
                    <th>股票代號</th><th>股票名稱</th><th>發生日期</th><th>開盤價</th><th>收盤價</th><th>前日收盤</th>
                </tr>
            </thead>
            <tbody>
                {% for s in reversal_stocks %}
                <tr>
                    <td class="stock-id">{{ s['股票代號'] }}</td>
                    <td>{{ s['股票名稱'] }}</td>
                    <td>{{ s['發生日期'] }}</td>
                    <td class="loss">{{ s['開盤價'] }}</td>
                    <td class="gain">{{ s['收盤價'] }}</td>
                    <td>{{ s['前日收盤'] }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
        {% else %}
        <div class="empty">❌ 沒有找到符合條件的股票</div>
        {% endif %}
    </div>

    <hr class="divider">

    <!-- 策略三 -->
    <div class="section">
        <div class="section-title title-3">📉 策略三：強勢股回檔（一年內5日漲30%，目前修正25%）</div>
        <div class="stat-box">
            <div class="num">{{ pullback_count }}</div>
            <div class="label">符合股票數</div>
        </div>
        {% if pullback_stocks %}
        <table>
            <thead>
                <tr>
                    <th>股票代號</th><th>股票名稱</th><th>5日最大漲幅</th><th>漲幅起始日</th><th>漲幅結束日</th><th>當時最高價</th><th>目前股價</th><th>從高點修正</th>
                </tr>
            </thead>
            <tbody>
                {% for s in pullback_stocks %}
                <tr>
                    <td class="stock-id">{{ s['股票代號'] }}</td>
                    <td>{{ s['股票名稱'] }}</td>
                    <td class="gain">{{ s['5日最大漲幅'] }}</td>
                    <td>{{ s['漲幅起始日'] }}</td>
                    <td>{{ s['漲幅結束日'] }}</td>
                    <td>{{ s['當時最高價'] }}</td>
                    <td>{{ s['目前股價'] }}</td>
                    <td class="loss">{{ s['從高點修正'] }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
        {% else %}
        <div class="empty">❌ 沒有找到符合條件的股票</div>
        {% endif %}
    </div>

    <p class="updated">資料來源：FinLab｜{{ update_time }}</p>
</body>
</html>
"""

def get_all_data():
    finlab.login(FINLAB_API_KEY)

    today = datetime.today()
    start_2026 = "2026-01-01"
    start_1yr = (today - timedelta(days=365)).strftime("%Y-%m-%d")
    end_date = today.strftime("%Y-%m-%d")

    # 抓一年資料（涵蓋所有策略）
    data.date_range = (start_1yr, end_date)

    close = data.get("price:收盤價")
    open_ = data.get("price:開盤價")
    stock_info = data.get("company_basic_info")
    name_dict = stock_info.set_index("stock_id")["公司簡稱"].to_dict()

    # 轉成普通 DataFrame
    close_df = pd.DataFrame(close.values, index=pd.to_datetime(close.index.astype(str)), columns=close.columns)
    open_df = pd.DataFrame(open_.values, index=pd.to_datetime(open_.index.astype(str)), columns=open_.columns)

    close_1yr = close_df[close_df.index >= pd.to_datetime(start_1yr)]
    close_2026 = close_df[close_df.index >= pd.to_datetime(start_2026)]
    open_2026 = open_df[open_df.index >= pd.to_datetime(start_2026)]

    # ===== 策略一：連續兩天漲停 =====
    daily_return_2026 = close_2026.pct_change()
    is_limit_up = daily_return_2026 >= 0.095
    consecutive = is_limit_up & is_limit_up.shift(1)

    limit_up_result = []
    for stock in consecutive.columns:
        dates = consecutive.index[consecutive[stock]]
        for date in dates:
            prev_idx = is_limit_up.index.get_loc(date) - 1
            prev_date = is_limit_up.index[prev_idx]
            limit_up_result.append({
                "股票代號": stock,
                "股票名稱": name_dict.get(stock, ""),
                "第一天漲停日": str(prev_date)[:10],
                "第二天漲停日": str(date)[:10],
                "第一天收盤": round(close_2026[stock].loc[prev_date], 2),
                "第二天收盤": round(close_2026[stock].loc[date], 2),
            })
    limit_up_result.sort(key=lambda x: x["第二天漲停日"], reverse=True)

    # ===== 策略二：跌停開→漲停收 =====
    prev_close = close_2026.shift(1)
    open_change = (open_2026 - prev_close) / prev_close
    close_change = daily_return_2026
    reversal = (open_change <= -0.095) & (close_change >= 0.095)

    reversal_result = []
    for stock in reversal.columns:
        dates = reversal.index[reversal[stock]]
        for date in dates:
            prev_idx = close_2026.index.get_loc(date) - 1
            prev_close_price = close_2026[stock].iloc[prev_idx] if prev_idx >= 0 else None
            reversal_result.append({
                "股票代號": stock,
                "股票名稱": name_dict.get(stock, ""),
                "發生日期": str(date)[:10],
                "開盤價": round(open_2026[stock].loc[date], 2),
                "收盤價": round(close_2026[stock].loc[date], 2),
                "前日收盤": round(prev_close_price, 2) if prev_close_price else "-",
            })
    reversal_result.sort(key=lambda x: x["發生日期"], reverse=True)

    # ===== 策略三：強勢股回檔 =====
    daily_return_1yr = close_1yr.pct_change()
    pullback_result = []

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
        start_idx = max(0, idx - 4)
        segment = close_1yr[stock].iloc[start_idx:idx+1]
        actual_gain = (segment.iloc[-1] / segment.iloc[0]) - 1

        if actual_gain < 0.30:
            continue
        if segment.index[0] < pd.to_datetime(start_1yr):
            continue

        peak_price = segment.max()
        current_price = close_1yr[stock].dropna().iloc[-1]
        drawdown = (current_price - peak_price) / peak_price

        if drawdown <= -0.25:
            pullback_result.append({
                "股票代號": stock,
                "股票名稱": name_dict.get(stock, ""),
                "5日最大漲幅": f"{actual_gain*100:.1f}%",
                "漲幅起始日": str(segment.index[0])[:10],
                "漲幅結束日": str(segment.index[-1])[:10],
                "當時最高價": round(peak_price, 2),
                "目前股價": round(current_price, 2),
                "從高點修正": f"{drawdown*100:.1f}%",
            })

    pullback_result.sort(key=lambda x: float(x["從高點修正"].replace("%", "")))

    return limit_up_result, reversal_result, pullback_result

@app.route("/")
def index():
    limit_up_stocks, reversal_stocks, pullback_stocks = get_all_data()
    update_time = datetime.now().strftime("%Y-%m-%d %H:%M")
    return render_template_string(
        HTML_TEMPLATE,
        limit_up_stocks=limit_up_stocks,
        limit_up_count=len(limit_up_stocks),
        reversal_stocks=reversal_stocks,
        reversal_count=len(reversal_stocks),
        pullback_stocks=pullback_stocks,
        pullback_count=len(pullback_stocks),
        update_time=update_time
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"🚀 啟動中，請用瀏覽器開啟 http://127.0.0.1:{port}")
    app.run(host="0.0.0.0", port=port, debug=False)
