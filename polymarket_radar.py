import requests
import os

# 战术参数配置 (从 GitHub Secrets 自动读取)
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

def fire_telegram_alert(msg):
    """向指挥官发送最高级别警报"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("未检测到 Telegram 密钥，无法发送警报。")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "Markdown"}
    requests.post(url, json=payload)

def global_radar_sweep():
    # 1. 广域扫描：获取 Polymarket 当前最活跃的 50 个未结算市场
    url = "https://gamma-api.polymarket.com/markets?active=true&closed=false&limit=50&order=volumeNum&ascending=false"
    
    print("雷达升空，开始全频段扫描...")
    try:
        response = requests.get(url).json()
        
        for market in response:
            question = market.get('question', '')
            volume = float(market.get('volume', 0))
            
            # 2. 垃圾过滤系统：交易量低于 5 万美金的野鸡盘直接无视
            if volume < 50000:
                continue
                
            # 3. 目标特征匹配：只盯着可能引发暴利的核心战场
            keywords = ["Iran", "Israel", "Oil", "Fed", "Rate", "Crypto", "Strike"]
            if not any(kw.lower() in question.lower() for kw in keywords):
                continue # 不包含核心关键词，跳过
                
            tokens = market.get('tokens', [])
            if not tokens: continue
            
            # 4. 获取当前 Yes 的价格 (即市场认为发生的概率)
            yes_price = float(tokens[0].get('price', 0))
            
            # 5. 极端错杀触发器：低于 20% (黑天鹅高赔率) 或 高于 80% (极高确定性)
            if yes_price <= 0.20 or yes_price >= 0.80:
                alert_msg = (
                    f"🚨 **[战术预警] 捕捉到高价值异常合约！**\n\n"
                    f"**目标靶区：** {question}\n"
                    f"**资金深度 (Volume)：** ${volume:,.2f}\n"
                    f"**当前 Yes 概率：** {yes_price * 100}%\n"
                    f"**战术动作：** 已触发极端赔率红线，请立刻登入 Polymarket 人工核准真实胜率！"
                )
                print(f"触发警报: {question}")
                fire_telegram_alert(alert_msg)
                
    except Exception as e:
        print(f"雷达受损: {e}")

if __name__ == "__main__":
    global_radar_sweep()
