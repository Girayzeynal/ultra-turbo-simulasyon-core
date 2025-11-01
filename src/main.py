import os
import asyncio
from datetime import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from aiohttp import web

# kendi pipeline fonksiyonunu kullan
from faz1_pipeline import run_faz1

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# --- Telegram command handlers ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("MK Ultra Turbo Simülasyon Core Aktif ✅")

async def fetch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if len(context.args) != 2:
            await update.message.reply_text("Kullanım: /fetch YYYY-MM-DD YYYY-MM-DD")
            return

        start_date, end_date = context.args
        # opsiyonel: parse kontrolü
        datetime.strptime(start_date, "%Y-%m-%d")
        datetime.strptime(end_date, "%Y-%m-%d")

        await update.message.reply_text("FETCH: başlıyor... ⏳")
        result = run_faz1(start_date, end_date)
        # result string dönüyorsa:
        await update.message.reply_text(str(result))
    except Exception as ex:
        await update.message.reply_text(f"FETCH HATA ⚠️\n{ex}")

# --- küçük health web server (aiohttp) ---
async def _health(request):
    return web.Response(text="ok")

async def start_web_server(host="0.0.0.0", port: int = 8080):
    app = web.Application()
    app.router.add_get("/health", _health)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host, port)
    await site.start()
    return runner

# --- bot startup (polling) ---
async def start_bot_and_web():
    if not TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN environment variable yok!")

    application = ApplicationBuilder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("fetch", fetch))

    # initialize & start the application
    await application.initialize()
    await application.start()

    # başlat polling (background)
    # start_polling() returns when polling started
    await application.updater.start_polling()

    # start a minimal web server for Fly healthchecks
    port = int(os.environ.get("PORT", "8080"))
    await start_web_server(port=port)

    # uygulama çalışır durumda kalsın
    try:
        while True:
            await asyncio.sleep(3600)
    finally:
        # temiz kapat
        await application.updater.stop()
        await application.stop()
        await application.shutdown()

if __name__ == "__main__":
    asyncio.run(start_bot_and_web())
