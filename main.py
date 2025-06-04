import asyncio
import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.tl.types import InputPeerUser
from telethon.errors import SessionPasswordNeededError

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
logging.getLogger("telethon").setLevel(logging.WARNING)

load_dotenv(".env")

# Конфигурация (замените значения на свои!)
text = Path('text.txt').read_text(encoding='utf-8')

phone = os.getenv("PHONE")  # Номер телефона, привязанный к аккаунту
channel = os.getenv("CHANNEL")  # Например: "@telegram" или "t.me/telegram"

#  Подключение клиента: https://my.telegram.org/auth
client = TelegramClient(
        session=os.getenv("SESSION"),  # Название сессии
        api_id=int(os.getenv("API_ID")),  # https://my.telegram.org/apps
        api_hash=os.getenv("API_HASH"),  # https://my.telegram.org/apps
        system_version="4.16.30-vxCUSTOM",
        device_model=os.getenv("DEVICE_MODEL")  # Например: Desktop
)


async def main():
    logger.info(f"Подключение к сессии... ({phone})")
    await client.connect()

    if not await client.is_user_authorized():
        try:
            await client.send_code_request(phone)
            code = input('Введите код из Telegram: ')
            await client.sign_in(phone, code)
        except SessionPasswordNeededError:
            password = input('Введите пароль 2FA: ')
            await client.sign_in(password=password)

    print("✅ Успешная авторизация! Сессия сохранена.")

    logger.info("Запуск функции...")
    await asyncio.gather(scrape_user_ids())


async def scrape_user_ids():
    logger.info("Получение сущности канала...")

    try:
        entity = await client.get_entity(channel)
    except Exception as e:
        logger.error(f"Ошибка: {e}. Проверьте название канала и права доступа.")
        return

    users = {}

    async for message in client.iter_messages(entity, limit=int(os.getenv("PARSING_LIMIT"))):  # limit=сколько сообщений парсить
        sender = message.sender

        if sender:
            user_id = sender.id
            username = getattr(sender, 'username', None)
            access_hash = sender.access_hash

            logger.debug(f"Пользователь: (id={user_id}, username={username})")

            users[user_id] = [username, access_hash]

    with open('users.txt', 'w', encoding='utf-8') as f:
        for user_id, value in users.items():
            user = InputPeerUser(user_id, value[1])
            f.write(f"{user_id} - @{value[0]}\n")

            await client.send_message(user, text)
            await asyncio.sleep(1)

    logger.info(f"✅ Готово! Найдено {len(users)} уникальных ID. Сохранено в users.txt")


client.loop.run_until_complete(main())
