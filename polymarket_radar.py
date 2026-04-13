import requests
import os
import smtplib
from email.mime.text import MIMEText
from email.header import Header

# 战术参数配置 (从 GitHub Secrets 自动读取)
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

# 新增：QQ 邮箱战术配置 (从 GitHub Secrets 自动读取)
QQ_SENDER = os.environ.get("QQ_SENDER")         # 你的发件 QQ 邮箱
QQ_AUTH_CODE = os.environ.get("QQ_AUTH_CODE")   # QQ 邮箱的 SMTP 授权码
EMAIL_RECEIVER = os.environ.get("EMAIL_RECEIVER") # 接收警报的邮箱

def fire_telegram_alert(msg):
    """向指挥官发送 Telegram 警报"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("未检测到 Telegram 密钥，跳过电报发送。")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "Markdown"}
    requests.post(url, json=payload)

def fire_email_alert(subject, msg):
    """向指挥官发送 QQ 邮箱警报"""
    if not QQ_SENDER or not QQ_AUTH_CODE or not EMAIL_RECEIVER:
        print("未检测到完整的邮箱密钥，跳过邮件发送。")
        return
    
    try:
        # 构建纯文本邮件内容
        message = MIMEText(msg, 'plain', 'utf-8')
        message['From'] = Header("战术中枢雷达", 'utf-8')
        message['To'] = Header("指挥官", 'utf-8')
        message['Subject'] = Header(subject, 'utf-8')
        
        # 建立 SMTP SSL 加密连接并开火
        server = smtplib.SMTP_SSL("smtp.qq.com", 465)
        server.login(QQ_SENDER, QQ_AUTH_CODE)
        server.sendmail(QQ_SENDER, [EMAIL_RECEIVER], message.as_string())
        server.quit()
        print("邮件穿甲弹发射成功！")
    except Exception as e:
        print(f"邮件发射失败: {e}")

def global_radar_sweep():
    # 1. 广域扫描：获取 Polymarket 当前最活跃的 50 个未结算市场
    url = "https://gamma-api.polymarket.com/markets?active=true&closed=false&limit=50&order=volumeNum&ascending=false"
    
    print("雷达升空，开始全频段扫描...")
    try:
        response = requests.get(url).json()
        
        for market in response:
            question = market.get('question', '')
            volume = float(market.get('volume', 0))
            
            # 2. 垃圾过滤系统：交易量低于 5 万美金的直接无视
            if volume < 50000:
                continue
                
            # 3. 目标特征匹配：只盯着核心战场
            keywords = ["Iran", "Israel", "Oil", "Fed", "Rate", "Crypto", "Strike"]
            if not any(kw.lower() in question.lower() for kw in keywords):
                continue
                
            tokens = market.get('tokens', [])
            if not tokens: continue
            
            # 4. 获取当前 Yes 的价格 (即市场认为发生的概率)
            yes_price = float(tokens[0].get('price', 0))
            
            # 5. 极端错杀触发器：低于 20% 或 高于 80%
            if yes_price <= 0.20 or yes_price >= 0.80:
                alert_msg = (
                    f"🚨 [战术预警] 捕捉到高价值异常合约！\n\n"
                    f"目标靶区： {question}\n"
                    f"资金深度： ${volume:,.2f}\n"
                    f"当前 Yes 概率： {yes_price * 100}%\n"
                    f"战术动作： 已触发极端赔率红线，请立刻登入 Polymarket 人工核准！"
                )
                print(f"触发警报: {question}")
                
                # 双轨全频段轰炸
                fire_telegram_alert(alert_msg)
                fire_email_alert("🚨 Polymarket 极端错杀警报！", alert_msg)
                
    except Exception as e:
        print(f"雷达受损: {e}")

if __name__ == "__main__":
    global_radar_sweep()
