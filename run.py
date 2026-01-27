import os
import sys
import yfinance as yf
import pandas as pd
import requests
import smtplib
from datetime import datetime
from email.mime.text import MIMEText
from email.utils import formataddr

# === 🌍 全球搞钱目标池 ===

# 1. 亚洲战队 (A股 + 港股) - 下午运行
# .SS=上海, .SZ=深圳, .HK=香港
ASIA_TICKERS = [
    "0700.HK",  # 腾讯
    "3690.HK",  # 美团
    "9888.HK",  # 百度
    "1810.HK",  # 小米
    "0981.HK",  # 中芯国际
    "600519.SS", # 贵州茅台
    "300750.SZ", # 宁德时代
    "601138.SS", # 工业富联 (AI服务器)
    "600036.SS", # 招商银行
    "002594.SZ"  # 比亚迪
]

# 2. 美股战队 - 晚上运行
US_TICKERS = [
    "BBAI", "IVDA", "MARA", "CLSK", "COIN", 
    "SOUN", "PLTR", "AI", "AMD", "NVDA", 
    "YINN", "BABA", "GME", "TSLA", "MSTR"
]

# === ⏰ 智能判断当前市场 ===
# 获取当前 UTC 时间 (GitHub服务器时间)
current_hour = datetime.utcnow().hour

if current_hour < 12:
    # UTC 0点-12点 (北京时间 8点-20点) -> 跑亚洲盘
    TARGET_TICKERS = ASIA_TICKERS
    MARKET_NAME = "🇨🇳 A股/港股"
    print(f"🌞 检测到亚洲时间 (UTC {current_hour}点)，准备扫描 A股和港股...")
else:
    # UTC 12点后 (北京时间 20点后) -> 跑美股盘
    TARGET_TICKERS = US_TICKERS
    MARKET_NAME = "🇺🇸 美股"
    print(f"🌜 检测到美股时间 (UTC {current_hour}点)，准备扫描美股...")

print(f"🚀 开始扫描 {len(TARGET_TICKERS)} 只股票...")
results = []

try:
    # ⬇️ 下载数据 (自动适配不同市场)
    data = yf.download(TARGET_TICKERS, period="3mo", interval="1d", group_by='ticker', progress=False)
    
    for symbol in TARGET_TICKERS:
        try:
            df = data[symbol].copy()
            # 过滤掉刚上市数据不足的
            if len(df) < 20: continue
            
            # 提取价格
            price = df['Close'].iloc[-1]
            prev = df['Close'].iloc[-2]
            chg = ((price - prev) / prev) * 100
            
            # === 💰 搞钱指标算法 ===
            # 1. RSI 相对强弱 (判断抄底/逃顶)
            delta = df['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            current_rsi = rsi.iloc[-1]
            
            # 2. 量比 (判断主力资金是否进场)
            vol_avg = df['Volume'].iloc[-11:-1].mean()
            vol_ratio = df['Volume'].iloc[-1] / vol_avg if vol_avg > 0 else 0

            # === 🚦 信号逻辑 ===
            signal = "⚪"
            
            # 逻辑A: 放量暴涨 (主力抢筹) -> 追涨
            if vol_ratio > 1.8 and chg > 2.5: 
                signal = "🔥 主力进场"
            
            # 逻辑B: 超卖反弹 (跌过头了) -> 抄底
            elif current_rsi < 30: 
                signal = "🟢 极度超卖(抄底)"
            
            # 逻辑C: 超买风险 -> 逃顶
            elif current_rsi > 80: 
                signal = "🔴 极度超买(风险)"

            # 只要有特殊信号，或者涨跌幅超过 5%，都记录下来
            if signal != "⚪" or abs(chg) > 5:
                results.append({
                    "Stock": symbol, 
                    "Price": float(price), 
                    "Chg": float(chg), 
                    "Signal": signal
                })
        except: continue
except: pass

# === 📝 生成报告 ===
if results:
    df_res = pd.DataFrame(results)
    # 按照涨幅从高到低排序，先看最猛的
    df_res = df_res.sort_values(by="Chg", ascending=False)
    
    msg = f"💰 {MARKET_NAME} 搞钱日报 💰\n"
    msg += f"⏰ 时间: {datetime.now().strftime('%Y-%m-%d')}\n\n"
    
    for _, r in df_res.iterrows():
        # 根据涨跌给图标
        icon = "📈" if r['Chg'] > 0 else "📉"
        if "主力" in r['Signal']: icon = "🚀"
        
        msg += f"{icon} {r['Stock']}\n"
        msg += f"   现价: {r['Price']:.2f} ({r['Chg']:+.2f}%)\n"
        msg += f"   信号: {r['Signal']}\n\n"
    
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
    print("-" * 20)
    m_user = os.environ.get("MAIL_USER")
    m_pass = os.environ.get("MAIL_PASS")
    
    if m_user and m_pass:
        try:
            email = MIMEText(msg, 'plain', 'utf-8')
            email['From'] = formataddr(["全球搞钱助手", m_user])
            email['To'] = formataddr(["Boss", m_user])
            email['Subject'] = f"🔥 {MARKET_NAME} 机会提醒"
            
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
    print(f"{MARKET_NAME} 今天风平浪静，无特殊机会。")
