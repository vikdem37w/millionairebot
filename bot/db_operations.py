from bot.db import db_engine, db_cursor
import asyncio
from sqlalchemy import select, insert, MetaData, Table
import datetime as dt

engine = asyncio.run(db_engine())
conn = asyncio.run(db_cursor())
reward = [0, 100, 200, 300, 500, 1000, 2000, 4000, 8000, 16000, 32000, 64000, 125000, 250000, 500000, 1000000]

async def get_questions():
    meta = MetaData()
    questionstable = Table("questions", meta, autoload_with=engine)
    questions = select(questionstable)
    return list(conn.execute(questions).fetchall())

async def stats_up(username, qindex: int, result: str):
    meta = MetaData()
    statstable = Table("stats", meta, autoload_with=engine)
    stat = insert(statstable).values(name=username, correctcount=qindex, result=result, creationdate=dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    conn.execute(stat)
    conn.commit()

async def fill_leaderboard(username):
    meta = MetaData()
    statstable = Table("stats", meta, autoload_with=engine)
    stats = select(statstable).order_by(statstable.c.correctcount.desc()).limit(10)
    leaderboard = list(conn.execute(stats).fetchall())
    leaderoutput = ["Leaderboard: \n"]
    for i in range(len(leaderboard)):
        leaderoutput.append(f"{i+1}. {leaderboard[i][0]} {"won" if leaderboard[i][2] == "win" else "lost"} {reward[leaderboard[i][1]]}₴ on {leaderboard[i][3].strftime("%b %d %H:%M")}")
    if username != "NULL":
        userstats = select(statstable).where(statstable.c.name == username).order_by(statstable.c.correctcount.desc()).limit(10)
        userstats = list(conn.execute(userstats).fetchall())
        leaderoutput.append(f"\n\n{username}'s personal leaderboard:\n")
        for i in range(len(userstats)):
            leaderoutput.append(f"{i+1}. You {"won" if userstats[i][2] == "win" else "lost"} {reward[userstats[i][1]]}₴ on {userstats[i][3].strftime("%b %d %H:%M")}")
    return "\n".join(leaderoutput)

async def is_admin(username):
    meta = MetaData()
    adminstable = Table("admin", meta, autoload_with=engine)
    admin = select(adminstable).where(adminstable.c.name == username)
    if conn.execute(admin).fetchall():
        return "admin"
    else:
        return "normal"

async def add_user(username, chat_id, admin):
    meta = MetaData()
    userstable = Table("users", meta, autoload_with=engine)
    user = select(userstable).where(userstable.c.name == username)
    if not conn.execute(user).fetchall():
        user = insert(userstable).values(name=username, chat_id=chat_id, usertype=admin, creationdate=dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        conn.execute(user)
        conn.commit()

async def commit_question(question, options, answer):
    meta = MetaData()
    questionstable = Table("questions", meta, autoload_with=engine)
    newq = insert(questionstable).values(question=question, options=options, answer=answer)
    conn.execute(newq)
    conn.commit()