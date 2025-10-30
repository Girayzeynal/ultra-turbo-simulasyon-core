
# main.py
import os
from threading import Thread
from flask import Flask
from telegram.ext import Updater, CommandHandler

# ----------------------
# Telegram command handlers
# ----------------------
def start(update, context):
    try:
        update.message.reply_text("MK Ultra Turbo Simulasyon Core Aktif ✅")
    except Exception:
        # mesaj gönderilemezse sessizce geç
        pass

# ----------------------
# Basit sağlık / ana sayfa için Flask
# ----------------------
app = Flask(__name__)

@app.route('/')
def home():
    return "MK Ultra Turbo Core Running ✅"

def run_web():
    port = int(os.environ.get("PORT", 5000))
    # Flask development server; Render için yeterli
    app.run(host="0.0.0.0", port=port)

# ----------------------
# Main: Bot başlatma ve web server paralel
# ----------------------
def main():
    bot_token = os.environ.get("BOT_TOKEN")
    if not bot_token:
        print("❌ BOT_TOKEN bulunamadı. Render environment'a eklemeyi unutma!")
        return

    # Updater oluştur (python-telegram-bot v13.x uyumlu)
    updater = Updater(token=bot_token, use_context=True)
    dispatcher = updater.dispatcher

    # Komut ekle
    dispatcher.add_handler(CommandHandler("start", start))

    # Bilgi mesajı
    print("MK Ultra Turbo Simulasyon Core Başlatılıyor... ✅")

    # Telegram polling başlat
    updater.start_polling()

    # Web server'ı ayrı bir thread'te başlat (Render için)
    Thread(target=run_web, daemon=True).start()

    # Botu canlı tut
    updater.idle()

if __name__ == "__main__":
    main()
