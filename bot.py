import asyncio
import os
import re

from dotenv import load_dotenv
from datetime import datetime

from city import city

load_dotenv('.env')

API_KEY = os.getenv('API_KEY')
OWNER_ID = os.getenv('OWNER_ID')
OWNER_ID = int(OWNER_ID)

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters
)

from main import afk_search

START, DATE, OT, TO, TIME, CD = range(6)

std_params = [['00:00', '24:00'], "Минск", "Слуцк", "2024-12-20", "30"]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    if update.effective_user.id == OWNER_ID:
        await update.message.reply_text('Дата, формат: yy-mm-dd')
        return DATE
    else:
        await update.message.reply_text('Неверный ID пользователя, доступ открыт только для администатора')


async def edate(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(update.message.text)
    date = re.findall(r'\d+', update.message.text)
    date = [int(d) for d in date]
    year = datetime.today().date().year
    month = datetime.today().date().month

    if len(date) == 1 and 31 >= date[0] > 0:
        std_params[3] = f'{year}-{month}-{date[0]}'
    elif len(date) == 2 and 31 >= date[1] > 0 and 12 >= date[0] > 0:
        std_params[3] = f'{year}-{date[0]}-{date[1]}'
    elif len(date) == 3 and 31 >= date[2] > 0 and 12 >= date[1] > 0 and date[0] == year or date[0] == year + 1:
        std_params[3] = f'25{date[0]}-{date[1]}-{date[2]}'
    else:
        await update.message.reply_text('Неверный ввод поля date')
        return DATE

    await update.message.reply_text('Откуда, пример: \"Минск\"')
    return OT


async def ot (update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(update.message.text)
    if update.message.text.lower() in city:
        std_params[1] = update.message.text.title()
    else:
        await update.message.reply_text('Неверный ввод поля from')
        return OT

    await update.message.reply_text('Куда, пример: \"Слуцк\"')
    return TO


async def to(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(update.message.text)
    if update.message.text.lower() in city:
        std_params[2] = update.message.text.title()
    else:
        return TO

    await update.message.reply_text('Время, формат: HH:MM')
    return TIME


async def time(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(update.message.text)
    date = re.findall(r'\b\d{2}:\d{2}\b', update.message.text)

    if len(date) == 0:
        std_params[0] = ['00:00', '24:00']
    elif len(date) == 1:
        atlas_time = date[0].split(':')
        if 23 >= int(atlas_time[0]) >= 0:
            std_params[0] = [f'{atlas_time[0]}:{atlas_time[1]}', '24:00']
        else:
            await update.message.reply_text('Неверный ввод поля time')
            return TIME
    elif len(date) == 2:
        atlas_time = [date[0].split(':'), date[1].split(':')]
        if (
            23 >= int(atlas_time[0][0]) >= 0 and
            23 >= int(atlas_time[1][0]) >= 0
        ):
            std_params[0] = [
                f'{atlas_time[0][0]}:{atlas_time[0][1]}',
                f'{atlas_time[1][0]}:{atlas_time[1][1]}'
            ]
        else:
            await update.message.reply_text('Неверный ввод поля time')
            return TIME
    else:
        await update.message.reply_text('Неверный ввод поля time')
        return TIME

    await update.message.reply_text('Время запроса(сек), пример: "10"')
    return CD


async def cd (update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    for param in std_params:
        await update.message.reply_text(param)

    await update.message.reply_text(update.message.text)
    cooldown = re.findall(r'\d+', update.message.text)
    if 600 >= int(cooldown[0]) >= 10:
        std_params[4] = cooldown.group()
    else:
        await update.message.reply_text('Неверный ввод поля time')
        return CD

    await context.bot.send_message(chat_id=OWNER_ID, text="Ожидание подходящего транспорта")

    task = asyncio.create_task(afk_search(*std_params))
    bus_time = await task
    for r in bus_time:
        await context.bot.send_message(chat_id=OWNER_ID, text=r)


def main() -> None:
    application = Application.builder().token(API_KEY).build()

    register_from_heandler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            DATE: [MessageHandler(filters.TEXT, edate)],
            OT: [MessageHandler(filters.TEXT, ot)],
            TO: [MessageHandler(filters.TEXT, to)],
            TIME: [MessageHandler(filters.TEXT, time)],
            CD: [MessageHandler(filters.TEXT, cd)],
        },
        fallbacks=[CommandHandler("cancel", start)]
    )

    application.add_handler(register_from_heandler)

    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()