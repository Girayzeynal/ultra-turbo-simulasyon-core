import os
from datetime import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from faz1_pipeline import run_faz1

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("MK Ultra Turbo Simülasyon Core Aktif ✅")


async def fetch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if len(context.args) != 2:
            await update.message.reply_text("Kullanım: /fetch YYYY-MM-DD YYYY-MM-DD")
            return

        start_date, end_date = context.args

        datetime.strptime(start_date, "%Y-%m-%d")
        datetime.strptime(end_date, "%Y-%m-%d")

        await update.message.reply_text("FETCH: başlıyor... ⏳")
        result = run_faz1(start_date, end_date)
        await update.message.reply_text(result)

    except Exception as ex:
        await update.message.reply_text(f"FETCH HATA ⚠️\n{ex}")


async def main():
    if not TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN Render ortam değişkenine eklenmemiş!")

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("fetch", fetch))

    # Poling tek instance modunda
    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    await app.updater.idle()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
