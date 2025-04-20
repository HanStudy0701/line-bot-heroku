from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
import os

app = Flask(__name__)

# Channel 設定
CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
USER_ID = os.getenv("LINE_USER_ID")

line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

# 模擬資料產生（正式版會串 API）
def get_daily_summary():
    today = datetime.now().strftime("%Y/%m/%d (%A)")
    return f"""早安 HAN！🌞
今天是 {today}
📍 天氣：台北 多雲 22~29°C
📊 美股概況：道瓊 +0.83%、S&P500 +0.56%、NASDAQ +1.23%
🧠 今日知識：什麼是「債券殖利率倒掛」？這會暗示經濟衰退嗎？
📌 資料來源：OpenWeatherMap、Yahoo Finance、ChatGPT
"""


def get_hourly_news():
    now = datetime.now().strftime("%H:%M")
    return f"""📢 美股快訊 | {now}
📰 蘋果宣布進軍生成式 AI，將與 OpenAI 合作
🎯 受影響個股：AAPL（蘋果）
📈 分析：與 AI 領導品牌合作，可能為 AAPL 帶來新一波資金追捧
📌 資料來源：路透社、ChatGPT
"""


def get_life_reminder(content):
    return f"🔔 {content}"


# 定時排程
scheduler = BackgroundScheduler()
scheduler.add_job(lambda: line_bot_api.push_message(USER_ID, TextSendMessage(text=get_daily_summary())), 'cron', hour=8)

# 每小時推播新聞（08:00–19:00）
for h in range(8, 20):
    scheduler.add_job(lambda: line_bot_api.push_message(USER_ID, TextSendMessage(text=get_hourly_news())), 'cron', hour=h)

# 午餐提醒
scheduler.add_job(lambda: line_bot_api.push_message(USER_ID, TextSendMessage(text=get_life_reminder("吃飯囉！📣 別忘了補充能量"))), 'cron', hour=12, minute=0)
# 晚安提醒
scheduler.add_job(lambda: line_bot_api.push_message(USER_ID, TextSendMessage(text=get_life_reminder("辛苦一天了，別忘了休息與放鬆 🧘"))), 'cron', hour=18, minute=30)

# ✅ 測試推播：台灣時間 21:55（UTC+8 → UTC 13:55）
scheduler.add_job(lambda: line_bot_api.push_message(USER_ID, TextSendMessage(text="🧪 測試訊息：現在是台灣時間 21:55，我是你安排的測試任務！")), 'cron', hour=13, minute=55)

scheduler.start()

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    print("📦 Webhook Body：", body)
    try:
        handler.handle(body, signature)
    except Exception as e:
        print("❌ Error:", e)
        abort(400)
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    print("⭐️ 使用者 ID：", event.source.user_id)
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text='我收到你的訊息囉！'))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
