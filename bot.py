import telebot

TOKEN = "8977018536:AAESKjDng5xEr_vSGfyiO8udsyEOsyVbiMk"

bot = telebot.TeleBot(TOKEN)

@bot.message_handler(func=lambda message: True)
def reply_to_all(message):
    # Faqat guruhlarda ishlashi uchun
    if message.chat.type == "private":
        return  # Shaxsiy chatda javob bermaydi
    
    # Botning o'z xabariga javob bermasin
    if message.from_user.is_bot:
        return

    user = message.from_user
    username = user.username
    
    if username:
        mention = f"@{username}"
    else:
        mention = user.first_name

    text = f"{mention} rahmat ey oq kongil inson JAMA bekor chiqib ketdida"

    try:
        bot.reply_to(message, text)
    except:
        pass

print("Bot ishga tushdi... (Faqat guruhlarda ishlaydi)")
bot.infinity_polling()
