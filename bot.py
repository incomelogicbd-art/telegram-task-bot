import telebot
from telebot import types
import os
import psycopg2
from flask import Flask
from threading import Thread

# ======================
# RENDER FIX: WEB SERVER
# ======================
app = Flask('')
@app.route('/')
def home(): return "Bot is Alive and DB Connected!"

def run():
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()

# ======================
# DATABASE SETUP (PostgreSQL)
# ======================
DB_URL = os.getenv("DATABASE_URL")

def get_db_connection():
    return psycopg2.connect(DB_URL)

def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id BIGINT PRIMARY KEY,
            coins INTEGER DEFAULT 0,
            completed_tasks TEXT DEFAULT '',
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
    cur.execute("SELECT coins, completed_tasks, is_banned FROM users WHERE user_id = %s", (user_id,))
    res = cur.fetchone()
    if not res:
        cur.execute("INSERT INTO users (user_id) VALUES (%s)", (user_id,))
        conn.commit()
        res = (0, '', False)
    cur.close()
    conn.close()
    return {
        "coins": res[0],
        "completed_tasks": res[1].split(',') if res[1] else [],
        "is_banned": res[2]
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
        bot.send_message(message.chat.id, "🚫 আপনি এই বট থেকে ব্যান হয়েছেন।")
        return

    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row("📋 সকল টাস্ক", "🪙 আমার কয়েন")
    keyboard.row("👥 রেফারেল", "📤 উইথড্র")
    keyboard.row("📞 সাপোর্ট")
    if user_id == ADMIN_ID: keyboard.row("⚙️ অ্যাডমিন প্যানেল")

    bot.send_message(message.chat.id, f"👋 স্বাগতম <b>{message.from_user.first_name}</b>!", reply_markup=keyboard)

# ======================
# TASK LIST
# ======================
@bot.message_handler(func=lambda m: m.text == "📋 সকল টাস্ক")
def task_list(message):
    user_id = message.from_user.id
    user = get_user_data(user_id)
    if user["is_banned"]: return
    
    keyboard = types.InlineKeyboardMarkup()
    tasks_info = [
        ("task_1", 100), ("task_2", 100), ("task_3", 200), ("task_4", 100), ("task_5", 100),
        ("task_6", 100), ("task_7", 100), ("task_8", 100), ("task_9", 100), ("task_10", 100)
    ]
    
    for i, (tid, coin) in enumerate(tasks_info, 1):
        status_txt = f"✅ টাস্ক {i} (Done)" if tid in user["completed_tasks"] else f"টাস্ক {i} ({coin} কয়েন)"
        keyboard.add(types.InlineKeyboardButton(status_txt, callback_data=tid))
            
    bot.send_message(message.chat.id, "👇 নিচের যেকোনো টাস্ক ক্লিক করে কাজ সম্পন্ন করুন:", reply_markup=keyboard)

# ======================
# CALLBACK HANDLER
# ======================
@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    user_id = call.from_user.id
    user = get_user_data(user_id)

    task_details = {
        "task_1": "https://a29226311-ctrl.github.io/task1/",
        "task_2": "https://a29226311-ctrl.github.io/task2/",
        "task_3": "https://a29226311-ctrl.github.io/singup/",
        "task_4": "https://a29226311-ctrl.github.io/app/",
        "task_5": "https://a29226311-ctrl.github.io/abcd/",
        "task_6": "https://a29226311-ctrl.github.io/srst/",
        "task_7": "https://a29226311-ctrl.github.io/bhre/",
        "task_8": "https://a29226311-ctrl.github.io/auts/",
        "task_9": "https://a29226311-ctrl.github.io/katr/",
        "task_10": "https://a29226311-ctrl.github.io/tyre/"
    }

    if call.data in task_details:
        if call.data in user["completed_tasks"]:
            bot.answer_callback_query(call.id, "❌ আপনি এটি আগেই করেছেন!", show_alert=True)
            return
            
        user_status[user_id] = f"waiting_{call.data}"
        link = task_details[call.data]
        
        msg = f"📋 <b>{call.data.replace('task_', 'টাস্ক ')}</b>\n\n"
        msg += f"🛠 <b>কিভাবে কাজ করবেন নির্দেশনা লিংকের ভিতর দেয়া আছে।</b>\n\n"
        msg += f"🔗 <b>লিঙ্ক:</b> {link}\n\n"
        msg += f"📸 কাজ শেষ করে নিচে স্ক্রিনশটটি পাঠান।"
        
        bot.edit_message_text(msg, call.message.chat.id, call.message.message_id, parse_mode="HTML")

    elif call.data.startswith("pay_"):
        method = call.data.replace("pay_", "")
        user_status[user_id] = f"waiting_number_{method}"
        bot.edit_message_text(f"📱 আপনার <b>{method}</b> নাম্বারটি লিখে সেন্ড করুন।", call.message.chat.id, call.message.message_id)

    elif "_" in call.data and user_id == ADMIN_ID:
        parts = call.data.split("_")
        action, uid = parts[0], int(parts[1])
        conn = get_db_connection(); cur = conn.cursor()

        if action == "approve":
            tid, reward = parts[2], int(parts[3])
            target_user = get_user_data(uid)
            if tid not in target_user["completed_tasks"]:
                new_tasks = ",".join(target_user["completed_tasks"] + [tid])
                cur.execute("UPDATE users SET coins = coins + %s, completed_tasks = %s WHERE user_id = %s", (reward, new_tasks, uid))
                conn.commit()
                bot.send_message(uid, f"💰 অভিনন্দন! {reward} কয়েন যোগ হয়েছে।\n✅ পেমেন্ট প্রুফ গ্রুপ: {PAYMENT_GROUP}")
                bot.edit_message_caption(f"✅ Approved for {uid}", call.message.chat.id, call.message.message_id)
        elif action == "reject":
            bot.send_message(uid, "❌ আপনার প্রুফটি সঠিক নয়। দয়া করে নির্দেশনা মেনে আবার কাজ করুন।")
            bot.edit_message_caption(f"❌ Rejected for {uid}", call.message.chat.id, call.message.message_id)
        
        cur.close(); conn.close()

# ======================
# INPUT HANDLER
# ======================
@bot.message_handler(content_types=['text', 'photo'])
def handle_inputs(message):
    user_id = message.from_user.id
    user = get_user_data(user_id)
    status = user_status.get(user_id, "none")

    if message.content_type == 'photo' and status.startswith("waiting_task_"):
        tid = status.replace("waiting_", "")
        rewards = {"task_1": 100, "task_2": 150, "task_3": 200, "task_4": 100, "task_5": 300, "task_6": 150, "task_7": 200, "task_8": 100, "task_9": 500, "task_10": 250}
        reward = rewards.get(tid, 50)
        
        markup = types.InlineKeyboardMarkup()
        markup.row(types.InlineKeyboardButton("✅ Approve", callback_data=f"approve_{user_id}_{tid}_{reward}"),
                   types.InlineKeyboardButton("❌ Reject", callback_data=f"reject_{user_id}"))
        
        bot.send_photo(ADMIN_ID, message.photo[-1].file_id, caption=f"🔔 নতুন প্রুফ!\nID: {user_id}\nTask: {tid}", reply_markup=markup)
        bot.reply_to(message, "✅ আপনার প্রুফ জমা হয়েছে! অ্যাডমিন চেক করে রিওয়ার্ড দিয়ে দেবে।")
        user_status[user_id] = "none"

    elif message.content_type == 'text' and status.startswith("waiting_number_"):
        method = status.replace("waiting_number_", "")
        bot.send_message(ADMIN_ID, f"💰 <b>উইথড্র রিকোয়েস্ট!</b>\n🆔 আইডি: {user_id}\n💳 মেথড: {method}\n📱 নাম্বার: {message.text}\n🪙 কয়েন: {user['coins']}")
        bot.reply_to(message, "✅ আপনার রিকোয়েস্ট জমা হয়েছে। ২৪ ঘণ্টার মধ্যে পেমেন্ট পেয়ে যাবেন।")
        user_status[user_id] = "none"

    elif message.text == "🪙 আমার কয়েন":
        bot.reply_to(message, f"🪙 আপনার বর্তমান ব্যালেন্স: <b>{user['coins']} কয়েন</b>")
    elif message.text == "📞 সাপোর্ট":
        bot.reply_to(message, f"📢 আমাদের সাপোর্ট গ্রুপ: {PAYMENT_GROUP}\n👤 অ্যাডমিন: {SUPPORT_USER}")
    elif message.text == "📤 উইথড্র":
        if user["coins"] < 1000:
            bot.reply_to(message, "⚠️ উইথড্র করতে কমপক্ষে ১০০০ কয়েন লাগবে।")
        else:
            keyboard = types.InlineKeyboardMarkup()
            keyboard.row(types.InlineKeyboardButton("বিকাশ", callback_data="pay_Bkash"), types.InlineKeyboardButton("নগদ", callback_data="pay_Nagad"))
            bot.send_message(message.chat.id, "💳 পেমেন্ট মেথড সিলেক্ট করুন:", reply_markup=keyboard)

if __name__ == "__main__":
    keep_alive()
    bot.infinity_polling()
    
