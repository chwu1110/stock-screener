import os
import finlab
from finlab import data
import pandas as pd
from datetime import datetime, timedelta
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
    </style>
</head>
<body>
    <h1>📊 台股選股平台</h1>
    <p class="subtitle">更新時間：{{ update_time }}｜點擊策略卡片查看詳細結果</p>

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
        <a href="/strategy/8" class="card">
            <div class="card-icon">🚀</div>
            <div class="card-title">興櫃爆量強漲</div>
            <div class="card-desc">興櫃股票當日成交量≥5日均量10倍、成交≥500張、漲幅≥30%</div>
            <div class="card-count">{{ counts[7] }}</div>
            <div class="card-count-label">符合股票數</div>
        </a>
        <a href="/strategy/9" class="card">
            <div class="card-icon">📉</div>
            <div class="card-title">興櫃當天拉回</div>
            <div class="card-desc">興櫃股票當天從最高點拉回幅度≥25%</div>
            <div class="card-count">{{ counts[8] }}</div>
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
    start_1yr = (today - timedelta(days=90)).strftime("%Y-%m-%d")  # 改為3個月，加快速度
    start_3m = (today - timedelta(days=90)).strftime("%Y-%m-%d")
    start_1m = (today - timedelta(days=30)).strftime("%Y-%m-%d")
    end_date = today.strftime("%Y-%m-%d")

    data.date_range = (start_3m, end_date)

    close = data.get("price:收盤價")
    open_ = data.get("price:開盤價")
    stock_info = data.get("company_basic_info")
    name_dict = stock_info.set_index("stock_id")["公司簡稱"].to_dict()
    industry_dict = stock_info.set_index("stock_id")["產業類別"].to_dict()

    close_df = pd.DataFrame(close.values, index=pd.to_datetime(close.index.astype(str)), columns=close.columns)
    open_df = pd.DataFrame(open_.values, index=pd.to_datetime(open_.index.astype(str)), columns=open_.columns)

    close_1yr = close_df[close_df.index >= pd.to_datetime(start_1yr)]
    close_3m = close_df[close_df.index >= pd.to_datetime(start_3m)]
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


    # 策略八：興櫃爆量強漲（使用 FinLab 興櫃資料）
    s8 = []
    try:
        # 用 FinLab 抓興櫃資料
        data.date_range = (start_1m, end_date)
        esb_close  = data.get("emerging_stock:收盤價")
        esb_vol    = data.get("emerging_stock:成交量")
        esb_open   = data.get("emerging_stock:開盤價")
        esb_high   = data.get("emerging_stock:最高價")

        esb_close_df = pd.DataFrame(esb_close.values, index=pd.to_datetime(esb_close.index.astype(str)), columns=esb_close.columns)
        esb_vol_df   = pd.DataFrame(esb_vol.values,   index=pd.to_datetime(esb_vol.index.astype(str)),   columns=esb_vol.columns)
        esb_high_df  = pd.DataFrame(esb_high.values,  index=pd.to_datetime(esb_high.index.astype(str)),  columns=esb_high.columns)

        # 取最後一個交易日
        last_date = esb_close_df.index[-1]
        prev_date = esb_close_df.index[-2] if len(esb_close_df) >= 2 else None

        for stock in esb_close_df.columns:
            try:
                today_close = esb_close_df[stock].loc[last_date]
                today_vol   = esb_vol_df[stock].loc[last_date]   # 單位：張
                prev_close  = esb_close_df[stock].loc[prev_date] if prev_date is not None else None

                if pd.isna(today_close) or pd.isna(today_vol) or today_close <= 0 or today_vol <= 0:
                    continue

                # 近5日均量（不含今天）
                past_vols = esb_vol_df[stock].iloc[:-1].dropna()
                avg5 = past_vols.iloc[-5:].mean() if len(past_vols) >= 1 else 0

                # 漲幅
                change_pct = (today_close - prev_close) / prev_close if prev_close and prev_close > 0 else 0

                # 條件：量>=10倍均量、>=500張、漲幅>=30%
                if avg5 > 0 and today_vol >= avg5 * 10 and today_vol >= 500 and change_pct >= 0.30:
                    ratio = today_vol / avg5
                    s8.append({
                        "股票代號": stock,
                        "股票名稱": name_dict.get(stock, ""),
                        "日期": str(last_date)[:10],
                        "收盤價": round(today_close, 2),
                        "漲幅": f"{change_pct*100:.1f}%",
                        "成交張數": f"{int(today_vol):,}",
                        "5日均量(張)": f"{int(avg5):,}",
                        "爆量倍數": f"{ratio:.1f}x",
                    })
            except:
                continue

        s8.sort(key=lambda x: float(x["漲幅"].replace("%", "")), reverse=True)

    except Exception as e8:
        print(f"興櫃爆量錯誤: {e8}")
        s8 = []


    # 策略九：興櫃當天拉回（使用 FinLab 興櫃資料）
    s9 = []
    try:
        # 重用策略八已抓的資料
        if 'esb_close_df' not in dir():
            data.date_range = (start_1m, end_date)
            esb_close9  = data.get("emerging_stock:收盤價")
            esb_high9   = data.get("emerging_stock:最高價")
            esb_close_df9 = pd.DataFrame(esb_close9.values, index=pd.to_datetime(esb_close9.index.astype(str)), columns=esb_close9.columns)
            esb_high_df9  = pd.DataFrame(esb_high9.values,  index=pd.to_datetime(esb_high9.index.astype(str)),  columns=esb_high9.columns)
        else:
            esb_close_df9 = esb_close_df
            esb_high_df9  = esb_high_df

        last_date9 = esb_close_df9.index[-1]
        prev_date9 = esb_close_df9.index[-2] if len(esb_close_df9) >= 2 else None

        for stock in esb_close_df9.columns:
            try:
                today_close9 = esb_close_df9[stock].loc[last_date9]
                today_high9  = esb_high_df9[stock].loc[last_date9]
                prev_close9  = esb_close_df9[stock].loc[prev_date9] if prev_date9 is not None else None

                if pd.isna(today_close9) or pd.isna(today_high9) or today_high9 <= 0 or today_close9 <= 0:
                    continue

                pullback = (today_high9 - today_close9) / today_high9
                if pullback >= 0.25:
                    change_pct9 = (today_close9 - prev_close9) / prev_close9 if prev_close9 and prev_close9 > 0 else 0
                    s9.append({
                        "股票代號": stock,
                        "股票名稱": name_dict.get(stock, ""),
                        "日期": str(last_date9)[:10],
                        "今日最高": round(today_high9, 2),
                        "收盤價": round(today_close9, 2),
                        "拉回幅度": f"{pullback*100:.1f}%",
                        "漲跌幅": f"{change_pct9*100:.1f}%",
                    })
            except:
                continue

        s9.sort(key=lambda x: float(x["拉回幅度"].replace("%", "")), reverse=True)

    except Exception as e9:
        print(f"興櫃拉回錯誤: {e9}")
        s9 = []

    return s1, s2, s3, s4, s5, s6, s7, s8, s9



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
    s1, s2, s3, s4, s5, s6, s7, s8, s9 = get_cached_data()
    update_time = datetime.now().strftime("%Y-%m-%d %H:%M")
    return render_template_string(HOME_TEMPLATE, counts=[len(s1), len(s2), len(s3), len(s4), len(s5), len(s6), len(s7), len(s8), len(s9)], update_time=update_time)

@app.route("/strategy/<int:sid>")
def strategy(sid):
    s1, s2, s3, s4, s5, s6, s7, s8, s9 = get_cached_data()
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
            "stocks": s8, "columns": ["股票代號", "股票名稱", "日期", "收盤價", "漲幅", "成交張數", "5日均量(張)", "爆量倍數"]},
        9: {"title": "興櫃當天拉回", "icon": "📉", "desc": "興櫃股票當天從最高點拉回幅度≥25%，拉回最多的在前",
            "stocks": s9, "columns": ["股票代號", "股票名稱", "日期", "今日最高", "收盤價", "拉回幅度", "漲跌幅"]},
    }

    if sid not in strategies:
        return "找不到此策略", 404

    s = strategies[sid]
    return render_template_string(DETAIL_TEMPLATE, update_time=update_time, **s)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"🚀 啟動中，請用瀏覽器開啟 http://127.0.0.1:{port}")
    app.run(host="0.0.0.0", port=port, debug=False)
