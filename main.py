import os 
import re
import asyncio
import json
from pyrogram import Client, filters
from pyrogram.enums import ChatType
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, Document, Video, Audio
from pyrogram.errors import UserNotParticipant, MessageNotModified, ChatAdminRequired, RPCError
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from typing import List, Dict, Any, Union
from fastapi import FastAPI, Request, Response 
from contextlib import asynccontextmanager
from http import HTTPStatus
import uvicorn

# Load variables from the .env file
load_dotenv()

# --- GLOBAL STATUS FLAGS AND VARIABLES ---
IS_INDEXING_RUNNING = False
BOT_USERNAME: str = "" # To be set on startup

# --- CUSTOM CAPTION FOR SENT FILES ---
NEW_CAPTION = (
    "°•➤@Mala_Television 🍿\n"
    "°•➤@Mala_Tv\n"
    "°•➤@MalaTvbot ™️\n\n"
    "🙂🙂"
)

# --- CONFIG VARIABLES ---
API_ID = int(os.environ.get("API_ID", 12345))
API_HASH = os.environ.get("API_HASH", "YOUR_API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "YOUR_BOT_TOKEN")
PRIVATE_FILE_STORE = int(os.environ.get("PRIVATE_FILE_STORE", -100)) 
LOG_CHANNEL = int(os.environ.get("LOG_CHANNEL", -100))
USER_SESSION_STRING = os.environ.get("USER_SESSION_STRING", None) 

# Admin list
ADMINS = []
admin_env = os.environ.get("ADMINS", "")
if admin_env:
    ADMINS = [int(admin.strip()) for admin in admin_env.split(',') if admin.strip().isdigit()]

DATABASE_URL = os.environ.get("DATABASE_URL", "mongodb://localhost:27017")
FORCE_SUB_CHANNEL = os.environ.get("FORCE_SUB_CHANNEL", None) 

# Webhook details for Render/Cloud deployment
WEBHOOK_URL_BASE = os.environ.get("WEBHOOK_URL_BASE", None)
PORT = int(os.environ.get("PORT", 8080))
WEBHOOK_PATH = f"/{BOT_TOKEN}"

# --- MONGODB SETUP ---

class Database:
    """Handles database operations for storing file indexes."""
    def __init__(self, uri: str, database_name: str):
        self._client = AsyncIOMotorClient(uri)
        self.db = self._client[database_name]
        self.files_col = self.db["files"]

    async def find_one(self, query: Dict[str, Any]) -> Union[Dict[str, Any], None]:
        """Finds a single document matching the query."""
        return await self.files_col.find_one(query)

    async def update_one(self, query: Dict[str, Any], update: Dict[str, Any], upsert: bool = False):
        """Updates a single document. Inserts if upsert is True and no match is found."""
        await self.files_col.update_one(query, update, upsert=upsert)

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
        if app.is_running:
            bot_info = await app.get_me()
            BOT_USERNAME = bot_info.username
            print(f"Bot Username fetched: @{BOT_USERNAME}")
        else:
             print("Bot client is not running yet, skipping BOT_USERNAME fetch.")
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
            member = await client.get_chat_member(FORCE_SUB_CHANNEL, user_id) 
            if member.status in ["member", "administrator", "creator"]:
                return True
            return False 
        except UserNotParticipant:
            return False 
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

async def get_file_details(query: str):
    """Searches for file details in the database using advanced tokenization and Regex."""
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
        
    cursor = db.files_col.find(search_query).limit(10)
    files = await cursor.to_list(length=10)
    
    return files

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

# --- CORE FILE DELIVERY LOGIC ---

async def handle_send_file(client, user_id, message_id):
    """
    Core function to copy/forward the file content with fallback.
    It now schedules the deletion of the sent message after 60 seconds.
    """
    
    file = await db.files_col.find_one({"message_id": message_id}) 
    
    if not file:
        try:
            await client.send_message(user_id, "❌ ക്ഷമിക്കണം, ഈ ഫയൽ ഡാറ്റാബീസിൽ നിന്ന് നീക്കം ചെയ്തിരിക്കുന്നു. (Sorry, file removed.)")
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
                if not user_client.is_running:
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
        error_msg = ("❌ **ക്ഷമിക്കണം, ഫയൽ അയക്കാൻ കഴിഞ്ഞില്ല!** ❌\n\n"
                     "പ്രധാനമായും 2 കാരണങ്ങൾ ഉണ്ടാകാം:\n"
                     "1. നിങ്ങൾ എന്നെ ബ്ലോക്ക് ചെയ്തിരിക്കാം. എങ്കിൽ അൺബ്ലോക്ക് ചെയ്യുക.\n"
                     "2. നിങ്ങളുടെ പ്രൈവറ്റ് ചാറ്റ് സെറ്റിംഗ്‌സിൽ ഫയലുകൾ ലഭിക്കാൻ അനുമതി നൽകിയിട്ടില്ല.\n\n"
                     "ദയവായി **അൺബ്ലോക്ക് ചെയ്ത ശേഷം **/start** അയച്ച് വീണ്ടും ശ്രമിക്കുക.")
        try:
            await client.send_message(user_id, error_msg)
        except Exception:
            pass 
            
        return False, error_msg
        
    except Exception as e:
        print(f"Unexpected error copying file to user {user_id}: {e}")
        error_msg = "❌ ഫയൽ അയക്കുന്നതിൽ ഒരു അപ്രതീക്ഷിത പിശക് സംഭവിച്ചു. (Failed to copy file)"
        try:
            await client.send_message(user_id, error_msg)
        except Exception:
            pass
        return False, error_msg


# --- START COMMAND (Handles /start and /start payload) ---
@app.on_message(filters.command("start") & filters.private)
async def start_command(client, message: Message):
    """
    Handles the /start command in a private chat. 
    Checks for a deep-link payload to deliver a file.
    """
    global IS_INDEXING_RUNNING
    
    if IS_INDEXING_RUNNING:
        await message.reply_text("ഇൻഡെക്സിംഗ് ഇപ്പോൾ നടന്നുകൊണ്ടിരിക്കുകയാണ്. ഇത് പൂർത്തിയാകും വരെ ദയവായി കാത്തിരിക്കുക.")
        return
    
    # Check for deep-link payload: /start file_messageId_groupMsgId_groupId
    if len(message.command) > 1:
        payload = message.command[1]
        
        if payload.startswith("file_"):
            try:
                # payload is expected to be file_{message_id}_{group_msg_id}_{group_chat_id}
                _, message_id_str, group_msg_id_str, group_chat_id_str = payload.split('_')
                message_id = int(message_id_str)
                # Group message details are still included in the payload but no longer used for deletion.
                # group_msg_id = int(group_msg_id_str)
                # group_chat_id = int(group_chat_id_str)
                
                await message.reply_text("✅ ഡെലിവറി ആരംഭിക്കുന്നു. ദയവായി കാത്തിരിക്കുക...")
                
                success, _ = await handle_send_file(
                    client, 
                    message.from_user.id, 
                    message_id
                    # No delete_message_id/delete_chat_id passed, as group message deletion is disabled.
                )
                
                if success:
                    await message.reply_text("🎉 ഫയൽ വിജയകരമായി അയച്ചു! ഇത് 60 സെക്കൻഡിന് ശേഷം ഡിലീറ്റ് ആകും. അടുത്ത ഫയലിനായി ഗ്രൂപ്പിൽ പോകുക.")
                return

            except Exception as e:
                print(f"Error processing deep-link payload: {e}")
                await message.reply_text("❌ ഫയൽ ഡെലിവറി പരാജയപ്പെട്ടു. ലിങ്ക് തകരാറിലായിരിക്കാം. ഗ്രൂപ്പിലെ ബട്ടണിൽ വീണ്ടും ക്ലിക്ക് ചെയ്യുക.")
                return

    # Standard /start message
    start_text = (
        "ഹായ്! ഞാനാണ് നിങ്ങളുടെ **ഓട്ടോ ഫിൽട്ടർ ബോട്ട്.** 🤩\n\n"
        "🔎 **എന്നെ എങ്ങനെ ഉപയോഗിക്കാം?**\n"
        "1. ഞാൻ അഡ്മിനായുള്ള ഏതെങ്കിലും ഗ്രൂപ്പിലോ ചാനലിലോ നിങ്ങൾക്കാവശ്യമുള്ള സിനിമയുടെയോ സീരീസിൻ്റെയോ പേര് ടൈപ്പ് ചെയ്യുക.\n"
        "2. അവിടെ വരുന്ന റിസൾട്ട് ബട്ടണിൽ ക്ലിക്ക് ചെയ്യുക. \n"
        "3. **'ഫയൽ ലഭിക്കാൻ ഇവിടെ ക്ലിക്കുചെയ്യുക'** എന്ന ബട്ടൺ വരും. അതിൽ ക്ലിക്കുചെയ്ത് DM-ൽ **/start** അയക്കുക.\n"
        "4. ഫയൽ ഉടൻ നിങ്ങളുടെ ഈ പ്രൈവറ്റ് ചാറ്റിലേക്ക് (DM) അയച്ചുതരും! 🎉 (ശ്രദ്ധിക്കുക: ഫയൽ 60 സെക്കൻഡിന് ശേഷം ഡിലീറ്റ് ആകും)\n\n"
        "🔗 **ഞങ്ങളുടെ ചാനലുകൾ:**\n"
        "°•➤ @Mala_Television\n"
        "°•➤ @Mala_Tv\n"
        "°•➤ @MalaTvbot ™️\n\n"
        "**അഡ്മിൻ കമാൻഡുകൾ (Admin Commands):**\n"
        "• `/index` - ചാനലിലെ എല്ലാ ഫയലുകളും ഇൻഡെക്സ് ചെയ്യാൻ.\n"
        "• `/dbcount` - ഡാറ്റാബേസിലെ ഫയലുകളുടെ എണ്ണം പരിശോധിക്കാൻ."
    )
    
    await message.reply_text(start_text)

# --- ADMIN COMMANDS (Indexing, etc. remains the same) ---

@app.on_message(filters.command("index") & filters.user(ADMINS))
async def index_command(client, message: Message):
    """
    Command to index all files from the file store channel using the user session.
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
        if not user_client.is_running:
            await user_client.start() 

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
            await client.send_message(LOG_CHANNEL, f"🚫 **Copyright message deleted!**\n\n**Chat ID:** `{chat_id}`\n**User:** {message.from_user.mention}\n**Message:** `{query}`")
            return
        except Exception as e:
            print(f"Error deleting copyright message in chat {chat_id}: {e}")
            return
            
    # --- 2. AUTO-FILTER SEARCH (ONLY IN GROUPS/CHANNELS) ---
    
    if chat_type == ChatType.PRIVATE:
        await message.reply_text("👋 ഫയലുകൾ തിരയാനായി, ദയവായി ഞാൻ അഡ്മിനായുള്ള ഒരു ഗ്രൂപ്പിലോ ചാനലിലോ പോയി പേര് ടൈപ്പ് ചെയ്യുക. അവിടെ വരുന്ന ബട്ടൺ ക്ലിക്ക് ചെയ്താൽ ഫയൽ ഇവിടെ ലഭിക്കും.")
        return
        
    if chat_id == PRIVATE_FILE_STORE:
        return
        
    # --- SEARCH IN GROUPS AND CHANNELS ---
    
    files = await get_file_details(query)
    
    if files:
        # Files found: Send inline buttons
        text = f"✅ **{query} എന്നതിനായുള്ള റിസൾട്ടുകൾ:**\n\nഫയൽ ലഭിക്കാൻ താഴെയുള്ള ബട്ടണിൽ ക്ലിക്ക് ചെയ്യുക. എന്നിട്ട് DM-ൽ **/start** അയക്കുക."
        buttons = []
        # --- START BUTTON GENERATION LOOP ---
        for file in files:
            media_icon = {"document": "📄", "video": "🎬", "audio": "🎵"}.get(file.get('media_type', 'document'), '❓')
            file_name_clean = file.get("title", "File").rsplit('.', 1)[0].strip() 
            
            # Use callback_data to hold the message ID and its original location details
            # Format: getfile_{file_message_id}_{group_message_id}_{group_chat_id}
            callback_data = f"getfile_{file.get('message_id')}_{message.id}_{message.chat.id}"
            buttons.append([
                InlineKeyboardButton(
                    text=f"{media_icon} {file_name_clean}",
                    callback_data=callback_data
                )
            ])
        # --- END BUTTON GENERATION LOOP ---
        
        if len(files) == 10:
             buttons.append([InlineKeyboardButton("കൂടുതൽ റിസൾട്ടുകൾ ➡️", url="https://t.me/your_search_group")]) 

        sent_message = await message.reply_text(
            text=text,
            reply_markup=InlineKeyboardMarkup(buttons),
            disable_web_page_preview=True
        )
        
        # NOTE: Group message auto-delete after 60 seconds is now DISABLED as per user request.
    else:
        pass
                
# --- CALLBACK QUERY HANDLER (Redirects to DM via Deep Link) ---

@app.on_callback_query(filters.regex("^getfile_")) 
async def redirect_to_dm_handler(client, callback):
    """
    Handles the initial filter button click and redirects the user to DM using a deep link.
    """
    global BOT_USERNAME
    user_id = callback.from_user.id
    
    # callback data: getfile_{file_message_id}_{group_message_id}_{group_chat_id}
    data_parts = callback.data.split('_')
    
    # The payload for the deep link will be: file_{file_message_id}_{group_message_id}_{group_chat_id}
    deep_link_payload = f"file_{data_parts[1]}_{data_parts[2]}_{data_parts[3]}"
    
    if not BOT_USERNAME:
        await callback.answer("❌ ബോട്ട് യൂസർ നെയിം ലഭ്യമല്ല. ദയവായി കുറച്ച് സമയത്തിന് ശേഷം വീണ്ടും ശ്രമിക്കുക.", show_alert=True)
        return

    deep_link = f"https://t.me/{BOT_USERNAME}?start={deep_link_payload}"
    
    # 1. FORCE SUB CHECK (if applicable)
    if FORCE_SUB_CHANNEL and not await is_subscribed(client, user_id, max_retries=2):
        join_button = [
            [InlineKeyboardButton("✅ ചാനലിൽ ജോയിൻ ചെയ്യുക", url=f"https://t.me/{FORCE_SUB_CHANNEL.replace('@', '')}")],
            [InlineKeyboardButton("👍 ജോയിൻ ചെയ്തു, ഫയലിനായി DM-ൽ വരിക", url=deep_link)]
        ]
        
        await callback.answer("✋ ഫയൽ ലഭിക്കാൻ ചാനലിൽ ജോയിൻ ചെയ്യുക. (Click the button to join the channel)", show_alert=True)
        
        # Modify the message to show the Join/DeepLink buttons
        await callback.message.edit_text(
            "🔑 **നിർബന്ധമായും ചെയ്യേണ്ട കാര്യം:** നിങ്ങൾ ഞങ്ങളുടെ ചാനലിൽ ജോയിൻ ചെയ്തിരിക്കണം.\n\n"
            "താഴെയുള്ള ബട്ടൺ ക്ലിക്കുചെയ്ത് ചാനലിൽ ജോയിൻ ചെയ്യുക. അതിനുശേഷം വീണ്ടും DM-ലേക്ക് വരിക.",
            reply_markup=InlineKeyboardMarkup(join_button)
        )
        return 
        
    # 2. SUBSCRIBED / NO FORCE SUB: Direct Deep Link
    
    deep_link_button = [
        [InlineKeyboardButton("🔑 ഫയൽ ലഭിക്കാൻ ഇവിടെ ക്ലിക്കുചെയ്യുക", url=deep_link)]
    ]
    
    await callback.answer("ഫയൽ ലഭിക്കാൻ DM-ൽ **/start** അയക്കുക.", show_alert=False)
    
    # Modify the message to show the DeepLink button
    await callback.message.edit_text(
        "🎉 **ഫയൽ ലഭിക്കാൻ ഒരു ക്ലിക്ക് കൂടി!**\n\n"
        "താഴെയുള്ള ബട്ടൺ ക്ലിക്കുചെയ്ത് DM-ൽ എത്തി **/start** അയക്കുക. ഫയൽ ഉടൻ ലഭിക്കും.",
        reply_markup=InlineKeyboardMarkup(deep_link_button)
    )

# --- MAIN ENTRY POINT ---

if __name__ == "__main__":
    if WEBHOOK_URL_BASE:
        # Use uvicorn to serve the FastAPI app (for Render deployment)
        uvicorn.run("main:api_app", host="0.0.0.0", port=PORT, log_level="info")
    else:
        # Use app.run() for local polling mode testing
        print("Starting Pyrogram in polling mode...")
        asyncio.run(startup_initial_checks())
        app.run()

