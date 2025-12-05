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
import httpx

# Load variables from the .env file
load_dotenv()

# --- GLOBAL STATUS FLAG ---
IS_INDEXING_RUNNING = False

# --- CONFIG VARIABLES ---
API_ID = int(os.environ.get("API_ID", 12345))
API_HASH = os.environ.get("API_HASH", "YOUR_API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "YOUR_BOT_TOKEN")
PRIVATE_FILE_STORE = int(os.environ.get("PRIVATE_FILE_STORE", -100)) # Channel ID where files are stored
LOG_CHANNEL = int(os.environ.get("LOG_CHANNEL", -100))
USER_SESSION_STRING = os.environ.get("USER_SESSION_STRING", None) 

# IMDb Integration
OMDB_API_KEY = os.environ.get("OMDB_API_KEY", None)
OMDB_API_URL = "http://www.omdbapi.com/"

# Admin list
ADMINS = []
admin_env = os.environ.get("ADMINS", "")
if admin_env:
    ADMINS = [int(admin.strip()) for admin in admin_env.split(',') if admin.strip().isdigit()]

DATABASE_URL = os.environ.get("DATABASE_URL", "mongodb://localhost:27017")
FORCE_SUB_CHANNEL = os.environ.get("FORCE_SUB_CHANNEL", None) # Force subscribe channel (e.g., @MyChannel)

# Webhook details
WEBHOOK_URL_BASE = os.environ.get("WEBHOOK_URL_BASE", None)
PORT = int(os.environ.get("PORT", 8080))
WEBHOOK_PATH = f"/{BOT_TOKEN}"

# --- MONGODB SETUP ---

class Database:
    """Handles database operations."""
    def __init__(self, uri: str, database_name: str):
        self._client = AsyncIOMotorClient(uri)
        self.db = self._client[database_name]
        self.files_col = self.db["files"]

    async def get_all_files(self) -> List[Dict[str, Any]]:
        """Returns all file entries as a list."""
        cursor = self.files_col.find({})
        return await cursor.to_list(length=None)

    async def find_one(self, query: Dict[str, Any]) -> Dict[str, Any] | None:
        return await self.files_col.find_one(query)

    async def update_one(self, query: Dict[str, Any], update: Dict[str, Any], upsert: bool = False):
        await self.files_col.update_one(query, update, upsert=upsert)

# Database instance
db = Database(DATABASE_URL, "AutoFilterBot")

# --- OMDb/IMDb HELPERS (Moved to the top) ---

def get_file_name_for_search(file_title: str) -> str:
    """
    Extracts a cleaner title from the file name for OMDb/IMDb search, 
    removing common resolution, quality, or group tags.
    """
    if not file_title:
        return ""
        
    # Remove common file extensions and special characters (keeping spaces)
    clean_title = file_title.rsplit('.', 1)[0]
    # Replace common separators with spaces
    clean_title = re.sub(r'[\(\)\[\]\{\}\-_\.]+', ' ', clean_title).strip()
    
    # Remove common video quality/encoding tags aggressively
    clean_title = re.sub(r'\b(s\d{1,2}e\d{1,2}|s\d{1,2}|e\d{1,2})\b', '', clean_title, flags=re.IGNORECASE) # Season/Episode tags
    clean_title = re.sub(r'\b(\d{3,4}p|4k|hd|bluray|webrip|x\d{3}|aac|mp4|mkv|avi|dual audio|eng sub|sub eng|tamil dubbed|hevc|x265|x264|v2|official|yts|p2p|fars)\b', 
                         '', clean_title, flags=re.IGNORECASE)
    
    # Attempt to capture the year if present
    match_year = re.search(r'(\s(19|20)\d{2}\s)', clean_title)
    year = match_year.group(1).strip() if match_year else None
    
    # Split and remove short words/single characters unless they are crucial
    parts = clean_title.split()
    final_parts = []
    
    for part in parts:
        # Ignore common noise words but keep title integrity
        if part.lower() in ["the", "a", "an", "and", "in", "of", "with"] and len(parts) > 3:
            continue
        # Stop if a likely year is encountered
        if year and part == year and len(final_parts) > 1:
            break
        
        if len(part.strip()) > 1:
            final_parts.append(part.strip())
        
    final_search_term = " ".join(final_parts).strip()
    
    # Fallback if cleaning was too aggressive
    if len(final_search_term) < 3:
        return file_title.rsplit('.', 1)[0].strip()
        
    return final_search_term


async def fetch_omdb_data(title: str) -> Dict[str, str]:
    """
    Fetches movie/series information from OMDb API based on the title.
    Returns a dictionary of relevant info or an empty dict on failure.
    """
    if not OMDB_API_KEY:
        print("WARNING: OMDB_API_KEY not set. Skipping IMDb info fetch.")
        return {}

    search_title = get_file_name_for_search(title)
    if not search_title:
        print("DEBUG: OMDb search skipped because search_title is empty.")
        return {}
        
    params = {
        'apikey': OMDB_API_KEY,
        't': search_title, 
        'plot': 'short'    
    }

    print(f"DEBUG: Attempting OMDb search for query: '{search_title}'")
    
    try:
        async with httpx.AsyncClient() as client:
            # Set a retry mechanism for transient network issues
            for attempt in range(3):
                try:
                    response = await client.get(OMDB_API_URL, params=params, timeout=7)
                    response.raise_for_status() 
                    break # Success
                except httpx.RequestError as e:
                    if attempt < 2:
                        print(f"OMDb Request failed (Attempt {attempt+1}), retrying: {e}")
                        await asyncio.sleep(2 ** attempt)
                    else:
                        raise e # Re-raise if final attempt fails
            
            data = response.json()
            
            if data.get('Response') == 'True':
                imdb_info = {
                    'Title': data.get('Title', 'N/A'),
                    'Year': data.get('Year', 'N/A'),
                    'Genre': data.get('Genre', 'N/A'),
                    'Rating': data.get('imdbRating', 'N/A'),
                    'Plot': data.get('Plot', 'No plot summary available.'),
                    'Poster': data.get('Poster', 'N/A')
                }
                print(f"DEBUG: Successfully fetched IMDb info for {imdb_info['Title']}")
                return imdb_info
            else:
                print(f"DEBUG: OMDb search failed for title '{search_title}'. Reason: {data.get('Error', 'Unknown Error')}")
                return {}
                
    except httpx.HTTPStatusError as e:
        print(f"ERROR: HTTP error during OMDb fetch (Status {e.response.status_code}). Check OMDB_API_KEY or network.")
        return {}
    except httpx.RequestError as e:
        print(f"ERROR: Network error or all retries failed during OMDb fetch: {e}")
        return {}
    except Exception as e:
        print(f"ERROR: Unexpected error during OMDb fetch: {e}")
        return {}

# --- PYROGRAM CLIENT ---
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

# --- BOT INSTANCE (GLOBAL PYROGRAM CLIENT) ---
app = AutoFilterBot()

# --- HELPERS ---

async def is_subscribed(client, user_id, max_retries=3, delay=1):
    """
    Checks if the user is a member of the force subscribe channel, with a robust retry mechanism
    to mitigate Telegram membership cache delays.
    """
    if not FORCE_SUB_CHANNEL:
        return True
    
    for attempt in range(max_retries):
        try:
            member = await client.get_chat_member(FORCE_SUB_CHANNEL, user_id) 
            if member.status in ["member", "administrator", "creator"]:
                return True
            
            return False 
        
        except UserNotParticipant:
            if attempt < max_retries - 1:
                await asyncio.sleep(delay) 
            else:
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
    """
    Searches for file details in the database using advanced tokenization and Regex.
    """
    
    print(f"DEBUG: Search query: '{query}'")

    # 1. Prepare for Advanced Search: Tokenize the query
    words = [word.strip() for word in re.split(r'\W+', query) if len(query.strip()) > 2 and len(word.strip()) > 1]
    
    # --- Search Logic 1: All tokens must be present (Order agnostic) ---
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

    # --- Search Logic 2: Simple Phrase Match (Fallback/Boost) ---
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
    
    print(f"DEBUG: Found {len(files)} files for query '{query}'")
    
    return files

# Function to extract file details
def get_file_info(message: Message) -> tuple[str, str, Union[Document, Video, Audio, None]]:
    """Finds file_id, file_name, and file_object from a message."""
    if message.document and message.document.file_name:
        return message.document.file_id, message.document.file_name, message.document
    if message.video:
        file_name = message.caption.strip() if message.caption else f"Video_{message.id}"
        if message.video.file_name: # Use actual file name if available
             file_name = message.video.file_name
        return message.video.file_id, file_name, message.video
    if message.audio:
        file_name = message.audio.file_name or message.audio.title or f"Audio_{message.id}"
        return message.audio.file_id, file_name, message.audio
    return None, None, None

# --- START COMMAND ---
@app.on_message(filters.command("start") & filters.private)
async def start_command(client, message: Message):
    """Handles the /start command in a private chat with custom text."""
    global IS_INDEXING_RUNNING
    
    if IS_INDEXING_RUNNING:
        await message.reply_text("Indexing is currently running. Please wait until it is complete.")
        return
        
    # English Start message
    start_text = (
        "🍿 **Hello! I'm your Auto Filter Bot!** 🎬\n\n"
        "🔎 **How to Use Me:**\n"
        "1. Type the name of the movie/series you need in any group or channel where I am an Admin.\n"
        "2. Click the result button that appears.\n"
        "3. The file will be sent to you in this **Private Chat (DM)!**\n\n"
        "⚠️ **Important Note:** To receive files, you must have established a connection with the bot by sending `/start` once in this private chat. Then, click the button in the group.\n\n"
        "🔗 **Our Channels:**\n"
        "°•➤ @Mala_Television\n"
        "°•➤ @Mala_Tv\n"
        "°•➤ @MalaTvbot ™️\n\n"
        "**Admin Commands:**\n"
        "• `/index` - To index all files in the channel.\n"
        "• `/dbcount` - To check the number of files in the database."
    )
    
    await message.reply_text(start_text)
    print(f"DEBUG: Received start command from ID {message.from_user.id}")

@app.on_message(filters.command("index") & filters.user(ADMINS))
async def index_command(client, message: Message):
    """
    Command to index all files from the file store channel using the user session.
    """
    global IS_INDEXING_RUNNING
    
    if IS_INDEXING_RUNNING:
        await message.reply_text("❌ WARNING: Indexing process is currently running. Wait for the current job to complete.")
        return

    if PRIVATE_FILE_STORE == -100:
        await message.reply_text("PRIVATE_FILE_STORE ID is not provided in ENV. Indexing is not possible.")
        return
    
    if not USER_SESSION_STRING:
         await message.reply_text("❌ Indexing Error: **USER_SESSION_STRING** is not provided in ENV. Please generate and provide a user session string.")
         return

    IS_INDEXING_RUNNING = True 
    
    msg = await message.reply_text("🔑 Starting full automatic file indexing using user session... This may take time. (Check logs)")
    
    total_files_indexed = 0
    total_messages_processed = 0
    
    # --- INITIALIZE USER CLIENT FOR INDEXING ---
    user_client = Client(
        "indexer_session",
        api_id=API_ID,
        api_hash=API_HASH,
        session_string=USER_SESSION_STRING, 
    )

    try:
        await user_client.start() 

        # Iterate through all messages using Pyrogram's get_chat_history
        async for chat_msg in user_client.get_chat_history(chat_id=PRIVATE_FILE_STORE): 
            total_messages_processed += 1
            file_id, file_name, file_object = get_file_info(chat_msg)
            
            if file_id and file_name:
                caption = chat_msg.caption.html if chat_msg.caption else None 
                
                try:
                    # Save/update file details in MongoDB
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
                             await msg.edit_text(f"✅ Indexed files: {total_files_indexed} / {total_messages_processed}")
                             print(f"INDEX_DEBUG: Successfully indexed {file_name}") 
                         except MessageNotModified:
                             pass 

                except Exception as db_error:
                    print(f"INDEX_DEBUG: DB WRITE error for file {file_name}: {db_error}")
            else:
                if chat_msg.text:
                    print(f"INDEX_DEBUG: Skipping text message {chat_msg.id}")
                else:
                    print(f"INDEX_DEBUG: Skipping message {chat_msg.id} - Not a supported file type (Doc/Vid/Aud).")
            
        # Final report after indexing is complete
        await msg.edit_text(f"🎉 Indexing complete! Total {total_files_indexed} files added or updated. ({total_messages_processed} messages processed)")
        
    except Exception as general_error:
        await msg.edit_text(f"❌ Indexing Error: {general_error}. Please check if the user account has access to the channel and the ID is correct.")
        print(f"INDEX_DEBUG: Fatal indexing error: {general_error}")
        
    finally:
        await user_client.stop() 
        IS_INDEXING_RUNNING = False

@app.on_message(filters.command("dbcount") & filters.user(ADMINS))
async def dbcount_command(client, message: Message):
    """Command to check the total number of files in the database."""
    try:
        count = await db.files_col.count_documents({})
        await message.reply_text(f"📊 **Database File Count:**\nTotal indexed files: **{count}**")
    except Exception as e:
        await message.reply_text(f"❌ Error fetching database count: {e}")

# Auto-filter and Copyright Handler (Global)
@app.on_message(filters.text & filters.incoming & ~filters.command(["start", "index", "dbcount"])) 
async def global_handler(client, message: Message):
    """Handles all incoming text messages: copyright deletion and auto-filter search."""
    query = message.text.strip()
    chat_id = message.chat.id
    chat_type = message.chat.type
    
    # Check if indexing is running
    global IS_INDEXING_RUNNING
    if IS_INDEXING_RUNNING:
        # Only reply to admins if indexing is running, ignore others to reduce spam
        if message.from_user.id in ADMINS:
            await message.reply_text("Indexing is currently running. Please try again when the process is complete.")
        return
    
    # --- 1. COPYRIGHT MESSAGE DELETION LOGIC ---
    COPYRIGHT_KEYWORDS = ["copyright", "unauthorized", "DMCA", "piracy"] 
    is_copyright_message = any(keyword.lower() in query.lower() for keyword in COPYRIGHT_KEYWORDS)
    is_protected_chat = chat_id == PRIVATE_FILE_STORE or chat_id in ADMINS
    
    if is_copyright_message and is_protected_chat:
        try:
            await message.delete()
            # Log the deletion
            await client.send_message(LOG_CHANNEL, f"🚫 **Copyright Message Deleted!**\n\n**Chat ID:** `{chat_id}`\n**User:** {message.from_user.mention}\n**Message:** `{query}`")
            return
        except Exception as e:
            print(f"Error deleting copyright message in chat {chat_id}: {e}")
            return
            
    # --- 2. AUTO-FILTER SEARCH (ONLY IN GROUPS/CHANNELS) ---
    
    if chat_type == ChatType.PRIVATE:
        await message.reply_text("👋 To search for files, type the name in any group or channel where I'm an admin. Click the button, and the file will be sent here in DM.")
        return
        
    if chat_id == PRIVATE_FILE_STORE:
        return
        
    # --- SEARCH IN GROUPS AND CHANNELS ---
    
    files = await get_file_details(query)
    
    if files:
        # Files found: Send inline buttons (Modernized)
        text = f"✅ Search results for **{query}**:\n\nClick the button below to get the file. It will be sent to your private chat."
        buttons = []
        for file in files:
            media_icon = {"document": "📄", "video": "🎬", "audio": "🎵"}.get(file.get('media_type', 'document'), '❓')
            file_name_clean = file.get("title", "File").rsplit('.', 1)[0].strip() 
            
            # Use a clear, modern button text
            buttons.append([
                InlineKeyboardButton(
                    text=f"{media_icon} {file_name_clean}",
                    callback_data=f"getmsg_{file.get('message_id')}" 
                )
            ])
        
        if len(files) == 10:
             buttons.append([InlineKeyboardButton("More Results ➡️", url="https://t.me/your_search_group")]) 

        sent_message = await message.reply_text(
            text=text,
            reply_markup=InlineKeyboardMarkup(buttons),
            disable_web_page_preview=True
        )
        
        print(f"DEBUG: Sent filter results for search '{query}'. Starting autodelete timer.")
        
        # --- AUTODELETE LOGIC (after 60 seconds) ---
        await asyncio.sleep(60)
        try:
            await sent_message.delete()
        except Exception as e:
            print(f"Error during autodelete: {e}")
    else:
        # Optional: Reply if nothing found to indicate the search completed
        pass
                
# --- CALLBACK QUERY HANDLER (INLINE BUTTON CLICK) ---

async def handle_send_file(client, user_id, message_id, delete_message_id=None, delete_chat_id=None):
    """Core function to fetch details, get IMDb, and forward/copy the file."""
    
    file = await db.files_col.find_one({"message_id": message_id}) 
    
    if not file:
        await client.send_message(user_id, "❌ This file has been removed from the database.")
        return False, "File removed."

    file_title = file.get('title', 'Requested File')
    
    # 1. Fetch IMDb Data & Construct Caption
    imdb_info = await fetch_omdb_data(file_title)
    
    caption = f"🎬 **{file_title}**\n\n"
    
    if imdb_info and imdb_info.get('Title') != 'N/A' and imdb_info.get('Plot'):
        caption = f"**🍿 {imdb_info.get('Title')}** ({imdb_info.get('Year')})\n"
        caption += f"🌟 **IMDb Rating:** {imdb_info.get('Rating')}\n"
        caption += f"🎭 **Genre:** {imdb_info.get('Genre')}\n\n"
        caption += f"📖 **Plot Summary:** {imdb_info.get('Plot')}\n\n"
        caption += f"🔗 **Filname:** `{file_title}`\n\n"
        caption += "👇 **The file is provided below** 👇"
    else:
        caption += "❌ **IMDb information not available**\n"
        caption += f"🔗 **Filename:** `{file_title}`\n\n"
        caption += "👇 **The file is provided below** 👇"


    # 2. Send Poster (if available)
    poster_sent = False
    
    if imdb_info and imdb_info.get('Poster') and imdb_info['Poster'] != 'N/A':
        try:
            await client.send_photo(
                chat_id=user_id,
                photo=imdb_info['Poster'],
                caption=caption
            )
            caption = None 
            poster_sent = True
        except Exception as e:
            print(f"Error sending poster photo to user {user_id}: {e}. Falling back to text caption and file forwarding.")
    
    # 3. Copy the File (Fix for Forward Restriction)
    try:
        # If poster wasn't sent, send the caption text first before the file
        if not poster_sent and caption:
             await client.send_message(user_id, caption)
             caption = None 

        # *** CRITICAL FIX: Use copy_message instead of forward_messages ***
        await client.copy_message(
            chat_id=user_id, 
            from_chat_id=file['chat_id'],
            message_ids=file['message_id']
        )
        
        # Optional: Delete the original group filter message if needed (handled in check_sub_handler)
        if delete_message_id and delete_chat_id:
            try:
                await client.delete_messages(delete_chat_id, delete_message_id)
            except Exception as e:
                print(f"Error deleting original group message: {e}")

        return True, "File sent successfully."
        
    except RPCError as e:
        # Catches common Pyrogram errors, including when user has not started chat (BOT_BLOCKED)
        if "BOT_BLOCKED" in str(e) or "PEER_ID_INVALID" in str(e):
            error_msg = "❌ **File could not be sent!** ❌\n\nYou have not given the bot permission to DM (Private Chat). Please send the `/start` command privately to this bot first, and then try again."
            await client.send_message(user_id, error_msg)
            return False, error_msg
        
        print(f"Error copying file to user {user_id}: {e}")
        error_msg = f"❌ An error occurred while sending the file: {e}. Please contact the admin."
        await client.send_message(user_id, error_msg)
        return False, error_msg
    except Exception as e:
        print(f"Unexpected error copying file to user {user_id}: {e}")
        error_msg = "❌ An unexpected error occurred while sending the file."
        await client.send_message(user_id, error_msg)
        return False, error_msg


@app.on_callback_query(filters.regex("^getmsg_")) 
async def send_file_handler(client, callback):
    """Handles the initial inline button click from the group/channel."""
    
    user_id = callback.from_user.id
    message_id_str = callback.data.split("_")[1]
    message_id = int(message_id_str)
    
    is_admin = user_id in ADMINS
    
    # 1. ADMIN CHECK
    if is_admin:
        await callback.answer("Admin detected. Copying file...", show_alert=False)
        await handle_send_file(client, user_id, message_id)
        try:
             # Delete the inline search message for admins immediately
            await callback.message.delete()
        except Exception:
            pass # Ignore deletion errors
        return
        
    # 2. FORCE SUB CHECK
    if FORCE_SUB_CHANNEL and not await is_subscribed(client, user_id, max_retries=3):
        join_button = [
            [InlineKeyboardButton("✅ Join Channel", url=f"https://t.me/{FORCE_SUB_CHANNEL.replace('@', '')}")],
            # Pass group chat and message ID to delete it later
            [InlineKeyboardButton("👍 Joined, Send File", callback_data=f"checksub_{message_id}_{callback.message.id}_{callback.message.chat.id}")] 
        ]
        
        await callback.answer("✋ To get the file, please join the channel. More details in DM.", show_alert=True)
        try:
            # Send the Force Sub message to DM
            await client.send_message(
                chat_id=user_id,
                text=f"🔑 You must join the channel {FORCE_SUB_CHANNEL} to get this file. Please join and then click the button below.\n\n**Note:** You must have sent /start in DM to receive the file.",
                reply_markup=InlineKeyboardMarkup(join_button)
            )
            await callback.answer("Click the button that appeared in your Private Chat (DM).", show_alert=True)
        except Exception as e:
            # This is the critical error: User blocked bot or never started chat
            print(f"Error sending force sub message to user {user_id}: {e}")
            await callback.answer("❌ File could not be sent! Please send /start to the bot first, then try again.", show_alert=True)
        return 

    # 3. SUBSCRIBED / NO FORCE SUB: Direct send
    await callback.answer("Sending file to DM...", show_alert=False)
    success, result_message = await handle_send_file(
        client, 
        user_id, 
        message_id, 
        delete_message_id=callback.message.id, 
        delete_chat_id=callback.message.chat.id
    )
    
    if success:
        await callback.answer("File received in your DM.", show_alert=False)
    else:
        # If sending failed (e.g., BOT_BLOCKED), don't show the generic message in the group
        pass

            
# --- NEW CALLBACK HANDLER FOR FORCE SUB CHECK IN DM ---
@app.on_callback_query(filters.regex("^checksub_")) 
async def check_sub_handler(client, callback):
    """Handles the 'Check Subscription and Send File' button in the private chat."""
    
    user_id = callback.from_user.id
    
    # Data is split into: [checksub, message_id, group_message_id, group_chat_id]
    data_parts = callback.data.split("_")
    message_id = int(data_parts[1])
    group_message_id = int(data_parts[2])
    group_chat_id = int(data_parts[3])

    # Re-check subscription
    if FORCE_SUB_CHANNEL and not await is_subscribed(client, user_id, max_retries=2): 
        await callback.answer("❌ You have not joined the channel. Please try again.", show_alert=True)
        return
    
    # Subscription SUCCESS: Now send the file (reusing core logic)
    await callback.answer("✅ Subscription verified. Sending file...", show_alert=False)
    
    success, result_message = await handle_send_file(
        client, 
        user_id, 
        message_id, 
        delete_message_id=group_message_id, 
        delete_chat_id=group_chat_id
    )
    
    if success:
        # Edit the original "Join Channel" message to say success in DM
        await callback.message.edit_text("✅ Subscription verified. File sent successfully.")
    else:
        # If handle_send_file failed, it has already sent an error message to the user.
        await callback.message.edit_text(f"❌ An error occurred while sending the file.\n\n_{result_message}_")


# --- RENDER WEBHOOK SETUP (FastAPI) ---

# --- STARTUP/SHUTDOWN LIFECYCLE ---
async def startup_initial_checks():
    """Checks to run on startup."""
    print("Performing initial startup checks...")
    
    # 1. Database check
    try:
        files_count = await db.files_col.count_documents({})
        print(f"Database check complete. Found {files_count} files in the database.")
    except Exception as e:
        print(f"WARNING: Database connection failed on startup: {e}")
        
    # 2. Force Sub Admin check (CRITICAL)
    if FORCE_SUB_CHANNEL:
        print(f"FORCE_SUB_CHANNEL is set to: {FORCE_SUB_CHANNEL}. Verifying bot administration status...")
        # A simplified check without client starting/stopping
        if not USER_SESSION_STRING:
             print("WARNING: USER_SESSION_STRING not available. Skipping Force Sub Admin check.")
        
    # 3. OMDB Key check
    if not OMDB_API_KEY:
        print("----------------------------------------------------------------------")
        print("⚠️ WARNING: OMDB_API_KEY is NOT set. IMDb information will not be shown.")
        print("----------------------------------------------------------------------")
    else:
        print("✅ OMDB_API_KEY is set.")


@asynccontextmanager
async def lifespan(web_app: FastAPI):
    # Run checks only once when the bot starts
    await startup_initial_checks()
    
    if WEBHOOK_URL_BASE:
        await app.start() 
        await app.set_webhook(url=f"{WEBHOOK_URL_BASE}{WEBHOOK_PATH}")
        print(f"Webhook successfully set: {WEBHOOK_URL_BASE}{WEBHOOK_PATH}")
    else:
        await app.start()
        print("Starting in polling mode (for local testing only).")
        
    yield
    await app.stop()
    print("Application stopped.")

# FastAPI instance
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
