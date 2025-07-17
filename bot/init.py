from bot.db import db_engine, db_cursor
from sqlalchemy import Table, Column, Integer, Text, MetaData, VARCHAR, TIMESTAMP, ARRAY, insert
import json

async def setup_db():
    engine = await db_engine()
    conn = await db_cursor()
    meta = MetaData()
    if not engine.dialect.has_table(conn, "questions"):
        questionstable = Table(
        'questions', meta,
        Column('question', Text),
        Column('options', ARRAY(Text)),
        Column('answer', Text),
        )
        meta.create_all(engine)
        questions = json.load(open("whocanbeamillionairetho.json"))
        for i in questions:
            cmt = insert(questionstable).values(question=i['question'], options=i['options'], answer=i['answer'])
            conn.execute(cmt)
        conn.commit()
    Table(
    'stats', meta,
    Column('name', VARCHAR(35), primary_key=True),
    Column('correctcount', Integer),
    Column('result', Text),
    Column('creationdate', TIMESTAMP),
    )
    Table(
    'users', meta,
    Column('name', VARCHAR(35), primary_key=True),
    Column('chat_id', Integer),
    Column('usertype', Text),
    Column('creationdate', TIMESTAMP),
    )
    Table(
    'admin', meta,
    Column('name', VARCHAR(35))
    )
    meta.create_all(engine)