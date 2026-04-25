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
            <div class="card-desc">目前正在被處置的股票，且收盤價跌破10日均線（每支只列一筆）</div>
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
            <div class="card-desc">兩個月內曾被處置的股票，股價在20日均線上下6%以內</div>
            <div class="card-count">{{ counts[11] }}</div>
            <div class="card-count-label">符合股票數</div>
            <div style="margin-top:10px;font-size:12px;color:#38bdf8;">🔴 <a href="/strategy/12/realtime" style="color:#38bdf8;">即時版（盤中）</a></div>
        </a>
        <a href="/strategy/13" class="card">
            <div class="card-icon">⏳</div>
            <div class="card-title">20分處置股</div>
            <div class="card-desc">目前正在被處置的股票，依出關日由近到遠排列，含走勢圖</div>
            <div class="card-count">{{ counts[12] }}</div>
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
        .stock-id-cell { display: flex; align-items: center; gap: 8px; }
        .copy-btn {
            background: #1e3a5f; border: 1px solid #2d5a8e; color: #7dd3fc;
            border-radius: 5px; padding: 2px 8px; font-size: 11px; cursor: pointer;
            transition: all 0.15s; white-space: nowrap; flex-shrink: 0;
        }
        .copy-btn:hover { background: #2d5a8e; color: #e0f2fe; }
        .copy-btn.copied { background: #14532d; border-color: #166534; color: #4ade80; }
        .copy-all-btn {
            display: inline-flex; align-items: center; gap: 6px;
            background: #1e3a5f; border: 1px solid #2d5a8e; color: #7dd3fc;
            border-radius: 8px; padding: 7px 16px; font-size: 13px; cursor: pointer;
            margin-bottom: 14px; transition: all 0.15s;
        }
        .copy-all-btn:hover { background: #2d5a8e; color: #e0f2fe; }
        .copy-all-btn.copied { background: #14532d; border-color: #166534; color: #4ade80; }
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
    <div>
        <button class="copy-all-btn" onclick="copyAll(this)">
            <span class="btn-icon">📋</span><span class="btn-text">複製全部代號</span>
        </button>
    </div>
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
                ">
                    {% if col == '股票代號' %}
                    <div class="stock-id-cell">
                        <span>{{ s[col] }}</span>
                        <button class="copy-btn" onclick="copySingle(this, '{{ s[col] }}')">複製</button>
                    </div>
                    {% else %}
                    {{ s[col] }}
                    {% endif %}
                </td>
                {% endfor %}
            </tr>
            {% endfor %}
        </tbody>
    </table>
    {% else %}
    <div class="empty">❌ 沒有找到符合條件的股票</div>
    {% endif %}

    <p class="updated">資料來源：FinLab｜更新時間：{{ update_time }}</p>

    <script>
        function copySingle(btn, code) {
            navigator.clipboard.writeText(code).then(function() {
                btn.textContent = '✓';
                btn.classList.add('copied');
                setTimeout(function() {
                    btn.textContent = '複製';
                    btn.classList.remove('copied');
                }, 1500);
            }).catch(function() {
                fallbackCopy(code);
                btn.textContent = '✓';
                btn.classList.add('copied');
                setTimeout(function() {
                    btn.textContent = '複製';
                    btn.classList.remove('copied');
                }, 1500);
            });
        }

        function copyAll(btn) {
            var codes = [];
            document.querySelectorAll('tbody .stock-id-cell span').forEach(function(el) {
                codes.push(el.textContent.trim());
            });
            var text = codes.join('\\n');
            navigator.clipboard.writeText(text).then(function() {
                showCopied(btn, codes.length);
            }).catch(function() {
                fallbackCopy(text);
                showCopied(btn, codes.length);
            });
        }

        function showCopied(btn, count) {
            btn.querySelector('.btn-icon').textContent = '✓';
            btn.querySelector('.btn-text').textContent = '已複製 ' + count + ' 個代號';
            btn.classList.add('copied');
            setTimeout(function() {
                btn.querySelector('.btn-icon').textContent = '📋';
                btn.querySelector('.btn-text').textContent = '複製全部代號';
                btn.classList.remove('copied');
            }, 2000);
        }

        function fallbackCopy(text) {
            var ta = document.createElement('textarea');
            ta.value = text;
            ta.style.position = 'fixed';
            ta.style.opacity = '0';
            document.body.appendChild(ta);
            ta.focus();
            ta.select();
            document.execCommand('copy');
            document.body.removeChild(ta);
        }

        document.querySelectorAll('td').forEach(function(td) {
            if (td.textContent.includes('★')) {
                td.innerHTML = td.innerHTML.replace(/★/g, '<span style="color:#ff4444">★</span>');
            }
        });
    </script>
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
    <p class="subtitle">兩個月內曾被處置的股票，即時股價在20日均線上下6%以內，偏離最小的在前</p>
    <div class="badge">🔴 即時模式｜每5分鐘自動更新</div><br>

    <div class="stat-box">
        <div class="num">{{ stocks|length }}</div>
        <div class="label">符合股票數</div>
    </div>

    {% if stocks %}
    <table>
        <thead>
            <tr>
                <th>股票代號</th><th>股票名稱</th><th>處置期間</th>
                <th>即時股價</th><th>20日均線</th><th>偏離幅度</th><th>資料時間</th>
            </tr>
        </thead>
        <tbody>
            {% for s in stocks %}
            <tr>
                <td class="stock-id">{{ s['股票代號'] }}</td>
                <td>{{ s['股票名稱'] }}</td>
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
    open_1m = open_df[open_df.index >= pd.to_datetime(start_1m)]

    try:
        low_ = data.get("price:最低價")
        low_df = pd.DataFrame(low_.values, index=pd.to_datetime(low_.index.astype(str)), columns=low_.columns)
        low_1m = low_df[low_df.index >= pd.to_datetime(start_1m)]
        print("Daily usage: -- price:最低價 載入完成")
    except Exception as e:
        print(f"price:最低價 載入失敗，改用開盤價判斷: {e}")
        low_1m = None

    def gap_stars(stock, dates):
        """判斷是否為跳空漲停（一價到底）：開盤＝漲停價 且 最低＝漲停價"""
        stars = 0
        for d in dates:
            try:
                idx = close_1m.index.get_loc(d)
                if idx < 1:
                    continue
                prev_c = close_1m[stock].iloc[idx - 1]
                open_p = open_1m[stock].loc[d] if d in open_1m.index else None
                if pd.notna(prev_c) and prev_c > 0 and open_p is not None and pd.notna(open_p):
                    limit_up = round(prev_c * 1.1, 2)
                    if abs(open_p - limit_up) < 0.02:
                        # 有最低價資料就用一價到底判斷，沒有就只用開盤判斷
                        if low_1m is not None and d in low_1m.index:
                            low_p = low_1m[stock].loc[d]
                            if pd.notna(low_p) and abs(low_p - limit_up) < 0.02:
                                stars += 1
                        else:
                            stars += 1
            except:
                pass
        return "★" * stars if stars > 0 else ""


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
                "股票代號": stock, "股票名稱": name_dict.get(stock, "") + gap_stars(stock, [prev_date, date]),
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
                    "股票代號": stock, "股票名稱": name_dict.get(stock, "") + gap_stars(stock, [d1, d2, d3]),
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
                    "股票代號": stock, "股票名稱": name_dict.get(stock, "") + gap_stars(stock, [d1, d2, d3, d4]),
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
                d2 = series.index[idx-3]
                d3 = series.index[idx-2]
                d4 = series.index[idx-1]
                d5 = series.index[idx]
                s6_dict[stock] = {
                    "股票代號": stock, "股票名稱": name_dict.get(stock, "") + gap_stars(stock, [d1, d2, d3, d4, d5]),
                    "第一天": str(d1)[:10], "第五天": str(d5)[:10],
                    "第一天收盤": round(close_1m[stock].loc[d1], 2),
                    "第五天收盤": round(close_1m[stock].loc[d5], 2),
                    "五日累積漲幅": f"{gain*100:.1f}%",
                }

    s6 = list(s6_dict.values())
    s6.sort(key=lambda x: x["第五天"], reverse=True)

    # 去重複：同一支股票只出現在最高等級的策略（五手>四手>三手>二手）
    s6_stocks = set(x["股票代號"] for x in s6)
    s5 = [x for x in s5 if x["股票代號"] not in s6_stocks]
    s5_stocks = set(x["股票代號"] for x in s5)
    s4 = [x for x in s4 if x["股票代號"] not in s6_stocks and x["股票代號"] not in s5_stocks]
    s4_stocks = set(x["股票代號"] for x in s4)
    s1_seen = set()
    s1_new = []
    for x in s1:
        sid = x["股票代號"]
        if sid not in s6_stocks and sid not in s5_stocks and sid not in s4_stocks and sid not in s1_seen:
            s1_new.append(x)
            s1_seen.add(sid)
    s1 = s1_new


    # 策略七：目前正在被處置的股票，且目前收盤價跌破10日線（每支只列一筆）
    s7 = []
    try:
        # 即時抓目前正在處置中的股票清單
        disposal_url = "https://www.twse.com.tw/rwd/zh/announcement/punish?response=json"
        disposal_res = requests.get(disposal_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10, verify=False)
        disposal_data = disposal_res.json()

        disposal_stocks_now = {}
        if disposal_data.get("stat") == "OK":
            for row in disposal_data.get("data", []):
                try:
                    stock_id = row[2].strip()
                    stock_name = row[3].strip()
                    period = row[5].strip() if len(row) > 5 else ""
                    disposal_stocks_now[stock_id] = {"name": stock_name, "period": period}
                except:
                    continue

        for stock_id, info in disposal_stocks_now.items():
            try:
                if stock_id not in close_3m.columns:
                    continue
                prices = close_3m[stock_id].dropna()
                if len(prices) < 10:
                    continue

                ma10 = prices.rolling(10).mean()
                current_price = prices.iloc[-1]
                current_ma10 = ma10.iloc[-1]

                if pd.isna(current_ma10) or current_ma10 <= 0:
                    continue

                # 每支股票只列一筆，看目前最新收盤價是否跌破10日線
                if current_price < current_ma10:
                    diff_pct = (current_price - current_ma10) / current_ma10
                    s7.append({
                        "股票代號": stock_id,
                        "股票名稱": info["name"],
                        "處置期間": info.get("period", ""),
                        "目前收盤價": round(current_price, 2),
                        "10日均線": round(current_ma10, 2),
                        "跌破幅度": f"{diff_pct*100:.1f}%",
                    })
            except:
                continue

        # 跌破幅度最大的排前面
        s7.sort(key=lambda x: float(x["跌破幅度"].replace("%", "")))

    except Exception as e:
        print(f"處置股10日線策略失敗: {e}")
        s7 = []




    s8 = []
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

                if abs(diff_pct) <= 0.06:
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

    # 策略十三：20分處置股 - 目前正在被處置，依出關日由近到遠排列（上市＋上櫃）
    s13 = []
    s13_seen = set()

    def parse_roc_date(s):
        try:
            parts = s.strip().split("/")
            y = int(parts[0]) + 1911
            return datetime(y, int(parts[1]), int(parts[2]))
        except:
            return None

    def parse_s13_row(stock_id, stock_name, period, content):
        """解析一筆處置股資料，回傳 dict 或 None"""
        if "二十分鐘" not in content:
            return None
        if stock_id in s13_seen:
            return None
        sep = "～" if "～" in period else ("~" if "~" in period else "")
        end_str   = period.split(sep)[-1].strip() if sep else ""
        start_str = period.split(sep)[0].strip() if sep else ""
        end_date   = parse_roc_date(end_str)
        start_date = parse_roc_date(start_str)
        if end_date is None:
            return None
        today13 = datetime.now().date()
        days_left = (end_date.date() - today13).days
        if stock_id not in close_3m.columns:
            return None
        prices = close_3m[stock_id].dropna()
        if len(prices) < 10:
            return None
        ma10 = prices.rolling(10).mean()
        ma20 = prices.rolling(20).mean()
        current_price = round(float(prices.iloc[-1]), 2)
        current_ma10  = round(float(ma10.iloc[-1]), 2) if not pd.isna(ma10.iloc[-1]) else None
        current_ma20  = round(float(ma20.iloc[-1]), 2) if not pd.isna(ma20.iloc[-1]) else None
        return {
            "股票代號": stock_id,
            "股票名稱": stock_name,
            "處置期間": period,
            "出關日期": end_date.strftime("%Y-%m-%d"),
            "剩餘天數": days_left,
            "目前股價": current_price,
            "10日均線": current_ma10,
            "月線(MA20)": current_ma20,
            "處置開始日": start_date.strftime("%Y-%m-%d") if start_date else "",
        }

    try:
        # ── 上市（TWSE） ──
        twse_res = requests.get("https://www.twse.com.tw/rwd/zh/announcement/punish?response=json",
                                headers={"User-Agent": "Mozilla/5.0"}, timeout=10, verify=False)
        twse_data = twse_res.json()
        if twse_data.get("stat") == "OK":
            for row in twse_data.get("data", []):
                try:
                    stock_id   = row[2].strip()
                    stock_name = row[3].strip()
                    period     = row[6].strip() if len(row) > 6 else ""
                    content    = row[8].strip() if len(row) > 8 else ""
                    rec = parse_s13_row(stock_id, stock_name, period, content)
                    if rec:
                        s13.append(rec)
                        s13_seen.add(stock_id)
                except:
                    continue
    except Exception as e:
        print(f"策略13 TWSE 失敗: {e}")

    try:
        # ── 上櫃（OTC/TPEX） ──
        otc_res = requests.get("https://www.tpex.org.tw/web/bulletin/disposal/disposal_ajax.php?l=zh-tw",
                               headers={"User-Agent": "Mozilla/5.0"}, timeout=10, verify=False)
        otc_data = otc_res.json()
        # TPEX 回傳格式：{"aaData": [[...], ...]}
        rows_otc = otc_data.get("aaData", otc_data.get("data", []))
        for row in rows_otc:
            try:
                stock_id   = str(row[2]).strip()
                stock_name = str(row[3]).strip()
                period     = str(row[6]).strip() if len(row) > 6 else ""
                content    = str(row[8]).strip() if len(row) > 8 else ""
                rec = parse_s13_row(stock_id, stock_name, period, content)
                if rec:
                    s13.append(rec)
                    s13_seen.add(stock_id)
            except:
                continue
    except Exception as e:
        print(f"策略13 OTC 失敗: {e}")

    s13.sort(key=lambda x: x["剩餘天數"])
        s13 = []

    return s1, s2, s3, s4, s5, s6, s7, s8, s9, s10, s11, s12, s13






# 快取資料
_cache = {"data": None, "time": None}
_global_disposal_2m = {}
_global_close_3m = None
_cache_lock = __import__("threading").Lock()
_cache_loading = False

def _refresh_cache():
    """背景執行緒：下載資料並更新快取"""
    global _cache_loading
    try:
        _cache_loading = True
        print("背景快取：開始更新資料...")
        new_data = get_all_data()
        with _cache_lock:
            _cache["data"] = new_data
            _cache["time"] = datetime.now()
        print("背景快取：更新完成")
    except Exception as e:
        print(f"背景快取更新失敗: {e}")
    finally:
        _cache_loading = False

def _schedule_refresh():
    """定時每30分鐘更新一次"""
    import threading
    _refresh_cache()
    t = threading.Timer(1800, _schedule_refresh)
    t.daemon = True
    t.start()

def get_cached_data():
    with _cache_lock:
        data = _cache["data"]
    if data is None:
        # 資料還沒準備好，回傳空的
        return [], [], [], [], [], [], [], [], [], [], [], [], []
    return data

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

            if abs(diff_pct) <= 0.06:
                s12_rt.append({
                    "股票代號": stock_id,
                    "股票名稱": info.get("name", ""),
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

@app.route("/")
def home():
    s1, s2, s3, s4, s5, s6, s7, s8, s9, s10, s11, s12, s13 = get_cached_data()
    update_time = datetime.now().strftime("%Y-%m-%d %H:%M")
    if all(len(x) == 0 for x in [s1, s2, s3, s4, s5, s6, s7, s10, s12, s13]) and _cache_loading:
        return "<html><body style='background:#0f172a;color:#e2e8f0;font-family:Microsoft JhengHei;padding:60px;text-align:center'><h2>⏳ 資料載入中，請稍候1~2分鐘後重新整理...</h2></body></html>"
    return render_template_string(HOME_TEMPLATE, counts=[len(s1), len(s2), len(s3), len(s4), len(s5), len(s6), len(s7), 0, 0, len(s10), 0, len(s12), len(s13)], update_time=update_time)

@app.route("/strategy/<int:sid>")
def strategy(sid):
    s1, s2, s3, s4, s5, s6, s7, s8, s9, s10, s11, s12, s13 = get_cached_data()
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
        7: {"title": "處置股跌破10日線", "icon": "⚠️", "desc": "目前正在被處置的股票，且目前收盤價跌破10日均線，每支只列一筆，跌破幅度最大的在前",
            "stocks": s7, "columns": ["股票代號", "股票名稱", "處置期間", "目前收盤價", "10日均線", "跌破幅度"]},
        10: {"title": "處置股拉回", "icon": "🔻", "desc": "兩個月內曾被處置的股票，連續下跌5天，跌最多的在前",
            "stocks": s10, "columns": ["股票代號", "股票名稱", "處置期間", "目前股價", "5日前股價", "5日跌幅", "最近下跌日"]},
        12: {"title": "處置股來到月線", "icon": "📊", "desc": "兩個月內曾被處置的股票，股價在20日均線上下6%以內，偏離最小的在前",
            "stocks": s12, "columns": ["股票代號", "股票名稱", "處置期間", "目前股價", "20日均線", "偏離幅度"]},
    }

    if sid not in strategies:
        return "找不到此策略", 404

    s = strategies[sid]
    return render_template_string(DETAIL_TEMPLATE, update_time=update_time, **s)


STRATEGY13_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>⏳ 20分處置股</title>
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
        .cards { display: flex; flex-direction: column; gap: 24px; }
        .card { background: #1e293b; border-radius: 14px; padding: 20px 24px; border: 1px solid #334155; }
        .card-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 14px; flex-wrap: wrap; gap: 8px; }
        .card-title { font-size: 17px; font-weight: bold; color: #f1f5f9; }
        .badge-days { padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: bold; }
        .badge-urgent { background: #4c1d1d; color: #f87171; }
        .badge-soon { background: #3d2c00; color: #fbbf24; }
        .badge-ok { background: #1a3a2a; color: #4ade80; }
        .info-row { display: flex; gap: 24px; margin-bottom: 14px; flex-wrap: wrap; }
        .info-item { font-size: 13px; color: #94a3b8; }
        .info-item span { color: #e2e8f0; font-weight: bold; }
        .chart-container { position: relative; height: 220px; background: #0f172a; border-radius: 10px; padding: 10px; }
        canvas { width: 100% !important; }
        .empty { text-align: center; color: #94a3b8; padding: 40px; background: #1e293b; border-radius: 12px; }
        .updated { text-align: center; color: #475569; font-size: 12px; margin-top: 20px; }
        .disposal-start-line { color: #f87171; font-size: 12px; margin-top: 6px; }
    </style>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.0/chart.umd.min.js"></script>
</head>
<body>
    <a class="back" href="/">← 返回首頁</a>
    <h1>⏳ 20分處置股</h1>
    <p class="subtitle">目前正在被處置的股票（僅限20分鐘搓合），依出關日由近到遠排列。圖表顯示處置前5天＋處置期間走勢，含10日線（橘）與月線（藍）。</p>
    <div class="stat-box"><div class="num">{{ stocks|length }}</div><div class="label">目前處置中股票數</div></div>

    {% if stocks %}
    <div class="cards">
    {% for s in stocks %}
    <div class="card">
        <div class="card-header">
            <div class="card-title">{{ s.股票代號 }} {{ s.股票名稱 }}</div>
            <span class="badge-days {% if s.剩餘天數 <= 3 %}badge-urgent{% elif s.剩餘天數 <= 7 %}badge-soon{% else %}badge-ok{% endif %}">
                出關：{{ s.出關日期 }}（剩 {{ s.剩餘天數 }} 天）
            </span>
        </div>
        <div class="info-row">
            <div class="info-item">處置期間 <span>{{ s.處置期間 }}</span></div>
            <div class="info-item">目前股價 <span>{{ s.目前股價 }}</span></div>
            {% if s["10日均線"] %}<div class="info-item">10日線 <span style="color:#fb923c;">{{ s["10日均線"] }}</span></div>{% endif %}
            {% if s["月線(MA20)"] %}<div class="info-item">月線 <span style="color:#60a5fa;">{{ s["月線(MA20)"] }}</span></div>{% endif %}
        </div>
        <div class="chart-container">
            <canvas id="chart_{{ loop.index }}"></canvas>
        </div>
        {% if s.chart_data %}
        <script>
        (function(){
            var cd = {{ s.chart_data | tojson }};
            var ctx = document.getElementById("chart_{{ loop.index }}").getContext("2d");
            new Chart(ctx, {
                type: "line",
                data: {
                    labels: cd.labels,
                    datasets: [
                        { label: "收盤價", data: cd.close, borderColor: "#e2e8f0", borderWidth: 2, pointRadius: 3, pointBackgroundColor: "#e2e8f0", tension: 0.2, fill: false },
                        { label: "10日線", data: cd.ma10, borderColor: "#fb923c", borderWidth: 1.5, pointRadius: 0, tension: 0.2, fill: false, borderDash: [] },
                        { label: "月線MA20", data: cd.ma20, borderColor: "#60a5fa", borderWidth: 1.5, pointRadius: 0, tension: 0.2, fill: false, borderDash: [] }
                    ]
                },
                options: {
                    responsive: true, maintainAspectRatio: false,
                    animation: false,
                    plugins: {
                        legend: { labels: { color: "#94a3b8", font: { size: 11 } } },
                    },
                    scales: {
                        x: { ticks: { color: "#64748b", font: { size: 10 }, maxRotation: 45 }, grid: { color: "#1e293b" } },
                        y: { ticks: { color: "#64748b", font: { size: 10 } }, grid: { color: "#334155" } }
                    }
                }
            });
        })();
        </script>
        {% endif %}
    </div>
    {% endfor %}
    </div>
    {% else %}
    <div class="empty">❌ 目前沒有正在被處置的股票</div>
    {% endif %}
    <p class="updated">更新時間：{{ update_time }}</p>
</body>
</html>
"""

@app.route("/strategy/13")
def strategy13():
    s1, s2, s3, s4, s5, s6, s7, s8, s9, s10, s11, s12, s13 = get_cached_data()
    update_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    close_3m = _global_close_3m

    # 為每支股票準備走勢圖資料（處置前5天 + 處置期間）
    for s in s13:
        try:
            stock_id = s["股票代號"]
            if close_3m is None or stock_id not in close_3m.columns:
                s["chart_data"] = None
                continue

            prices = close_3m[stock_id].dropna()
            prices.index = pd.to_datetime(prices.index)

            # 找處置開始日
            start_dt = pd.to_datetime(s["處置開始日"]) if s["處置開始日"] else None
            end_dt   = pd.to_datetime(s["出關日期"])

            # 用完整歷史資料算MA，確保每個點都有值
            ma10_full = prices.rolling(10).mean()
            ma20_full = prices.rolling(20).mean()

            # 找顯示範圍：處置前5天到今天
            today_str = datetime.now().strftime("%Y-%m-%d")
            if start_dt is not None:
                pre_idx = prices.index.searchsorted(start_dt)
                pre_start_idx = max(0, pre_idx - 5)
            else:
                pre_start_idx = max(0, len(prices) - 40)

            chart_prices = prices.iloc[pre_start_idx:]
            chart_prices = chart_prices[chart_prices.index <= today_str]
            chart_ma10   = ma10_full.iloc[pre_start_idx:][ma10_full.iloc[pre_start_idx:].index <= today_str]
            chart_ma20   = ma20_full.iloc[pre_start_idx:][ma20_full.iloc[pre_start_idx:].index <= today_str]

            if len(chart_prices) < 2:
                s["chart_data"] = None
                continue

            disposal_start_idx = None
            if start_dt is not None:
                for i, d in enumerate(chart_prices.index):
                    if d >= start_dt:
                        disposal_start_idx = i
                        break

            def to_list(series):
                return [round(v, 2) if not pd.isna(v) else None for v in series]

            s["chart_data"] = {
                "labels": [d.strftime("%m/%d") for d in chart_prices.index],
                "close":  to_list(chart_prices),
                "ma10":   to_list(chart_ma10),
                "ma20":   to_list(chart_ma20),
                "disposal_start_idx": disposal_start_idx,
            }
        except Exception as e:
            s["chart_data"] = None

    return render_template_string(STRATEGY13_TEMPLATE, stocks=s13, update_time=update_time)

# 啟動時在背景開始下載資料（gunicorn 也會執行這段）
import threading as _threading
_bg_thread = _threading.Thread(target=_schedule_refresh, daemon=True)
_bg_thread.start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"🚀 啟動中，請用瀏覽器開啟 http://127.0.0.1:{port}")
    app.run(host="0.0.0.0", port=port, debug=False)
