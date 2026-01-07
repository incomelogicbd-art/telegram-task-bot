import telebot
from telebot import types
import os

# ======================
# BOT TOKEN (Railway Variable)
# ======================
BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

# ======================
# TEMP DATABASE (later Firebase)
# ======================
users = {}

# ======================
# SETTINGS
# ======================
TASK_REWARD = 200
REFERRAL_BONUS = 100
MIN_WITHDRAW = 1000

# ======================
# INIT USER
# ======================
def init_user(user_id, referred_by=None):
    if user_id not in users:
        users[user_id] = {
            "coins": 0,
            "referred_by": referred_by,
            "referral_bonus_given": False,
            "task_done": False
        }

# ======================
# START
# ======================
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    name = message.from_user.first_name or "User"

    args = message.text.split()
    ref_id = None
    if len(args) > 1:
        try:
            ref_id = int(args[1])
            if ref_id == user_id:
                ref_id = None
        except:
            ref_id = None

    init_user(user_id, ref_id)

    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row("📋 টাস্ক লিস্ট", "🪙 আমার কয়েন")
    keyboard.row("✅ টাস্ক সম্পন্ন করেছি")
    keyboard.row("👥 রেফারেল", "📤 উইথড্র")
    keyboard.row("📞 সাপোর্ট")

    bot.send_message(
        message.chat.id,
        f"""
👋 স্বাগতম <b>{name}</b>!

🤖 <b>BD Simple Task Bot</b>

🪙 টাস্ক করে কয়েন ইনকাম করুন
🎁 রেফার বোনাস: <b>{REFERRAL_BONUS}</b> কয়েন
💸 <b>{MIN_WITHDRAW}</b> কয়েন হলে উইথড্র

👇 মেনু ব্যবহার করুন
""",
        reply_markup=keyboard
    )

# ======================
# TASK LIST
# ======================
@bot.message_handler(func=lambda m: m.text and "টাস্ক লিস্ট" in m.text)
def task_list(message):
    bot.reply_to(
        message,
        f"📋 <b>বর্তমান টাস্ক</b>\n\n"
        f"👉 ১টি ডেমো টাস্ক\n"
        f"🏆 রিওয়ার্ড: <b>{TASK_REWARD}</b> কয়েন\n\n"
        f"শেষ হলে <b>টাস্ক সম্পন্ন করেছি</b> চাপুন"
    )

# ======================
# TASK DONE
# ======================
@bot.message_handler(func=lambda m: m.text and "টাস্ক সম্পন্ন" in m.text)
def task_done(message):
    user_id = message.from_user.id
    init_user(user_id)

    if users[user_id]["task_done"]:
        bot.reply_to(message, "❌ আপনি ইতিমধ্যে টাস্ক শেষ করেছেন।")
        return

    users[user_id]["task_done"] = True
    users[user_id]["coins"] += TASK_REWARD

    ref_id = users[user_id]["referred_by"]
    if ref_id and ref_id in users and not users[user_id]["referral_bonus_given"]:
        users[ref_id]["coins"] += REFERRAL_BONUS
        users[user_id]["referral_bonus_given"] = True

        bot.send_message(
            ref_id,
            f"🎉 অভিনন্দন!\nআপনি {REFERRAL_BONUS} কয়েন রেফার বোনাস পেয়েছেন।"
        )

    bot.reply_to(
        message,
        f"✅ টাস্ক সম্পন্ন!\n🪙 আপনি পেয়েছেন {TASK_REWARD} কয়েন"
    )

# ======================
# MY COINS
# ======================
@bot.message_handler(func=lambda m: m.text and "কয়েন" in m.text)
def my_coins(message):
    user_id = message.from_user.id
    init_user(user_id)

    bot.reply_to(
        message,
        f"🪙 আপনার কয়েন:\n<b>{users[user_id]['coins']}</b>"
    )

# ======================
# REFERRAL
# ======================
@bot.message_handler(func=lambda m: m.text and "রেফার" in m.text)
def referral(message):
    user_id = message.from_user.id
    bot_username = bot.get_me().username

    link = f"https://t.me/{bot_username}?start={user_id}"

    bot.reply_to(
        message,
        f"👥 <b>রেফারেল লিংক</b>\n{link}\n\n"
        f"🎁 প্রতি রেফারে {REFERRAL_BONUS} কয়েন"
    )

# ======================
# WITHDRAW
# ======================
@bot.message_handler(func=lambda m: m.text and "উইথড্র" in m.text)
def withdraw(message):
    user_id = message.from_user.id
    init_user(user_id)

    coins = users[user_id]["coins"]
    if coins < MIN_WITHDRAW:
        bot.reply_to(
            message,
            f"❌ উইথড্র সম্ভব নয়\n"
            f"দরকার: {MIN_WITHDRAW} কয়েন\n"
            f"আপনার আছে: {coins} কয়েন"
        )
    else:
        bot.reply_to(
            message,
            f"✅ উইথড্র রিকুয়েস্ট করা যাবে\n"
            f"🪙 আপনার কয়েন: {coins}\n"
            f"📞 সাপোর্টে যোগাযোগ করুন"
        )

# ======================
# SUPPORT
# ======================
@bot.message_handler(func=lambda m: m.text and "সাপোর্ট" in m.text)
def support(message):
    bot.reply_to(message, "📞 সাপোর্ট\n👉 @incomelogicbd2")

# ======================
print("✅ Railway Bot Running...")
bot.infinity_polling(skip_pending=True)
