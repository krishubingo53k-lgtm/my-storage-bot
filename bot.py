import os
import sqlite3
from pyrogram import Client, filters
from pyrogram.types import Message
import aiohttp

BOT_TOKEN = os.environ["BOT_TOKEN"]
API_ID = int(os.environ["API_ID"])
API_HASH = os.environ["API_HASH"]

ADMIN_IDS = set(int(x) for x in os.environ["ADMIN_IDS"].split(","))

DB_PATH = "database.db"


# ---------- DB SETUP ----------
def init_db():
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id TEXT,
            message_id INTEGER,
            file_id TEXT,
            caption TEXT
        )
    """)
    con.commit()
    con.close()


def add_file(chat_id, message_id, file_id, caption):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute(
        "INSERT INTO files (chat_id, message_id, file_id, caption) VALUES (?,?,?,?,?)",
        (chat_id, message_id, file_id, caption)
    )
    con.commit()
    con.close()


def search_files(q):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute(
        "SELECT id, chat_id, message_id, caption FROM files WHERE caption LIKE ?",
        (f"%{q}%",)
    )
    rows = cur.fetchall()
    con.close()
    return rows


# ---------- BOT SETUP ----------
app = Client(
    "StorageBot",
    bot_token=BOT_TOKEN,
    api_id=API_ID,
    api_hash=API_HASH
)


# ---------- COMMANDS ----------
@app.on_message(filters.command("start"))
async def start_cmd(client, message: Message):
    await message.reply_text(
        "⭐ Movie Storage Bot Running!\n\n"
        "Commands:\n"
        "/index @channel\n"
        "/search text"
    )


@app.on_message(filters.command("index"))
async def index_cmd(client, message: Message):
    user_id = message.from_user.id

    if user_id not in ADMIN_IDS:
        return await message.reply("❌ You are not admin")

    if len(message.command) < 2:
        return await message.reply("Usage: /index @channelusername")

    channel = message.command[1]
    await message.reply("⏳ Indexing started, wait...")

    count = 0
    async for msg in client.iter_history(channel, limit=5000):
        media = msg.photo or msg.video or msg.document
        if media:
            add_file(
                msg.chat.id,
                msg.message_id,
                media.file_id,
                msg.caption or ""
            )
            count += 1

    await message.reply(f"✅ Indexing Complete!\nAdded: {count} files")


@app.on_message(filters.command("search"))
async def search_cmd(client, message: Message):
    if len(message.command) < 2:
        return await message.reply("Usage: /search keyword")

    q = " ".join(message.command[1:])
    results = search_files(q)

    if not results:
        return await message.reply("❌ No results found")

    text = ""
    for rid, chat_id, msg_id, caption in results[:10]:
        link = f"https://t.me/c/{str(chat_id).lstrip('-100')}/{msg_id}"
        text += f"🎬 {caption[:40]}...\n🔗 {link}\n\n"

    await message.reply(text)


# ---------- START BOT ----------
init_db()
app.run()
