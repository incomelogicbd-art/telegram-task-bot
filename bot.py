import telebot  # spelling fixed
from telebot import types
import os
import psycopg2
from flask import Flask
from threading import Thread
from datetime import datetime, timedelta

# ======================
# RENDER FIX: WEB SERVER
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
    # SSL Mode require is essential for Neon DB
    return psycopg2.connect(DB_URL)

def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
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
    conn.commit()
    cur.close()
    conn.close()

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
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT coins, task_count, is_banned, last_task_time, referred_by FROM users WHERE user_id = %s", (user_id,))
    res = cur.fetchone()
    if not res:
        cur.execute("INSERT INTO users (user_id) VALUES (%s)", (user_id,))
        conn.commit()
        res = (0, 0, False, None, None)
    cur.close()
    conn.close()
    return {
        "coins": res[0],
        "task_count": res[1],
        "is_banned": res[2],
        "last_task_time": res[3],
        "referred_by": res[4]
    }

user_status = {}

# ======================
# START COMMAND
# ======================
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    user = get_user_data(user_id)
    
    if user["is_banned"]:
        bot.send_message(message.chat.id, "🚫 আপনি এই বট থেকে আজীবনের জন্য ব্যান হয়েছেন।")
        return

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

    welcome_msg = f"👋 স্বাগতম, {message.from_user.first_name}!\n\nছোট ছোট টাস্ক সম্পন্ন করে কয়েন ইনকাম করুন।\n🚀 কাজ শুরু করতে '📋 সকল টাস্ক' বাটনে ক্লিক করুন।"
    bot.send_message(message.chat.id, welcome_msg, reply_markup=keyboard)

# ======================
# ADMIN PANEL
# ======================
@bot.message_handler(func=lambda m: m.text == "⚙️ অ্যাডমিন প্যানেল")
def admin_panel(message):
    if message.from_user.id == ADMIN_ID:
        conn = get_db_connection(); cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM users"); total_users = cur.fetchone()[0]
        cur.close(); conn.close()
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🚫 ইউজার ব্যান করুন", callback_data="admin_ban_user"))
        bot.send_message(message.chat.id, f"📊 অ্যাডমিন প্যানেল\n👥 মোট ইউজার: {total_users} জন", reply_markup=markup)

# ======================
# CALLBACKS & ADMIN CONTROL
# ======================
@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    user_id = call.from_user.id
    
    if call.data == "admin_ban_user" and user_id == ADMIN_ID:
        user_status[user_id] = "waiting_ban_id"
        bot.send_message(call.message.chat.id, "🆔 আপনি যাকে ব্যান করতে চান তার ইউজার আইডি দিন:")
        return

    task_details = {
        "task_1": "https://a29226311-ctrl.github.io/task1/", "task_2": "https://a29226311-ctrl.github.io/task2/",
        "task_3": "https://a29226311-ctrl.github.io/singup/", "task_4": "https://a29226311-ctrl.github.io/app/",
        "task_5": "https://a29226311-ctrl.github.io/abcd/", "task_6": "https://a29226311-ctrl.github.io/srst/",
        "task_7": "https://a29226311-ctrl.github.io/bhre/", "task_8": "https://a29226311-ctrl.github.io/auts/",
        "task_9": "https://a29226311-ctrl.github.io/katr/", "task_10": "https://a29226311-ctrl.github.io/tyre/"
    }

    if call.data in task_details:
        user_status[user_id] = f"waiting_{call.data}"
        msg = f"📋 <b>{call.data.replace('task_', 'টাস্ক ')}</b>\n\n🔗 <b>লিঙ্ক:</b> {task_details[call.data]}\n\n📸 কাজ শেষ করে স্ক্রিনশটটি এখানে পাঠান।"
        bot.edit_message_text(msg, call.message.chat.id, call.message.message_id)

    elif call.data.startswith("pay_"):
        method = call.data.replace("pay_", "")
        user_status[user_id] = f"waiting_number_{method}"
        bot.edit_message_text(f"📱 আপনার <b>{method}</b> নাম্বারটি লিখুন:", call.message.chat.id, call.message.message_id)

    elif "_" in call.data and user_id == ADMIN_ID:
        parts = call.data.split("_")
        action, uid = parts[0], int(parts[1])
        conn = get_db_connection(); cur = conn.cursor()

        if action == "approve":
            tid, reward = parts[2], int(parts[3])
            cur.execute("UPDATE users SET coins = coins + %s, task_count = task_count + 1, last_task_time = %s WHERE user_id = %s", (reward, datetime.now(), uid))
            conn.commit()
            bot.send_message(uid, f"✅ আপনার টাস্ক অ্যাপ্রুভ হয়েছে! ১০০ কয়েন যোগ হয়েছে।")
            bot.edit_message_caption(f"✅ Approved User: {uid}", call.message.chat.id, call.message.message_id)
        elif action == "reject":
            bot.send_message(uid, "❌ আপনার প্রুফটি সঠিক নয়।")
            bot.edit_message_caption(f"❌ Rejected User: {uid}", call.message.chat.id, call.message.message_id)
        elif action == "ban":
            cur.execute("UPDATE users SET is_banned = TRUE WHERE user_id = %s", (uid,))
            conn.commit()
            bot.send_message(uid, "🚫 আপনাকে ব্যান করা হয়েছে।")
            bot.edit_message_caption(f"🚫 Banned User: {uid}", call.message.chat.id, call.message.message_id)
        elif action == "paycomplete":
            cur.execute("UPDATE users SET coins = coins - 1000 WHERE user_id = %s", (uid,))
            conn.commit()
            bot.send_message(uid, "💰 উইথড্র রিকোয়েস্ট সফল! ১০০০ কয়েন কাটা হয়েছে।")
            bot.edit_message_text(f"✅ Paid for {uid}", call.message.chat.id, call.message.message_id)
        
        cur.close(); conn.close()

# ======================
# INPUT HANDLER
# ======================
@bot.message_handler(content_types=['text', 'photo'])
def handle_inputs(message):
    user_id = message.from_user.id
    user = get_user_data(user_id)
    if user["is_banned"]: return
    
    status = user_status.get(user_id, "none")

    if user_id == ADMIN_ID and status == "waiting_ban_id":
        try:
            target_id = int(message.text)
            conn = get_db_connection(); cur = conn.cursor()
            cur.execute("UPDATE users SET is_banned = TRUE WHERE user_id = %s", (target_id,))
            conn.commit(); cur.close(); conn.close()
            bot.reply_to(message, f"✅ ইউজার {target_id} ব্যান হয়েছে।")
        except: 
            bot.reply_to(message, "❌ সঠিক আইডি দিন।")
        user_status[user_id] = "none"; return

    if message.content_type == 'photo' and status.startswith("waiting_task_"):
        tid = status.replace("waiting_", "")
        markup = types.InlineKeyboardMarkup()
        markup.row(types.InlineKeyboardButton("✅ Approve", callback_data=f"approve_{user_id}_{tid}_100"),
                   types.InlineKeyboardButton("❌ Reject", callback_data=f"reject_{user_id}"))
        markup.row(types.InlineKeyboardButton("🚫 Ban User", callback_data=f"ban_{user_id}"))
        bot.send_photo(ADMIN_ID, message.photo[-1].file_id, caption=f"🔔 নতুন প্রুফ!\nID: {user_id}\nTask: {tid}", reply_markup=markup)
        bot.reply_to(message, "✅ প্রুফ জমা হয়েছে। অ্যাডমিন চেক করলে কয়েন পাবেন।")
        user_status[user_id] = "none"

    elif message.text == "📋 সকল টাস্ক":
        if user["last_task_time"] and datetime.now() < user["last_task_time"] + timedelta(hours=24):
            wait_time = (user["last_task_time"] + timedelta(hours=24)) - datetime.now()
            hours, remainder = divmod(wait_time.seconds, 3600); minutes, _ = divmod(remainder, 60)
            bot.reply_to(message, f"⚠️ আবার কাজ করতে {hours} ঘণ্টা {minutes} মিনিট অপেক্ষা করুন।")
            return
        keyboard = types.InlineKeyboardMarkup()
        tasks_info = [("task_1", 100), ("task_2", 100), ("task_3", 100), ("task_4", 100), ("task_5", 100),
                      ("task_6", 100), ("task_7", 100), ("task_8", 100), ("task_9", 100), ("task_10", 100)]
        for i, (tid, coin) in enumerate(tasks_info, 1):
            keyboard.add(types.InlineKeyboardButton(f"✨ টাস্ক {i} ({coin} কয়েন)", callback_data=tid))
        bot.send_message(message.chat.id, "👇 টাস্কগুলো সম্পন্ন করুন:", reply_markup=keyboard)

    elif message.text == "👥 রেফারেল":
        ref_link = f"https://t.me/{BOT_USERNAME}?start={user_id}"
        bot.reply_to(message, f"👥 আপনার রেফারেল লিঙ্ক:\n<code>{ref_link}</code>\n\nপ্রতি রেফারে পাবেন ১০০ কয়েন!")

    elif message.text == "🪙 আমার কয়েন":
        bot.reply_to(message, f"🪙 ব্যালেন্স: {user['coins']} কয়েন\n✅ মোট সম্পন্ন টাস্ক: {user['task_count']} টি")
    
    elif message.text == "📤 উইথড্র":
        if user["coins"] < 1000:
            bot.reply_to(message, f"⚠️ উইথড্র করতে কমপক্ষে ১০০০ কয়েন লাগবে। আপনার আছে {user['coins']} কয়েন।")
        elif user["task_count"] < 10: 
            bot.reply_to(message, f"⚠️ আপনি রেফার করে কয়েন জমালেও, টাকা তুলতে হলে অন্তত ১০টি টাস্ক পূরণ করতে হবে। আপনি করেছেন {user['task_count']}টি।")
        else:
            keyboard = types.InlineKeyboardMarkup()
            keyboard.row(types.InlineKeyboardButton("বিকাশ", callback_data="pay_Bkash"), types.InlineKeyboardButton("নগদ", callback_data="pay_Nagad"))
            bot.send_message(message.chat.id, "💳 পেমেন্ট মেথড সিলেক্ট করুন:", reply_markup=keyboard)

    elif message.text == "📞 সাপোর্ট":
        bot.reply_to(message, f"📢 সাপোর্ট গ্রুপ: {PAYMENT_GROUP}")

    elif message.content_type == 'text' and status.startswith("waiting_number_"):
        method = status.replace("waiting_number_", "")
        pay_markup = types.InlineKeyboardMarkup()
        pay_markup.add(types.InlineKeyboardButton("✅ পেমেন্ট করেছি (১০০০ কাটুন)", callback_data=f"paycomplete_{user_id}"))
        bot.send_message(ADMIN_ID, f"💰 উইথড্র রিকোয়েস্ট!\n🆔 আইডি: {user_id}\n💳 মেথড: {method}\n📱 নাম্বার: {message.text}\n✅ সম্পন্ন টাস্ক: {user['task_count']}টি", reply_markup=pay_markup)
        bot.reply_to(message, "✅ রিকোয়েস্ট জমা হয়েছে।")
        user_status[user_id] = "none"

if __name__ == "__main__":
    keep_alive()
    bot.remove_webhook() # Added to clear connection conflicts
    bot.infinity_polling() 
