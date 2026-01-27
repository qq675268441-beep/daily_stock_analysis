import os
import sys

# 1. 尝试导入库，如果失败打印具体原因
try:
    import yfinance as yf
    import pandas as pd
    import pandas_ta as ta
    import requests
    import smtplib
    from email.mime.text import MIMEText
    from email.header import Header
    print("✅ 库导入成功")
except Exception as e:
    print(f"❌ 库导入失败: {e}")
    sys.exit(1)

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
            
            # 简单的 RSI 和量比
            rsi = ta.rsi(df['Close'], length=14).iloc[-1]
            vol_avg = df['Volume'].iloc[-11:-1].mean()
            vol_ratio = df['Volume'].iloc[-1] / vol_avg if vol_avg > 0 else 0

            signal = "⚪"
            if vol_ratio > 1.5 and chg > 3: signal = "🔥 追涨"
            elif rsi < 30: signal = "🟢 抄底"
            elif rsi > 75: signal = "🔴 逃顶"

            # 只要有信号，或者是你的持仓，就记录
            if signal != "⚪" or symbol in ["BBAI", "IVDA"]:
                results.append({"Stock": symbol, "Price": price, "Chg": chg, "Signal": signal})
        except: continue
except Exception as e:
    print(f"⚠️ 扫描过程出错: {e}")

# === 生成报告 ===
if results:
    df_res = pd.DataFrame(results)
    msg = "💰 搞钱扫描报告 💰\n\n"
    for _, r in df_res.iterrows():
        msg += f"{r['Signal'].split(' ')[0]} {r['Stock']}: ${r['Price']:.2f} ({r['Chg']:+.1f}%)\n   {r['Signal']}\n\n"
    
    print("-" * 20)
    print(msg)
    print("-" * 20)

    # 1. Telegram 推送
    tg_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    tg_chat = os.environ.get("TELEGRAM_CHAT_ID")
    if tg_token and tg_chat:
        try:
            requests.post(f"https://api.telegram.org/bot{tg_token}/sendMessage", data={"chat_id": tg_chat, "text": msg})
            print("✅ Telegram 发送成功")
        except Exception as e: print(f"❌ TG 发送失败: {e}")

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
            print("✅ QQ邮件 发送成功")
        except Exception as e: print(f"❌ 邮件发送失败: {e}")
    else:
        print("⚠️ 邮箱没配好，跳过发送")

else:
    print("今天风平浪静，无机会。")
