import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ASK_BUDGET, ASK_PARTICIPANTS = range(2)
games = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    games[chat_id] = {"budget": None, "participants": []}
    await update.message.reply_text("Введите сумму подарка (например: 3000):")
    return ASK_BUDGET

async def set_budget(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    try:
        budget = int(update.message.text.strip())
    except:
        await update.message.reply_text("Введите число, например 3000:")
        return ASK_BUDGET

    games[chat_id]["budget"] = budget
    await update.message.reply_text(
        "Теперь отправьте список участников через @, по одному в сообщении.\n"
        "Когда закончите — напишите: ГОТОВО"
    )
    return ASK_PARTICIPANTS

async def collect_participants(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    text = update.message.text.strip()

    if text.upper() == "ГОТОВО":
        participants = games[chat_id]["participants"]
        if len(participants) < 2:
            await update.message.reply_text("Нужно минимум 2 участника.")
            return ASK_PARTICIPANTS
        await assign_and_send(update, context)
        return ConversationHandler.END

    if not text.startswith("@"):
        await update.message.reply_text("Отправляйте никнеймы начинающиеся с @")
        return ASK_PARTICIPANTS

    games[chat_id]["participants"].append(text)
    await update.message.reply_text(f"Добавлен: {text}")
    return ASK_PARTICIPANTS

async def assign_and_send(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    game = games[chat_id]
    people = game["participants"][:]

    import random
    random.shuffle(people)
    assigned = people[1:] + people[:1]

    for giver, receiver in zip(people, assigned):
        try:
            await context.bot.send_message(
                chat_id=giver,
                text=f"Твой получатель: {receiver}\nБюджет подарка: {game['budget']}₽"
            )
        except:
            pass

    await update.message.reply_text("Рассылка завершена! Тайный Санта создан.")

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Отменено.")
    return ConversationHandler.END

def main():
    import os
    token = os.getenv("BOT_TOKEN")
    app = ApplicationBuilder().token(token).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            ASK_BUDGET: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_budget)],
            ASK_PARTICIPANTS: [MessageHandler(filters.TEXT & ~filters.COMMAND, collect_participants)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv)
    app.run_polling()

if __name__ == "__main__":
    main()
