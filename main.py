import os
import re
import asyncio
from pyrogram import Client, filters
from pyrogram.enums import MessagesFilter 
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, Document, Video, Audio
from pyrogram.errors import UserNotParticipant
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from typing import List, Dict, Any, Union
from fastapi import FastAPI, Request, Response
from contextlib import asynccontextmanager
from http import HTTPStatus
import uvicorn

# Loading variables from .env file (for local testing)
load_dotenv()

# --- Config Variables ---
API_ID = int(os.environ.get("API_ID", 12345))
API_HASH = os.environ.get("API_HASH", "YOUR_API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "YOUR_BOT_TOKEN")
# Channel ID where the files are stored (Private Channel)
PRIVATE_FILE_STORE = int(os.environ.get("PRIVATE_FILE_STORE", -100)) 
# Channel ID for logging copyright issues or bot activity
LOG_CHANNEL = int(os.environ.get("LOG_CHANNEL", -100))

# Creating ADMINS list
ADMINS = []
admin_env = os.environ.get("ADMINS", "")
if admin_env:
    # Ensure all listed IDs are integers
    ADMINS = [int(admin.strip()) for admin in admin_env.split(',') if admin.strip().isdigit()]

DATABASE_URL = os.environ.get("DATABASE_URL", "mongodb://localhost:27017")
# Force Subscribe Channel username or ID
FORCE_SUB_CHANNEL = os.environ.get("FORCE_SUB_CHANNEL", None)

# Webhook Details
WEBHOOK_URL_BASE = os.environ.get("WEBHOOK_URL_BASE", None)
PORT = int(os.environ.get("PORT", 8080))
WEBHOOK_PATH = f"/{BOT_TOKEN}"

# --- MongoDB Setup ---

class Database:
    """Handles database operations."""
    def __init__(self, uri: str, database_name: str):
        self._client = AsyncIOMotorClient(uri)
        self.db = self._client[database_name]
        self.files_col = self.db["files"]

    async def get_all_files(self) -> List[Dict[str, Any]]:
        """Retrieves all documents from the files collection."""
        cursor = self.files_col.find({})
        return await cursor.to_list(length=None)

    async def find_one(self, query: Dict[str, Any]) -> Dict[str, Any] | None:
        """Finds a single document matching the query."""
        return await self.files_col.find_one(query)

    async def update_one(self, query: Dict[str, Any], update: Dict[str, Any], upsert: bool = False):
        """Updates or inserts a document."""
        await self.files_col.update_one(query, update, upsert=upsert)

# Database instance
db = Database(DATABASE_URL, "AutoFilterBot")

# --- Pyrogram Client ---
class AutoFilterBot(Client):
    """Custom Pyrogram Client for the bot."""
    def __init__(self):
        super().__init__(
            "AutoFilterBot",
            api_id=API_ID,
            api_hash=API_HASH,
            bot_token=BOT_TOKEN,
            plugins=dict(root="plugins"), # Assuming plugins directory exists
            sleep_threshold=30
        )

# --- Bot Instance (Global Pyrogram Client) ---
app = AutoFilterBot()

# --- Helpers ---

async def is_subscribed(client: Client, user_id: int) -> bool:
    """Checks if the user is a member of the Force Subscribe Channel."""
    if not FORCE_SUB_CHANNEL:
        return True
    try:
        member = await client.get_chat_member(FORCE_SUB_CHANNEL, user_id) 
        # Check for standard member, administrator, or creator status
        if member.status in ["member", "administrator", "creator"]:
            return True
        return False
    except UserNotParticipant:
        # User is definitely not subscribed
        return False
    except Exception as e:
        print(f"Error checking subscription: {e}")
        # Default to True on API error to not unnecessarily block users
        return True 

async def get_file_details(query: str) -> List[Dict[str, Any]]:
    """Searches for file information from the database."""
    # Case-insensitive search across title and caption
    cursor = db.files_col.find({ 
        "$or": [
            {"title": {"$regex": query, "$options": "i"}},
            {"caption": {"$regex": query, "$options": "i"}}
        ]
    }).limit(10)
    
    files = await cursor.to_list(length=10)
    return files

def get_file_info(message: Message) -> tuple[Union[str, None], Union[str, None], Union[Document, Video, Audio, None]]:
    """Finds file_id, file_name, and file_object from the message."""
    if message.document:
        return message.document.file_id, message.document.file_name, message.document
    if message.video:
        # file_name is often unavailable for video messages, so use caption or a default name
        file_name = message.caption.strip() if message.caption else f"Video_{message.id}"
        # If the video has a title/file_name property, use it
        if message.video.file_name:
             file_name = message.video.file_name
        return message.video.file_id, file_name, message.video
    if message.audio:
        # Use file_name, title, or a default name for audio
        file_name = message.audio.file_name or message.audio.title or f"Audio_{message.id}"
        return message.audio.file_id, file_name, message.audio
        
    # You can also add Photos, GIFs, etc. here
    return None, None, None

# --- Handlers ---

@app.on_message(filters.command("start") & filters.private)
async def start_command(client: Client, message: Message):
    """Handles the /start command with a new model and inline buttons."""
    
    bot_info = await client.get_me()
    
    welcome_message = (
        f"🤖 **Hello, I am {bot_info.first_name}!**\n\n"
        "I am an **Auto-Filter Bot** designed to help groups manage and retrieve files efficiently. "
        "Add me to your group, and I'll automatically respond to search queries by linking files from my private store.\n\n"
        "**Key Features:**\n"
        "✨ Automatic file filtering in groups.\n"
        "📂 Centralized private file storage.\n"
        "🔒 Optional Force Subscription to a channel.\n"
        "🛡️ Admin-only file indexing and content moderation.\n\n"
        "**Commands:**\n"
        "• `/start` - Get this welcome message.\n"
        "• `/index` - (Admin Only) Index files from the private store."
    )
    
    # Define buttons
    buttons = [
        [
            InlineKeyboardButton("➕ Add Me to a Group", url=f"https://t.me/{bot_info.username}?startgroup=true")
        ],
        [
            # Placeholder links - update these with your actual channel/developer links
            InlineKeyboardButton("📢 Support Channel", url="https://t.me/your_support_channel"),
            InlineKeyboardButton("👨‍💻 Developer", url="https://t.me/your_developer_username")
        ]
    ]

    await message.reply_text(
        welcome_message,
        reply_markup=InlineKeyboardMarkup(buttons),
        disable_web_page_preview=True,
        parse_mode="markdown"
    )

@app.on_message(filters.command("index") & filters.user(ADMINS))
async def index_command(client: Client, message: Message):
    """Command for admins to index files in the file store channel."""
    if PRIVATE_FILE_STORE == -100:
        await message.reply_text("`PRIVATE_FILE_STORE` ID is not provided in the ENV variable. Indexing is not possible.")
        return

    msg = await message.reply_text("Starting to index files...")
    
    total_files = 0
    
    # Major change: Searching for all media types using ALL
    async for chat_msg in client.search_messages(chat_id=PRIVATE_FILE_STORE, filter=MessagesFilter.ALL):
        
        file_id, file_name, file_object = get_file_info(chat_msg)
        
        if file_id and file_name:
            # If caption exists, use HTML format
            caption = chat_msg.caption.html if chat_msg.caption else None 
            
            # Adding file information to the database
            await db.files_col.update_one( 
                {"file_id": file_id},
                {
                    "$set": {
                        "title": file_name,
                        "caption": caption,
                        "file_id": file_id,
                        "chat_id": PRIVATE_FILE_STORE,
                        "message_id": chat_msg.id,
                        # Can store the file type for filtering
                        "media_type": file_object.__class__.__name__.lower()
                    }
                },
                upsert=True
            )
            total_files += 1
            
            if total_files % 100 == 0:
                 await msg.edit_text(f"✅ Indexed Files: {total_files}")
                 
    await msg.edit_text(f"🎉 Indexing complete! Total {total_files} files added.")


# Auto-Filter Handler
@app.on_message(filters.text & filters.private | filters.group & filters.text & filters.incoming & ~filters.command(["start", "index"])) 
async def auto_filter_handler(client: Client, message: Message):
    """Searches for filter files when text messages arrive."""
    query = message.text.strip()
    
    # 1. Force Subscribe Check
    is_private = message.chat.type == "private"
    if not is_private or await is_subscribed(client, message.from_user.id):
        
        # 2. Copyright message delete logic (only works in admin groups/private chats)
        COPYRIGHT_KEYWORDS = ["copyright", "unauthorized", "DMCA", "piracy", "abuse", "illegal content"] 
        if message.chat.type in ["group", "supergroup", "private"] and message.from_user.id in ADMINS and any(keyword.lower() in query.lower() for keyword in COPYRIGHT_KEYWORDS):
             try:
                 # Delete the message if an admin sends a suspicious message
                 await message.delete() 
                 await client.send_message(LOG_CHANNEL, 
                                           f"🚫 **Copyright/Abuse Message Removed!**\n\n**Chat ID:** `{message.chat.id}`\n**User:** {message.from_user.mention}\n**Message:** `{query}`")
                 return
             except Exception as e:
                 print(f"Error deleting copyright message: {e}")
        
        # 3. Auto-Filter Search
        files = await get_file_details(query)
        
        if files:
            # Send inline buttons if file is found
            text = f"Here are the files related to your search for **{query}**:\n\n"
            buttons = []
            for file in files:
                # Displaying file name and media type
                media_icon = {"document": "📄", "video": "🎬", "audio": "🎶"}.get(file.get('media_type', 'document'), '❓')
                # Excluding Extension
                file_name = file.get("title", "File").rsplit('.', 1)[0].strip() 
                
                buttons.append([
                    InlineKeyboardButton(
                        text=f"{media_icon} {file_name}",
                        callback_data=f"getfile_{file.get('file_id')}" 
                    )
                ])
            
            # Add a 'More Results' button if the limit was reached
            if len(files) == 10:
                 # Add a support group link here
                 buttons.append([InlineKeyboardButton("More Results", url="https://t.me/your_search_group")]) 

            await message.reply_text(
                text=text,
                reply_markup=InlineKeyboardMarkup(buttons),
                disable_web_page_preview=True,
                parse_mode="markdown"
            )

    elif is_private:
        # If not Force Subscribed
        if not FORCE_SUB_CHANNEL: return # Do nothing if channel doesn't exist
        
        join_button = [
            [InlineKeyboardButton("Join Channel", url=f"https://t.me/{FORCE_SUB_CHANNEL.replace('@', '')}")]
        ]
        await message.reply_text(
            f"You must join our channel first to get the files.",
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
            await callback.answer("An error occurred while sending the file. Check if the bot has access.", show_alert=True)
            print(f"File forward error: {e}")
    else:
        await callback.answer("File removed from the database.", show_alert=True)
    
    try:
        # Delete the inline message after sending the file
        await callback.message.delete()
    except Exception as e:
        print(f"Error deleting inline message: {e}")

# --- Render Webhook Setup (FastAPI for a scalable deployment) ---

# --- STARTUP/SHUTDOWN Lifecycle ---
async def startup_initial_checks():
    """Checks to run on startup."""
    print("Running initial startup checks...")
    try:
        files_count = len(await db.get_all_files())
        print(f"Database check completed. Found {files_count} files in the database.")
    except Exception as e:
        print(f"Warning: Database check failed during startup: {e}")


@asynccontextmanager
async def lifespan(web_app: FastAPI):
    await startup_initial_checks()
    
    if WEBHOOK_URL_BASE:
        await app.start() 
        # Set webhook for cloud deployment (e.g., Render)
        await app.set_webhook(url=f"{WEBHOOK_URL_BASE}{WEBHOOK_PATH}")
        print(f"Webhook set successfully to: {WEBHOOK_URL_BASE}{WEBHOOK_PATH}")
    else:
        await app.start()
        print("Starting in Polling Mode (for local testing only).")
        
    yield
    await app.stop()
    print("Application stopped.")

# FastAPI instance (Global variable 'api_app' used in uvicorn command)
api_app = FastAPI(lifespan=lifespan)

# Webhook endpoint for Telegram updates
@api_app.post(WEBHOOK_PATH)
async def process_update(request: Request):
    """Receiving Telegram updates."""
    try:
        req = await request.json()
        await app.process_update(req)
        return Response(status_code=HTTPStatus.OK)
    except Exception as e:
        print(f"Error processing update: {e}")
        return Response(status_code=HTTPStatus.INTERNAL_SERVER_ERROR)

# Health Check endpoint for Render
@api_app.get("/")
async def health_check():
    """Health Check for Render."""
    return {"status": "ok"}

# --- Main Entry Point ---

if __name__ == "__main__":
    if WEBHOOK_URL_BASE:
        # For cloud deployment with webhook
        uvicorn.run("autofilter_bot:api_app", host="0.0.0.0", port=PORT, log_level="info")
    else:
        # For local testing in polling mode
        print("Starting Pyrogram in Polling Mode...")
        asyncio.run(startup_initial_checks())
        app.run()
