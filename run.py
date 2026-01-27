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
    msg = "💰 搞钱扫描 (诊断版) 💰\n\n"
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
        except Exception as e: print(f"❌ TG 发送失败: {e}")

    # 2. QQ 邮箱 (开启详细诊断)
    print("-" * 20)
    print("📧 开始尝试发送邮件...")
    
    m_user = os.environ.get("MAIL_USER")
    m_pass = os.environ.get("MAIL_PASS")
    
    # 诊断步骤 1: 检查密钥是否存在
    if not m_user:
        print("❌ 错误: 未找到 MAIL_USER (QQ号)！请去 Settings -> Secrets 检查变量名。")
    elif not m_pass:
        print("❌ 错误: 未找到 MAIL_PASS (授权码)！请去 Settings -> Secrets 检查变量名。")
    else:
        print(f"✅ 找到邮箱配置: {m_user[:3]}***@qq.com")
        try:
            email = MIMEText(msg, 'plain', 'utf-8')
            email['From'] = Header("搞钱助手", 'utf-8')
            email['To'] = Header("Boss", 'utf-8')
            email['Subject'] = Header('🔥 美股扫描结果', 'utf-8')
            
            # 诊断步骤 2: 连接服务器
            print("🔄 正在连接 QQ 服务器...")
            smtp = smtplib.SMTP_SSL('smtp.qq.com', 465)
            
            # 诊断步骤 3: 登录
            print("🔄 正在登录...")
            smtp.login(m_user, m_pass)
            
            # 诊断步骤 4: 发送
            print("🔄 正在发送...")
            smtp.sendmail(m_user, [m_user], email.as_string())
            print("✅ 邮件发送成功！快去收信！")
            smtp.quit()
        except smtplib.SMTPAuthenticationError:
            print("❌ 登录失败！原因：授权码错误。请不要用QQ密码，一定要用网页版生成的16位授权码！")
        except Exception as e:
            print(f"❌ 发送过程报错: {e}")

else:
    print("无机会")
