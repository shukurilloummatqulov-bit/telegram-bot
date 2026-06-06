import os
import requests
import telebot

BOT_TOKEN = os.getenv("8977018536:AAESKjDng5xEr_vSGfyiO8udsyEOsyVbiMk")
GROK_API_KEY = os.getenv("xai-xw8y83z0k8zqB2MN8ZtOldIKjUu2eh9VtQCK5RYjnvR6nhQMrbt6ZvvqnrHzSrUDmo1qjmVax8jY5avA")

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
            "model": "grok-beta",
            "messages": [
                {"role": "user", "content": message.text}
            ]
        }
    )

    data = response.json()
    print(data)  # Railway logda ko‘rish uchun

    if "choices" in data:
        answer = data["choices"][0]["message"]["content"]
        bot.reply_to(message, answer)
    else:
        bot.reply_to(message, f"Xato: {data}")

bot.polling()
