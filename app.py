from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
import os
import requests
import yfinance as yf
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
USER_ID = os.getenv("LINE_USER_ID")
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
NEWS_API_KEY = os.getenv("NEWS_API_KEY")

line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

stocks = ["AAPL", "TSLA", "MSFT", "NVDA", "PLTR"]

def get_weather():
    url = f"https://api.openweathermap.org/data/2.5/weather?q=Taipei&appid={OPENWEATHER_API_KEY}&units=metric&lang=zh_tw"
    res = requests.get(url).json()
    desc = res['weather'][0]['description']
    temp = res['main']['temp']
    return f"📍 台北天氣：{desc}，{temp:.1f}°C"

def get_stock_summary():
    summary = []
    index_map = {"^DJI": "道瓊", "^GSPC": "S&P500", "^IXIC": "NASDAQ"}
    for code, name in index_map.items():
        stock = yf.Ticker(code)
        hist = stock.history(period="2d")
        if len(hist) >= 2:
            change = hist['Close'][-1] - hist['Close'][-2]
            pct = (change / hist['Close'][-2]) * 100
            summary.append(f"{name}：{change:+.2f}（{pct:+.2f}％）")
    return "📊 美股指數：\n" + "\n".join(summary)

def get_news_and_analysis():
    url = f"https://newsapi.org/v2/top-headlines?category=business&language=en&apiKey={NEWS_API_KEY}"
    res = requests.get(url).json()
    if not res['articles']:
        return "📰 暫無新聞"
    top = res['articles'][0]
    title = top['title']
    source = top['source']['name']
    return f"📰 最新新聞：{title}（{source}）\n🎯 分析：可能影響 AAPL，因其涉及科技領域消息擴散效應。"

def get_daily_report():
    today = datetime.now().strftime("%Y/%m/%d (%A)")
    weather = get_weather()
    stocks = get_stock_summary()
    news = get_news_and_analysis()
    return f"☀️ 早安 HAN！\n今天是 {today}\n{weather}\n{stocks}\n{news}"

scheduler = BackgroundScheduler()
scheduler.add_job(lambda: line_bot_api.push_message(USER_ID, TextSendMessage(text=get_daily_report())), 'cron', hour=8)

def push_hourly_news():
    now = datetime.now().strftime("%H:%M")
    news = get_news_and_analysis()
    line_bot_api.push_message(USER_ID, TextSendMessage(text=f"🕐 {now} 快訊更新：\n{news}"))

for hour in range(9, 20):
    scheduler.add_job(push_hourly_news, 'cron', hour=hour)

scheduler.start()

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except Exception as e:
        print("❌ Error:", e)
        abort(400)
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    print("⭐️ 使用者 ID：", event.source.user_id)
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text="已收到！你可以專心投資，我會幫你追蹤市場資訊📈"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
