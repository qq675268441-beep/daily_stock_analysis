import os
import sys
import yfinance as yf
import pandas as pd
import requests
import smtplib
from datetime import datetime
from email.mime.text import MIMEText
from email.utils import formataddr

# === 🌍 全球百大核心资产池 (极限扩容版) ===

# 1. 🇨🇳 亚洲战队 (A股核心 + 港股 + 题材)
ASIA_POOL = [
    # --- 👑 A股茅指数/宁组合 (核心资产) ---
    "600519.SS", "000858.SZ", "600809.SS", "600276.SS", "603259.SS", # 茅台/五粮液/汾酒/恒瑞/药明
    "300750.SZ", "002594.SZ", "300014.SZ", "002812.SZ", "600438.SS", # 宁德/比亚迪/亿纬/恩捷/通威
    "601012.SS", "600150.SS", "600030.SS", "300059.SZ", # 隆基/中国船舶/中信/东财
    
    # --- 🇨🇳 中特估/高股息 (银行/石油/运营商) ---
    "601318.SS", "600036.SS", "601398.SS", "601288.SS", "601939.SS", # 平安/招行/工/农/建
    "601857.SS", "600028.SS", "601088.SS", "601899.SS", # 中石油/中石化/神华/紫金
    "601728.SS", "600941.SS", "600050.SS", # 中国电信/移动/联通
    
    # --- 🔥 A股人气妖股 (华为/算力/CPO) ---
    "601127.SS", "000977.SZ", "002230.SZ", "300308.SZ", "002261.SZ", # 赛力斯/浪潮/讯飞/中际/拓维
    "002456.SZ", "601138.SS", "603019.SS", "002475.SZ", # 欧菲光/工富/曙光/立讯
    
    # --- 🇭🇰 港股科网 & 消费 ---
    "0700.HK", "3690.HK", "9988.HK", "1810.HK", "9618.HK", "9888.HK", "1024.HK", # 腾讯/美团/阿里/小米/京东/百度/快手
    "2015.HK", "9868.HK", "9866.HK", "0981.HK", "0992.HK", # 理想/小鹏/蔚来/中芯/联想
    
    # --- 🇭🇰 港股红利 ---
    "0941.HK", "0883.HK", "0005.HK", "1398.HK", "3988.HK" # 移动/海油/汇丰/工行/中行
]

# 2. 🇺🇸 美股战队 (科技 + 芯片 + 妖股 + 传统巨头)
US_POOL = [
    # --- 👑 科技七巨头 (Mag 7) ---
    "NVDA", "TSLA", "AAPL", "MSFT", "GOOG", "AMZN", "META",
    
    # --- 🍟 芯片半导体 ---
    "AMD", "AVGO", "TSM", "QCOM", "INTC", "MU", "TXN", "LRCX", "AMAT", "ARM", "SMCI",
    
    # --- 💰 加密货币 & 金融科技 ---
    "COIN", "MSTR", "MARA", "CLSK", "RIOT", "HOOD", "PYPL", "SQ",
    
    # --- 💊 医药 & 消费 (减肥药/零售) ---
    "LLY", "NVO", "PFE", "MRK", # 礼来/诺和诺德(减肥药双雄)
    "WMT", "COST", "TGT", "KO", "PEP", # 沃尔玛/Costco
    
    # --- 🛢️ 能源 & 银行 ---
    "XOM", "CVX", "JPM", "BAC", "WFC", "BRK-B",
    
    # --- 😈 顶级妖股/中概股 ---
    "GME", "AMC", "DJT", "FFIE", "CVNA", "UPST", "PLTR", "AI", "SOUN", "BBAI", "IVDA",
    "BABA", "PDD", "JD", "NIO", "XPEV", "LI", "BILI", "YINN"
]

# === ⏰ 智能判断当前市场 ===
current_hour = datetime.utcnow().hour
if current_hour < 12:
    TARGET_TICKERS = ASIA_POOL
    MARKET_NAME = "🇨🇳 A股/港股 (百大核心版)"
else:
    TARGET_TICKERS = US_POOL
    MARKET_NAME = "🇺🇸 美股 (百大核心版)"

print(f"🚀 启动！正在扫描 {len(TARGET_TICKERS)} 只全球核心资产...")
results = []

try:
    # ⬇️ 批量下载 (分批处理更稳，这里直接下，若超时则需拆分)
    # 使用线程池或许更快，但为了代码简单稳定，直接请求
    data = yf.download(TARGET_TICKERS, period="60d", interval="1d", group_by='ticker', progress=False)
    
    for symbol in TARGET_TICKERS:
        try:
            df = data[symbol].copy()
            if len(df) < 20: continue
            
            # === 📊 数据计算 ===
            price = df['Close'].iloc[-1]
            prev = df['Close'].iloc[-2]
            chg = ((price - prev) / prev) * 100
            
            # 1. RSI
            delta = df['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            current_rsi = rsi.iloc[-1]
            
            # 2. 量比
            vol_avg = df['Volume'].iloc[-11:-1].mean()
            vol_ratio = df['Volume'].iloc[-1] / vol_avg if vol_avg > 0 else 0

            # === ⚡️ 筛选逻辑 ===
            signal = "⚪"
            
            # 逻辑1: 追涨 (兼顾妖股与蓝筹启动)
            if vol_ratio > 1.5 and chg > 3: 
                signal = "🔥 资金抢筹/追涨"
            
            # 逻辑2: 抄底 (黄金坑)
            elif current_rsi < 30: 
                signal = "🟢 极度超卖/抄底"
            
            # 逻辑3: 逃顶
            elif current_rsi > 80: 
                signal = "🔴 风险提示/逃顶"

            # 💡 筛选规则：只保留有信号的，或者你的重点持仓
            if signal != "⚪" or symbol in ["GME", "BBAI", "IVDA", "600519.SS"]:
                results.append({
                    "Stock": symbol, 
                    "Price": float(price), 
                    "Chg": float(chg), 
                    "Signal": signal
                })
        except: continue
except Exception as e:
    print(f"扫描部分出错: {e}")

# === 📝 生成报告 ===
if results:
    df_res = pd.DataFrame(results)
    df_res = df_res.sort_values(by="Chg", ascending=False)
    
    msg = f"💰 {MARKET_NAME} 深度扫描 💰\n"
    msg += f"⏰ {datetime.now().strftime('%m-%d %H:%M')}\n"
    msg += f"🔍 覆盖: {len(TARGET_TICKERS)} 只行业龙头+妖股\n\n"
    
    for _, r in df_res.iterrows():
        icon = r['Signal'].split(' ')[0]
        if icon == "⚪": icon = "👀"
        
        msg += f"{icon} {r['Stock']}: ${r['Price']:.2f} ({r['Chg']:+.2f}%)\n"
        msg += f"   信号: {r['Signal']}\n\n"
    
    print(msg)

    # 推送部分
    tg_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    tg_chat = os.environ.get("TELEGRAM_CHAT_ID")
    if tg_token and tg_chat:
        try:
            requests.post(f"https://api.telegram.org/bot{tg_token}/sendMessage", data={"chat_id": tg_chat, "text": msg})
        except: pass

    m_user = os.environ.get("MAIL_USER")
    m_pass = os.environ.get("MAIL_PASS")
    if m_user and m_pass:
        try:
            email = MIMEText(msg, 'plain', 'utf-8')
            email['From'] = formataddr(["全球百大雷达", m_user])
            email['To'] = formataddr(["Boss", m_user])
            email['Subject'] = f"🚀 {MARKET_NAME} 深度机会"
            
            smtp = smtplib.SMTP_SSL('smtp.qq.com', 465)
            smtp.login(m_user, m_pass)
            smtp.sendmail(m_user, [m_user], email.as_string())
            print("✅ 邮件已发送")
            smtp.quit()
        except: pass
else:
    print("今日扫描完毕，百大核心资产均未触发信号。")
