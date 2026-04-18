import os
import finlab
from finlab import data
import pandas as pd
from datetime import datetime, timedelta
from flask import Flask, render_template_string

app = Flask(__name__)

# ✅ 從環境變數讀取 API Key（安全做法）
FINLAB_API_KEY = os.environ.get("FINLAB_API_KEY", "LBmwu3n0/lor77y1Z0aBH/Q0WBI6+bLJrA2TlchZAM1jb6jJaURRbaQRZRWjozwP#vip_m")

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>強勢股回檔選股</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: 'Microsoft JhengHei', sans-serif; background: #0f172a; color: #e2e8f0; padding: 30px; }
        h1 { text-align: center; font-size: 24px; margin-bottom: 8px; color: #f8fafc; }
        .subtitle { text-align: center; color: #94a3b8; font-size: 14px; margin-bottom: 24px; }
        .stats { display: flex; justify-content: center; gap: 20px; margin-bottom: 24px; }
        .stat-box { background: #1e293b; border-radius: 10px; padding: 14px 24px; text-align: center; }
        .stat-box .num { font-size: 28px; font-weight: bold; color: #38bdf8; }
        .stat-box .label { font-size: 12px; color: #94a3b8; margin-top: 4px; }
        table { width: 100%; border-collapse: collapse; background: #1e293b; border-radius: 12px; overflow: hidden; }
        thead tr { background: #0f172a; }
        th { padding: 14px 16px; text-align: left; font-size: 13px; color: #94a3b8; font-weight: 600; }
        td { padding: 13px 16px; font-size: 14px; border-top: 1px solid #334155; }
        tr:hover td { background: #263548; }
        .gain { color: #4ade80; font-weight: bold; }
        .loss { color: #f87171; font-weight: bold; }
        .stock-id { color: #38bdf8; font-weight: bold; }
        .updated { text-align: center; color: #475569; font-size: 12px; margin-top: 20px; }
        .loading { text-align: center; color: #94a3b8; margin-top: 60px; font-size: 18px; }
    </style>
</head>
<body>
    <h1>📈 強勢股回檔選股</h1>
    <p class="subtitle">條件：一年內任意5交易日漲幅 ≥ 30%，且目前從高點修正 ≥ 25%</p>
    <div class="stats">
        <div class="stat-box">
            <div class="num">{{ total }}</div>
            <div class="label">符合股票數</div>
        </div>
        <div class="stat-box">
            <div class="num">{{ update_time }}</div>
            <div class="label">資料更新時間</div>
        </div>
    </div>
    {% if stocks %}
    <table>
        <thead>
            <tr>
                <th>股票代號</th>
                <th>股票名稱</th>
                <th>5日最大漲幅</th>
                <th>漲幅起始日</th>
                <th>漲幅結束日</th>
                <th>當時最高價</th>
                <th>目前股價</th>
                <th>從高點修正</th>
            </tr>
        </thead>
        <tbody>
            {% for s in stocks %}
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
    <p style="text-align:center; color:#94a3b8; margin-top:40px;">❌ 沒有找到符合條件的股票</p>
    {% endif %}
    <p class="updated">資料來源：FinLab｜更新時間：{{ update_time }}</p>
</body>
</html>
"""

def get_stocks():
    finlab.login(FINLAB_API_KEY)

    end_date = datetime.today()
    start_date = end_date - timedelta(days=365)

    data.date_range = (start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"))

    close = data.get("price:收盤價")
    stock_info = data.get("company_basic_info")
    name_dict = stock_info.set_index("stock_id")["公司簡稱"].to_dict()

    close_df = pd.DataFrame(close.values, index=pd.to_datetime(close.index.astype(str)), columns=close.columns)
    close_df = close_df[close_df.index >= pd.to_datetime(start_date)]

    daily_return = close_df.pct_change()
    result = []

    for stock in daily_return.columns:
        series = daily_return[stock].dropna()
        if len(series) < 5:
            continue

        rolling_5 = (1 + series).rolling(5).apply(lambda x: x.prod(), raw=True) - 1
        max_gain = rolling_5.max()

        if max_gain < 0.30:
            continue

        best_end_date = rolling_5.idxmax()
        idx = series.index.get_loc(best_end_date)
        start_idx = max(0, idx - 4)
        segment = close_df[stock].iloc[start_idx:idx+1]
        actual_gain = (segment.iloc[-1] / segment.iloc[0]) - 1

        if actual_gain < 0.30:
            continue
        if segment.index[0] < pd.to_datetime(start_date):
            continue

        peak_price = segment.max()
        current_price = close_df[stock].dropna().iloc[-1]
        drawdown = (current_price - peak_price) / peak_price

        if drawdown <= -0.25:
            result.append({
                "股票代號": stock,
                "股票名稱": name_dict.get(stock, ""),
                "5日最大漲幅": f"{actual_gain*100:.1f}%",
                "漲幅起始日": str(segment.index[0])[:10],
                "漲幅結束日": str(segment.index[-1])[:10],
                "當時最高價": round(peak_price, 2),
                "目前股價": round(current_price, 2),
                "從高點修正": f"{drawdown*100:.1f}%",
            })

    result.sort(key=lambda x: float(x["從高點修正"].replace("%", "")))
    return result

@app.route("/")
def index():
    stocks = get_stocks()
    update_time = datetime.now().strftime("%Y-%m-%d %H:%M")
    return render_template_string(HTML_TEMPLATE, stocks=stocks, total=len(stocks), update_time=update_time)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"🚀 啟動中，請用瀏覽器開啟 http://127.0.0.1:{port}")
    app.run(host="0.0.0.0", port=port, debug=False)
