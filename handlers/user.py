# handlers/user.py
from telebot import types
from database import *
from keyboards import build_menu_buttons, build_content_kb
from utils import format_balance, is_admin
from config import ADMIN_IDS
from templates import DEFAULT_TEMPLATES

# waiting map for ask-info: user_id -> (button_id,kb_id,info_key)
waiting = {}

def register_handlers(bot):
    @bot.message_handler(commands=['start'])
    def start_cmd(message):
        ensure_user(message.from_user.id)
        if is_banned(message.from_user.id):
            bot.reply_to(message, "لقد تم حظرك. تواصل مع الأدمن.")
            return
        roots = list_children(0)
        if roots:
            kb = build_menu_buttons(roots)
            bot.send_message(message.chat.id, "اختر من القائمة:", reply_markup=kb)
        else:
            bot.send_message(message.chat.id, "لا يوجد خدمات حالياً.")

    @bot.message_handler(commands=['balance'])
    def bal_cmd(message):
        ensure_user(message.from_user.id)
        bot.reply_to(message, f"رصيدك الحالي: {format_balance(message.from_user.id)}")

    # callback handlers
    @bot.callback_query_handler(func=lambda call: call.data and call.data.startswith("open:"))
    def open_node(call):
        _, sid = call.data.split(":")
        sid = int(sid)
        node = get_button(sid)
        if not node:
            roots = list_children(0)
            kb = build_menu_buttons(roots)
            try:
                bot.edit_message_text("القائمة الرئيسية:", call.message.chat.id, call.message.message_id, reply_markup=kb)
            except:
                bot.send_message(call.message.chat.id, "القائمة الرئيسية:", reply_markup=kb)
            return
        # node: id,parent_id,title,kind,content_text,content_photo
        _, parent_id, title, kind, content_text, content_photo = node
        if kind == 'menu':
            children = list_children(sid)
            if children:
                kb = build_menu_buttons(children)
                try:
                    bot.edit_message_text(f"<b>{title}</b>\nاختر:", call.message.chat.id, call.message.message_id, parse_mode="HTML", reply_markup=kb)
                except:
                    bot.send_message(call.message.chat.id, f"<b>{title}</b>\nاختر:", parse_mode="HTML", reply_markup=kb)
            else:
                bot.answer_callback_query(call.id, "لا يوجد عناصر.")
        else:
            kb_rows = get_kb_for(sid)
            kb = build_content_kb(kb_rows, sid)
            if content_photo:
                try:
                    bot.edit_message_media(types.InputMediaPhoto(media=content_photo, caption=content_text or title, parse_mode="HTML"),
                                           call.message.chat.id, call.message.message_id, reply_markup=kb)
                except Exception:
                    bot.send_photo(call.message.chat.id, content_photo, caption=content_text or title, parse_mode="HTML", reply_markup=kb)
            else:
                try:
                    bot.edit_message_text(content_text or title, call.message.chat.id, call.message.message_id, parse_mode="HTML", reply_markup=kb)
                except Exception:
                    bot.send_message(call.message.chat.id, content_text or title, parse_mode="HTML", reply_markup=kb)

    @bot.callback_query_handler(func=lambda call: call.data and call.data.startswith("ask:"))
    def ask_handler(call):
        # data format: ask:{button_id}:{kb_id}:{info_key}
        _, button_id, kb_id, info_key = call.data.split(":")
        button_id = int(button_id); kb_id = int(kb_id)
        waiting[call.from_user.id] = (button_id, kb_id, info_key)
        bot.answer_callback_query(call.id, "الرجاء ارسال المعلومة الآن (ستظهر رسالة تأكيد).")
        bot.send_message(call.message.chat.id, f"الرجاء إرسال {info_key} الآن.\nبعد الإرسال سيظهر: 'طلبك قيد المعالجة'")

    @bot.callback_query_handler(func=lambda call: call.data and call.data.startswith("action:"))
    def action_handler(call):
        bot.answer_callback_query(call.id, "تم الضغط على الزر. إن أردت طلب الخدمة اضغط الزر المناسب.")

    # capture info messages
    @bot.message_handler(func=lambda m: m.from_user.id in waiting)
    def capture_info(message):
        if message.from_user.id not in waiting:
            return
        button_id, kb_id, info_key = waiting.pop(message.from_user.id)
        # save request
        create_request(message.from_user.id, button_id, info_key, message.text or "")
        # notify user
        bot.reply_to(message, "طلبك قيد المعالجة يرجى الأنتظار بصبر حتى أتمام العملية ✅")
        # notify admins
        path_names = []
        cur_id = button_id
        while cur_id != 0:
            row = get_button(cur_id)
            if not row: break
            path_names.append(row[2])
            cur_id = row[1]
        path = " > ".join(reversed(path_names))
        admin_text = (f"📩 <b>طلب جديد</b>\n"
                      f"من: <b>{message.from_user.full_name}</b>\n"
                      f"ID: {message.from_user.id}\n"
                      f"الخدمة: {path}\n"
                      f"المعلومة ({info_key}):\n{message.text}")
        for aid in ADMIN_IDS:
            try:
                bot.send_message(aid, admin_text, parse_mode="HTML")
            except:
                pass
