import os
import logging
import traceback
from zoneinfo import ZoneInfo
import random
from datetime import date, datetime

from telegram import (
    Update,
    BotCommandScopeChat,
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    Defaults,
)
from telegram.helpers import escape_markdown

from data import TOKEN, MY_ID
from quotes import famous_quotes


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_some_wisdom(update)


async def command_put_on(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != MY_ID:
        await send_some_wisdom(update)

    dates = get_history()
    today = date.today()
    if dates and dates[-1] == today:
        await update.message.reply_text('За сегодня уже отметил 😉')
        return

    dates.append(today)
    save_history(dates)
    day = len(dates)
    emoji = random.choice(['👌', '🤝', '👍', '🙌', '✍'])
    msg = f'Отметил {emoji}\nЭти линзы ты надеваешь в {pick_up_ending(day)} раз'
    if day >= 14:
        msg += '\n\nПора взять новую пару!'
    await update.message.reply_text(msg)


async def command_throw_away(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != MY_ID:
        await send_some_wisdom(update)

    clear_history()
    await context.bot.send_sticker(MY_ID, sticker='CAACAgIAAxkBAAEBlDhowNvrL5A48qSJg0BAKuRWyqI7_QADYAACuZ05SwqrqNicUdj4NgQ')


async def command_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != MY_ID:
        await send_some_wisdom(update)

    global COMMANDS_SET
    if not COMMANDS_SET:
        COMMANDS_SET = True
        await context.bot.set_my_commands(commands=bot_commands, scope=BotCommandScopeChat(MY_ID))
        await update.message.reply_text('👌')
        return

    dates = get_history()
    if not dates:
        await update.message.reply_text('История пуста 😢')
        return

    msg = f'Всего ты надевал данные линзы *{pick_up_ending_2(len(dates))}*:\n'
    for no, d in enumerate(dates, start=1):
        msg += f'\n{no}) {d:%d.%m.%Y}'
    await update.message.reply_text(msg, parse_mode='markdown')


def get_history() -> list[date]:
    with open(HISTORY_FILE, encoding='utf-8') as file:
        dates_str = list(filter(lambda line: line.strip(), file.readlines()))
        dates = list(map(lambda line: datetime.strptime(line.strip(), '%d.%m.%Y').date(), dates_str))
    return dates

def save_history(dates: list[date]) -> None:
    with open(HISTORY_FILE, 'w', encoding='utf-8') as file:
        for d in dates:
            file.write(d.strftime('%d.%m.%Y') + '\n')

def clear_history() -> None:
    file_stats = os.stat(HISTORY_FILE)
    if file_stats.st_size == 0:  # Файл уже очищен
        return
    if not os.path.exists(HISTORY_FILE_OLD):
        open(HISTORY_FILE_OLD, 'w').close()
    with open(HISTORY_FILE, 'r', encoding='utf-8') as src_file, open(HISTORY_FILE_OLD, 'w', encoding='utf-8') as dest_file:
        dest_file.writelines(src_file.readlines())
    open(HISTORY_FILE, 'w').close()


def pick_up_ending(n: int) -> str:
    if 11 <= n % 100 <= 19 or n % 10 in [0, 1, 4, 5, 9]:
        return f'{n}-ый'
    elif n % 10 == 3:
        return f'{n}-ий'
    else:
        return f'{n}-ой'

def pick_up_ending_2(n: int) -> str:
    if n % 10 in [2, 3, 4] and n % 100 not in [12, 13, 14]:
        return f'{n} раза'
    else:
        return f'{n} раз'


async def send_some_wisdom(update: Update):
    msg = escape_markdown(random.choice(famous_quotes), version=1).replace('«', '_').replace('».', '_\n©')
    await update.message.reply_text(msg, parse_mode='markdown')


async def handle_error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f'{context.error}\n{traceback.format_exc()}')


def run_bot():
    print('Starting bot...')
    defaults = Defaults(tzinfo=ZoneInfo('Europe/Moscow'))
    app = Application.builder().token(TOKEN).defaults(defaults).build()

    # Commands
    app.add_handler(CommandHandler('put_on', command_put_on))
    app.add_handler(CommandHandler('throw_away', command_throw_away))
    app.add_handler(CommandHandler('info', command_info))

    # Errors
    app.add_error_handler(handle_error)

    # Messages
    app.add_handler(MessageHandler(filters.TEXT, handle_message))

    # Pools the bot
    print('Polling...')
    app.run_polling(poll_interval=1)


if __name__ == '__main__':
    # Настройка логов
    logging.basicConfig(
        format='%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
        filename='info.log',
        filemode='w',
        level=logging.INFO
    )
    logger = logging.getLogger('httpx')
    logger.setLevel(logging.WARNING)

    COMMANDS_SET = False
    HISTORY_FILE = 'history.txt'
    HISTORY_FILE_OLD = 'history_old.txt'
    if not os.path.exists(HISTORY_FILE):
        open(HISTORY_FILE, 'w').close()

    bot_commands = [
        ('put_on', 'Надел линзы'),
        ('throw_away', 'Выкинул линзы'),
        ('info', 'История'),
    ]
    run_bot()
