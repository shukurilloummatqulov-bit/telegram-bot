import os
import logging
import telebot
from groq import Groq
 
# ─────────────────────────────────────────────────────────────
#  LOGGING  –  Railway "Deploy Logs" da ko'rinadi
# ─────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)
 
 
# ─────────────────────────────────────────────────────────────
#  TOKENLAR  –  Railway → Service → Variables bo'limiga qo'ying
#  Kodga hech qachon to'g'ridan-to'g'ri token yozmang!
# ─────────────────────────────────────────────────────────────
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
GROQ_API_KEY   = os.environ.get("GROQ_API_KEY", "")
 
if not TELEGRAM_TOKEN:
    raise RuntimeError("TELEGRAM_TOKEN topilmadi. Railway Variables ga o'rnating.")
if not GROQ_API_KEY:
    raise RuntimeError("GROQ_API_KEY topilmadi. Railway Variables ga o'rnating.")
 
 
# ─────────────────────────────────────────────────────────────
#  BOT VA GROQ CLIENT
# ─────────────────────────────────────────────────────────────
bot    = telebot.TeleBot(TELEGRAM_TOKEN)
client = Groq(api_key=GROQ_API_KEY)
 
 
# ─────────────────────────────────────────────────────────────
#  SOZLAMALAR  –  kerak bo'lsa o'zgartiring
# ─────────────────────────────────────────────────────────────
GROQ_MODEL  = "llama3-70b-8192"  # console.groq.com/docs dan boshqa model tanlashingiz mumkin
MAX_TOKENS  = 1024                # Bir javob uchun maksimal token
TEMPERATURE = 0.7                 # 0.0 = quruq/aniq,  1.0 = erkin/ijodiy
MAX_HISTORY = 20                  # Har user uchun xotirada nechta xabar saqlanadi
 
SYSTEM_PROMPT = (
    "Sen do'stona, aqlli va har tomonlama yordam bera oladigan AI assistantsan. "
    "Foydalanuvchi bilan doimo o'zbek tilida muloqot qil. "
    "Javoblarni qisqa va aniq yoz. "
    "Savol murakkab bo'lsa, bosqichma-bosqich tushuntir."
)
 
 
# ─────────────────────────────────────────────────────────────
#  SUHBAT TARIXI  –  har bir foydalanuvchi uchun alohida
# ─────────────────────────────────────────────────────────────
histories: dict[int, list[dict]] = {}
 
 
def add_message(user_id: int, role: str, content: str) -> None:
    """Xabarni tarixga qo'shadi. Limit oshsa eskisini o'chiradi."""
    if user_id not in histories:
        histories[user_id] = []
    histories[user_id].append({"role": role, "content": content})
    if len(histories[user_id]) > MAX_HISTORY:
        histories[user_id] = histories[user_id][-MAX_HISTORY:]
 
 
def get_ai_reply(user_id: int, user_text: str) -> str:
    """Groq API ga so'rov yuborib AI javobini qaytaradi."""
    add_message(user_id, "user", user_text)
 
    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            *histories[user_id],
        ],
        max_tokens=MAX_TOKENS,
        temperature=TEMPERATURE,
    )
 
    reply = response.choices[0].message.content.strip()
    add_message(user_id, "assistant", reply)
    return reply
 
 
def safe_reply(message: telebot.types.Message, text: str) -> None:
    """
    Xabarga reply yuboradi.
    Telegram 4096 belgidan uzun xabarlarni rad etadi,
    shu sababli kerak bo'lsa bo'lib yuboradi.
    """
    limit = 4096
    if len(text) <= limit:
        bot.reply_to(message, text)
        return
    bot.reply_to(message, text[:limit])
    for start in range(limit, len(text), limit):
        bot.send_message(message.chat.id, text[start : start + limit])
 
 
# ─────────────────────────────────────────────────────────────
#  KOMANDALAR  (faqat DM / private chat)
# ─────────────────────────────────────────────────────────────
@bot.message_handler(commands=["start"])
def cmd_start(message: telebot.types.Message) -> None:
    if message.chat.type != "private":
        return
    name = message.from_user.first_name or "Do'stim"
    bot.reply_to(message,
        f"Salom, {name}! 👋\n\n"
        "Men AI assistantman — istalgan savolingizga javob beraman.\n\n"
        "💬  Savolingizni yozing\n"
        "🧠  Suhbat tarixini eslab qolaman\n"
        "🔄  /reset — Suhbatni tozalash\n"
        "❓  /help  — Yordam"
    )
 
 
@bot.message_handler(commands=["help"])
def cmd_help(message: telebot.types.Message) -> None:
    if message.chat.type != "private":
        return
    bot.reply_to(message,
        "❓ Yordam:\n\n"
        "• Istalgan mavzuda savol bering — javob beraman\n"
        "• Oldingi suhbatimizni eslab qolaman\n"
        "• /reset — Suhbatni yangidan boshlash\n"
        "• /start — Bosh sahifa"
    )
 
 
@bot.message_handler(commands=["reset"])
def cmd_reset(message: telebot.types.Message) -> None:
    if message.chat.type != "private":
        return
    histories.pop(message.from_user.id, None)
    bot.reply_to(message, "✅ Suhbat tarixi tozalandi. Yangidan boshlang!")
 
 
# ─────────────────────────────────────────────────────────────
#  MATNLI XABARLAR  (faqat DM / private chat)
# ─────────────────────────────────────────────────────────────
@bot.message_handler(
    func=lambda m: m.chat.type == "private",
    content_types=["text"],
)
def handle_text(message: telebot.types.Message) -> None:
    text = (message.text or "").strip()
    if not text:
        return
 
    user_id = message.from_user.id
    bot.send_chat_action(message.chat.id, "typing")
 
    try:
        reply = get_ai_reply(user_id, text)
        safe_reply(message, reply)
        log.info("User %s  ✓", user_id)
    except Exception as exc:
        log.error("User %s  ✗  %s: %s", user_id, type(exc).__name__, exc)
        bot.reply_to(message,
            "❌ Xatolik yuz berdi. Biroz kutib, qayta urinib ko'ring."
        )
 
 
# ─────────────────────────────────────────────────────────────
#  RASM, VIDEO, OVOZ VA BOSHQA FAYLLAR  (faqat DM)
# ─────────────────────────────────────────────────────────────
@bot.message_handler(
    func=lambda m: m.chat.type == "private",
    content_types=["photo", "video", "audio", "voice", "document", "sticker", "animation"],
)
def handle_media(message: telebot.types.Message) -> None:
    bot.reply_to(message,
        "Hozircha faqat matnli xabarlarni tushunaman 📝\n"
        "Savolingizni yozib yuboring."
    )
 
 
# ─────────────────────────────────────────────────────────────
#  ISHGA TUSHIRISH
# ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    me = bot.get_me()
    log.info("Bot ishga tushdi!  @%s  (id: %s)", me.username, me.id)
    bot.infinity_polling(timeout=30, long_polling_timeout=30)
 
