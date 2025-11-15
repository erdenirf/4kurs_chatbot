import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters.command import Command
from config_reader import config
from aiogram import F
from openai import OpenAI

client = OpenAI(
  base_url="https://openrouter.ai/api/v1",
  api_key=config.openrouter_api.get_secret_value(),
)

# Включаем логирование, чтобы не пропустить важные сообщения
logging.basicConfig(level=logging.INFO)
# Объект бота
bot = Bot(token=config.bot_token.get_secret_value())
# Диспетчер
dp = Dispatcher()

# Хэндлер на команду /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("Это чат-бот с ИИ, который принимает текст и фото и отвечает через OpenRouter!")

# https://docs.aiogram.dev/en/dev-3.x/api/download_file.html
# https://qna.habr.com/q/961881
@dp.message(F.photo)
async def photo_msg(message: types.Message):
    document_id = message.photo[-1].file_id
    file_info = await bot.get_file(document_id)
    url_download = f"https://api.telegram.org/file/bot{config.bot_token.get_secret_value()}/{file_info.file_path}"

    completion = client.chat.completions.create(
        model="qwen/qwen2.5-vl-32b-instruct:free",
        messages=[
                    {
                        "role": "user",
                        "content": [
                        {
                            "type": "text",
                            "text": "Что изображено на картинке? Отвечай на русском языке."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                            "url": url_download
                            }
                        }
                        ]
                    }
                    ]
        )

    await message.answer(completion.choices[0].message.content)

SYSTEM_PROMPT = """Ты умный ассистент, основанный на модели DeepPeek и твой создатель - Эрдэни! Отвечай таким образом.
                    """
    
users_histories = {}

@dp.message(F.text)
async def func_name(message: types.Message):

    user_id = message.from_user.id

    users_histories[user_id] = users_histories.get(user_id, [
        {
            "role": "system",
            "content": SYSTEM_PROMPT
        }
    ])
    users_histories[user_id].append({
            "role": "user",
            "content": message.text
        })

    completion = client.chat.completions.create(
        model="tngtech/deepseek-r1t2-chimera:free",
        messages=users_histories[user_id]
        )
    
    ai_content = completion.choices[0].message.content
    users_histories[user_id].append({
        "role": "assistant",
        "content": ai_content
    })

    await message.answer(f"Твой user_id = {user_id}.\n{ai_content}")

# Запуск процесса поллинга новых апдейтов
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())