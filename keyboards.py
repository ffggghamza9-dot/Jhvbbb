# keyboards.py
from telebot import types

def admin_reply_kb():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=4)
    kb.row("🛠 إدارة الأزرار", "👤 إدارة المستخدمين", "📦 إدارة الطلبات", "📝 القوالب")
    kb.row("🖼 تحديث المحتوى", "📩 بث رسالة", "📊 إحصائيات", "📜 السجل")
    kb.row("🔁 تحديث الواجهة", "🔙 رجوع")
    return kb

def user_main_kb():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
    kb.row("🎮 الخدمات", "💰 رصيدي", "📞 الدعم")
    return kb

# inline builders for menus (used by handlers)
def build_menu_buttons(buttons):
    # buttons: list of tuples (id, title, kind)
    kb = types.InlineKeyboardMarkup()
    for bid, title, kind in buttons:
        kb.add(types.InlineKeyboardButton(title, callback_data=f"open:{bid}"))
    return kb

def build_content_kb(kb_rows, parent_id):
    kb = types.InlineKeyboardMarkup()
    for kid, text, ask_info in kb_rows:
        if ask_info:
            kb.add(types.InlineKeyboardButton(text, callback_data=f"ask:{parent_id}:{kid}:{ask_info}"))
        else:
            kb.add(types.InlineKeyboardButton(text, callback_data=f"action:{parent_id}:{kid}"))
    kb.add(types.InlineKeyboardButton("🔙 رجوع", callback_data=f"open:{parent_id}"))
    return kb
