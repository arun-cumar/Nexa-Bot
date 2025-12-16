
import os 
import re
import asyncio
import json
import time 
from pyrogram import Client, filters
# CRITICAL FIX: Ensure InlineKeyboardButton is imported for creating buttons
from pyrogram.enums import ChatType, ChatMemberStatus 
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, Document, Video, Audio, CallbackQuery
from pyrogram.errors import UserNotParticipant, MessageNotModified, ChatAdminRequired, RPCError
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from typing import List, Dict, Any, Union, Tuple
from fastapi import FastAPI, Request, Response 
from contextlib import asynccontextmanager, suppress
from http import HTTPStatus
import uvicorn
import urllib.parse

# Load variables from the .env file
load_dotenv()

# --- GLOBAL STATUS FLAGS AND VARIABLES ---
IS_INDEXING_RUNNING = False
BOT_USERNAME: str = "" # To be set on startup
RESULTS_PER_PAGE = 10 # Define the pagination limit

# --- CUSTOM CAPTION FOR SENT FILES (A custom caption for files delivered in DM) ---
NEW_CAPTION = (
    "°•➤@Mala_Television 🍿\n"
    "°•➤@Mala_Tv\n"
    "°•➤@MalaTvbot ™️\n\n"
    "Enjoy! 🙂🙂"
)

# --- CONFIG VARIABLES ---
API_ID = int(os.environ.get("API_ID", 12345))
API_HASH = os.environ.get("API_HASH", "YOUR_API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "YOUR_BOT_TOKEN")
PRIVATE_FILE_STORE = int(os.environ.get("PRIVATE_FILE_STORE", -100)) 
LOG_CHANNEL = int(os.environ.get("LOG_CHANNEL", -100))
USER_SESSION_STRING = os.environ.get("USER_SESSION_STRING", None) 
ADMINS = []
admin_env = os.environ.get("ADMINS", "")
if admin_env:
    ADMINS = [int(admin.strip()) for admin in admin_env.split(',') if admin.strip().isdigit()]
DATABASE_URL = os.environ.get("DATABASE_URL", "mongodb://localhost:27017")
FORCE_SUB_CHANNEL = os.environ.get("FORCE_SUB_CHANNEL", None) 
WEBHOOK_URL_BASE = os.environ.get("WEBHOOK_URL_BASE", None)
PORT = int(os.environ.get("PORT", 8080))
WEBHOOK_PATH = f"/{BOT_TOKEN}"

# --- MONGODB SETUP ---

class Database:
    """Handles database operations for storing file indexes, search cache, and bot stats."""
    def __init__(self, uri: str, database_name: str):
        self._client = AsyncIOMotorClient(uri)
        self.db = self._client[database_name]
        self.files_col = self.db["files"]
        self.search_cache_col = self.db["search_cache"] 
        self.stats_col = self.db["stats"]

    async def find_one(self, query: Dict[str, Any]) -> Union[Dict[str, Any], None]:
        return await self.files_col.find_one(query)

    async def update_one(self, query: Dict[str, Any], update: Dict[str, Any], upsert: bool = False):
        await self.files_col.update_one(query, update, upsert=upsert)

    async def cache_query(self, message_id: int, query_text: str):
        await self.search_cache_col.update_one(
            {"_id": message_id},
            {"$set": {"query": query_text, "timestamp": time.time()}}, 
            upsert=True
        )

    async def get_cached_query(self, message_id: int) -> Union[str, None]:
        doc = await self.search_cache_col.find_one({"_id": message_id})
        return doc.get('query') if doc else None

    async def increment_start_count(self):
        result = await self.stats_col.find_one_and_update(
            {"_id": "start_count"},
            {"$inc": {"count": 1}},
            upsert=True,
            return_document="after"
        )
        return result.get("count", 1) 

# Database instance
db = Database(DATABASE_URL, "AutoFilterBot")

# --- PYROGRAM CLIENTS ---

class AutoFilterBot(Client):
    def __init__(self):
        super().__init__(
            "AutoFilterBot",
            api_id=API_ID,
            api_hash=API_HASH,
            bot_token=BOT_TOKEN,
            sleep_threshold=30
        )

app = AutoFilterBot()

user_client: Union[Client, None] = None
if USER_SESSION_STRING:
    user_client = Client(
        "indexer_session",
        api_id=API_ID,
        api_hash=API_HASH,
        session_string=USER_SESSION_STRING, 
    )

# --- HELPERS ---

async def delete_after_delay(client: Client, chat_id: int, message_id: int, delay: int = 60):
    """Deletes a message after a specified delay."""
    await asyncio.sleep(delay)
    with suppress(Exception):
        await client.delete_messages(chat_id, message_id)

async def is_subscribed(client, user_id, max_retries=3, delay=1):
    """
    Checks if the user is a member of the force subscribe channel, with retries.
    Checks all users (member, admin, creator).
    """
    if not FORCE_SUB_CHANNEL:
        return True
    
    for attempt in range(max_retries):
        try:
            # Bot MUST be an admin in the FORCE_SUB_CHANNEL to run get_chat_member
            member = await client.get_chat_member(FORCE_SUB_CHANNEL, user_id) 
            
            # CRITICAL: Check if the user is an active member
            if member.status not in [ChatMemberStatus.LEFT, ChatMemberStatus.BANNED]:
                return True
            
            return False # Status is LEFT or BANNED

        except UserNotParticipant:
            return False 
        except ChatAdminRequired:
             print("CRITICAL ERROR: Bot needs to be an admin in the FORCE_SUB_CHANNEL to check membership.")
             return False
        except Exception as e:
            print(f"Error checking subscription (Attempt {attempt+1}): {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(delay) 
            else:
                 return False
            
    return False

async def get_file_details(query: str, page: int = 1, limit: int = RESULTS_PER_PAGE) -> Tuple[List[Dict[str, Any]], int]:
    """Searches for file details in the database using regex with pagination."""
    min_query_length = 3 
    words = [word.strip() for word in re.split(r'\W+', query) if len(word.strip()) > 1]
    
    all_word_conditions = []
    if len(query.strip()) >= min_query_length and words:
        for word in words:
            word_regex = re.escape(word)
            all_word_conditions.append({
                "$or": [
                    {"title": {"$regex": f".*\\b{word_regex}\\b.*", "$options": "i"}},
                    {"caption": {"$regex": f".*\\b{word_regex}\\b.*", "$options": "i"}}
                ]
            })

    escaped_query = re.escape(query)
    phrase_regex = f".*{escaped_query}.*"
    phrase_condition = {
        "$or": [
            {"title": {"$regex": phrase_regex, "$options": "i"}},
            {"caption": {"$regex": phrase_regex, "$options": "i"}}
        ]
    }

    if all_word_conditions:
        search_query = {
            "$or": [
                {"$and": all_word_conditions}, 
                phrase_condition             
            ]
        }
    else:
        search_query = phrase_condition
        
    total_count = await db.files_col.count_documents(search_query)
    skip_amount = (page - 1) * limit
    cursor = db.files_col.find(search_query).skip(skip_amount).limit(limit)
    files = await cursor.to_list(length=limit)
    
    return files, total_count

def get_file_details_from_message(message: Message) -> tuple[Union[str, None], Union[str, None], Union[Document, Video, Audio, None]]:
    """Finds file_id, file_name, and file_object from a message."""
    if message.document and message.document.file_name:
        return message.document.file_id, message.document.file_name, message.document
    if message.video:
        file_name = message.caption.strip() if message.caption else f"Video_{message.id}"
        if message.video.file_name:
             file_name = message.video.file_name
        return message.video.file_id, file_name, message.video
    if message.audio:
        file_name = message.audio.file_name or message.audio.title or f"Audio_{message.id}"
        return message.audio.file_id, file_name, message.audio
    return None, None, None

async def index_message(message: Message) -> bool:
    """Indexes a single file message into the database."""
    file_id, file_name, file_object = get_file_details_from_message(message)
    
    if not file_id:
        return False

    caption = message.caption.html if message.caption else None
    
    try:
        await db.files_col.update_one( 
            {"file_id": file_id},
            {
                "$set": {
                    "title": file_name,
                    "caption": caption,
                    "file_id": file_id,
                    "chat_id": message.chat.id, 
                    "message_id": message.id,
                    "media_type": file_object.__class__.__name__.lower()
                }
            },
            upsert=True
        )
        return True
    except Exception as db_error:
        print(f"INDEX_MESSAGE_ERROR: DB write failed for message {message.id}: {db_error}")
        return False

def create_file_buttons(files: List[Dict[str, Any]], original_msg_id: int, original_chat_id: int):
    """Generates the main file result buttons."""
    buttons = []
    for file in files:
        media_icon = {"document": "📄", "video": "🎬", "audio": "🎵"}.get(file.get('media_type', 'document'), '❓')
        file_name_clean = file.get("title", "File").rsplit('.', 1)[0].strip() 
        callback_data = f"getfile_{file.get('message_id')}_{original_msg_id}_{original_chat_id}"
        buttons.append([
            InlineKeyboardButton(text=f"{media_icon} {file_name_clean}", callback_data=callback_data)
        ])
    return buttons

def create_pagination_buttons(page: int, total_count: int, original_msg_id: int):
    """Generates the Next/Back pagination buttons."""
    limit = RESULTS_PER_PAGE
    total_pages = (total_count + limit - 1) // limit
    
    if total_pages <= 1:
        return []
        
    pagination_row = []
    
    if page > 1:
        pagination_row.append(InlineKeyboardButton("⬅️ Back", callback_data=f"page_prev_{page-1}_{original_msg_id}"))
    
    pagination_row.append(InlineKeyboardButton(f"Page {page}/{total_pages}", callback_data="ignore"))
    
    if page < total_pages:
        pagination_row.append(InlineKeyboardButton("Next ➡️", callback_data=f"page_next_{page+1}_{original_msg_id}"))

    return [pagination_row] if pagination_row else []

async def handle_send_file(client, user_id, message_id):
    """Core function to copy/forward the file content with fallback."""
    file = await db.files_col.find_one({"message_id": message_id}) 
    
    if not file:
        with suppress(Exception):
            await client.send_message(user_id, "❌ Sorry, this file has been removed from the database.")
        return False, "File removed."

    try:
        sent_msg: Message = await client.copy_message(
            chat_id=user_id, 
            from_chat_id=file['chat_id'],
            message_id=file['message_id'],
            caption=NEW_CAPTION
        )
        asyncio.create_task(delete_after_delay(client, sent_msg.chat.id, sent_msg.id, delay=60))
        return True, "File sent successfully via copy."
        
    except RPCError as e:
        global user_client
        if user_client and ("MESSAGE_PROTECTED" in str(e).upper() or "CANT_COPY" in str(e).upper()):
            try:
                if not user_client.is_connected:
                     await user_client.start()
                sent_msgs: List[Message] = await user_client.forward_messages(
                    chat_id=user_id, from_chat_id=file['chat_id'], message_ids=[file['message_id']] 
                )
                if sent_msgs:
                    asyncio.create_task(delete_after_delay(user_client, sent_msgs[0].chat.id, sent_msgs[0].id, delay=60))
                return True, "File forwarded successfully via user session."
            except Exception as forward_e:
                print(f"Fallback forwarding failed: {forward_e}")
        
        error_msg = ("❌ **Sorry, the file could not be sent!** ❌\n\n"
                     "Please unblock the bot and try again.")
        with suppress(Exception):
            await client.send_message(user_id, error_msg)
        return False, error_msg
        
    except Exception as e:
        print(f"Unexpected error copying file: {e}")
        error_msg = "❌ An unexpected error occurred while sending the file."
        with suppress(Exception):
            await client.send_message(user_id, error_msg)
        return False, error_msg

async def handle_start_log(client, message: Message):
    """Logs the user who started the bot and the current overall start count. (For Log Channel)"""
    
    start_count = await db.increment_start_count()
    user = message.from_user
    
    log_text = (
        f"🤖 **New Bot Start!**\n"
        f"---------------------------\n"
        f"👤 **User:** {user.mention} (`{user.id}`)\n"
        f"🏷️ **Username:** @{user.username or 'N/A'}\n"
        f"🔢 **Total Starts:** `{start_count}`"
    )

    if LOG_CHANNEL:
        with suppress(Exception):
            await client.send_message(LOG_CHANNEL, log_text, disable_web_page_preview=True)


# --- STARTUP/LIFESPAN ---

async def startup_initial_checks():
    """Checks to run on startup."""
    global BOT_USERNAME
    try:
        bot_info = await app.get_me()
        BOT_USERNAME = bot_info.username
        print(f"Bot Username fetched: @{BOT_USERNAME}")
    except Exception as e:
        print(f"CRITICAL: Failed to fetch bot username: {e}")
    try:
        files_count = await db.files_col.count_documents({})
        print(f"Database check complete. Found {files_count} files in the database.")
    except Exception as e:
        print(f"WARNING: Database connection failed on startup: {e}")

@asynccontextmanager
async def lifespan(web_app: FastAPI):
    # Start Pyrogram client first to fetch BOT_USERNAME
    await app.start() 
    if user_client:
        await user_client.start()

    await startup_initial_checks()
    
    # RENDER/WEBHOOK FIX: We do not call app.set_webhook() manually here.
    if WEBHOOK_URL_BASE:
        print("Bot starting in Webhook Mode (FastAPI listening for updates).")
    else:
        print("Starting in polling mode (for local testing only).")
        
    yield
    await app.stop()
    if user_client:
         await user_client.stop()
    print("Application stopped.")

api_app = FastAPI(lifespan=lifespan)

@api_app.post(WEBHOOK_PATH)
async def process_update(request: Request):
    """Receives and processes Telegram updates."""
    try:
        req = await request.json()
        await app.process_update(req)
        return Response(status_code=HTTPStatus.OK)
    except Exception as e:
        print(f"Error processing update: {e}")
        return Response(status_code=HTTPStatus.INTERNAL_SERVER_ERROR)

@api_app.get("/")
async def health_check():
    """Render health check endpoint."""
    return {"status": "ok"}


# --- HANDLERS (Moved from separate file into main.py) ---

@app.on_message(filters.command("start") & filters.private)
async def start_command(client, message: Message):
    """Handles the /start command, deep links, and the Force Sub check in DM."""
    global IS_INDEXING_RUNNING
    user_id = message.from_user.id
    
    asyncio.create_task(handle_start_log(client, message)) # Log Channel Call
    
    if IS_INDEXING_RUNNING:
        await message.reply_text("Indexing is currently running. Please wait until it is complete.")
        return
    
    if len(message.command) > 1:
        payload = message.command[1]
        
        if payload.startswith("file_"):
            
            # 1. FORCE SUB CHECK in DM (Applies to all users, even admins, if not using a specific exemption logic)
            if FORCE_SUB_CHANNEL: # Check only if FORCE_SUB_CHANNEL is set
                is_subbed = await is_subscribed(client, user_id, max_retries=3)
                
                if not is_subbed:
                    # Force Sub Check Failed: Display Join Button in DM
                    join_button = [
                        [InlineKeyboardButton("🔗 Join Channel", url=f"https://t.me/{FORCE_SUB_CHANNEL.replace('@', '')}")],
                        # CRITICAL: The next button calls /start again with the same payload
                        [InlineKeyboardButton("✅ Joined, Send File!", url=f"https://t.me/{BOT_USERNAME}?start={payload}")]
                    ]
                    
                    await message.reply_text(
                        "🔑 **Mandatory Subscription:** You must join our channel to get the file.\n\n"
                        "1. Click the **Join Channel** button.\n"
                        "2. After joining, click the **✅ Joined, Send File!** button to complete the process and get your file.",
                        reply_markup=InlineKeyboardMarkup(join_button)
                    )
                    return 
            
            # 2. SUBSCRIBED / NO FORCE SUB: Deliver File
            try:
                _, message_id_str, _, _ = payload.split('_')
                file_message_id = int(message_id_str)
                
                await message.reply_text("✅ Starting file delivery. Please wait...")
                
                success, _ = await handle_send_file(client, user_id, file_message_id)
                
                if success:
                    await message.reply_text("🎉 File sent successfully! It will be deleted after 60 seconds. Go to the group for the next file.")
                return

            except Exception:
                await message.reply_text("❌ File delivery failed. The link might be broken. Please click the button in the group again.")
                return

    # Standard /start message 
    start_text = (
        "Hi! I am your **Auto Filter Bot.** 🤩\n\n"
        "🔎 **How to use me?**\n"
        "[...Your standard welcome text...]"
    )
    
    await message.reply_text(start_text)

@app.on_message(filters.chat(PRIVATE_FILE_STORE) & (filters.document | filters.video | filters.audio))
async def realtime_indexer(client, message: Message):
    """Handles new file uploads in the PRIVATE_FILE_STORE channel and indexes them immediately."""
    if PRIVATE_FILE_STORE != -100:
        await index_message(message)

@app.on_message(filters.command("index") & filters.user(ADMINS))
async def index_command(client, message: Message):
    """Admin command to index all files from the file store channel."""
    global IS_INDEXING_RUNNING, user_client

    if IS_INDEXING_RUNNING:
        await message.reply_text("❌ Note: The indexing process is currently running. Please wait until it is complete.")
        return

    if PRIVATE_FILE_STORE == -100 or not user_client:
         await message.reply_text("❌ Indexing Error: Required configs (PRIVATE_FILE_STORE or USER_SESSION_STRING) are missing.")
         return

    IS_INDEXING_RUNNING = True 
    msg = await message.reply_text("🔑 Starting file indexing...")
    total_files_indexed = 0
    total_messages_processed = 0
    
    try:
        if not user_client.is_connected: 
            await user_client.start() 

        async for chat_msg in user_client.get_chat_history(chat_id=PRIVATE_FILE_STORE): 
            total_messages_processed += 1
            if await index_message(chat_msg):
                total_files_indexed += 1
                if total_files_indexed % 50 == 0:
                     with suppress(MessageNotModified):
                         await msg.edit_text(f"✅ Indexed Files: {total_files_indexed} / {total_messages_processed}")

        await msg.edit_text(f"🎉 Indexing complete! Total {total_files_indexed} files added or updated.")
        
    except Exception as general_error:
        await msg.edit_text(f"❌ Indexing Error: {general_error}.")
        
    finally:
        IS_INDEXING_RUNNING = False

@app.on_message(filters.command("dbcount") & filters.user(ADMINS))
async def dbcount_command(client, message: Message):
    """Command to check the total number of files in the database."""
    try:
        count = await db.files_col.count_documents({})
        await message.reply_text(f"📊 **Database Count:**\nTotal indexed files: **{count}**")
    except Exception as e:
        await message.reply_text(f"❌ Error getting database count: {e}")

@app.on_message(filters.text & filters.incoming & ~filters.command(["start", "index", "dbcount"])) 
async def global_handler(client, message: Message):
    """Handles all incoming text messages: copyright deletion and auto-filter search."""
    
    query = message.text.strip()
    chat_id = message.chat.id
    chat_type = message.chat.type
    
    if IS_INDEXING_RUNNING or chat_type == ChatType.PRIVATE or chat_id == PRIVATE_FILE_STORE:
        return
        
    # --- COPYRIGHT DELETION LOGIC --- (Simplified, targeting only the store)
    COPYRIGHT_KEYWORDS = ["copyright", "unauthorized", "DMCA", "piracy"] 
    if any(keyword.lower() in query.lower() for keyword in COPYRIGHT_KEYWORDS):
        if chat_id == PRIVATE_FILE_STORE:
            with suppress(Exception):
                await message.delete()
                await client.send_message(LOG_CHANNEL, f"🚫 **Copyright message deleted**...")
            return
            
    # --- AUTO-FILTER SEARCH ---
    page = 1
    files, total_count = await get_file_details(query, page=page)
    
    if files:
        await db.cache_query(message.id, query)
        file_buttons = create_file_buttons(files, message.id, message.chat.id)
        pagination_buttons = create_pagination_buttons(page, total_count, message.id)
        buttons = file_buttons + pagination_buttons
        text = f"✅ **Results for {query}:**\n\nFound **{total_count}** matches. Click the button below to get the file. You will be redirected to DM."
        sent_msg = await message.reply_text(text=text, reply_markup=InlineKeyboardMarkup(buttons), disable_web_page_preview=True)
        asyncio.create_task(delete_after_delay(client, sent_msg.chat.id, sent_msg.id, delay=600))
    else:
        # Fallback
        encoded_query = urllib.parse.quote_plus(query)
        fallback_buttons = InlineKeyboardMarkup([[InlineKeyboardButton(text="🌐 Search on Google", url=f"https://www.google.com/search?q={encoded_query}")]])
        fallback_text = f"😔 **Files Not Found** 😔\n\nNo files matching the name **'{query}'** were found."
        sent_msg = await message.reply_text(text=fallback_text, reply_markup=fallback_buttons, disable_web_page_preview=True)
        asyncio.create_task(delete_after_delay(client, sent_msg.chat.id, sent_msg.id, delay=600))

@app.on_callback_query(filters.regex("^page_(prev|next)_"))
async def handle_pagination_callback(client: Client, callback: CallbackQuery):
    """Handles 'Next Page' and 'Previous Page' button clicks."""
    try:
        _, action, page_str, original_msg_id_str = callback.data.split('_')
        new_page = int(page_str)
        original_msg_id = int(original_msg_id_str)
    except Exception:
        await callback.answer("❌ Invalid pagination data.", show_alert=True)
        return

    query = await db.get_cached_query(original_msg_id)
    if not query:
        await callback.answer("❌ Search expired. Please search again.", show_alert=True)
        return

    files, total_count = await get_file_details(query, page=new_page)
    
    if not files:
        await callback.answer("❌ No results found on this page.", show_alert=True)
        return

    file_buttons = create_file_buttons(files, original_msg_id, callback.message.chat.id)
    pagination_buttons = create_pagination_buttons(new_page, total_count, original_msg_id)
    buttons = file_buttons + pagination_buttons
    
    text = f"✅ **Results for {query}:**\n\nFound **{total_count}** matches. Click the button below to get the file. You will be redirected to DM."

    try:
        await callback.message.edit_text(text=text, reply_markup=InlineKeyboardMarkup(buttons), disable_web_page_preview=True)
        await callback.answer()
    except MessageNotModified:
        await callback.answer("Nothing to change.")
    except Exception:
        await callback.answer("❌ Failed to update results.", show_alert=True)
                
@app.on_callback_query(filters.regex("^getfile_")) 
async def redirect_to_dm_handler(client, callback):
    """Handles the initial filter button click and redirects to DM."""
    global BOT_USERNAME
    
    data_parts = callback.data.split('_')
    deep_link_payload = f"file_{data_parts[1]}_{data_parts[2]}_{data_parts[3]}"
    
    if not BOT_USERNAME:
        await callback.answer("❌ Bot username is not available.", show_alert=True)
        return

    deep_link = f"https://t.me/{BOT_USERNAME}?start={deep_link_payload}"
    
    try:
        await callback.answer(
            text="🔑 Redirecting to DM... Please press 'Send' on the /start message there.", 
            show_alert=False,
            url=deep_link 
        )
    except Exception:
        await callback.answer("❌ Failed to redirect to DM. Please try again.", show_alert=True)
        return
    
    try:
        # Edit the group message to confirm action
        await callback.message.edit_text(
            "✅ **Redirected to DM:**\n\n"
            "Please go to the bot's private chat and press the **Send** button. The file will be delivered shortly. (The file will be deleted in 60 seconds)",
        )
    except Exception:
         pass # Ignore if message edit fails


# --- MAIN ENTRY POINT ---

if __name__ == "__main__":
    if WEBHOOK_URL_BASE:
        # Use uvicorn to serve the FastAPI app (for Render deployment)
        uvicorn.run("main:api_app", host="0.0.0.0", port=PORT, log_level="info")
    else:
        # Use app.run() for local polling mode testing
        async def start_polling():
            await app.start()
            if user_client:
                 await user_client.start()
            await startup_initial_checks()
            await app.idle()
            if user_client:
                 await user_client.stop()
            await app.stop()
        
        asyncio.run(start_polling())
