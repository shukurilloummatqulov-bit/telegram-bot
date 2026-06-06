import os
import requests
import telebot

BOT_TOKEN = os.getenv("BOT_TOKEN")
GROK_API_KEY = os.getenv("GROK_API_KEY")

bot = telebot.TeleBot(BOT_TOKEN)

@bot.message_handler(func=lambda message: True)
def chat(message):

    response = requests.post(
        "https://api.x.ai/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {GROK_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": "grok-4",
            "messages": [
                {"role": "user", "content": message.text}
            ]
        }
    )

    answer = response.json()["choices"][0]["message"]["content"]

    bot.reply_to(message, answer)

bot.infinity_polling()
