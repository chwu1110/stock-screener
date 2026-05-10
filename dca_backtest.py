"""
定期定額回測：0050 vs 0051/006201
回測期間：2015-01-01 ~ 2025-12-31
每月1日（或最近交易日）買入1萬元
"""

import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import os
import finlab
from finlab import data
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from datetime import date
import warnings
warnings.filterwarnings("ignore")

# ── 登入 ──────────────────────────────────────────────
FINLAB_API_KEY = "LBmwu3n0/lor77y1Z0aBH/Q0WBI6+bLJrA2TlchZAM1jb6jJaURRbaQRZRWjozwP#vip_m"
finlab.login(FINLAB_API_KEY)

# ── 參數 ──────────────────────────────────────────────
START_DATE   = "2015-01-01"
END_DATE     = "2025-04-30"   # 抓到目前最新
MONTHLY_AMT  = 10_000          # 每月定投金額

STRATEGY_A = {"code": "0050", "name": "元大台灣50 (0050)"}
STRATEGY_B_CANDIDATES = [
    {"code": "0051", "name": "元大中型100 (0051)"},
    {"code": "006201", "name": "元大富櫃50 (006201)"},
]

# ── 字型（Windows 中文）──────────────────────────────
def setup_chinese_font():
    for name in ["Microsoft JhengHei", "Microsoft YaHei", "SimHei", "Arial Unicode MS"]:
        try:
            prop = fm.FontProperties(family=name)
            plt.rcParams["font.family"] = prop.get_name()
            plt.rcParams["axes.unicode_minus"] = False
            return name
        except Exception:
            pass
    return None

font_name = setup_chinese_font()

# ── 抓價格資料 ─────────────────────────────────────────
print("正在載入收盤價資料...")
close = data.get("price:收盤價")
close = close.index_str_to_date()
close = close.loc[START_DATE:END_DATE]

# ── 選 0051 或 006201 ────────────────────────────────
strategy_b = None
for cand in STRATEGY_B_CANDIDATES:
    if cand["code"] in close.columns:
        col = close[cand["code"]].dropna()
        if len(col) >= 100:
            strategy_b = cand
            break

if strategy_b is None:
    raise RuntimeError("無法取得 0051 或 006201 的足夠資料")

print(f"策略A: {STRATEGY_A['name']}")
print(f"策略B: {strategy_b['name']}")

# ── DCA 回測核心 ──────────────────────────────────────
def dca_backtest(price_series: pd.Series, monthly_amt: int, start: str, end: str) -> pd.DataFrame:
    """
    每月1日（若非交易日則取下一個最近交易日）定投 monthly_amt 元。
    回傳每個交易日的持倉市值 DataFrame。
    """
    s = price_series.loc[start:end].dropna()
    trading_days = s.index

    # 產生所有月份的買入日期（每月1日）
    months = pd.date_range(start=start, end=end, freq="MS")  # Month Start

    records = []
    shares_held = 0.0
    total_invested = 0.0

    buy_dates = set()
    for m in months:
        # 找 >= m 的第一個交易日
        future = trading_days[trading_days >= m]
        if len(future) == 0:
            continue
        buy_date = future[0]
        buy_dates.add(buy_date)

    buy_dates = sorted(buy_dates)

    # 每個交易日計算市值
    invested_at_date = {}
    shares_at_date   = {}
    running_invested = 0.0
    running_shares   = 0.0

    buy_map = {}
    for bd in buy_dates:
        if bd in s.index:
            price = s.loc[bd]
            bought_shares = monthly_amt / price
            buy_map[bd] = (price, bought_shares)

    for d in trading_days:
        if d in buy_map:
            price, bought = buy_map[d]
            running_shares   += bought
            running_invested += monthly_amt

        if running_shares > 0:
            market_value = running_shares * s.loc[d]
        else:
            market_value = 0.0

        records.append({
            "date":        d,
            "invested":    running_invested,
            "market_value": market_value,
            "shares":      running_shares,
        })

    df = pd.DataFrame(records).set_index("date")
    df["profit"] = df["market_value"] - df["invested"]
    df["return_pct"] = (df["profit"] / df["invested"].replace(0, np.nan)) * 100
    return df

# ── 執行回測 ──────────────────────────────────────────
print("\n執行回測中...")
df_a = dca_backtest(close[STRATEGY_A["code"]],  MONTHLY_AMT, START_DATE, END_DATE)
df_b = dca_backtest(close[strategy_b["code"]],  MONTHLY_AMT, START_DATE, END_DATE)

# ── 計算年化報酬 ──────────────────────────────────────
def annualized_return(df: pd.DataFrame) -> float:
    first_invest = df[df["invested"] > 0].index[0]
    last_date    = df.index[-1]
    years = (last_date - first_invest).days / 365.25
    if years <= 0 or df["invested"].iloc[-1] <= 0:
        return 0.0
    final_mv  = df["market_value"].iloc[-1]
    total_inv = df["invested"].iloc[-1]
    # 用 XIRR 簡化：假設等額月投，以最終市值近似年化
    # 簡易公式：(MV/Invested)^(1/years) - 1
    return ((final_mv / total_inv) ** (1 / years) - 1) * 100

ann_a = annualized_return(df_a)
ann_b = annualized_return(df_b)

# ── 文字報告 ──────────────────────────────────────────
def print_report(name: str, df: pd.DataFrame, ann: float):
    last = df.iloc[-1]
    total_inv  = last["invested"]
    total_mv   = last["market_value"]
    total_prof = last["profit"]
    ret_pct    = last["return_pct"]
    months     = (df.index[-1] - df[df["invested"] > 0].index[0]).days // 30

    print(f"""
{'='*55}
  {name}
{'='*55}
  回測期間   : {df[df['invested']>0].index[0].date()} ~ {df.index[-1].date()}
  投入月數   : {months} 個月
  總投入金額 : NT$ {total_inv:>12,.0f}
  最終市值   : NT$ {total_mv:>12,.0f}
  總獲利     : NT$ {total_prof:>12,.0f}
  累積報酬率 : {ret_pct:>8.2f} %
  年化報酬率 : {ann:>8.2f} % (簡易估算)
{'='*55}""")

print_report(STRATEGY_A["name"],  df_a, ann_a)
print_report(strategy_b["name"],  df_b, ann_b)

# 比較
print(f"""
{'─'*55}
  策略比較摘要
{'─'*55}
  {'策略':<20} {'累積報酬率':>10}  {'年化報酬率':>10}
  {STRATEGY_A['name']:<20} {df_a['return_pct'].iloc[-1]:>9.2f}%  {ann_a:>9.2f}%
  {strategy_b['name']:<20} {df_b['return_pct'].iloc[-1]:>9.2f}%  {ann_b:>9.2f}%
{'─'*55}
""")

# ── 折線圖 ────────────────────────────────────────────
print("繪製圖表...")
fig, axes = plt.subplots(2, 1, figsize=(14, 10), dpi=120)
fig.suptitle("定期定額回測比較：台灣加權(0050) vs 上櫃/中型(0051/006201)\n2015–2025 每月投入 NT$10,000",
             fontsize=13, fontweight="bold")

# 上圖：資產成長
ax1 = axes[0]
ax1.plot(df_a.index, df_a["market_value"] / 1_000, label=f"{STRATEGY_A['name']} 市值", color="#E05C5C", lw=2)
ax1.plot(df_b.index, df_b["market_value"] / 1_000, label=f"{strategy_b['name']} 市值", color="#4C7FBF", lw=2)
ax1.plot(df_a.index, df_a["invested"] / 1_000,     label="總投入成本", color="gray", lw=1.5, ls="--", alpha=0.7)
ax1.set_ylabel("金額（千元）")
ax1.set_title("資產市值成長曲線")
ax1.legend(loc="upper left")
ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x:,.0f}K"))
ax1.grid(True, alpha=0.3)

# 下圖：累積報酬率
ax2 = axes[1]
ax2.plot(df_a.index, df_a["return_pct"], label=f"{STRATEGY_A['name']}", color="#E05C5C", lw=2)
ax2.plot(df_b.index, df_b["return_pct"], label=f"{strategy_b['name']}", color="#4C7FBF", lw=2)
ax2.axhline(0, color="black", lw=0.8, ls="-")
ax2.set_ylabel("累積報酬率 (%)")
ax2.set_title("累積報酬率走勢")
ax2.legend(loc="upper left")
ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x:.0f}%"))
ax2.grid(True, alpha=0.3)

# 標註最終數值
for ax, df, color in [(ax1, df_a, "#E05C5C"), (ax1, df_b, "#4C7FBF"),
                       (ax2, df_a, "#E05C5C"), (ax2, df_b, "#4C7FBF")]:
    last_d = df.index[-1]
    if ax == ax1:
        val = df["market_value"].iloc[-1] / 1_000
        ax.annotate(f"{val:,.0f}K", xy=(last_d, val),
                    xytext=(10, 0), textcoords="offset points",
                    color=color, fontsize=8, va="center")
    else:
        val = df["return_pct"].iloc[-1]
        ax.annotate(f"{val:.1f}%", xy=(last_d, val),
                    xytext=(10, 0), textcoords="offset points",
                    color=color, fontsize=8, va="center")

plt.tight_layout()
out_path = os.path.join(os.path.dirname(__file__), "dca_backtest_result.png")
plt.savefig(out_path, bbox_inches="tight")
print(f"\n圖表已儲存：{out_path}")
plt.close()

# ── 年度績效表 ────────────────────────────────────────
print("\n--- 各年度末累積報酬率 ---")
print(f"{'年份':<6} {STRATEGY_A['name']:>22} {strategy_b['name']:>24}")
print("─" * 56)
for yr in range(2015, 2026):
    yr_str = str(yr)
    sub_a = df_a[df_a.index.year == yr]
    sub_b = df_b[df_b.index.year == yr]
    if sub_a.empty or sub_b.empty:
        continue
    ra = sub_a["return_pct"].iloc[-1]
    rb = sub_b["return_pct"].iloc[-1]
    print(f"{yr_str:<6} {ra:>20.2f}%  {rb:>22.2f}%")
