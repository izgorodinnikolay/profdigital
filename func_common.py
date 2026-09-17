import os
import requests
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine


load_dotenv(r'C:\Users\user\Desktop\Maks\projects\invoices_2026_07_26\variables.env')

BOT_TOKEN = os.getenv("BOT_TOKEN")
BOT_CHAT_ID = os.getenv("BOT_CHAT_ID")


def send_telegram_message(token: str = BOT_TOKEN, chat_id: str = BOT_CHAT_ID,
                          message: str = 'Процесс обновления счетов упал') -> None:
    """Отправляет сообщение в Telegram. Возвращает True при успехе."""

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown",
    }

    response = requests.post(url, json=payload, timeout=10)
    response.raise_for_status()


def build_engine(
    db_user: str,
    db_password: str,
    db_host: str,
    db_port: int,
    db_dbname: str,
    read_timeout: int=300,
    write_timeout: int=300,
    connect_timeout: int=300
) -> Engine:
    """Создаёт engine SQLAlchemy с таймаутами и проверкой соединения."""
    return create_engine(
        f"mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_dbname}",
        pool_pre_ping=True,
        pool_recycle=3600,
        connect_args={
            "read_timeout": read_timeout,
            "write_timeout": write_timeout,
            "connect_timeout": connect_timeout,
            "charset": "utf8mb4",
        },
    )
