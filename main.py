import os
import logging
from threading import Thread
from flask import Flask
from telegram.ext import Updater, CommandHandler

# ---------- Logging ----------
logging.basicConfig(
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    level=logging.INFO,
)
log = logging.getLogger("mk-ultra-core")

# ---------- Telegram Bot ----------
def cmd_start(update, context):
    update.message.reply_text("MK Ultra Turbo Simulasyon Core Aktif ✅")

def run_bot():
    bot_token = os.environ.get("BOT_TOKEN", "").strip()
    if not bot_token:
        log.error("❌ BOT_TOKEN bulunamadı. Render Environment > Variables kısmına ekleyin.")
        return

    updater = Updater(token=bot_token, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", cmd_start))

    log.info("Telegram bot başlatılıyor…")
    updater.start_polling()
    log.info("Telegram bot çalışıyor ✅")
    updater.idle()  # Thread içinde bloklasın

# ---------- Web (Flask) ----------
app = Flask(__name__)

@app.route("/")
def home():
    return "MK Ultra Turbo Core Running ✅"

def run_web():
    # Render 'PORT' veriyor; lokalde 5000’e düşer
    port = int(os.environ.get("PORT", "5000"))
    # Ana thread'de çalışsın ki Render portu hemen görsün
    log.info(f"Flask web sunucusu {port} portunda başlıyor…")
    app.run(host="0.0.0.0", port=port)

# ---------- Main ----------
if __name__ == "__main__":
    # Bot’u arka planda başlat
    Thread(target=run_bot, daemon=True).start()
    # Web’i ana thread’de başlat (Render port tarayıcısı için kritik)
    run_web()
