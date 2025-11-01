import os
import asyncio
from datetime import datetime
from flask import Flask, request, jsonify

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Analiz fonksiyonun (mevcut kodundan)
from faz1_pipeline import run_faz1

# Ortam değişkeni ismi senin repo ile uyumlu:
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    raise RuntimeError("TELEGRAM_BOT_TOKEN ortam değişkeni eksik!")

app = Flask(__name__)

# PTB v20 uygulaması
application = Application.builder().token(TOKEN).build()

# --- Komutlar ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("MK Ultra Turbo Simulasyon Core Aktif ✅")

async def fetch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if len(context.args) != 2:
            await update.message.reply_text("Kullanım: /fetch YYYY-MM-DD YYYY-MM-DD")
            return

        start_date, end_date = context.args
        # Tarih doğrulama
        datetime.strptime(start_date, "%Y-%m-%d")
        datetime.strptime(end_date, "%Y-%m-%d")

        await update.message.reply_text("FETCH: başlıyor... ⛏️")
        result = run_faz1(start_date, end_date)
        await update.message.reply_text(result)
    except Exception as ex:
        await update.message.reply_text(f"FETCH HATA ⚠️\n{ex}")

# Handler’ları ekle
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("fetch", fetch))

# --- Webhook entegrasyonu ---
@app.before_first_request
def _startup_bot():
    """Flask ilk isteği almadan önce PTB uygulamasını başlat."""
    loop = asyncio.get_event_loop()
    loop.create_task(application.initialize())
    loop.create_task(application.start())

@app.route("/", methods=["GET"])
def health():
    return jsonify(ok=True), 200

@app.route(f"/{TOKEN}", methods=["POST"])
def receive_update():
    """Telegram'dan gelen güncellemeleri PTB kuyruğuna bırak."""
    data = request.get_json(force=True)
    update = Update.de_json(data, application.bot)
    application.update_queue.put_nowait(update)
    return "OK", 200

# Geliştirici çalıştırması için (Docker'da gunicorn çalışacak)
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 8080)))
