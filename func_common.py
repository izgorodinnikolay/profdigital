from datetime import *
import html
import os
import requests
import sqlglot
import sys
import traceback
from functools import wraps
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlglot import exp
from zoneinfo import ZoneInfo


load_dotenv('variables.env')

BOT_TOKEN = os.getenv("BOT_TOKEN")
BOT_CHAT_ID = os.getenv("BOT_CHAT_ID")
BOT_CHAT_ID_3 = os.getenv("BOT_CHAT_ID_3")
CHAT_3_TOPIC_ALARM = os.getenv("CHAT_3_TOPIC_ALARM")
PROXY = os.getenv("PROXY")


def log_errors(func):
    """Декоратор-обертка для автоматического логирования любых ошибок функции."""

    # wraps сохраняет имя исходной функции и её документацию
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            # Выполняем оригинальную функцию
            return func(*args, **kwargs)
        except Exception as e:
            # 1. Формируем трейсбэк
            error_traceback = traceback.format_exc()

            # 2. Логируем в файл по МСК
            moscow_now = datetime.now(ZoneInfo("Europe/Moscow")).strftime("%Y-%m-%d %H:%M:%S")
            file_msg = f"[{moscow_now}] КРИТИЧЕСКАЯ ОШИБКА в функции '{func.__name__}':\n{error_traceback}"

            with open('script_errors.log', 'a', encoding='utf-8') as log_file:
                log_file.write(file_msg + "\n" + "=" * 80 + "\n")

            # 3. Отправляем в Telegram
            safe_error = html.escape(f"{type(e).__name__}: {str(e)}")
            tg_msg = (
                f"🚨 <b>Упала функция:</b> <code>{func.__name__}</code>\n\n"
                f"<b>Ошибка:</b> <pre>{safe_error}</pre>\n"
                f"Детали сохранены в файл логов."
            )
            send_telegram_message(chat_id=BOT_CHAT_ID_3, message=tg_msg, topic_id=CHAT_3_TOPIC_ALARM)

            # Прерываем скрипт
            sys.exit(1)

    return wrapper

def read_sql_script(file_name:str) -> str:
    with open(file_name, 'r', encoding='utf-8') as file:
        query = file.read()
    return query

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

def float_rus_format(num: str) -> str:
    return (f"{num:_.0f}").replace("_", " ")


def send_telegram_message(token: str = BOT_TOKEN,
                          chat_id: str = BOT_CHAT_ID,
                          message: str = 'Процесс обновления счетов упал',
                          topic_id: int = None,  # Добавили ID топика (message_thread_id)
                          proxy_url: str = PROXY  # Добавили аргумент для прокси
                          ) -> None:
    """Отправляет сообщение в Telegram через прокси с безопасным HTML-форматированием."""
    response = None
    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"

        # Экранируем спецсимволы (<, >, &), чтобы Telegram не выдавал ошибку Bad Request
        # safe_message = html.escape(message)

        payload = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "HTML",
        }

        # Если передан ID топика, перенаправляем сообщение туда
        if topic_id:
            payload["message_thread_id"] = topic_id

        proxies = {"http": proxy_url, "https": proxy_url} if proxy_url else None

        response = requests.post(url, json=payload, timeout=10, proxies=proxies)
        response.raise_for_status()

    except Exception as e:
        if response is not None:
            print(f"❌ Ошибка Telegram API (Status {response.status_code}): {response.text}")
        else:
            print(f"❌ Сетевая ошибка (возможно, прокси недоступен): {e}")
        raise e

def get_document_structure(document: str) -> dict:
    config_vars = {}

    with open(f'{document}.txt', 'r', encoding='utf-8') as file:
        config_code = file.read()

    exec(config_code, {}, config_vars)

    return config_vars


def get_table_name(sql_query: str):
    tables = set()

    parsed = sqlglot.parse_one(sql_query, read="mysql")

    for table in parsed.find_all(exp.Table):
        if table.name not in parsed.ctes:
            if table.db:
                tables.add(f"{table.db}.{table.name}")

    return tables