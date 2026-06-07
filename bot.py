import telebot
from groq import Groq

# ================== TOKENLAR ==================
TELEGRAM_TOKEN = "8977018536:AAESKjDng5xEr_vSGfyiO8udsyEOsyVbiMk"
GROQ_API_KEY = "xai-xw8y83z0k8zqB2MN8ZtOldIKjUu2eh9VtQCK5RYjnvR6nhQMrbt6ZvvqnrHzSrUDmo1qjmVax8jY5avA"

bot = telebot.TeleBot(TELEGRAM_TOKEN)
client = Groq(api_key=GROQ_API_KEY)

# AI bilan suhbat uchun
@bot.message_handler(func=lambda message: True)
def ai_reply(message):
    if message.chat.type == "private":
        return  # Shaxsiy chatda ishlamasin (xohlasangiz o'chirsa bo'ladi)

    if message.from_user.is_bot:
        return

    user = message.from_user
    mention = f"@{user.username}" if user.username else user.first_name

    try:
        # Groq orqali AI javobini olish
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "Sen do'stona, hazilkash va yordam beruvchi Grok botsan. O'zbek tilida javob ber."
                },
                {
                    "role": "user",
                    "content": message.text
                }
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.7,
            max_tokens=500
        )

        ai_text = chat_completion.choices[0].message.content

        # Javobni yuborish
        bot.reply_to(message, f"{mention} {ai_text}")

    except Exception as e:
        bot.reply_to(message, f"{mention} Kechirasiz, hozir biroz bandman 😅")

print("AI Bot ishga tushdi... (Grok uslubida)")
bot.infinity_polling()
