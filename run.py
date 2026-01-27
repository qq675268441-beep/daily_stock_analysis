import os
import sys
import yfinance as yf
import pandas as pd
import requests
import smtplib
from datetime import datetime
from email.mime.text import MIMEText
from email.utils import formataddr

# === 🌍 全球资产池 (精英 + 妖股) ===

# 1. 🇨🇳 亚洲战队 (A股/港股: 核心资产 + 题材妖股)
ASIA_POOL = [
    # --- A股核心 (茅/宁/招/平) ---
    "600519.SS", "000858.SZ", "300750.SZ", "002594.SZ", "600036.SS", 
    "601318.SS", "601138.SS", "601899.SS",
    # --- A股人气妖股 (华为/算力/CPO) ---
    "601127.SS", # 赛力斯 (华为车龙)
    "000977.SZ", # 浪潮信息 (AI算力)
    "002230.SZ", # 科大讯飞 (AI语音)
    "300308.SZ", # 中际旭创 (光模块龙)
    "002261.SZ", # 拓维信息 (鸿蒙/华为算力)
    "002456.SZ", # 欧菲光 (华为手机链)
    "300059.SZ", # 东方财富 (牛市风向标)
    # --- 港股 (科网 + 新势力) ---
    "0700.HK", "3690.HK", "9988.HK", "1810.HK", "0981.HK", 
    "2015.HK", "9868.HK", "9866.HK", "0020.HK" # 商汤(AI妖股)
]

# 2. 🇺🇸 美股战队 (科技七子 + 芯片 + 加密 + 顶级妖股)
US_POOL = [
    # --- 科技巨头 (稳健) ---
    "NVDA", "TSLA", "AAPL", "MSFT", "GOOG", "AMZN", "META",
    # --- 芯片半导体 (高波动) ---
    "AMD", "TSM", "AVGO", "SMCI", "ARM", "INTC", "MU",
    # --- 加密货币/区块链 (币圈高贝塔) ---
    "COIN", "MSTR", "MARA", "CLSK", "RIOT", "HOOD",
    # --- 🇺🇸 顶级妖股/散户抱团 (Meme Stocks) ---
    "GME",  # 游戏驿站 (散户信仰)
    "AMC",  # AMC院线
    "DJT",  # 特朗普媒体 (懂王概念)
    "FFIE", # 法拉第未来 (贾跃亭/极度波动)
    "CVNA", # Carvana (逼空之王)
    "UPST", # Upstart (AI借贷/波动极大)
    "OPEN", # Opendoor
    "PLTR", # Palantir (散户最爱)
    "AI",   # C3.ai
    "SOUN", # SoundHound
    "BBAI", # BigBear (你的持仓)
    "IVDA"  # Iveda (你的持仓)
]

# === ⏰ 智能判断当前市场 ===
current_hour = datetime.utcnow().hour
if current_hour < 12:
    TARGET_TICKERS = ASIA_POOL
    MARKET_NAME = "🇨🇳 A股/港股 (精英+妖股)"
else:
    TARGET_TICKERS = US_POOL
    MARKET_NAME = "🇺🇸 美股 (精英+妖股)"

print(f"🚀 启动！正在用【暴利逻辑】扫描 {len(TARGET_TICKERS)} 只目标 (含妖股)...")
results = []

try:
    # 批量下载数据
    data = yf.download(TARGET_TICKERS, period="60d", interval="1d", group_by='ticker', progress=False)
    
    for symbol in TARGET_TICKERS:
        try:
            df = data[symbol].copy()
            if len(df) < 20: continue
            
            # === 📊 数据计算 ===
            price = df['Close'].iloc[-1]
            prev = df['Close'].iloc[-2]
            chg = ((price - prev) / prev) * 100
            
            # RSI (相对强弱)
            delta = df['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            current_rsi = rsi.iloc[-1]
            
            # 量比 (Volume Ratio)
            vol_avg = df['Volume'].iloc[-11:-1].mean()
            vol_ratio = df['Volume'].iloc[-1] / vol_avg if vol_avg > 0 else 0

            # === ⚡️ 暴利逻辑 (原版) ===
            signal = "⚪"
            
            # 逻辑1: 暴力追涨 (妖股启动信号)
            # 必须放量(1.5倍) + 涨幅不错(>3%)
            if vol_ratio > 1.5 and chg > 3: 
                signal = "🔥 妖股启动/追涨"
            
            # 逻辑2: 极度超卖 (黄金坑)
            elif current_rsi < 30: 
                signal = "🟢 极度超卖/抄底"
            
            # 逻辑3: 极度超买 (风险提示)
            elif current_rsi > 80: 
                signal = "🔴 风险/逃顶"

            # 💡 筛选规则：
            # 1. 有信号的必定记录
            # 2. 你的重点持仓 (BBAI/IVDA/GME/600519) 无论涨跌都监控
            if signal != "⚪" or symbol in ["GME", "BBAI", "IVDA", "DJT", "600519.SS", "300750.SZ"]:
                results.append({
                    "Stock": symbol, 
                    "Price": float(price), 
                    "Chg": float(chg), 
                    "Signal": signal
                })
        except: continue
except Exception as e:
    print(f"扫描出错: {e}")

# === 📝 生成报告 ===
if results:
    df_res = pd.DataFrame(results)
    # 按照涨幅排序，涨得最疯的妖股排最前面
    df_res = df_res.sort_values(by="Chg", ascending=False)
    
    msg = f"💰 {MARKET_NAME} 机会报告 💰\n"
    msg += f"⏰ {datetime.now().strftime('%m-%d %H:%M')}\n"
    msg += f"🔥 包含高波动妖股扫描\n\n"
    
    for _, r in df_res.iterrows():
        # 图标美化
        icon = r['Signal'].split(' ')[0]
        if icon == "⚪": icon = "👀"
        
        msg += f"{icon} {r['Stock']}: ${r['Price']:.2f} ({r['Chg']:+.2f}%)\n"
        msg += f"   信号: {r['Signal']}\n\n"
    
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
    m_user = os.environ.get("MAIL_USER")
    m_pass = os.environ.get("MAIL_PASS")
    if m_user and m_pass:
        try:
            email = MIMEText(msg, 'plain', 'utf-8')
            email['From'] = formataddr(["妖股雷达", m_user])
            email['To'] = formataddr(["Boss", m_user])
            email['Subject'] = f"🚀 {MARKET_NAME} 暴利机会"
            
            smtp = smtplib.SMTP_SSL('smtp.qq.com', 465)
            smtp.login(m_user, m_pass)
            smtp.sendmail(m_user, [m_user], email.as_string())
            print("✅ 邮件发送成功")
            smtp.quit()
        except: pass
else:
    print("今日扫描完毕，市场平淡，妖股休息。")
