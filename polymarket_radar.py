import requests
import os

# 1. 战术参数配置
TARGET_MARKET_URL = "https://gamma-api.polymarket.com/markets/这里填你抓到的靶点ID"
TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_TOKEN"] # 从 GitHub Secrets 读取
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

def fire_telegram_alert(msg):
    """向指挥官发送最高级别警报"""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "Markdown"}
    requests.post(url, json=payload)

def scan_market():
    # 2. 雷达扫描
    response = requests.get(TARGET_MARKET_URL).json()
    
    # 3. 提取核心物理参数 (通常 'Yes' 的价格就是概率)
    yes_price = float(response['tokens'][0]['price']) # 具体字段根据实际API JSON结构微调
    market_question = response['question']
    
    # 4. 极端博弈阈值判定 (例如：概率跌破 30% 就是严重错杀)
    trigger_threshold = 0.30 
    
    if yes_price <= trigger_threshold:
        alert_msg = (
            f"🚨 **[战术预警] 极端错杀机会出现！**\n\n"
            f"**靶点：** {market_question}\n"
            f"**当前 Yes 赔率：** `${yes_price}` (发生概率仅 {yes_price*100}%)\n"
            f"**战术动作：** 存在严重低估，请立刻人工接入进行最终核准！"
        )
        fire_telegram_alert(alert_msg)

if __name__ == "__main__":
    scan_market()
