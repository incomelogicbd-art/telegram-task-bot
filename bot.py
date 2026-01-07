import telebot
from telebot import types
import os
from flask import Flask
from threading import Thread

# ======================
# RENDER FIX: WEB SERVER
# ======================
app = Flask('')
@app.route('/')
def home():
    return "Bot is Running!"

def run():
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()

# ======================
# BOT SETTINGS (Your Info Integrated)
# ======================
BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

ADMIN_ID = 8214414683  # আপনার আইডি
BOT_USERNAME = "bd_simple_task_bot" # বটের ইউজারনেম
CHANNEL_LINK = "https://t.me/simpletaskbd24" # চ্যানেল লিংক
SUPPORT_USER = "@incomelogicbd2" # আপনার ইউজারনেম

# সাময়িক ইউজার ডাটা
users = {}

def init_user(user_id, referred_by=None):
    if user_id not in users:
        users[user_id] = {
            "coins": 0,
            "referred_by": referred_by,
            "referral_bonus_given": False
        }

# ======================
# START & REFERRAL LOGIC
# ======================
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    name = message.from_user.first_name or "User"
    
    # রেফারেল চেক
    args = message.text.split()
    ref_id = None
    if len(args) > 1:
        try:
            ref_id = int(args[1])
            if ref_id == user_id: ref_id = None
        except: ref_id = None

    init_user(user_id, ref_id)

    # রেফারেল বোনাস লজিক
    if ref_id and ref_id in users and not users[user_id]["referral_bonus_given"]:
        users[ref_id]["coins"] += 100
        users[user_id]["referral_bonus_given"] = True
        try:
            bot.send_message(ref_id, f"🎉 অভিনন্দন! আপনার রেফারেল লিংক থেকে <b>{name}</b> জয়েন করেছে। আপনি <b>১০০ কয়েন</b> বোনাস পেয়েছেন।")
        except: pass

    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row("📋 টাস্ক লিস্ট", "🪙 আমার কয়েন")
    keyboard.row("✅ টাস্ক সম্পন্ন করেছি")
    keyboard.row("👥 রেফারেল", "📤 উইথড্র")
    keyboard.row("📞 সাপোর্ট")
    
    if user_id == ADMIN_ID:
        keyboard.row("⚙️ অ্যাডমিন প্যানেল")

    welcome_text = (
        f"👋 <b>আমাদের বটে আপনাকে স্বাগতম!</b>\n\n"
        f"এখানে আপনি খুব সহজে ছোট ছোট <b>টাস্ক সম্পন্ন করে টাকা আয় করতে পারবেন।</b>\n\n"
        f"🤖 <b>BD Simple Task Bot</b>\n"
        f"💰 প্রতি টাস্কে রিওয়ার্ড: <b>১০০</b> কয়েন\n"
        f"🎁 রেফার বোনাস: <b>১০০</b> কয়েন\n"
        f"💸 জমানো কয়েন সরাসরি বিকাশ/নগদে উইথড্র দেওয়া যায়।\n\n"
        f"👇 কাজ শুরু করতে নিচের মেনু ব্যবহার করুন।"
    )
    bot.send_message(message.chat.id, welcome_text, reply_markup=keyboard)

# ======================
# MENU HANDLERS
# ======================
@bot.message_handler(func=lambda m: True)
def handle_menu(message):
    user_id = message.from_user.id
    init_user(user_id)

    if message.text == "📋 টাস্ক লিস্ট":
        bot.reply_to(
            message, 
            f"📋 <b>আজকের টাস্ক</b>\n\n"
            f"👉 আমাদের অফিশিয়াল চ্যানেলে জয়েন করুন:\n{CHANNEL_LINK}\n\n"
            f"🏆 রিওয়ার্ড: <b>১০০</b> কয়েন।\n\n"
            f"<i>জয়েন করা শেষ হলে '✅ টাস্ক সম্পন্ন করেছি' বাটনে ক্লিক করুন।</i>"
        )

    elif message.text == "🪙 আমার কয়েন":
        bot.reply_to(message, f"🪙 আপনার বর্তমান ব্যালেন্স:\n<b>{users[user_id]['coins']} কয়েন</b>")

    elif message.text == "👥 রেফারেল":
        link = f"https://t.me/{BOT_USERNAME}?start={user_id}"
        bot.reply_to(
            message, 
            f"👥 <b>আপনার রেফারেল লিংক:</b>\n\n<code>{link}</code>\n\n"
            f"🎁 প্রতি সফল রেফারে পাবেন <b>১০০ কয়েন</b>!\n"
            f"লিংকটি কপি করে বন্ধুদের পাঠান।"
        )

    elif message.text == "✅ টাস্ক সম্পন্ন করেছি":
        bot.reply_to(message, "✅ আপনার টাস্ক রিভিউতে পাঠানো হয়েছে। অ্যাডমিন চেক করে কিছুক্ষণের মধ্যে কয়েন যোগ করে দিবে।")
        bot.send_message(ADMIN_ID, f"🔔 <b>টাস্ক অ্যালার্ট!</b>\nইউজার আইডি: <code>{user_id}</code>\nনাম: {message.from_user.first_name}\nটাস্ক চেক করুন।")

    elif message.text == "📤 উইথড্র":
        bot.reply_to(message, f"📤 উইথড্র করতে কমপক্ষে <b>১০০০</b> কয়েন প্রয়োজন। আপনার ব্যালেন্স হয়ে গেলে সাপোর্টে {SUPPORT_USER} যোগাযোগ করুন।")

    elif message.text == "📞 সাপোর্ট":
        bot.reply_to(message, f"📞 যেকোনো প্রয়োজনে আমাদের সাথে যোগাযোগ করুন:\n👉 {SUPPORT_USER}")

    elif message.text == "⚙️ অ্যাডমিন প্যানেল" and user_id == ADMIN_ID:
        total_users = len(users)
        bot.reply_to(message, f"⚙️ <b>অ্যাডমিন কন্ট্রোল</b>\n\n👥 মোট ইউজার: {total_users}\n📢 সিস্টেম স্ট্যাটাস: সচল")

if __name__ == "__main__":
    keep_alive()
    print("✅ Bot is ready with your info!")
    bot.infinity_polling()
    
