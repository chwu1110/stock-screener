import os
import finlab
from finlab import data
import pandas as pd
from datetime import datetime
from flask import Flask, render_template_string

app = Flask(__name__)

FINLAB_API_KEY = os.environ.get("FINLAB_API_KEY", "LBmwu3n0/lor77y1Z0aBH/Q0WBI6+bLJrA2TlchZAM1jb6jJaURRbaQRZRWjozwP#vip_m")

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>強勢股選股</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: 'Microsoft JhengHei', sans-serif; background: #0f172a; color: #e2e8f0; padding: 30px; }
        h1 { text-align: center; font-size: 24px; margin-bottom: 8px; color: #f8fafc; }
        .subtitle { text-align: center; color: #94a3b8; font-size: 14px; margin-bottom: 24px; }
        .section { margin-bottom: 40px; }
        .section-title { font-size: 18px; font-weight: bold; margin-bottom: 12px; padding: 8px 16px; border-radius: 8px; }
        .title-a { background: #7c3aed33; color: #a78bfa; }
        .title-b { background: #dc262633; color: #f87171; }
        .stats { display: flex; gap: 16px; margin-bottom: 16px; }
        .stat-box { background: #1e293b; border-radius: 10px; padding: 10px 20px; text-align: center; }
        .stat-box .num { font-size: 24px; font-weight: bold; color: #38bdf8; }
        .stat-box .label { font-size: 12px; color: #94a3b8; margin-top: 4px; }
        table { width: 100%; border-collapse: collapse; background: #1e293b; border-radius: 12px; overflow: hidden; margin-bottom: 12px; }
        thead tr { background: #0f172a; }
        th { padding: 12px 16px; text-align: left; font-size: 13px; color: #94a3b8; font-weight: 600; }
        td { padding: 11px 16px; font-size: 14px; border-top: 1px solid #334155; }
        tr:hover td { background: #263548; }
        .gain { color: #4ade80; font-weight: bold; }
        .loss { color: #f87171; font-weight: bold; }
        .stock-id { color: #38bdf8; font-weight: bold; }
        .updated { text-align: center; color: #475569; font-size: 12px; margin-top: 20px; }
        .empty { text-align: center; color: #94a3b8; padding: 30px; }
    </style>
</head>
<body>
    <h1>📈 強勢股選股</h1>
    <p class="subtitle">時間範圍：2026/01/01 ~ 今天｜更新時間：{{ update_time }}</p>

    <div class="section">
        <div class="section-title title-a">🔥 條件一：連續兩天漲停</div>
        <div class="stats">
            <div class="stat-box">
                <div class="num">{{ limit_up_count }}</div>
                <div class="label">符合股票數</div>
            </div>
        </div>
        {% if limit_up_stocks %}
        <table>
            <thead>
                <tr>
                    <th>股票代號</th>
                    <th>股票名稱</th>
                    <th>第一天漲停日</th>
                    <th>第二天漲停日</th>
                    <th>第一天收盤</th>
                    <th>第二天收盤</th>
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
        <p class="empty">❌ 沒有找到符合條件的股票</p>
        {% endif %}
    </div>

    <div class="section">
        <div class="section-title title-b">⚡ 條件二：單日跌停開盤→漲停收盤</div>
        <div class="stats">
            <div class="stat-box">
                <div class="num">{{ reversal_count }}</div>
                <div class="label">符合股票數</div>
            </div>
        </div>
        {% if reversal_stocks %}
        <table>
            <thead>
                <tr>
                    <th>股票代號</th>
                    <th>股票名稱</th>
                    <th>發生日期</th>
                    <th>開盤價</th>
                    <th>收盤價</th>
                    <th>前日收盤</th>
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
        <p class="empty">❌ 沒有找到符合條件的股票</p>
        {% endif %}
    </div>

    <p class="updated">資料來源：FinLab</p>
</body>
</html>
"""

def get_data():
    finlab.login(FINLAB_API_KEY)

    start_date = "2026-01-01"
    end_date = datetime.today().strftime("%Y-%m-%d")

    data.date_range = (start_date, end_date)

    close = data.get("price:收盤價")
    open_ = data.get("price:開盤價")

    stock_info = data.get("company_basic_info")
    name_dict = stock_info.set_index("stock_id")["公司簡稱"].to_dict()

    close_df = pd.DataFrame(close.values, index=pd.to_datetime(close.index.astype(str)), columns=close.columns)
    open_df = pd.DataFrame(open_.values, index=pd.to_datetime(open_.index.astype(str)), columns=open_.columns)

    close_df = close_df[close_df.index >= pd.to_datetime(start_date)]
    open_df = open_df[open_df.index >= pd.to_datetime(start_date)]

    daily_return = close_df.pct_change()

    # 條件一：連續兩天漲停
    is_limit_up = daily_return >= 0.095
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
                "第一天收盤": round(close_df[stock].loc[prev_date], 2),
                "第二天收盤": round(close_df[stock].loc[date], 2),
            })

    limit_up_result.sort(key=lambda x: x["第二天漲停日"], reverse=True)

    # 條件二：開盤跌停且收盤漲停
    prev_close = close_df.shift(1)
    open_change = (open_df - prev_close) / prev_close
    close_change = daily_return

    is_open_limit_down = open_change <= -0.095
    is_close_limit_up = close_change >= 0.095
    reversal = is_open_limit_down & is_close_limit_up

    reversal_result = []
    for stock in reversal.columns:
        dates = reversal.index[reversal[stock]]
        for date in dates:
            prev_date_idx = close_df.index.get_loc(date) - 1
            prev_close_price = close_df[stock].iloc[prev_date_idx] if prev_date_idx >= 0 else None
            reversal_result.append({
                "股票代號": stock,
                "股票名稱": name_dict.get(stock, ""),
                "發生日期": str(date)[:10],
                "開盤價": round(open_df[stock].loc[date], 2),
                "收盤價": round(close_df[stock].loc[date], 2),
                "前日收盤": round(prev_close_price, 2) if prev_close_price else "-",
            })

    reversal_result.sort(key=lambda x: x["發生日期"], reverse=True)

    return limit_up_result, reversal_result

@app.route("/")
def index():
    limit_up_stocks, reversal_stocks = get_data()
    update_time = datetime.now().strftime("%Y-%m-%d %H:%M")
    return render_template_string(
        HTML_TEMPLATE,
        limit_up_stocks=limit_up_stocks,
        limit_up_count=len(limit_up_stocks),
        reversal_stocks=reversal_stocks,
        reversal_count=len(reversal_stocks),
        update_time=update_time
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"🚀 啟動中，請用瀏覽器開啟 http://127.0.0.1:{port}")
    app.run(host="0.0.0.0", port=port, debug=False)
