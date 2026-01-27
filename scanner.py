import yfinance as yf
import pandas as pd
import pandas_ta as ta
import requests
import smtplib
from email.mime.text import MIMEText
from email.header import Header
import os

# === 🎯 扫描目标 ===
tickers = [
    "BBAI", "IVDA", "MARA", "CLSK", "COIN", "MSTR", 
    "SOUN", "PLTR", "AI", "AMD", "NVDA", "YINN", "BABA", "GME"
]

print(f"🚀 正在扫描...")
results = []

try:
    data = yf.download(tickers, period="3mo", interval="1d", group_by='ticker', progress=False)
    for symbol in tickers:
        try:
            df = data[symbol].copy()
            if len(df) < 20: continue
            
            price = df['Close'].iloc[-1]
            change_pct = ((price - df['Close'].iloc[-2]) / df['Close'].iloc[-2]) * 100
            rsi = ta.rsi(df['Close'], length=14).iloc[-1]
            
            avg_vol = df['Volume'].iloc[-11:-1].mean()
            vol_ratio = df['Volume'].iloc[-1] / avg_vol if avg_vol > 0 else 0

            signal = "⚪"
            if vol_ratio > 1.5 and change_pct > 3: signal = "🔥 追涨"
            elif rsi < 30: signal = "🟢 抄底"
            elif rsi > 75: signal = "🔴 逃顶"

            if signal != "⚪" or symbol in ["BBAI", "IVDA"]:
                results.append({
                    "Stock": symbol, 
                    "Price": price, 
                    "Chg": change_pct, 
                    "Signal": signal
                })
        except: continue
except: pass

# === 生成报告 ===
if results:
    df_res = pd.DataFrame(results)
    
    msg_content = "💰 搞钱机会扫描 💰\n\n"
    for _, row in df_res.iterrows():
        icon = row['Signal'].split(' ')[0]
        msg_content += f"{icon} {row['Stock']}: ${row['Price']:.2f} ({row['Chg']:+.1f}%)\n"
        msg_content += f"   信号: {row['Signal']}\n\n"
    
    print(msg_content)
    
    # 1. 推送电报
    tg_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    tg_chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if tg_token and tg_chat_id:
        try:
            url = f"https://api.telegram.org/bot{tg_token}/sendMessage"
            requests.post(url, data={"chat_id": tg_chat_id, "text": msg_content})
            print("✅ 电报推送成功")
        except: print("❌ 电报推送失败")

    # 2. 推送 QQ 邮箱
    mail_user = os.environ.get("MAIL_USER")
    mail_pass = os.environ.get("MAIL_PASS")
    
    if mail_user and mail_pass:
        try:
            message = MIMEText(msg_content, 'plain', 'utf-8')
            message['From'] = Header("Github搞钱助手", 'utf-8')
            message['To'] = Header("Boss", 'utf-8')
            message['Subject'] = Header('🔥 今日美股机会报告', 'utf-8')
            
            smtpObj = smtplib.SMTP_SSL('smtp.qq.com', 465)
            smtpObj.login(mail_user, mail_pass)
            smtpObj.sendmail(mail_user, [mail_user], message.as_string())
            print("✅ 邮件发送成功")
        except Exception as e:
            print(f"❌ 邮件发送失败: {e}")
    else:
        print("⚠️ 未配置邮箱 Secret，跳过邮件发送")
else:
    print("无机会。")
