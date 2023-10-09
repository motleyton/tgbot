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
        await update.message.reply_text("Привет! Как тебя зовут?")

    async def send_menu(self, update: Update, context: CallbackContext) -> None:
        keyboard = [
            ["/start", "/help"],
        ]

        markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text("Выберите команду:", reply_markup=markup)

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
        state = context.user_data.get('state', '')

        if state == 'waiting_for_name':
            context.user_data['name'] = update.message.text
            await update.message.reply_text(f"Привет, {context.user_data['name']}! Сколько тебе лет?")
            context.user_data['state'] = 'waiting_for_age'

        elif state == 'waiting_for_age':
            context.user_data['age'] = update.message.text
            await update.message.reply_text(f"Отлично, {context.user_data['name']}! Есть ли у тебя какие-то увлечения?")
            context.user_data['state'] = 'waiting_for_interests'

        elif state == 'waiting_for_interests':
            context.user_data['interests'] = update.message.text
            await update.message.reply_text(f"Здорово! Я запомнил. Теперь можем общаться.")
            context.user_data['state'] = 'chatting'

        elif state == 'chatting':
            response = self.openai.get_response(context.user_data, update.message.text)
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

        application.add_handler(CommandHandler('start', self.send_menu))
        application.add_handler(CommandHandler('help', self.help))
        application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), self.message_handler))
        application.add_error_handler(error_handler)

        application.run_polling()
