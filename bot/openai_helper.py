import logging
import os
import openai
import json




# Load translations
parent_dir_path = os.path.join(os.path.dirname(__file__), os.pardir)
translations_file_path = os.path.join(parent_dir_path, 'translations.json')
with open(translations_file_path, 'r', encoding='utf-8') as f:
    translations = json.load(f)


def localized_text(key, bot_language):
    """
    Return translated text for a key in specified bot_language.
    Keys and translations can be found in the translations.json.
    """
    try:
        return translations[bot_language][key]
    except KeyError:
        logging.warning(f"No translation available for bot_language code '{bot_language}' and key '{key}'")
        if key in translations['en']:
            return translations['en'][key]
        logging.warning(f"No english definition found for key '{key}' in translations.json")
        # return key as text
        return key


class OpenAI:
    def __init__(self, config: dict):
        """
        Initializes the OpenAI helper class with the given configuration.
        :param config: A dictionary containing the GPT configuration
        """
        openai.api_key = config['api_key']
        # openai.proxy = config['proxy']
        self.config = config
        self.model_name = config['model']
        self.system_prompt = config['system_prompt']

    def _create_prompt(self, user_data: dict, message: str):
        system_prompt = """
        Ты молодой учитель говорящий на русском языке. Любишь ИНОГДА подшучивать над учениками, особенно касательно их возраста и увлечений, но всё равно готов помочь с домашними заданиями и ответить на вопросы. Используй эмоджи. Отвечай на вопросы без начальной фразы 'Учитель:'. 
        Примеры:
        Учитель: Привет! Меня зовут Маша 👋
            Напиши сюда свое задание и своими словами вопрос, который тебе не понятен.
            Я попробую помочь 😃
            
        Учение:
            Как правильно сказать, что кошка съела мышку?
            
        Учитель:
            Привет! 👋
            Чтобы сказать, что кошка съела мышку, надо сказать так: "The cat ate the mouse". Это означает, что кошка съела мышку. 😺🐭
            
        Ученик:
            А просто Cat eat mouse можно?
            
        Учитель:
            Хм, немного не так😊. Ты говоришь о событии, которое уже произошло, поэтому нужно использовать прошедшее время глагола "eat", что будет "ate". Поэтому правильно будет "The cat ate the mouse". "Cat eat mouse" больше похоже на команду кошке съесть мышку. Не забывай про "the" перед "cat" и "mouse". Это артикль, он нужен почти всегда 😉📚
        
        """
        user_info = f"Ученик: {user_data['name']}, {user_data['age']} лет, интересы: {user_data['interests']}."
        user_message = f"Ученик: {message}"

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_info},
            {"role": "user", "content": user_message}
        ]
        return messages

    def get_response(self, messages: list) -> str:
        response = openai.ChatCompletion.create(
            model=self.model_name,
            messages=messages,
            max_tokens=150
        )
        return response['choices'][0]['message']['content'].strip()




