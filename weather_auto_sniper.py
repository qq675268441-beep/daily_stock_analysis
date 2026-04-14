import requests
import os
from datetime import datetime, timedelta

# ==========================================
# 🎯 指挥官战术配置：一次设定，终身受用
# ==========================================
TARGET_CITY = "Chicago"  # 锁定战区：芝加哥
# 你的套利红线：只要超算概率与盘口价格偏差超过 40%，立刻开火
ARBITRAGE_GAP = 0.40 

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

def fire_alert(msg):
    if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "Markdown"})

def fetch_polymarket_targets():
    """动态雷达：自动搜寻 Polymarket 库里所有芝加哥气象合约"""
    print(f"🔍 正在全网搜寻 {TARGET_CITY} 的气象猎物...")
    # 动态抓取所有活跃的天气合约
    url = f"https://gamma-api.polymarket.com/markets?active=true&closed=false&limit=100&query={TARGET_CITY}+temperature"
    markets = requests.get(url).json()
    
    valid_targets = []
    for m in markets:
        # 自动提取靶点温度 (例如从标题 "Will Chicago hit 60°F..." 提取 60)
        title = m.get('question', '')
        if 'high' in title.lower() or 'hit' in title.lower():
            try:
                # 简单的字符切割提取温度数字
                temp_limit = float(title.split('hit ')[1].split('°')[0])
                yes_price = 0
                for t in m.get('tokens', []):
                    if t.get('outcome') == 'Yes':
                        yes_price = float(t.get('price', 0))
                
                valid_targets.append({
                    'id': m.get('id'),
                    'title': title,
                    'target_temp': temp_limit,
                    'price': yes_price
                })
            except: continue
    return valid_targets

def get_gfs_forecast():
    """超算探头：获取芝加哥未来 3 天的物理真理"""
    url = "https://api.open-meteo.com/v1/forecast?latitude=41.87&longitude=-87.62&daily=temperature_2m_max&temperature_unit=fahrenheit&timezone=America%2FChicago"
    res = requests.get(url).json()
    return res['daily']['time'], res['daily']['temperature_2m_max']

def run_auto_arbitrage():
    print("⚔️ 全自动气象套利流水线启动...")
    
    # 1. 获取物理世界的真理 (明天是索引1)
    dates, temps = get_gfs_forecast()
    tomorrow_date = dates[1]
    tomorrow_phys_temp = temps[1]
    
    # 2. 自动搜寻盘口猎物
    targets = fetch_polymarket_targets()
    
    for target in targets:
        # 只针对“明天”的合约进行精确降维打击
        if tomorrow_date.replace("-", "") in target['title'].replace("-", "") or "tomorrow" in target['title'].lower():
            print(f"🎯 锁定猎物: {target['title']} | 盘口价: ${target['price']}")
            
            # 3. 逻辑判定：物理上确定会超过，但价格却很便宜
            if tomorrow_phys_temp >= target['target_temp'] and target['price'] <= (1 - ARBITRAGE_GAP):
                msg = (
                    f"🌪️ **[发现物理级定价错误！]**\n\n"
                    f"**战区：** {target['title']}\n"
                    f"**超算事实：** {tomorrow_phys_temp}°F (必中)\n"
                    f"**散户定价：** ${target['price']} (白送钱)\n"
                    f"**套利空间：** 极高！请立即开火！"
                )
                fire_alert(msg)
            else:
                print("⚖️ 监控中：未发现足以触发警报的定价偏差。")

if __name__ == "__main__":
    run_auto_arbitrage()
