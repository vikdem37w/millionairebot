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
    select,
)
import json
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    metadata = MetaData()

questionstable = Table(
    "questions",
    Base.metadata,
    Column("question", Text),
    Column("options", ARRAY(Text)),
    Column("answer", Text),
)

statstable = Table(
    "stats",
    Base.metadata,
    Column("name", VARCHAR(35), primary_key=False),
    Column("correctcount", Integer),
    Column("result", Text),
    Column("creationdate", TIMESTAMP),
)

userstable = Table(
    "users",
    Base.metadata,
    Column("name", VARCHAR(35), primary_key=True),
    Column("chat_id", Integer),
    Column("usertype", Text),
    Column("creationdate", TIMESTAMP),
)


async def setup_db():
    engine = await db_engine()
    conn = await db_cursor()
    questions = select(questionstable)
    if not engine.dialect.has_table(conn, "questions") or len(conn.execute(questions).fetchall()) < len(json.load(open("whocanbeamillionairetho.json"))):
        Base.metadata.create_all(engine)
        questions = json.load(open("whocanbeamillionairetho.json"))
        for i in questions:
            cmt = insert(questionstable).values(
                question=i["question"], options=i["options"], answer=i["answer"]
            )
            conn.execute(cmt)
        conn.commit()
