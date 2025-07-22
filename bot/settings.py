from dotenv import load_dotenv
import os
import logging

load_dotenv()


def get_token():
    token = os.getenv("BOT")
    aitoken = os.getenv("AI")
    return token, aitoken


def get_connection():
    host = os.getenv("DB_HOST")
    database = os.getenv("DB_NAME")
    user = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD")
    port = 5432
    return host, database, user, password, port


def get_db_url():
    host, database, user, password, port = get_connection()
    return f"postgresql://{user}:{password}@{host}:{port}/{database}"


async def setup_logger():
    logger = logging.getLogger(__name__)
    logging.basicConfig(filename="log.log", level=logging.INFO)
    return logger
