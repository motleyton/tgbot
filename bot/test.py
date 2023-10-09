from langchain.chat_models import ChatOpenAI
from langchain.schema import (
    SystemMessage,
    HumanMessage,
    AIMessage
)

# chat = ChatOpenAI(
#     openai_api_key='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',
#     temperature=0,
#     model='gpt-4')
#
# # setup first system message
# messages = [
#     SystemMessage(
#         content="You are a helpful assistant that translates English to French."
#     ),
#     HumanMessage(
#         content="Translate this sentence from English to French. I love programming."
#     ),
# ]
# print(chat(messages))
print(config)
openai.api_key = config['api_key']