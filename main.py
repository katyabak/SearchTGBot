import sqlite3
from telegram import Bot, Update
from telegram.ext import Application, Updater, CommandHandler, MessageHandler, filters, ConversationHandler, CallbackContext
import logging

# Чтение токена бота из файла конфигурации
with open('config.txt', 'r') as f:
    TOKEN = f.read().strip()

# Инициализация логгера
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# создание updater
updater = Application.builder().token(TOKEN).build()

# Состояния диалога
COUNTRY, PO, MODE, IZMGOL, RESULTS = range(5)

# подключение к базе данных
conn = sqlite3.connect('equipment.db')
cursor = conn.cursor()

# объявление команд
async def start(update: Update, context: CallbackContext) -> int:
    logger.info("Пользователь %s начал диалог.", update.effective_user.first_name)
    await update.message.reply_text("Привет! Я бот для поиска оборудования.\nВыберите страну изготовления:\nИндия, Германия")
    return COUNTRY

async def get_country(update: Update, context: CallbackContext) -> int:
    context.user_data['country'] = update.message.text
    await update.message.reply_text("Введите ПО:\nArcoCAD\nCALYPSO")
    return PO

async def get_po(update: Update, context: CallbackContext) -> int:
    context.user_data['PO'] = update.message.text
    await update.message.reply_text("Введите мод:\nРучной\nРучной и авто")
    return MODE

async def get_mode(update: Update, context: CallbackContext) -> int:
    context.user_data['mode'] = update.message.text
    await update.message.reply_text("Введите тип измерительной головки:\nAccuLaser, PH6M, PH10 (M/MQ), PH10(M/MQ/T), PH20, REVO-2, SP80, VAST XT Gold, VAST XTR Gold, VAST XXT, RDS, TP (20/200), ZEISS Discovery.V12")
    return IZMGOL

async def get_izmgol(update: Update, context: CallbackContext) -> int:
    context.user_data['IzmGol'] = update.message.text

    # Создание SQL-запроса
    query = "SELECT * FROM tablica WHERE country = ? AND PO = ? AND mode = ? AND IzmGol = ?"
    params = (
        context.user_data['country'],
        context.user_data['PO'],
        context.user_data['mode'],
        context.user_data['IzmGol']
    )

    # Выполнение запроса
    cursor.execute(query, params)
    results = cursor.fetchall()

    if results:
        response = "Результаты поиска по вашим запросам:\n"
        for index, row in enumerate(results, start=1):
            response += f"{index}. Название оборудования: {row[1]}, Страна: {row[2]}, ПО: {row[3]}, Мод: {row[4]}, Изм. головка: {row[5]}\n"
            if index >= 10:  # Ограничение на вывод первых 5 записей
                break
    else:
        response = "К сожалению, ничего не найдено."

    await update.message.reply_text(response)
    return ConversationHandler.END

async def cancel(update: Update, context: CallbackContext) -> int:
    await update.message.reply_text("Поиск отменен.")
    return ConversationHandler.END
def go():
    # Add conversation handler
    conversation_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            COUNTRY: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_country)],
            PO: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_po)],
            MODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_mode)],
            IZMGOL: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_izmgol)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    updater.add_handler(conversation_handler)
    updater.run_polling()
    updater.idle()
if __name__ == '__main__':
    go()