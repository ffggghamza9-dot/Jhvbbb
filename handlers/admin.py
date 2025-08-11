# handlers/admin.py
from telebot import types
from config import ADMIN_IDS
from keyboards import admin_reply_kb
from database import *
from utils import is_admin
from templates import DEFAULT_TEMPLATES

# simple in-memory state for multi-step admin flows
admin_wait = {}

def register_handlers(bot):
    @bot.message_handler(commands=['admin'])
    def admin_panel(message):
        if not is_admin(message.from_user.id):
            bot.reply_to(message, "🚫 لست أدمن.")
            return
        bot.send_message(message.chat.id, "📌 لوحة الأدمن", reply_markup=admin_reply_kb())

    @bot.message_handler(func=lambda m: is_admin(m.from_user.id) and m.text in [
        "🛠 إدارة الأزرار", "👤 إدارة المستخدمين", "📦 إدارة الطلبات", "📝 القوالب",
        "🖼 تحديث المحتوى", "📩 بث رسالة", "📊 إحصائيات", "📜 السجل", "🔁 تحديث الواجهة"
    ])
    def admin_actions(message):
        text = message.text
        if text == "🛠 إدارة الأزرار":
            rows = list_children(0)
            if not rows:
                bot.send_message(message.chat.id, "لا يوجد أزرار حالياً. اكتب: addbtn <اسم الزر>")
            else:
                txt = "الأزرار الرئيسية:\n" + "\n".join([f"{r[0]} | {r[1]}" for r in rows])
                bot.send_message(message.chat.id, txt + "\n\nلإضافة زر جديد: addbtn <اسم>\nلإضافة فرعي: addchild <parent_id>|<اسم>")
        elif text == "👤 إدارة المستخدمين":
            bot.send_message(message.chat.id, "أوامر: user <id> | ban <id> | unban <id> | addbal <id>|<amt> | subbal <id>|<amt>")
        elif text == "📩 بث رسالة":
            bot.send_message(message.chat.id, "أرسل نص الرسالة الآن وسيتم بثه لجميع المستخدمين.")
            admin_wait[message.chat.id] = ("broadcast",)
        elif text == "📝 القوالب":
            tpls = list_templates()
            if not tpls:
                for k,v in DEFAULT_TEMPLATES.items():
                    add_template(k, v)
                tpls = list_templates()
            bot.send_message(message.chat.id, "قوالب الرد الحالية:\n" + "\n".join([f"{t[0]} | {t[1]}" for t in tpls]) + "\n\nلإضافة قالب: addtpl <name>|<text>\nلحذف: deltpl <id>")
        elif text == "📊 إحصائيات":
            users = len(get_all_user_ids())
            reqs = len(list_requests())
            bot.send_message(message.chat.id, f"👥 مستخدمين: {users}\n📩 طلبات: {reqs}")
        elif text == "📜 السجل":
            logs = recent_logs(20)
            txt = "\n".join([f"{l[0]} | {l[1]} | {l[2]} | {l[3]}" for l in logs])
            bot.send_message(message.chat.id, "آخر السجلات:\n" + (txt or "لا سجلات"))
        elif text == "🔁 تحديث الواجهة":
            bot.send_message(message.chat.id, "أوامر الواجهة:\naddbtn <name>\naddchild <parent_id>|<name>\neditbtn <id>|<new name>\ndelbtn <id>")
        else:
            bot.send_message(message.chat.id, "خيار غير معروف.")

    @bot.message_handler(func=lambda m: is_admin(m.from_user.id))
    def admin_text(message):
        txt = (message.text or "").strip()
        # add button
        if txt.startswith("addbtn "):
            name = txt.split(" ",1)[1].strip()
            bid = create_button(name, parent_id=0, kind='menu')
            bot.reply_to(message, f"تم إنشاء زر رئيسي: {name} (id={bid})")
        elif txt.startswith("addchild "):
            try:
                payload = txt.split(" ",1)[1]
                parent, name = payload.split("|",1)
                parent = int(parent.strip())
                bid = create_button(name.strip(), parent_id=parent, kind='menu')
                bot.reply_to(message, f"تم إنشاء زر فرعي: {name.strip()} (id={bid}) تحت {parent}")
            except:
                bot.reply_to(message, "خطأ في الصيغة. استخدم: addchild <parent_id>|<name>")
        elif txt.startswith("addcontent "):
            try:
                payload = txt.split(" ",1)[1]
                parent, title, content = payload.split("|",2)
                parent = int(parent.strip())
                bid = create_button(title.strip(), parent_id=parent, kind='content', content_text=content)
                bot.reply_to(message, f"تم إنشاء محتوى id={bid}")
            except:
                bot.reply_to(message, "خطأ. استخدم: addcontent <parent_id>|<title>|<text>")
        elif txt.startswith("editbtn "):
            try:
                payload = txt.split(" ",1)[1]
                bid, name = payload.split("|",1)
                bid = int(bid.strip())
                update_button(bid, title=name.strip())
                bot.reply_to(message, "تم التعديل.")
            except:
                bot.reply_to(message, "خطأ. استخدم: editbtn <id>|<new name>")
        elif txt.startswith("delbtn "):
            try:
                bid = int(txt.split(" ",1)[1].strip())
                delete_button(bid)
                bot.reply_to(message, "تم الحذف.")
            except Exception:
                bot.reply_to(message, "خطأ بالحذف.")
        elif txt.startswith("user "):
            try:
                uid = int(txt.split(" ",1)[1].strip())
                ensure_user(uid)
                bal = get_balance(uid)
                banned = is_banned(uid)
                bot.reply_to(message, f"User {uid}\nرصيد: ${bal:.2f}\nمحظور: {banned}")
            except:
                bot.reply_to(message, "خطأ. استخدم: user <id>")
        elif txt.startswith("ban ") or txt.startswith("unban "):
            parts = txt.split()
            try:
                cmd = parts[0]; uid = int(parts[1])
                set_ban(uid, 1 if cmd=="ban" else 0)
                bot.reply_to(message, f"تم {'حظر' if cmd=='ban' else 'فك الحظر'} {uid}")
                if cmd == "ban":
                    try:
                        bot.send_message(uid, "لقد تم حظرك. تواصل مع الأدمن.")
                    except: pass
            except:
                bot.reply_to(message, "خطأ. استخدام: ban <id> أو unban <id>")
        elif txt.startswith("addbal ") or txt.startswith("subbal "):
            try:
                payload = txt.split(" ",1)[1]
                uid_s, amount_s = payload.split("|",1)
                uid = int(uid_s.strip()); amount = float(amount_s.strip())
                if txt.startswith("addbal "):
                    add_balance(uid, amount)
                    bot.reply_to(message, f"تم اضافة ${amount:.2f} إلى {uid}")
                else:
                    add_balance(uid, -amount)
                    bot.reply_to(message, f"تم خصم ${amount:.2f} من {uid}")
            except:
                bot.reply_to(message, "خطأ. الصيغة: addbal <id>|<amount>  أو subbal <id>|<amount>")
        elif txt.startswith("addtpl "):
            try:
                payload = txt.split(" ",1)[1]
                name, content = payload.split("|",1)
                add_template(name.strip(), content.strip())
                bot.reply_to(message, "تم إضافة القالب.")
            except:
                bot.reply_to(message, "خطأ. استخدم: addtpl <name>|<text>")
        elif txt.startswith("deltpl "):
            try:
                tid = int(txt.split(" ",1)[1].strip())
                del_template(tid)
                bot.reply_to(message, "تم حذف القالب.")
            except:
                bot.reply_to(message, "خطأ. deltpl <id>")
        elif message.chat.id in admin_wait and admin_wait[message.chat.id][0] == "broadcast":
            text = message.text
            users = get_all_user_ids()
            sent = 0
            for uid in users:
                try:
                    bot.send_message(uid, text, parse_mode="HTML")
                    sent += 1
                except:
                    pass
            bot.reply_to(message, f"تم الإرسال إلى {sent}/{len(users)}")
            admin_wait.pop(message.chat.id, None)
        else:
            # reply-as-bot: admin can reply to notification containing "ID: <num>"
            if message.reply_to_message and message.reply_to_message.text:
                import re
                m = re.search(r"ID:\s*(\d+)", message.reply_to_message.text)
                if m:
                    uid = int(m.group(1))
                    bot.send_message(uid, f"📩 رسالة من الأدمن:\n{message.text}", parse_mode="HTML")
                    bot.reply_to(message, "تم الإرسال للمستخدم.")
                    log("admin_reply", f"admin {message.from_user.id} -> user {uid}")
                    return
            bot.reply_to(message, "أمر غير معروف أو تنسيق خاطئ.")
