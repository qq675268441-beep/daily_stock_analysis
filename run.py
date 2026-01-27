import os
import sys
import yfinance as yf
import pandas as pd
import requests
import smtplib
from email.mime.text import MIMEText
from email.header import Header

# === 🎯 扫描目标 ===
tickers = ["BBAI", "IVDA", "MARA", "CLSK", "COIN", "SOUN", "PLTR", "AI", "AMD", "NVDA", "YINN", "BABA", "GME"]

print(f"🚀 开始扫描 {len(tickers)} 只股票 (轻量版)...")
results = []

try:
    # 下载数据
    data = yf.download(tickers, period="3mo", interval="1d", group_by='ticker', progress=False)
    
    for symbol in tickers:
        try:
            df = data[symbol].copy()
            if len(df) < 20: continue
            
            # --- 手动计算指标 (不依赖第三方库) ---
            close = df['Close']
            price = close.iloc[-1]
            prev = close.iloc[-2]
            chg = ((price - prev) / prev) * 100
            
            # 1. 手写 RSI 算法
            delta = close.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            current_rsi = rsi.iloc[-1]
            
            # 2. 简单的量比
            vol = df['Volume']
            vol_avg = vol.iloc[-11:-1].mean()
            vol_ratio = vol.iloc[-1] / vol_avg if vol_avg > 0 else 0

            # --- 信号判定 ---
            signal = "⚪"
            if vol_ratio > 1.5 and chg > 3: signal = "🔥 追涨"
            elif current_rsi < 30: signal = "🟢 抄底"
            elif current_rsi > 75: signal = "🔴 逃顶"

            # 只要有信号，或者是你的持仓，就记录
            if signal != "⚪" or symbol in ["BBAI", "IVDA"]:
                results.append({
                    "Stock": symbol, 
                    "Price": float(price), 
                    "Chg": float(chg), 
                    "Signal": signal
                })
        except Exception as e:
            continue

except Exception as e:
    print(f"扫描出错: {e}")

# === 生成报告 ===
if results:
    df_res = pd.DataFrame(results)
    msg = "💰 搞钱扫描 (无敌版) 💰\n\n"
    for _, r in df_res.iterrows():
        msg += f"{r['Signal'].split(' ')[0]} {r['Stock']}: ${r['Price']:.2f} ({r['Chg']:+.1f}%)\n   {r['Signal']}\n\n"
    
    print(msg)

    # 1. Telegram 推送
    tg_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    tg_chat = os.environ.get("TELEGRAM_CHAT_ID")
    if tg_token and tg_chat:
        try:
            requests.post(f"https://api.telegram.org/bot{tg_token}/sendMessage", data={"chat_id": tg_chat, "text": msg})
            print("✅ TG 发送成功")
        except: pass

    # 2. QQ 邮箱推送
    m_user = os.environ.get("MAIL_USER")
    m_pass = os.environ.get("MAIL_PASS")
    if m_user and m_pass:
        try:
            email = MIMEText(msg, 'plain', 'utf-8')
            email['From'] = Header("搞钱助手", 'utf-8')
            email['To'] = Header("Boss", 'utf-8')
            email['Subject'] = Header('🔥 美股扫描结果', 'utf-8')
            
            smtp = smtplib.SMTP_SSL('smtp.qq.com', 465)
            smtp.login(m_user, m_pass)
            smtp.sendmail(m_user, [m_user], email.as_string())
            print("✅ 邮件发送成功")
        except: pass
else:
    print("无机会")
