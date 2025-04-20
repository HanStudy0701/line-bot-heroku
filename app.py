from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from apscheduler.schedulers.background import BackgroundScheduler
import os

app = Flask(__name__)

# Channel 設定
CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
USER_ID = os.getenv("LINE_USER_ID")

line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

# 每天固定發的內容
def send_daily_message():
    message = "☀️ 早安！今日天氣晴朗，祝你有美好的一天！"
    line_bot_api.push_message(USER_ID, TextSendMessage(text=message))

# 定時排程
scheduler = BackgroundScheduler()
scheduler.add_job(send_daily_message, 'cron', hour=8)  # 每天早上8點
scheduler.start()

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

@handler.add(MessageEvent)
def debug_all(event):
    print("🌀 收到事件：", event)
    try:
        user_id = event.source.user_id
        print("⭐️ 使用者 ID：", user_id)
    except Exception as e:
        print("❌ 無法取得使用者 ID：", e)

    if isinstance(event.message, TextMessage):
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text='我收到你的訊息囉！'))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
