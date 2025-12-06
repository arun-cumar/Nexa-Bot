import os 
import re
import asyncio
import json
import time 
from pyrogram import Client, filters
from pyrogram.enums import ChatType
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, Document, Video, Audio, CallbackQuery
from pyrogram.errors import UserNotParticipant, MessageNotModified, ChatAdminRequired, RPCError
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from typing import List, Dict, Any, Union, Tuple
from fastapi import FastAPI, Request, Response 
from contextlib import asynccontextmanager
from http import HTTPStatus
import uvicorn

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
    "🙂🙂"
)

# --- CONFIG VARIABLES ---
# API credentials (Get these from my.telegram.org)
API_ID = int(os.environ.get("API_ID", 12345))
API_HASH = os.environ.get("API_HASH", "YOUR_API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "YOUR_BOT_TOKEN")

# ID of the channel where indexed files are stored (e.g., -1001234567890)
PRIVATE_FILE_STORE = int(os.environ.get("PRIVATE_FILE_STORE", -100)) 
# ID of the channel for logging important messages
LOG_CHANNEL = int(os.environ.get("LOG_CHANNEL", -100))
# Optional: Session string for a user account to index/forward protected content
USER_SESSION_STRING = os.environ.get("USER_SESSION_STRING", None) 

# Admin list (Comma-separated user IDs)
ADMINS = []
admin_env = os.environ.get("ADMINS", "")
if admin_env:
    ADMINS = [int(admin.strip()) for admin in admin_env.split(',') if admin.strip().isdigit()]

# MongoDB connection details
DATABASE_URL = os.environ.get("DATABASE_URL", "mongodb://localhost:27017")
# Force subscribe channel username (without @, e.g., 'MalayalamMovies')
FORCE_SUB_CHANNEL = os.environ.get("FORCE_SUB_CHANNEL", None) 

# Webhook details for Render/Cloud deployment
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
        self.stats_col = self.db["stats"] # New collection for stats

    async def find_one(self, query: Dict[str, Any]) -> Union[Dict[str, Any], None]:
        """Finds a single document matching the query."""
        return await self.files_col.find_one(query)

    async def update_one(self, query: Dict[str, Any], update: Dict[str, Any], upsert: bool = False):
        """Updates a single document. Inserts if upsert is True and no match is found."""
        await self.files_col.update_one(query, update, upsert=upsert)

    async def cache_query(self, message_id: int, query_text: str):
        """Caches the search query tied to a message ID."""
        await self.search_cache_col.update_one(
            {"_id": message_id},
            {"$set": {"query": query_text, "timestamp": time.time()}}, 
            upsert=True
        )

    async def get_cached_query(self, message_id: int) -> Union[str, None]:
        """Retrieves the cached search query."""
        doc = await self.search_cache_col.find_one({"_id": message_id})
        return doc.get('query') if doc else None

    async def increment_start_count(self):
        """Increments the global bot start count and returns the new count."""
        result = await self.stats_col.find_one_and_update(
            {"_id": "start_count"},
            {"$inc": {"count": 1}},
            upsert=True,
            return_document=True # Returns the updated document
        )
        # Ensure count is returned, defaulting to 1 if it's the very first start
        return result.get("count", 1) 

# Database instance
db = Database(DATABASE_URL, "AutoFilterBot")

# --- PYROGRAM CLIENTS ---

# Bot Client
class AutoFilterBot(Client):
    def __init__(self):
        super().__init__(
            "AutoFilterBot",
            api_id=API_ID,
            api_hash=API_HASH,
            bot_token=BOT_TOKEN,
            plugins=dict(root="plugins"),
            sleep_threshold=30
        )

# Global Bot Instance
app = AutoFilterBot()

# Global User Client Instance (for indexing and protected content forwarding)
user_client: Union[Client, None] = None
if USER_SESSION_STRING:
    user_client = Client(
        "indexer_session",
        api_id=API_ID,
        api_hash=API_HASH,
        session_string=USER_SESSION_STRING, 
    )
    print("User session initialized for indexing/forwarding.")


# --- RENDER WEBHOOK SETUP (FastAPI) ---

async def startup_initial_checks():
    """Checks to run on startup."""
    global BOT_USERNAME
    print("Performing initial startup checks...")
    
    # Get Bot Username
    try:
        bot_info = await app.get_me()
        BOT_USERNAME = bot_info.username
        print(f"Bot Username fetched: @{BOT_USERNAME}")
    except Exception as e:
        print(f"CRITICAL: Failed to fetch bot username: {e}")
        
    # 1. Database check
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
    
    if WEBHOOK_URL_BASE:
        await app.set_webhook(url=f"{WEBHOOK_URL_BASE}{WEBHOOK_PATH}")
        print(f"Webhook successfully set: {WEBHOOK_URL_BASE}{WEBHOOK_PATH}")
    else:
        print("Starting in polling mode (for local testing only).")
        
    yield
    await app.stop()
    if user_client:
         await user_client.stop()
    print("Application stopped.")

# FastAPI instance (CRITICAL: Defined at module level for Uvicorn)
api_app = FastAPI(lifespan=lifespan)

# Webhook endpoint for Telegram updates
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

# Render health check endpoint
@api_app.get("/")
async def health_check():
    """Render health check endpoint."""
    return {"status": "ok"}


# --- HELPERS ---

async def delete_after_delay(client: Client, chat_id: int, message_id: int, delay: int = 60):
    """Deletes a message after a specified delay."""
    await asyncio.sleep(delay)
    try:
        await client.delete_messages(chat_id, message_id)
        print(f"DEBUG: Deleted message {message_id} in chat {chat_id} after {delay} seconds.")
    except Exception as e:
        # This will fail if the user deleted the message or blocked the bot
        print(f"Error deleting message {message_id} in chat {chat_id} after delay: {e}")

async def is_subscribed(client, user_id, max_retries=3, delay=1):
    """Checks if the user is a member of the force subscribe channel, with retries."""
    if not FORCE_SUB_CHANNEL:
        return True
    
    for attempt in range(max_retries):
        try:
            # Use get_chat_member to check if the user is present and active
            member = await client.get_chat_member(FORCE_SUB_CHANNEL, user_id) 
            if member.status in ["member", "administrator", "creator"]:
                return True
            return False 
        except UserNotParticipant:
            return False # User is definitely not a member
        except ChatAdminRequired:
             print("ERROR: Bot needs to be an admin in the FORCE_SUB_CHANNEL to check membership.")
             return False
        except Exception as e:
            print(f"Error checking subscription (Attempt {attempt+1}): {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(delay) 
            else:
                 return False
            
    return False

async def get_file_details(query: str, page: int = 1, limit: int = RESULTS_PER_PAGE) -> Tuple[List[Dict[str, Any]], int]:
    """
    Searches for file details in the database using advanced tokenization and Regex with pagination.
    Returns: (list of files, total count of all matching files)
    """
    # Split query into words for better matching (word-boundary searches)
    words = [word.strip() for word in re.split(r'\W+', query) if len(query.strip()) > 2 and len(word.strip()) > 1]
    
    all_word_conditions = []
    if words:
        for word in words:
            word_regex = re.escape(word)
            all_word_conditions.append({
                "$or": [
                    {"title": {"$regex": f".*\\b{word_regex}\\b.*", "$options": "i"}},
                    {"caption": {"$regex": f".*\\b{word_regex}\\b.*", "$options": "i"}}
                ]
            })

    # Exact phrase search (to prioritize high-relevance matches)
    escaped_query = re.escape(query)
    phrase_regex = f".*{escaped_query}.*"
    phrase_condition = {
        "$or": [
            {"title": {"$regex": phrase_regex, "$options": "i"}},
            {"caption": {"$regex": phrase_regex, "$options": "i"}}
        ]
    }

    # Combine search conditions
    if all_word_conditions:
        search_query = {
            "$or": [
                {"$and": all_word_conditions}, # All words must be present (high relevance)
                phrase_condition             # Or the exact phrase must be present
            ]
        }
    else:
        # If the query is too short, rely only on the phrase condition
        search_query = phrase_condition
        
    # 1. Get total count first for pagination logic
    total_count = await db.files_col.count_documents(search_query)
    
    # 2. Apply skip and limit for pagination
    skip_amount = (page - 1) * limit
    # NOTE: No orderBy used to prevent requiring extra indexes in MongoDB.
    cursor = db.files_col.find(search_query).skip(skip_amount).limit(limit)
    files = await cursor.to_list(length=limit)
    
    return files, total_count

def get_file_info(message: Message) -> tuple[Union[str, None], Union[str, None], Union[Document, Video, Audio, None]]:
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

def create_file_buttons(files: List[Dict[str, Any]], original_msg_id: int, original_chat_id: int):
    """Generates the main file result buttons."""
    buttons = []
    for file in files:
        media_icon = {"document": "📄", "video": "🎬", "audio": "🎵"}.get(file.get('media_type', 'document'), '❓')
        file_name_clean = file.get("title", "File").rsplit('.', 1)[0].strip() 
        
        # Format: getfile_{file_message_id}_{group_message_id}_{group_chat_id}
        callback_data = f"getfile_{file.get('message_id')}_{original_msg_id}_{original_chat_id}"
        buttons.append([
            InlineKeyboardButton(
                text=f"{media_icon} {file_name_clean}",
                callback_data=callback_data
            )
        ])
    return buttons

def create_pagination_buttons(page: int, total_count: int, original_msg_id: int):
    """Generates the Next/Back pagination buttons."""
    limit = RESULTS_PER_PAGE
    total_pages = (total_count + limit - 1) // limit
    
    if total_pages <= 1:
        return []
        
    pagination_row = []
    
    # Back button
    if page > 1:
        # Callback: page_prev_{page-1}_{original_message_id}
        pagination_row.append(InlineKeyboardButton("⬅️ Back", callback_data=f"page_prev_{page-1}_{original_msg_id}"))
    
    # Page indicator
    pagination_row.append(InlineKeyboardButton(f"Page {page}/{total_pages}", callback_data="ignore"))
    
    # Next button
    if page < total_pages:
        # Callback: page_next_{page+1}_{original_message_id}
        pagination_row.append(InlineKeyboardButton("Next ➡️", callback_data=f"page_next_{page+1}_{original_msg_id}"))

    return [pagination_row] if pagination_row else []

# --- CORE FILE DELIVERY LOGIC ---

async def handle_send_file(client, user_id, message_id):
    """
    Core function to copy/forward the file content with fallback.
    Schedules the deletion of the sent message after 60 seconds.
    """
    
    file = await db.files_col.find_one({"message_id": message_id}) 
    
    if not file:
        try:
            await client.send_message(user_id, "❌ Sorry, this file has been removed from the database.")
        except Exception:
            pass
        return False, "File removed."

    # --- 1. Attempt to Copy the File (Bot client) ---
    try:
        sent_msg: Message = await client.copy_message(
            chat_id=user_id, 
            from_chat_id=file['chat_id'],
            message_id=file['message_id'],
            caption=NEW_CAPTION
        )
        
        # SCHEDULE AUTODELETE FOR DM MESSAGE (Bot Client)
        asyncio.create_task(delete_after_delay(client, sent_msg.chat.id, sent_msg.id, delay=60))

        return True, "File sent successfully via copy."
        
    except RPCError as e:
        print(f"RPC Error copying file to user {user_id}: {e}")
        
        # --- 2. FALLBACK: Attempt to Forward using User Session (for protected content) ---
        global user_client
        if user_client and ("MESSAGE_PROTECTED" in str(e).upper()):
            print(f"Falling back to user session forwarding for user {user_id}...")
            try:
                # FIX: Check for 'is_connected' instead of 'is_running' for Pyrogram V2
                if not user_client.is_connected:
                     await user_client.start()
                
                sent_msgs: List[Message] = await user_client.forward_messages(
                    chat_id=user_id, 
                    from_chat_id=file['chat_id'], 
                    message_ids=[file['message_id']] 
                )
                
                if sent_msgs:
                    # SCHEDULE AUTODELETE FOR DM MESSAGE (User Client - as it was forwarded by user)
                    asyncio.create_task(delete_after_delay(user_client, sent_msgs[0].chat.id, sent_msgs[0].id, delay=60))
                        
                return True, "File forwarded successfully via user session."
            except Exception as forward_e:
                print(f"Fallback forwarding failed for user {user_id}: {forward_e}")
        
        # --- 3. Final Error Message (After all failures) ---
        error_msg = ("❌ **Sorry, the file could not be sent!** ❌\n\n"
                     "Two main reasons:\n"
                     "1. You might have blocked me. Please unblock.\n"
                     "2. Your private chat settings might restrict receiving files.\n\n"
                     "Please **unblock and send /start** to try again.")
        try:
            await client.send_message(user_id, error_msg)
        except Exception:
            pass 
            
        return False, error_msg
        
    except Exception as e:
        print(f"Unexpected error copying file to user {user_id}: {e}")
        error_msg = "❌ An unexpected error occurred while sending the file. (Failed to copy file)"
        try:
            await client.send_message(user_id, error_msg)
        except Exception:
            pass
        return False, error_msg

# --- NEW LOGGING FUNCTION FOR /start ---

async def handle_start_log(client, message: Message):
    """Logs the user who started the bot and the current overall start count."""
    
    # 1. Increment Start Count in DB
    start_count = await db.increment_start_count()
    
    user = message.from_user
    
    # 2. Create the log message
    log_text = (
        f"🤖 **New Bot Start!**\n"
        f"---------------------------\n"
        f"👤 **User:** {user.mention} (`{user.id}`)\n"
        f"🏷️ **Username:** @{user.username or 'N/A'}\n"
        f"🔢 **Total Starts:** `{start_count}`"
    )

    # 3. Send to Log Channel
    if LOG_CHANNEL:
        try:
            await client.send_message(LOG_CHANNEL, log_text, disable_web_page_preview=True)
        except Exception as e:
            print(f"Error sending start log to LOG_CHANNEL: {e}")


# --- START COMMAND (Handles /start and /start payload) ---
@app.on_message(filters.command("start") & filters.private)
async def start_command(client, message: Message):
    """
    Handles the /start command in a private chat. 
    Checks for a deep-link payload to deliver a file immediately.
    """
    global IS_INDEXING_RUNNING
    
    # LOGGING: Call the handler to log the user and count
    asyncio.create_task(handle_start_log(client, message))
    
    if IS_INDEXING_RUNNING:
        await message.reply_text("Indexing is currently running. Please wait until it is complete.")
        return
    
    # Check for deep-link payload: /start file_messageId_groupMsgId_groupId
    if len(message.command) > 1:
        payload = message.command[1]
        
        if payload.startswith("file_"):
            try:
                # payload is expected to be file_{file_message_id}_{group_msg_id}_{group_chat_id}
                _, message_id_str, group_msg_id_str, group_chat_id_str = payload.split('_')
                file_message_id = int(message_id_str)
                
                await message.reply_text("✅ Starting file delivery. Please wait...")
                
                success, _ = await handle_send_file(
                    client, 
                    message.from_user.id, 
                    file_message_id
                )
                
                if success:
                    await message.reply_text("🎉 File sent successfully! It will be deleted after 60 seconds. Go to the group for the next file.")
                return

            except Exception as e:
                print(f"Error processing deep-link payload: {e}")
                await message.reply_text("❌ File delivery failed. The link might be broken. Please click the button in the group again.")
                return

    # Standard /start message
    start_text = (
        "Hi! I am your **Auto Filter Bot.** 🤩\n\n"
        "🔎 **How to use me?**\n"
        "1. Type the name of the movie or series you want in any group or channel where I am an Admin.\n"
        "2. Click the result button that appears. \n"
        "3. You will be redirected here. Press **'Send' on the /start** message automatically filled.\n"
        "4. The file will be sent to your private chat (DM) immediately! 🎉 (Note: The file will be deleted after 60s)\n\n"
        "🔗 **Our Channels:**\n"
        "°•➤ @Mala_Television\n"
        "°•➤ @Mala_Tv\n"
        "°•➤ @MalaTvbot ™️\n\n"
        "**Admin Commands:**\n"
        "• `/index` - To index all files in the channel.\n"
        "• `/dbcount` - To check the number of files in the database."
    )
    
    await message.reply_text(start_text)

# --- ADMIN COMMANDS (Indexing, etc.) ---

@app.on_message(filters.command("index") & filters.user(ADMINS))
async def index_command(client, message: Message):
    """
    Command to index all files from the file store channel using the user session.
    
    FIX: Changed user_client.is_running to user_client.is_connected for Pyrogram V2.
    """
    global IS_INDEXING_RUNNING
    global user_client

    if IS_INDEXING_RUNNING:
        await message.reply_text("❌ Note: The indexing process is currently running. Please wait until it is complete.")
        return

    if PRIVATE_FILE_STORE == -100:
        await message.reply_text("PRIVATE_FILE_STORE ID is not provided in ENV. Indexing is not possible.")
        return
    
    if not USER_SESSION_STRING or not user_client:
         await message.reply_text("❌ Indexing Error: **USER_SESSION_STRING** is missing. Please provide the user session string.")
         return

    IS_INDEXING_RUNNING = True 
    
    msg = await message.reply_text("🔑 Starting file indexing using the user session... This may take some time. (Check logs)")
    
    total_files_indexed = 0
    total_messages_processed = 0
    
    try:
        # FIX APPLIED HERE: Using is_connected for Pyrogram V2
        if not user_client.is_connected: 
            await user_client.start() 

        # Iterate over chat history of the file store channel
        async for chat_msg in user_client.get_chat_history(chat_id=PRIVATE_FILE_STORE): 
            total_messages_processed += 1
            file_id, file_name, file_object = get_file_info(chat_msg)
            
            if file_id and file_name:
                caption = chat_msg.caption.html if chat_msg.caption else None 
                
                try:
                    await db.files_col.update_one( 
                        {"file_id": file_id},
                        {
                            "$set": {
                                "title": file_name,
                                "caption": caption,
                                "file_id": file_id,
                                "chat_id": PRIVATE_FILE_STORE,
                                "message_id": chat_msg.id,
                                "media_type": file_object.__class__.__name__.lower()
                            }
                        },
                        upsert=True
                    )
                    total_files_indexed += 1
                    
                    if total_files_indexed % 50 == 0:
                         try:
                             await msg.edit_text(f"✅ Indexed Files: {total_files_indexed} / {total_messages_processed}")
                         except MessageNotModified:
                             pass 

                except Exception as db_error:
                    print(f"INDEX_DEBUG: DB WRITE error for file {file_name}: {db_error}")
            
        await msg.edit_text(f"🎉 Indexing complete! Total {total_files_indexed} files added or updated. ({total_messages_processed} messages checked)")
        
    except Exception as general_error:
        await msg.edit_text(f"❌ Indexing Error: {general_error}. Please check if the user account has access to the channel and the ID is correct.")
        
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

# Auto-filter and Copyright Handler (Global)
@app.on_message(filters.text & filters.incoming & ~filters.command(["start", "index", "dbcount"])) 
async def global_handler(client, message: Message):
    """Handles all incoming text messages: copyright deletion and auto-filter search."""
    query = message.text.strip()
    chat_id = message.chat.id
    chat_type = message.chat.type
    
    if IS_INDEXING_RUNNING:
        if message.from_user.id in ADMINS:
            await message.reply_text("Indexing is running. Please try again when the process is complete.")
        return
    
    # --- 1. COPYRIGHT MESSAGE DELETION LOGIC ---
    COPYRIGHT_KEYWORDS = ["copyright", "unauthorized", "DMCA", "piracy"] 
    is_copyright_message = any(keyword.lower() in query.lower() for keyword in COPYRIGHT_KEYWORDS)
    is_protected_chat = chat_id == PRIVATE_FILE_STORE or chat_id in ADMINS
    
    if is_copyright_message and is_protected_chat:
        try:
            await message.delete()
            # Send notification to the LOG_CHANNEL
            await client.send_message(LOG_CHANNEL, f"🚫 **Copyright message deleted!**\n\n**Chat ID:** `{chat_id}`\n**User:** {message.from_user.mention}\n**Message:** `{query}`")
            return
        except Exception as e:
            print(f"Error deleting copyright message in chat {chat_id}: {e}")
            return
            
    # --- 2. AUTO-FILTER SEARCH (ONLY IN GROUPS/CHANNELS) ---
    
    if chat_type == ChatType.PRIVATE:
        await message.reply_text("👋 To search for files, please go to a group or channel where I am an admin and type the name. Click the button there to get the file here.")
        return
        
    if chat_id == PRIVATE_FILE_STORE:
        return
        
    # --- SEARCH IN GROUPS AND CHANNELS (First Page) ---
    
    page = 1
    files, total_count = await get_file_details(query, page=page)
    
    if files:
        # Cache the original query linked to the message ID for pagination
        await db.cache_query(message.id, query)

        # Generate file and pagination buttons
        file_buttons = create_file_buttons(files, message.id, message.chat.id)
        pagination_buttons = create_pagination_buttons(page, total_count, message.id)
        
        # Combine all buttons
        buttons = file_buttons + pagination_buttons

        text = f"✅ **Results for {query}:**\n\nFound **{total_count}** matches. Click the button below to get the file. You will be redirected to DM."
        
        await message.reply_text(
            text=text,
            reply_markup=InlineKeyboardMarkup(buttons),
            disable_web_page_preview=True
        )
    else:
        pass

# --- CALLBACK QUERY HANDLER (PAGINATION) ---

@app.on_callback_query(filters.regex("^page_(prev|next)_"))
async def handle_pagination_callback(client: Client, callback: CallbackQuery):
    """Handles 'Next Page' and 'Previous Page' button clicks."""
    
    # Format: page_{action}_{page_num}_{original_message_id}
    try:
        _, action, page_str, original_msg_id_str = callback.data.split('_')
        new_page = int(page_str)
        original_msg_id = int(original_msg_id_str)
    except Exception as e:
        print(f"Error parsing pagination callback data: {e}")
        await callback.answer("❌ Invalid pagination data.", show_alert=True)
        return

    # 1. Get the cached search query
    query = await db.get_cached_query(original_msg_id)
    if not query:
        await callback.answer("❌ Search expired. Please search again.", show_alert=True)
        # Attempt to remove buttons if possible
        try:
             await callback.message.edit_reply_markup(reply_markup=None)
        except Exception:
             pass
        return

    # 2. Get the new set of files
    files, total_count = await get_file_details(query, page=new_page)
    
    if not files:
        # Should not happen if logic is correct, but handles edge case
        await callback.answer("❌ No results found on this page.", show_alert=True)
        return

    # 3. Regenerate all buttons for the new page
    file_buttons = create_file_buttons(files, original_msg_id, callback.message.chat.id)
    pagination_buttons = create_pagination_buttons(new_page, total_count, original_msg_id)
    buttons = file_buttons + pagination_buttons
    
    text = f"✅ **Results for {query}:**\n\nFound **{total_count}** matches. Click the button below to get the file. You will be redirected to DM."

    # 4. Edit the original message
    try:
        await callback.message.edit_text(
            text=text,
            reply_markup=InlineKeyboardMarkup(buttons),
            disable_web_page_preview=True
        )
        await callback.answer() # Dismiss the loading state
    except MessageNotModified:
        await callback.answer("Nothing to change.")
    except Exception as e:
        print(f"Error editing message for pagination: {e}")
        await callback.answer("❌ Failed to update results.", show_alert=True)
                
# --- CALLBACK QUERY HANDLER (Direct Redirection to DM via URL Answer) ---

@app.on_callback_query(filters.regex("^getfile_")) 
async def redirect_to_dm_handler(client, callback):
    """
    Handles the initial filter button click and directly redirects the user to DM 
    by answering the callback query with the deep link URL.
    """
    global BOT_USERNAME
    user_id = callback.from_user.id
    
    # callback data: getfile_{file_message_id}_{group_message_id}_{group_chat_id}
    data_parts = callback.data.split('_')
    
    # The payload for the deep link will be: file_{file_message_id}_{group_msg_id}_{group_chat_id}
    deep_link_payload = f"file_{data_parts[1]}_{data_parts[2]}_{data_parts[3]}"
    
    if not BOT_USERNAME:
        await callback.answer("❌ Bot username is not available. Please try again shortly.", show_alert=True)
        return

    # Deep link structure: t.me/BOT_USERNAME?start=payload
    deep_link = f"https://t.me/{BOT_USERNAME}?start={deep_link_payload}"
    
    # 1. FORCE SUB CHECK (if applicable)
    # Check if force sub is enabled AND the user is NOT an admin AND the user is NOT subscribed.
    if FORCE_SUB_CHANNEL and user_id not in ADMINS and not await is_subscribed(client, user_id, max_retries=2):
        join_button = [
            [InlineKeyboardButton("✅ Join Channel", url=f"https://t.me/{FORCE_SUB_CHANNEL.replace('@', '')}")],
        ]
        
        await callback.answer("✋ Please join the channel to get the file. (Click the button to join the channel)", show_alert=True)
        
        # Modify the message to show the Join button (user must re-click filter button after joining)
        await callback.message.edit_text(
            "🔑 **Mandatory Step:** You must join our channel.\n\n"
            "Click the button below to join the channel, then **return to the group and click the filter button again.**",
            reply_markup=InlineKeyboardMarkup(join_button)
        )
        return 
        
    # 2. SUBSCRIBED / NO FORCE SUB / ADMIN: Direct Redirection
    
    # Answer the callback with the deep link URL. This instantly redirects the user to the DM.
    try:
        await callback.answer(
            text="🔑 Redirecting to DM... Press Send on the /start message there.", 
            show_alert=False,
            url=deep_link # <-- CRITICAL: Direct redirection via URL
        )
    except Exception as e:
        print(f"Error answering callback with URL: {e}")
        await callback.answer("❌ Failed to redirect to DM. Please try again.", show_alert=True)
        return
    
    # Update the group message to confirm the action and remove the clickable button
    try:
        await callback.message.edit_text(
            "✅ **Redirected to DM!**\n\n"
            "Please go to the bot's private chat and press the **Send** button. The file will be sent immediately. (File will be deleted after 60s)",
            reply_markup=None # Remove buttons after redirection
        )
    except Exception as e:
         print(f"Error editing message after redirect: {e}")

# --- MAIN ENTRY POINT ---

if __name__ == "__main__":
    if WEBHOOK_URL_BASE:
        # Use uvicorn to serve the FastAPI app (for Render deployment)
        # CRITICAL: 'main' is used here assuming the file is named 'main.py'
        uvicorn.run("main:api_app", host="0.0.0.0", port=PORT, log_level="info")
    else:
        # Use app.run() for local polling mode testing
        print("Starting Pyrogram in polling mode...")
        # Note: In polling mode, we start the client first then run checks.
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
