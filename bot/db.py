from bot.settings import get_connection
import sqlalchemy
engine = None

async def db_engine():
    global engine
    if engine is None:
        host, database, user, password, port = get_connection()
        engine = sqlalchemy.create_engine(f"postgresql://{user}:{password}@{host}:{port}/{database}")
    return engine

async def db_cursor():
    global engine
    if engine is None:
        engine = await db_engine()
    return engine.connect()