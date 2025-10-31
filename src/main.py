import os
from datetime import datetime
from telegram.ext import Updater, CommandHandler
from faz1_pipeline import run_faz1

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

def start(update, context):
    update.message.reply_text("MK Ultra Turbo Simulasyon Core Aktif ✅")

def fetch(update, context):
    try:
        # /fetch YYYY-MM-DD YYYY-MM-DD
        if len(context.args) != 2:
            update.message.reply_text("Kullanım: /fetch YYYY-MM-DD YYYY-MM-DD")
            return
        start_date, end_date = context.args

        # tarih doğrulama
        datetime.strptime(start_date, "%Y-%m-%d")
        datetime.strptime(end_date, "%Y-%m-%d")

        update.message.reply_text("FETCH: başlıyor…")
        msg = run_faz1(start_date, end_date)
        update.message.reply_text(msg)
    except Exception as ex:
        update.message.reply_text(f"FETCH:\nERR: {ex}")

def main():
    if not TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN boş. Render > Environment'a ekleyin.")

    updater = Updater(TOKEN, use_context=True)

    # Güvenli başlat: bekleyen webhook’u düşür (polling ile çakışmayı engeller)
    try:
        updater.bot.delete_webhook(drop_pending_updates=True)
    except Exception:
        pass

    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("Start", start))  # büyük S gelenler için
    dp.add_handler(CommandHandler("fetch", fetch))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
