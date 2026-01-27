import os
import sys
import yfinance as yf
import pandas as pd
import requests
import smtplib
from email.mime.text import MIMEText
from email.utils import formataddr  # 👈 新增这个工具

# === 🎯 扫描目标 ===
tickers = ["BBAI", "IVDA", "MARA", "CLSK", "COIN", "SOUN", "PLTR", "AI", "AMD", "NVDA", "YINN", "BABA", "GME"]

print(f"🚀 开始扫描 {len(tickers)} 只股票...")
results = []

try:
    data = yf.download(tickers, period="3mo", interval="1d", group_by='ticker', progress=False)
    for symbol in tickers:
        try:
            df = data[symbol].copy()
            if len(df) < 20: continue
            
            price = df['Close'].iloc[-1]
            prev = df['Close'].iloc[-2]
            chg = ((price - prev) / prev) * 100
            
            # 简单的 RSI 算法
            delta = df['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            current_rsi = rsi.iloc[-1]
            
            # 量比
            vol_avg = df['Volume'].iloc[-11:-1].mean()
            vol_ratio = df['Volume'].iloc[-1] / vol_avg if vol_avg > 0 else 0

            signal = "⚪"
            if vol_ratio > 1.5 and chg > 3: signal = "🔥 追涨"
            elif current_rsi < 30: signal = "🟢 抄底"
            elif current_rsi > 75: signal = "🔴 逃顶"

            if signal != "⚪" or symbol in ["BBAI", "IVDA", "COIN", "GME"]:
                results.append({"Stock": symbol, "Price": float(price), "Chg": float(chg), "Signal": signal})
        except: continue
except: pass

# === 生成报告 ===
if results:
    df_res = pd.DataFrame(results)
    msg = "💰 搞钱扫描 (最终版) 💰\n\n"
    for _, r in df_res.iterrows():
        msg += f"{r['Signal'].split(' ')[0]} {r['Stock']}: ${r['Price']:.2f} ({r['Chg']:+.1f}%)\n   {r['Signal']}\n\n"
    
    print(msg)

    # 1. Telegram
    tg_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    tg_chat = os.environ.get("TELEGRAM_CHAT_ID")
    if tg_token and tg_chat:
        try:
            requests.post(f"https://api.telegram.org/bot{tg_token}/sendMessage", data={"chat_id": tg_chat, "text": msg})
            print("✅ TG 发送成功")
        except: pass

    # 2. QQ 邮箱
    print("-" * 20)
    m_user = os.environ.get("MAIL_USER")
    m_pass = os.environ.get("MAIL_PASS")
    
    if m_user and m_pass:
        try:
            email = MIMEText(msg, 'plain', 'utf-8')
            # 👇 关键修改：用标准格式生成发件人
            email['From'] = formataddr(["搞钱助手", m_user])
            email['To'] = formataddr(["Boss", m_user])
            email['Subject'] = "🔥 美股机会报告"
            
            smtp = smtplib.SMTP_SSL('smtp.qq.com', 465)
            smtp.login(m_user, m_pass)
            smtp.sendmail(m_user, [m_user], email.as_string())
            print("✅ 邮件发送成功！")
            smtp.quit()
        except Exception as e:
            print(f"❌ 发送报错: {e}")
    else:
        print("⚠️ 邮箱未配置")
else:
    print("无机会")
