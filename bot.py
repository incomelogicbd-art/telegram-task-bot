import telebot
from telebot import types
import os
import psycopg2
from flask import Flask
from threading import Thread
from datetime import datetime, timedelta

# ======================
# WEB SERVER FOR HOSTING
# ======================
app = Flask('')
@app.route('/')
def home(): 
    return "Bot is Alive and DB Connected!"

def run():
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()

# ======================
# DATABASE SETUP
# ======================
DB_URL = os.getenv("DATABASE_URL")

def get_db_connection():
    return psycopg2.connect(DB_URL)

def init_db():
    conn = get_db_connection(); cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id BIGINT PRIMARY KEY,
            coins INTEGER DEFAULT 0,
            task_count INTEGER DEFAULT 0,
            completed_tasks TEXT DEFAULT '',
            last_task_time TIMESTAMP,
            referred_by BIGINT,
            is_banned BOOLEAN DEFAULT FALSE
        )
    ''')
    try:
        cur.execute('ALTER TABLE users ADD COLUMN IF NOT EXISTS last_task_time TIMESTAMP')
        cur.execute('ALTER TABLE users ADD COLUMN IF NOT EXISTS completed_tasks TEXT DEFAULT \'\'')
    except:
        conn.rollback()
    conn.commit()
    cur.close(); conn.close()

init_db()

# ======================
# BOT SETTINGS
# ======================
BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

ADMIN_ID = 8214414683 
BOT_USERNAME = "bd_simple_task_bot"
SUPPORT_USER = "@incomelogicbd2"
PAYMENT_GROUP = "https://t.me/simpletaskbd24"

def get_user_data(user_id):
    conn = get_db_connection(); cur = conn.cursor()
    cur.execute("SELECT coins, task_count, is_banned, last_task_time, referred_by, completed_tasks FROM users WHERE user_id = %s", (user_id,))
    res = cur.fetchone()
    
    if not res:
        cur.execute("INSERT INTO users (user_id, completed_tasks) VALUES (%s, '')", (user_id,))
        conn.commit()
        return {"coins": 0, "task_count": 0, "is_banned": False, "last_task_time": None, "referred_by": None, "completed_tasks": ""}
    
    coins, task_count, is_banned, last_task_time, referred_by, completed_tasks = res
    
    # ২৪ ঘণ্টা পর টাস্ক রিসেট লজিক
    if last_task_time and datetime.now() >= last_task_time + timedelta(hours=24):
        cur.execute("UPDATE users SET completed_tasks = '' WHERE user_id = %s", (user_id,))
        conn.commit()
        completed_tasks = ""

    cur.close(); conn.close()
    return {
        "coins": coins, "task_count": task_count, "is_banned": is_banned,
        "last_task_time": last_task_time, "referred_by": referred_by, "completed_tasks": completed_tasks or ""
    }

user_status = {}

# ======================
# HANDLERS
# ======================
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    user = get_user_data(user_id)
    if user["is_banned"]: return
    
    # রেফারেল হ্যান্ডলিং
    args = message.text.split()
    if len(args) > 1 and args[1].isdigit():
        ref_id = int(args[1])
        if not user["referred_by"] and ref_id != user_id:
            conn = get_db_connection(); cur = conn.cursor()
            cur.execute("UPDATE users SET referred_by = %s WHERE user_id = %s", (ref_id, user_id))
            cur.execute("UPDATE users SET coins = coins + 100 WHERE user_id = %s", (ref_id,))
            conn.commit(); cur.close(); conn.close()
            bot.send_message(ref_id, "🎉 আপনার রেফারেল লিঙ্কে নতুন কেউ জয়েন করেছে! আপনি ১০০ কয়েন পেয়েছেন।")

    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row("📋 সকল টাস্ক", "🪙 আমার কয়েন")
    keyboard.row("👥 রেফারেল", "📤 উইথড্র")
    keyboard.row("📞 সাপোর্ট")
    if user_id == ADMIN_ID: keyboard.row("⚙️ অ্যাডমিন প্যানেল")
    
    # [FIX] আপনার সেই আগের ওয়েলকাম মেসেজ
    welcome_msg = f"👋 স্বাগতম, {message.from_user.first_name}!\n\nছোট ছোট টাস্ক সম্পন্ন করে কয়েন ইনকাম করুন।\n🚀 কাজ শুরু করতে '📋 সকল টাস্ক' বাটনে ক্লিক করুন।"
    bot.send_message(message.chat.id, welcome_msg, reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    user_id = call.from_user.id
    user = get_user_data(user_id)
    
    task_details = {
        "task_1": "https://a29226311-ctrl.github.io/task1/", "task_2": "https://a29226311-ctrl.github.io/task2/",
        "task_3": "https://a29226311-ctrl.github.io/singup/", "task_4": "https://a29226311-ctrl.github.io/app/",
        "task_5": "https://a29226311-ctrl.github.io/abcd/", "task_6": "https://a29226311-ctrl.github.io/srst/",
        "task_7": "https://a29226311-ctrl.github.io/bhre/", "task_8": "https://a29226311-ctrl.github.io/auts/",
        "task_9": "https://a29226311-ctrl.github.io/katr/", "task_10": "https://a29226311-ctrl.github.io/tyre/"
    }

    if call.data in task_details:
        # [FIX] টাস্ক লকিং ও লিঙ্ক আসা নিশ্চিত করা
        if call.data in user["completed_tasks"].split(","):
            bot.answer_callback_query(call.id, "⚠️ এই টাস্কটি সম্পন্ন হয়েছে। ২৪ ঘণ্টা পর আবার করতে পারবেন।")
            return
        user_status[user_id] = f"waiting_{call.data}"
        msg = f"📋 <b>{call.data.replace('task_', 'টাস্ক ')}</b>\n\n🔗 <b>লিঙ্ক:</b> {task_details[call.data]}\n\n📸 কাজ শেষ করে স্ক্রিনশটটি এখানে পাঠান।"
        bot.edit_message_text(msg, call.message.chat.id, call.message.message_id)

    elif "_" in call.data and user_id == ADMIN_ID:
        parts = call.data.split("_")
        action, uid = parts[0], int(parts[1])
        conn = get_db_connection(); cur = conn.cursor()
        
        if action == "approve":
            tid = parts[2]
            # [FIX] ১০১ এর ঝামেলা মিটিয়ে সরাসরি ১০০ কয়েন
            cur.execute("UPDATE users SET coins = coins + 100, task_count = task_count + 1, last_task_time = %s, completed_tasks = CASE WHEN completed_tasks = '' THEN %s ELSE completed_tasks || ',' || %s END WHERE user_id = %s", (datetime.now(), tid, tid, uid))
            conn.commit()
            bot.send_message(uid, f"✅ আপনার টাস্ক অ্যাপ্রুভ হয়েছে! ১০০ কয়েন যোগ হয়েছে।")
            bot.edit_message_caption(f"✅ Approved: {uid}", call.message.chat.id, call.message.message_id)
        elif action == "reject":
            bot.send_message(uid, "❌ আপনার প্রুফটি সঠিক নয়।")
            bot.edit_message_caption(f"❌ Rejected: {uid}", call.message.chat.id, call.message.message_id)
        
        cur.close(); conn.close()

@bot.message_handler(content_types=['text', 'photo'])
def handle_inputs(message):
    user_id = message.from_user.id
    user = get_user_data(user_id)
    status = user_status.get(user_id, "none")

    if message.content_type == 'photo' and status.startswith("waiting_task_"):
        tid = status.replace("waiting_", "")
        markup = types.InlineKeyboardMarkup()
        markup.row(types.InlineKeyboardButton("✅ Approve", callback_data=f"approve_{user_id}_{tid}"),
                   types.InlineKeyboardButton("❌ Reject", callback_data=f"reject_{user_id}"))
        bot.send_photo(ADMIN_ID, message.photo[-1].file_id, caption=f"🔔 নতুন প্রুফ!\nID: {user_id}\nTask: {tid}", reply_markup=markup)
        bot.reply_to(message, "✅ প্রুফ জমা হয়েছে। অ্যাডমিন চেক করলে কয়েন পাবেন।")
        user_status[user_id] = "none"

    elif message.text == "📋 সকল টাস্ক":
        # ২৪ ঘণ্টার টাইম গ্যাপ চেক লজিক
        if user["last_task_time"] and datetime.now() < user["last_task_time"] + timedelta(hours=24):
            wait_time = (user["last_task_time"] + timedelta(hours=24)) - datetime.now()
            hours, remainder = divmod(wait_time.seconds, 3600); minutes, _ = divmod(remainder, 60)
            bot.reply_to(message, f"⚠️ আবার কাজ করতে {hours} ঘণ্টা {minutes} মিনিট অপেক্ষা করুন।")
            return
        
        completed_list = user["completed_tasks"].split(",")
        keyboard = types.InlineKeyboardMarkup()
        for i in range(1, 11):
            tid = f"task_{i}"
            btn_text = f"✅ টাস্ক {i} (Done)" if tid in completed_list else f"✨ টাস্ক {i} (১০০ কয়েন)"
            keyboard.add(types.InlineKeyboardButton(btn_text, callback_data=tid))
        bot.send_message(message.chat.id, "👇 টাস্কগুলো সম্পন্ন করুন:", reply_markup=keyboard)

    elif message.text == "🪙 আমার কয়েন":
        bot.reply_to(message, f"🪙 ব্যালেন্স: {user['coins']} কয়েন\n✅ মোট সম্পন্ন টাস্ক: {user['task_count']} টি")

if __name__ == "__main__":
    keep_alive()
    bot.remove_webhook()
    print("Bot is Starting...")
    bot.infinity_polling()
    
