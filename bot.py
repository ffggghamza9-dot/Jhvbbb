# bot.py
import telebot
from config import BOT_TOKEN
import handlers.admin as admin_h
import handlers.user as user_h
import handlers.requests as req_h
from database import init_db

init_db()

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

# register handlers
admin_h.register_handlers(bot)
user_h.register_handlers(bot)
req_h.register_handlers(bot)

if __name__ == "__main__":
    print("🚀 Bot is running...")
    bot.infinity_polling(timeout=60, long_polling_timeout=60)
