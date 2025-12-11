import os
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

games = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    admin_id = update.effective_user.id

    games[chat_id] = {
        "admin": admin_id,
        "participants": [],
        "gift_sum": None,
        "state": "waiting_sum"
    }

    await update.message.reply_text(
        "🧝 Привет! Введи сумму подарка (например 3000):"
    )

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    text = update.message.text

    if chat_id not in games:
        return

    game = games[chat_id]

    # Ждём сумму подарка
    if game["state"] == "waiting_sum":
        if user_id != game["admin"]:
            await update.message.reply_text("Только админ может задать сумму.")
            return

        if not text.isdigit():
            await update.message.reply_text("Введи число, например 3000.")
            return

        game["gift_sum"] = int(text)
        game["state"] = "collecting"

        await update.message.reply_text(
            f"Сумма установлена: {game['gift_sum']} ₽\n\n"
            "Теперь пусть участники пишут что-нибудь в чат для регистрации."
        )
        return

    # Сбор участников
    if game["state"] == "collecting":
        if user_id not in game["participants"]:
            game["participants"].append(user_id)
            await update.message.reply_text("Участник добавлен!")

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    if chat_id not in games:
        return

    game = games[chat_id]

    if user_id != game["admin"]:
        await update.message.reply_text("Только админ завершает игру.")
        return

    parts = game["participants"]

    if len(parts) < 2:
        await update.message.reply_text("Недостаточно участников.")
        return

    import random
    random.shuffle(parts)

    for i in range(len(parts)):
        giver = parts[i]
        receiver = parts[(i + 1) % len(parts)]

        try:
            await context.bot.send_message(
                chat_id=giver,
                text=f"🎁 Ты даришь подарок участнику с ID {receiver}\n"
                     f"Сумма подарка: {game['gift_sum']} ₽"
            )
        except:
            pass

    await update.message.reply_text("Игра завершена! Каждому отправлены личные сообщения.")
    del games[chat_id]


def main():
    token = os.getenv("BOT_TOKEN")

    app = ApplicationBuilder().token(token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stop", stop))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

    app.run_polling()


if __name__ == "__main__":
    main()
