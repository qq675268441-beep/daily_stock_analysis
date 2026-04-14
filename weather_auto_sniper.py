import requests
import os
import smtplib
from email.mime.text import MIMEText
from email.header import Header

# ==========================================
# 🎯 指挥官战术配置
# ==========================================
TARGET_CITY = "Chicago"  
ARBITRAGE_GAP = 0.40 # 利润红线

# 电报与QQ邮箱密钥 (从 GitHub Secrets 自动读取)
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
QQ_SENDER = os.environ.get("QQ_SENDER")         
QQ_AUTH_CODE = os.environ.get("QQ_AUTH_CODE")   
EMAIL_RECEIVER = os.environ.get("EMAIL_RECEIVER") 

def fire_telegram_alert(msg):
    if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "Markdown"})

def fire_email_alert(subject, msg):
    if QQ_SENDER and QQ_AUTH_CODE and EMAIL_RECEIVER:
        try:
            message = MIMEText(msg, 'plain', 'utf-8')
            message['From'] = Header("气象战术雷达", 'utf-8')
            message['To'] = Header("指挥官", 'utf-8')
            message['Subject'] = Header(subject, 'utf-8')
            server = smtplib.SMTP_SSL("smtp.qq.com", 465)
            server.login(QQ_SENDER, QQ_AUTH_CODE)
            server.sendmail(QQ_SENDER, [EMAIL_RECEIVER], message.as_string())
            server.quit()
            print("✉️ 邮件穿甲弹发射成功！")
        except Exception as e:
            print(f"邮件发射失败: {e}")

def fire_global_alert(msg):
    """双轨全频段开火"""
    print(msg)
    fire_telegram_alert(msg)
    fire_email_alert("🌪️ [Polymarket 气象套利预警]", msg)

def fetch_polymarket_targets():
    url = f"https://gamma-api.polymarket.com/markets?active=true&closed=false&limit=100&query={TARGET_CITY}+temperature"
    markets = requests.get(url).json()
    valid_targets = []
    for m in markets:
        title = m.get('question', '')
        if 'high' in title.lower() or 'hit' in title.lower():
            try:
                temp_limit = float(title.split('hit ')[1].split('°')[0])
                yes_price = 0
                for t in m.get('tokens', []):
                    if t.get('outcome') == 'Yes':
                        yes_price = float(t.get('price', 0))
                valid_targets.append({'title': title, 'target_temp': temp_limit, 'price': yes_price})
            except: continue
    return valid_targets

def get_gfs_forecast():
    url = "https://api.open-meteo.com/v1/forecast?latitude=41.87&longitude=-87.62&daily=temperature_2m_max&temperature_unit=fahrenheit&timezone=America%2FChicago"
    res = requests.get(url).json()
    return res['daily']['time'], res['daily']['temperature_2m_max']

def run_auto_arbitrage():
    print("⚔️ 全自动气象套利流水线启动...")
    dates, temps = get_gfs_forecast()
    tomorrow_date = dates[1]
    tomorrow_phys_temp = temps[1]
    targets = fetch_polymarket_targets()
    
    found_target = False
    for target in targets:
        if tomorrow_date.replace("-", "") in target['title'].replace("-", "") or "tomorrow" in target['title'].lower():
            print(f"🎯 锁定猎物: {target['title']} | 盘口价: ${target['price']}")
            
            # 逻辑判定
            if tomorrow_phys_temp >= target['target_temp'] and target['price'] <= (1 - ARBITRAGE_GAP):
                msg = (
                    f"🌪️ **[发现物理级定价错误！]**\n\n"
                    f"**战区：** {target['title']}\n"
                    f"**超算事实：** {tomorrow_phys_temp}°F (必中)\n"
                    f"**散户定价：** ${target['price']} (白送钱)\n"
                    f"**套利空间：** 请立即开火！"
                )
                fire_global_alert(msg)
                found_target = True
                
    if not found_target:
        print("⚖️ 监控中：未发现满足 40% 暴利红线的定价偏差。雷达保持静默。")

if __name__ == "__main__":
    run_auto_arbitrage()
