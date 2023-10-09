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
        system_prompt = self.system_prompt
        user_info = f"Ученик: {user_data['name']}, {user_data['age']} лет, интересы: {user_data['interests']}."
        user_message = f"Ученик: {message}"

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_info},
            {"role": "user", "content": user_message}
        ]
        return messages

    def get_response(self, user_data: dict, message: str) -> str:
        name = user_data.get('name', 'Пользователь')
        age = user_data.get('age', 'неизвестный возраст')
        interests = user_data.get('interests', 'неизвестные интересы')

        response = openai.ChatCompletion.create(
            model=self.model_name,
            messages=self._create_prompt(user_data, message),
            max_tokens=150
        )

        return response['choices'][0]['message']['content'].strip()




