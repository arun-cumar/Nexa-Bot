import os
import re
import asyncio
from pyrogram import Client, filters
# Imports pyrogram.enums
from pyrogram.enums import MessagesFilter 
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import UserNotParticipant
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, Request, Response
from contextlib import asynccontextmanager
from http import HTTPStatus
import uvicorn

# Loads variables from .env file (for local testing)
load_dotenv()

# --- Config Variables ---
# Provides default values if environment variables are not set
# Ensures API_ID, BOT_TOKEN are integers
API_ID = int(os.environ.get("API_ID", 12345))
API_HASH = os.environ.get("API_HASH", "YOUR_API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "YOUR_BOT_TOKEN")
# Ensures PRIVATE_FILE_STORE, LOG_CHANNEL are integers
PRIVATE_FILE_STORE = int(os.environ.get("PRIVATE_FILE_STORE", -100))
LOG_CHANNEL = int(os.environ.get("LOG_CHANNEL", -100))

# Creates the ADMINS list
ADMINS: List[int] = []
admin_env = os.environ.get("ADMINS", "")
if admin_env:
    ADMINS = [int(admin.strip()) for admin in admin_env.split(',') if admin.strip().isdigit()]

DATABASE_URL = os.environ.get("DATABASE_URL", "mongodb://localhost:27017")
FORCE_SUB_CHANNEL = os.environ.get("FORCE_SUB_CHANNEL", None)

# Webhook Details
WEBHOOK_URL_BASE = os.environ.get("WEBHOOK_URL_BASE", None)
PORT = int(os.environ.get("PORT", 8080))
WEBHOOK_PATH = f"/{BOT_TOKEN}"

# --- MongoDB Setup ---

class Database:
    """Handles database operations."""
    def __init__(self, uri: str, database_name: str):
        # Initializes the database client here
        self._client = AsyncIOMotorClient(uri)
        self.db = self._client[database_name]
        self.files_col = self.db["files"] # Collection to store file information

    async def get_all_files(self) -> List[Dict[str, Any]]:
        """Returns all file entries from the database as a list."""
        # Uses to_list() to convert the Cursor from Motor to a list.
        cursor = self.files_col.find({})
        return await cursor.to_list(length=None)

    async def find_one(self, query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Searches for a single document."""
        return await self.files_col.find_one(query)

    async def update_one(self, query: Dict[str, Any], update: Dict[str, Any], upsert: bool = False):
        """Updates or inserts a document."""
        await self.files_col.update_one(query, update, upsert=upsert)

# Database instance
db = Database(DATABASE_URL, "AutoFilterBot")

# --- Pyrogram Client ---
class AutoFilterBot(Client):
    def __init__(self):
        super().__init__(
            "AutoFilterBot",
            api_id=API_ID,
            api_hash=API_HASH,
            bot_token=BOT_TOKEN,
            plugins=dict(root="plugins"), # Can be removed if no plugins are used
            sleep_threshold=30 # Important: for low resource usage
        )

# --- Bot Instance (Global Pyrogram Client) ---
app = AutoFilterBot()

# --- Helpers ---

async def is_subscribed(client: Client, user_id: int) -> bool:
    """Checks if the user is a member of the force subscribe channel."""
    if not FORCE_SUB_CHANNEL:
        return True
    try:
        # get_chat_member requires user ID, not a message object
        member = await client.get_chat_member(FORCE_SUB_CHANNEL, user_id) 
        if member.status in ["member", "administrator", "creator"]:
            return True
        return False
    except UserNotParticipant:
        return False
    except Exception as e:
        print(f"Error checking subscription: {e}")
        # Allows proceeding by returning True if errors occur
        return True 

async def get_file_details(query: str) -> List[Dict[str, Any]]:
    """Searches for file information from the database."""
    # 'i' case-insensitive search
    # Searches in file title and file caption
    cursor = db.files_col.find({ 
        "$or": [
            {"title": {"$regex": query, "$options": "i"}},
            {"caption": {"$regex": query, "$options": "i"}}
        ]
    }).limit(10)
    
    files = await cursor.to_list(length=10)
    return files

# --- Handlers ---

@app.on_message(filters.command("start") & filters.private)
async def start_command(client: Client, message: Message):
    await message.reply_text(
        "👋 Hi! I'm an Auto-Filter Bot. Add me to your group, and I will send the files searched in the group. Contact the developer for more information."
    )

@app.on_message(filters.command("index") & filters.user(ADMINS))
async def index_command(client: Client, message: Message):
    """Command for admins to index files in the file store channel."""
    if PRIVATE_FILE_STORE == -100:
        await message.reply_text("PRIVATE_FILE_STORE ID is not provided in the ENV variable. Indexing is not possible.")
        return

    msg = await message.reply_text("Starting to index files...")
    
    total_files = 0
    # FIX: Uses MessagesFilter.DOCUMENT instead of filter="document"
    async for chat_msg in client.search_messages(chat_id=PRIVATE_FILE_STORE, filter=MessagesFilter.DOCUMENT):
        if chat_msg.document:
            file_id = chat_msg.document.file_id
            file_name = chat_msg.document.file_name
            # Uses HTML format for caption if it exists
            caption = chat_msg.caption.html if chat_msg.caption else None 
            
            # Adds file information to the database (using title)
            await db.files_col.update_one( 
                {"file_id": file_id},
                {
                    "$set": {
                        "title": file_name,
                        "caption": caption,
                        "file_id": file_id,
                        "chat_id": PRIVATE_FILE_STORE,
                        "message_id": chat_msg.id,
                    }
                },
                upsert=True # Inserts a new file if it doesn't exist
            )
            total_files += 1
            
            if total_files % 100 == 0:
                 # Updates status after 100 files
                 await msg.edit_text(f"✅ Indexed Files: {total_files}")
                 
    await msg.edit_text(f"🎉 Indexing completed! Total {total_files} files added.")


# Auto-Filter Handler
@app.on_message(filters.text & filters.private | filters.group & filters.text & filters.incoming & ~filters.command(["start", "index"])) 
async def auto_filter_handler(client: Client, message: Message):
    """Searches for filtered files when a text message arrives."""
    query = message.text.strip()
    
    # 1. Force Subscribe Check
    is_private = message.chat.type == "private"
    if not is_private or await is_subscribed(client, message.from_user.id):
        
        # 2. Copyright Message Delete Logic (Only works in admin groups/private chats if chat ID is in ADMINS)
        COPYRIGHT_KEYWORDS = ["copyright", "unauthorized", "DMCA", "piracy", "പകർപ്പവകാശം", "അനുമതിയില്ലാതെ"] 
        if message.chat.type in ["group", "supergroup"] and message.chat.id in ADMINS and any(keyword.lower() in query.lower() for keyword in COPYRIGHT_KEYWORDS):
             try:
                 await message.delete()
                 await client.send_message(LOG_CHANNEL, f"🚫 **Copyright Message Removed!**\n\n**Chat ID:** `{message.chat.id}`\n**User:** {message.from_user.mention}\n**Message:** `{query}`")
                 return
             except Exception as e:
                 print(f"Error deleting copyright message: {e}")
        
        # 3. Auto-Filter Search
        files = await get_file_details(query)
        
        if files:
            # Sends inline buttons if file is found
            text = f"Here are the files related to your search **{query}**:\n\n"
            buttons = []
            for file in files:
                file_name = file.get("title", "File").rsplit('.', 1)[0].strip() # Removes extension
                
                buttons.append([
                    InlineKeyboardButton(
                        text=file_name,
                        callback_data=f"getfile_{file.get('file_id')}" 
                    )
                ])
            
            # Adds a 'More' button
            if len(files) == 10:
                 buttons.append([InlineKeyboardButton("More Results", url="https://t.me/your_search_group")]) # Add a support group link

            await message.reply_text(
                text=text,
                reply_markup=InlineKeyboardMarkup(buttons),
                disable_web_page_preview=True
            )

    elif is_private:
        # If not force subscribed
        if not FORCE_SUB_CHANNEL: return # Do nothing if channel is not set
        
        join_button = [
            [InlineKeyboardButton("Join Channel", url=f"https://t.me/{FORCE_SUB_CHANNEL.replace('@', '')}")]
        ]
        await message.reply_text(
            f"To get files, you must first join our channel.",
            reply_markup=InlineKeyboardMarkup(join_button)
        )

# --- Callback Query Handler (Inline Button Click) ---

@app.on_callback_query(filters.regex("^getfile_"))
async def send_file_handler(client: Client, callback):
    """Sends the file when the button is clicked."""
    
    # Force Subscribe Check
    if FORCE_SUB_CHANNEL and not await is_subscribed(client, callback.from_user.id):
        await callback.answer("Join the channel to get the file.", show_alert=True)
        return

    file_id = callback.data.split("_")[1]
    file = await db.files_col.find_one({"file_id": file_id}) 
    
    if file:
        try:
            # Forwards the file from the original store channel
            await client.forward_messages(
                chat_id=callback.message.chat.id,
                from_chat_id=file['chat_id'],
                message_ids=file['message_id']
            )
            await callback.answer("File sent.", show_alert=False)
        except Exception as e:
            # Errors often occur when forwarding (due to private channels)
            await callback.answer("An error occurred while sending the file. Check if the bot has access.", show_alert=True)
            print(f"File forward error: {e}")
    else:
        await callback.answer("File has been removed from the database.", show_alert=True)
    
    # Deletes the message showing the search results (Optional)
    try:
        await callback.message.delete()
    except Exception as e:
        print(f"Error deleting inline message: {e}")

# --- Render Webhook Setup (FastAPI for a scalable deployment) ---

# --- STARTUP/SHUTDOWN Lifecycle ---
async def startup_initial_checks():
    """Checks to perform on startup."""
    print("Running initial startup checks...")
    try:
        # DB connection test
        files_count = len(await db.get_all_files())
        print(f"Database check completed. Found {files_count} files in the database.")
    except Exception as e:
        print(f"Warning: Database check failed during startup: {e}")


@asynccontextmanager
async def lifespan(web_app: FastAPI):
    # 'web_app' is the FastAPI instance. The Pyrogram client is the global variable 'app'.

    # 1. Runs essential startup checks
    await startup_initial_checks()
    
    # 2. Starts the Pyrogram client
    if WEBHOOK_URL_BASE:
        # To run via Webhook on Render: Start the Pyrogram client
        await app.start() 
        
        # Set up Webhook using the Pyrogram client
        await app.set_webhook(url=f"{WEBHOOK_URL_BASE}{WEBHOOK_PATH}")
        print(f"Webhook set successfully to: {WEBHOOK_URL_BASE}{WEBHOOK_PATH}")
    else:
        # Starts in Polling mode for local testing (This part won't run on Render)
        await app.start()
        print("Starting in Polling Mode (for local testing only).")
        
    yield
    # 3. Stops the Bot
    await app.stop() # Stops the Pyrogram client (global 'app')
    print("Application stopped.")

# FastAPI instance (Global variable 'api_app' used in uvicorn command)
api_app = FastAPI(lifespan=lifespan)

# Webhook endpoint for Telegram updates
@api_app.post(WEBHOOK_PATH)
async def process_update(request: Request):
    """Receives Telegram updates."""
    try:
        req = await request.json()
        await app.process_update(req) # Processes the Pyrogram update
        return Response(status_code=HTTPStatus.OK)
    except Exception as e:
        print(f"Error processing update: {e}")
        return Response(status_code=HTTPStatus.INTERNAL_SERVER_ERROR)

# Health Check endpoint for Render
@api_app.get("/")
async def health_check():
    """Render's Health Check."""
    return {"status": "ok"}

# --- Main Entry Point ---

if __name__ == "__main__":
    if WEBHOOK_URL_BASE:
        # To run in Webhook mode on Render (uvicorn main:api_app)
        uvicorn.run("main:api_app", host="0.0.0.0", port=PORT, log_level="info")
    else:
        # Polling mode for local testing
        print("Starting Pyrogram in Polling Mode...")
        asyncio.run(startup_initial_checks())
        app.run()
