def baslat():
    print("MK Ultra Turbo Simulasyon Core Baslatildi ✅")

if __name__ == "__main__":
    baslat()
from telegram.ext import Updater, CommandHandler

def start(update, context):
    update.message.reply_text("MK Ultra Turbo Simülasyon Core Aktif ✅")

updater = Updater(token=os.environ["BOT_TOKEN"], use_context=True)
dispatcher = updater.dispatcher

dispatcher.add_handler(CommandHandler("start", start))

print("MK Ultra Turbo Simulasyon Core Baslatildi ✅")
updater.start_polling()
updater.idle()
