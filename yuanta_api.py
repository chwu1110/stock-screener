import os
from datetime import datetime

# 元大 API 設定
ACCOUNT = os.environ.get("YUANTA_ACCOUNT", "A123363332")
PASSWORD = os.environ.get("YUANTA_PASSWORD", "Alex0722$$")
CERT_PATH = os.environ.get("YUANTA_CERT_PATH", r"C:\Users\chaow\OneDrive\Desktop\TWA123363332YU260418.pfx")
CERT_PASSWORD = os.environ.get("YUANTA_CERT_PASSWORD", "Alex0722$$")

def connect_yuanta():
    """建立元大 API 連線"""
    try:
        import SinopacAPI as si  # 元大 Python API 套件
        
        sdk = si.SDK()
        sdk.Login(
            account=ACCOUNT,
            password=PASSWORD,
            cert_path=CERT_PATH,
            cert_password=CERT_PASSWORD
        )
        print(f"✅ 元大 API 連線成功｜{datetime.now().strftime('%H:%M:%S')}")
        return sdk
    except ImportError:
        print("❌ 請先安裝元大 API 套件")
        print("請至元大證券官網下載 Python SDK 並安裝")
        return None
    except Exception as e:
        print(f"❌ 連線失敗：{e}")
        return None

def get_realtime_quote(sdk, stock_id):
    """取得即時報價"""
    try:
        quote = sdk.Quote.GetStockQuote(stock_id)
        return {
            "股票代號": stock_id,
            "即時價格": quote.Close,
            "開盤價": quote.Open,
            "最高價": quote.High,
            "最低價": quote.Low,
            "成交量": quote.Volume,
            "時間": quote.Time,
        }
    except Exception as e:
        print(f"❌ 取得 {stock_id} 報價失敗：{e}")
        return None

if __name__ == "__main__":
    sdk = connect_yuanta()
    if sdk:
        # 測試取得台積電報價
        quote = get_realtime_quote(sdk, "2330")
        if quote:
            print(quote)
