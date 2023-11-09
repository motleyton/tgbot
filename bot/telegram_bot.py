import datetime

from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, \
    filters, ContextTypes, CallbackContext

from database_helper import Database
from utils import error_handler
from openai_helper import localized_text, OpenAI

class ChatGPTTelegramBot:

    def __init__(self, config: dict, openai: OpenAI):
        self.config = config
        self.openai = openai
        self.allowed_usernames = config['allowed_usernames']
        self.max_requests_per_day = config['max_requests_per_day']
        self.db = Database("users_data.db")


    async def start(self, update: Update, context: CallbackContext) -> None:
        user_id = update.message.from_user.id
        bot_language = self.config['bot_language']
        username = "@" + update.message.from_user.username if update.message.from_user.username else None
        disallowed = (
            localized_text('disallowed', bot_language))
        if username not in self.allowed_usernames:
            await update.message.reply_text(disallowed, disable_web_page_preview=True)
            return

        start_keyboard = [['/start', '/help']]
        reply_markup = ReplyKeyboardMarkup(start_keyboard, one_time_keyboard=True, resize_keyboard=True)

        # Отправка сообщения с клавиатурой
        # await update.message.reply_text('Выберите команду:', reply_markup=reply_markup)

        user_data = self.db.get_user(user_id)
        if user_data:
            context.user_data[
                'state'] = 'chatting'  # Устанавливаем состояние 'chatting' для зарегистрированных пользователей
            await update.message.reply_text(f"Привет, {user_data['name']}! 👋. Что ты хочешь спросить у Мии?", reply_markup=reply_markup)
            return
        # Если пользователь не найден в базе данных, начинаем процесс регистрации
        context.user_data['state'] = 'waiting_for_name'
        await update.message.reply_text("Пожалуйста, ответь на вопросы.\nКак тебя зовут?", reply_markup=reply_markup)


    async def help(self, update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
        user_id = update.message.from_user.id
        username = "@" + update.message.from_user.username if update.message.from_user.username else None
        bot_language = self.config['bot_language']
        disallowed = (
            localized_text('disallowed', bot_language))
        if username not in self.allowed_usernames:
            await update.message.reply_text(disallowed, disable_web_page_preview=True)
            return

        help_text = (
            localized_text('help_text', bot_language)[0]
        )
        await update.message.reply_text(help_text, disable_web_page_preview=True)

    async def message_handler(self, update: Update, context: CallbackContext) -> None:
        user_id = update.message.from_user.id

        if self.db.get_message_count_today(user_id) >= self.max_requests_per_day:
            await update.message.reply_text("Достигнут лимит запросов. Приходи завтра.")
            return

        state = context.user_data.get('state', 'start')

        # Запись сообщения пользователя
        self.db.add_message(user_id, 'user', update.message.text)

        # Инициализация истории сообщений
        if 'messages' not in context.user_data:
            context.user_data['messages'] = self.db.get_message_history(user_id)


        # Добавление сообщения пользователя в историю
        user_message_content = f"Ученик: {update.message.text}"
        context.user_data['messages'].append({"role": "user", "content": user_message_content})

        if state == 'waiting_for_name':
            context.user_data['name'] = update.message.text
            self.db.add_or_update_user(user_id, name=update.message.text)
            await update.message.reply_text("Сколько тебе лет?")
            context.user_data['state'] = 'waiting_for_age'

        elif state == 'waiting_for_age':
            context.user_data['age'] = update.message.text
            self.db.add_or_update_user(user_id, age=update.message.text)
            await update.message.reply_text(
                f"Привет! Меня зовут Мия 👋 \nНапиши сюда свое задание и своими словами вопрос, который тебе не понятен. \nЯ попробую помочь 😃")
            context.user_data['state'] = 'chatting'


        elif state == 'chatting':

            user_id = update.message.from_user.id
            user_data = self.db.get_user(user_id)
            response = self.openai.get_response(user_data, update.message.text)

            # Добавление ответа учителя в историю
            context.user_data['messages'].append({"role": "assistant", "content": response})

            # Запись ответа бота в базу данных
            self.db.add_message(user_id, 'assistant', response)

            await update.message.reply_text(response)

    def run(self):
        """
        Runs the bot indefinitely until the user presses Ctrl+C
        """

        application = ApplicationBuilder() \
            .token(self.config['token']) \
            .proxy_url(self.config['proxy']) \
            .get_updates_proxy_url(self.config['proxy']) \
            .concurrent_updates(True) \
            .build()

        application.add_handler(CommandHandler('start', self.start))
        application.add_handler(CommandHandler('help', self.help))
        application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), self.message_handler))
        application.add_error_handler(error_handler)

        application.run_polling()