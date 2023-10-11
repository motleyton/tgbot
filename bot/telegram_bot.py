from telegram import BotCommandScopeAllGroupChats, Update, constants, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, \
    filters, InlineQueryHandler, CallbackQueryHandler, Application, ContextTypes, CallbackContext, Updater
from utils import error_handler
from openai_helper import localized_text, OpenAI
from telegram import ReplyKeyboardMarkup


class ChatGPTTelegramBot:

    def __init__(self, config: dict, openai: OpenAI):
        self.config = config
        self.openai = openai

    async def start(self, update: Update, context: CallbackContext) -> None:
        context.user_data['state'] = 'waiting_for_name'
        await update.message.reply_text("Пожалуйста, ответьте на вопросы.\nКак Вас зовут?")


    async def help(self, update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Shows the help menu.
        """
        user_id = update.message.from_user.id

        bot_language = self.config['bot_language']
        help_text = (
                localized_text('help_text', bot_language)[0] +
                '\n\n' +
                f"Personal ID: {user_id}"
        )
        await update.message.reply_text(help_text, disable_web_page_preview=True)

    async def message_handler(self, update: Update, context: CallbackContext) -> None:
        state = context.user_data.get('state', 'start')

        # Инициализация истории сообщений
        if 'messages' not in context.user_data:
            context.user_data['messages'] = []

        # Добавление сообщения пользователя в историю
        user_message_content = f"Ученик: {update.message.text}"
        context.user_data['messages'].append({"role": "user", "content": user_message_content})

        if state == 'waiting_for_name':
            context.user_data['name'] = update.message.text
            await update.message.reply_text("Сколько Вам лет?")
            context.user_data['state'] = 'waiting_for_age'

        elif state == 'waiting_for_age':
            context.user_data['age'] = update.message.text
            await update.message.reply_text(f"Отлично. Есть ли у тебя какие-то увлечения?")
            context.user_data['state'] = 'waiting_for_interests'

        elif state == 'waiting_for_interests':
            context.user_data['interests'] = update.message.text
            await update.message.reply_text(f"Привет! Меня зовут Маша 👋 \nНапиши сюда свое задание и своими словами вопрос, который тебе не понятен. \nЯ попробую помочь 😃")
            context.user_data['state'] = 'chatting'

        elif state == 'chatting':

            response = self.openai.get_response(context.user_data['messages'])

            # Добавление ответа учителя в историю

            context.user_data['messages'].append({"role": "assistant", "content": response})

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
