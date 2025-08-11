# handlers/requests.py
from database import list_requests, set_request_status, get_button
from utils import is_admin

def register_handlers(bot):
    @bot.message_handler(func=lambda m: is_admin(m.from_user.id) and m.text and m.text.startswith("showreq"))
    def show_requests(message):
        parts = message.text.split()
        status = None
        if len(parts) > 1:
            status = parts[1]
        rows = list_requests(status)
        if not rows:
            bot.reply_to(message, "لا يوجد طلبات.")
            return
        for r in rows:
            rid, uid, button_id, info_key, info_text, stat, created_at = r
            btn = get_button(button_id)
            svc = btn[2] if btn else "?"
            txt = f"ID:{rid} | User:{uid} | Service:{svc}\nInfoKey:{info_key}\n{info_text}\nStatus:{stat}\n{created_at}"
            bot.send_message(message.chat.id, txt)
