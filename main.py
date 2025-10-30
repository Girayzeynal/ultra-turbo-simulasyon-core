
import os
from telegram.ext import Updater, CommandHandler

def start(update, context):
    update.message.reply_text("MK Ultra Turbo Simulasyon Core Aktif ✅")

def main():
    bot_token = os.environ.get("BOT_TOKEN")
    if not bot_token:
        print("❌ BOT_TOKEN bulunamadı. Render environment variable kontrol et.")
        return

    updater = Updater(token=bot_token, use_context=True)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))

    print("MK Ultra Turbo Simülasyon Core Baslatildi ✅")
    updater.start_polling()
    updater.idle()   # ❗️ Render'ın botu kapatmasını engeller

if __name__ == "__main__":
    main()
import os
from threading import Thread
from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return "MK Ultra Turbo Core Running ✅"

def run_web():
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

# Telegram botun start kısmının hemen altına ekle:
Thread(target=run_web).start()
