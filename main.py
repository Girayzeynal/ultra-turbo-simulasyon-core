# =========================
# MK Ultra Turbo Simulasyon Core - main.py
# Temiz, tek-instance Telegram bot + Flask web
# =========================

import os
import logging
from threading import Thread
from flask import Flask
from telegram.ext import Updater, CommandHandler
from dateutil.parser import parse as dtparse
import subprocess

# --------- Logging ---------
logging.basicConfig(
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    level=logging.INFO,
)
log = logging.getLogger("mk-ultra-core")


# --------- Telegram Komutları ---------
def cmd_start(update, context):
    update.message.reply_text("MK Ultra Turbo Simulasyon Core Aktif ✅")


def cmd_fetch(update, context):
    """
    Kullanım:
      /fetch YYYY-MM-DD YYYY-MM-DD
    Örnek:
      /fetch 2024-10-03 2024-10-06
    """
    try:
        args = context.args
        if len(args) != 2:
            update.message.reply_text("Kullanım: /fetch YYYY-MM-DD YYYY-MM-DD")
            return

        d1 = dtparse(args[0]).date().isoformat()
        d2 = dtparse(args[1]).date().isoformat()

        # Ortama gerekli yolları/parametreleri geçir
        env = os.environ.copy()
        env["FETCH_FROM"] = d1
        env["FETCH_TO"] = d2
        # Bu yolları Render ortam değişkenlerinden alıyoruz (Environment → Variables)
        env["ALIAS_PATH"] = env.get("ALIAS_PATH", "team_aliases.csv")
        env["FAZ1_IN_CSV"] = env.get("FAZ1_IN_CSV", "euroleague_faz1.csv")

        # 1) Veriyi çek
        r1 = subprocess.run(
            ["python3", "fetch_data.py"],
            env=env,
            capture_output=True,
            text=True,
            timeout=180,
        )
        fetch_out = (r1.stdout or "") + ("\n" + (r1.stderr or ""))

        # 2) FAZ1 pipeline
        r2 = subprocess.run(
            ["python3", "faz1_pipeline.py"],
            env=env,
            capture_output=True,
            text=True,
            timeout=180,
        )
        pipe_out = (r2.stdout or "") + ("\n" + (r2.stderr or ""))

        # Telegram'a kısa/özet çıktı gönder (çok uzunsa kes)
        def clip(s, n=800):
            return s if len(s) <= n else s[: n - 3] + "..."

        update.message.reply_text(
            f"FETCH:\n{clip(fetch_out)}\n\nFAZ1:\n{clip(pipe_out)}"
        )
    except Exception as e:
        log.exception("cmd_fetch hata")
        update.message.reply_text(f"Hata: {e}")


# --------- Bot Çalıştır ---------
def run_bot():
    bot_token = os.environ.get("BOT_TOKEN", "").strip()
    if not bot_token:
        log.error("❌ BOT_TOKEN bulunamadı. Render → Environment → Variables kısmına ekleyin.")
        return

    updater = Updater(token=bot_token, use_context=True)
    dp = updater.dispatcher

    # Komutlar
    dp.add_handler(CommandHandler("start", cmd_start))
    dp.add_handler(CommandHandler("fetch", cmd_fetch))

    log.info("Telegram bot başlatılıyor…")

    # Çift instance / getUpdates çakışmasını engeller
    updater.start_polling(drop_pending_updates=True)

    log.info("Telegram bot çalışıyor ✅")
    updater.idle()  # thread içinde bloklasın


# --------- Web (Flask) ---------
app = Flask(__name__)


@app.route("/")
def home():
    return "MK Ultra Turbo Core Running ✅"


def run_web():
    # Render 'PORT' verir; lokal testte 5000'e düşer
    port = int(os.environ.get("PORT", "5000"))
    log.info(f"Flask web sunucusu {port} portunda başlıyor…")
    app.run(host="0.0.0.0", port=port)


# --------- Main ---------
if __name__ == "__main__":
    # Bot'u arka planda başlat
    Thread(target=run_bot, daemon=True).start()

    # Web'i ana thread'de çalıştır (Render health check/uyandırma için)
    run_web()
