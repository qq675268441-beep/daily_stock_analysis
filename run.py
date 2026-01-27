import os
import sys
import yfinance as yf
import pandas as pd
import requests
import smtplib
from datetime import datetime
from email.mime.text import MIMEText
from email.utils import formataddr

# === 🌍 核心资产池 (Market Radar) ===
# 这里不再是几只股票，而是覆盖核心板块

# 1. 🇨🇳 亚洲战队 (港股 + A股龙头)
ASIA_POOL = [
    # --- 港股科网 ---
    "0700.HK", "3690.HK", "9988.HK", "9888.HK", "1810.HK", "1024.HK", "0992.HK",
    # --- 港股汽车/消费 ---
    "2015.HK", "9866.HK", "9868.HK", "1211.HK", "2331.HK", "1928.HK",
    # --- 港股金融/高息 ---
    "0939.HK", "1398.HK", "0941.HK", "0883.HK", "0005.HK",
    # --- A股核心资产 (茅指数/宁组合) ---
    "600519.SS", "000858.SZ", "300750.SZ", "002594.SZ", "601138.SS", # 茅台/五粮液/宁德/比亚迪/工富
    "600036.SS", "601318.SS", "600276.SS", "603259.SS", "300059.SZ", # 招行/平安/恒瑞/药明/东方财富
    "002475.SZ", "002371.SZ", "600438.SS", "603019.SS", "002230.SZ"  # 立讯/北方华创/通威/曙光/科大讯飞
]

# 2. 🇺🇸 美股战队 (科技 + 芯片 + 加密 + 妖股)
US_POOL = [
    # --- 科技七巨头 (Mag 7) ---
    "NVDA", "AAPL", "MSFT", "GOOG", "AMZN", "META", "TSLA",
    # --- 芯片半导体 ---
    "AMD", "AVGO", "QCOM", "INTC", "TSM", "MU", "ARM", "SMCI", "ASML",
    # --- 加密货币概念 ---
    "COIN", "MSTR", "MARA", "CLSK", "RIOT", "HOOD",
    # --- AI 应用/SaaS ---
    "PLTR", "AI", "SOUN", "BBAI", "SNOW", "CRWD", "PATH", "U",
    # --- 热门中概股 ---
    "BABA", "PDD", "JD", "BIDU", "NIO", "XPEV", "LI", "YINN", "BILI",
    # --- 散户妖股 (Meme) ---
    "GME", "AMC", "DJT", "IVDA", "FFIE", "OPEN"
]

# === ⏰ 智能切换 ===
current_hour = datetime.utcnow().hour
if current_hour < 12:
    TARGET_TICKERS = ASIA_POOL
    MARKET_NAME = "🇨🇳 A股/港股 (全雷达)"
else:
    TARGET_TICKERS = US_POOL
    MARKET_NAME = "🇺🇸 美股 (全雷达)"

print(f"🚀 雷达启动！正在扫描 {len(TARGET_TICKERS)} 只核心股票...")
print(f"🔍 筛选逻辑: 1. RSI<30 (超卖抄底)  2. 量比>1.8 + 涨幅>2.5% (主力追涨)")
results = []

try:
    # 批量下载数据 (分批处理防止超时，这里一次性下，因为列表不算太大)
    data = yf.download(TARGET_TICKERS, period="60d", interval="1d", group_by='ticker', progress=False)
    
    for symbol in TARGET_TICKERS:
        try:
            df = data[symbol].copy()
            if len(df) < 20: continue
            
            # === 核心数据计算 ===
            price = df['Close'].iloc[-1]
            prev = df['Close'].iloc[-2]
            chg = ((price - prev) / prev) * 100
            
            # RSI 指标
            delta = df['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            current_rsi = rsi.iloc[-1]
            
            # 量比指标
            vol_avg = df['Volume'].iloc[-11:-1].mean()
            vol_ratio = df['Volume'].iloc[-1] / vol_avg if vol_avg > 0 else 0
            
            # 均线 (辅助判断)
            ma20 = df['Close'].rolling(window=20).mean().iloc[-1]

            # === ⚡️ 筛选器逻辑 (只输出符合条件的) ===
            signal = "⚪"
            
            # 🎯 逻辑1: 暴力追涨 (有人抢筹)
            # 条件: 量比大于1.8 (放量) + 涨幅大于2.5% + 价格在20日线上(趋势好)
            if vol_ratio > 1.8 and chg > 2.5 and price > ma20:
                signal = "🔥 主力抢筹(追)"
            
            # 🎯 逻辑2: 极度超卖 (黄金坑)
            # 条件: RSI 小于 30 (严重超卖)
            elif current_rsi < 30:
                signal = "🟢 极度超卖(抄)"
            
            # 🎯 逻辑3: 逃顶提示
            elif current_rsi > 80:
                signal = "🔴 风险提示(逃)"

            # 💡 关键修改：只有产生【特定信号】的股票才会被放入报告
            # 那些横盘的、没信号的，直接过滤掉，不打扰你
            if signal != "⚪":
                results.append({
                    "Stock": symbol, 
                    "Price": float(price), 
                    "Chg": float(chg), 
                    "Signal": signal
                })
        except: continue
except Exception as e:
    print(f"扫描出错: {e}")

# === 📝 生成简报 ===
if results:
    df_res = pd.DataFrame(results)
    df_res = df_res.sort_values(by="Chg", ascending=False)
    
    msg = f"💰 {MARKET_NAME} 机会扫描 💰\n"
    msg += f"⏰ {datetime.now().strftime('%m-%d %H:%M')}\n"
    msg += f"🔍 扫描范围: {len(TARGET_TICKERS)} 只核心龙头\n\n"
    
    for _, r in df_res.iterrows():
        icon = r['Signal'].split(' ')[0]
        msg += f"{icon} {r['Stock']}\n"
        msg += f"   现价: {r['Price']:.2f} ({r['Chg']:+.2f}%)\n"
        msg += f"   信号: {r['Signal']}\n\n"
    
    print(msg)

    # 推送代码 (Telegram + Email)
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
            email['From'] = formataddr(["全球雷达", m_user])
            email['To'] = formataddr(["Boss", m_user])
            email['Subject'] = f"🚀 {MARKET_NAME} 机会提醒"
            smtp = smtplib.SMTP_SSL('smtp.qq.com', 465)
            smtp.login(m_user, m_pass)
            smtp.sendmail(m_user, [m_user], email.as_string())
            smtp.quit()
        except: pass
else:
    print("今日扫描完毕，核心资产池内无符合条件的暴涨或超卖机会。")
