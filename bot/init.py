from bot.db import db_engine, db_cursor
from sqlalchemy import (
    Table,
    Column,
    Integer,
    Text,
    MetaData,
    VARCHAR,
    TIMESTAMP,
    ARRAY,
    insert,
)
import json
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    metadata = MetaData()


# Define tables with proper metadata registration
questions_table = Table(
    "questions",
    Base.metadata,
    Column("question", Text),
    Column("options", ARRAY(Text)),
    Column("answer", Text),
)

stats_table = Table(
    "stats",
    Base.metadata,
    Column("name", VARCHAR(35), primary_key=False),
    Column("correctcount", Integer),
    Column("result", Text),
    Column("creationdate", TIMESTAMP),
)

users_table = Table(
    "users",
    Base.metadata,
    Column("name", VARCHAR(35), primary_key=True),
    Column("chat_id", Integer),
    Column("usertype", Text),
    Column("creationdate", TIMESTAMP),
)

admin_table = Table("admin", Base.metadata, Column("name", VARCHAR(35)))


async def setup_db():
    engine = await db_engine()
    conn = await db_cursor()

    if not engine.dialect.has_table(conn, "questions"):
        Base.metadata.create_all(engine)
        questions = json.load(open("whocanbeamillionairetho.json"))
        for i in questions:
            cmt = insert(questions_table).values(
                question=i["question"], options=i["options"], answer=i["answer"]
            )
            conn.execute(cmt)
        conn.commit()
