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

# .env ഫയലിൽ നിന്ന് വേരിയബിളുകൾ ലോഡ് ചെയ്യുന്നു (ലോക്കൽ ടെസ്റ്റിങ്ങിന്)
load_dotenv()

# --- Config Variables ---
API_ID = int(os.environ.get("API_ID", 12345))
API_HASH = os.environ.get("API_HASH", "YOUR_API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "YOUR_BOT_TOKEN")
PRIVATE_FILE_STORE = int(os.environ.get("PRIVATE_FILE_STORE", -100))
LOG_CHANNEL = int(os.environ.get("LOG_CHANNEL", -100))

# ADMINS ലിസ്റ്റ് ഉണ്ടാക്കുന്നു
ADMINS = []
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
    """ഡാറ്റാബേസ് പ്രവർത്തനങ്ങൾ കൈകാര്യം ചെയ്യുന്നു."""
    def __init__(self, uri: str, database_name: str):
        self._client = AsyncIOMotorClient(uri)
        self.db = self._client[database_name]
        self.files_col = self.db["files"]

    async def get_all_files(self) -> List[Dict[str, Any]]:
        """ഡാറ്റാബേസിലെ എല്ലാ ഫയൽ എൻട്രികളും ലിസ്റ്റ് ആയി തിരികെ നൽകുന്നു."""
        cursor = self.files_col.find({})
        return await cursor.to_list(length=None)

    async def find_one(self, query: Dict[str, Any]) -> Dict[str, Any] | None:
        return await self.files_col.find_one(query)

    async def update_one(self, query: Dict[str, Any], update: Dict[str, Any], upsert: bool = False):
        await self.files_col.update_one(query, update, upsert=upsert)

# ഡാറ്റാബേസ് ഇൻസ്റ്റൻസ്
db = Database(DATABASE_URL, "AutoFilterBot")

# --- Pyrogram Client ---
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

# --- Bot Instance (Global Pyrogram Client) ---
app = AutoFilterBot()

# --- Helpers ---

async def is_subscribed(client, user_id):
    """ഫോഴ്സ് സബ്സ്ക്രൈബ് ചാനലിൽ യൂസർ അംഗമാണോ എന്ന് പരിശോധിക്കുന്നു."""
    if not FORCE_SUB_CHANNEL:
        return True
    try:
        member = await client.get_chat_member(FORCE_SUB_CHANNEL, user_id) 
        if member.status in ["member", "administrator", "creator"]:
            return True
        return False
    except UserNotParticipant:
        print("DEBUG: User not participant in force sub channel.")
        return False
    except Exception as e:
        print(f"Error checking subscription: {e}")
        return True 

async def get_file_details(query):
    """ഡാറ്റാബേസിൽ നിന്ന് ഫയൽ വിവരങ്ങൾ തിരയുന്നു."""
    
    # DEBUG: തിരയുന്ന വാക്ക് ലോഗിൽ കാണിക്കുന്നു
    print(f"DEBUG: Searching for query: '{query}'")

    cursor = db.files_col.find({ 
        "$or": [
            {"title": {"$regex": query, "$options": "i"}},
            {"caption": {"$regex": query, "$options": "i"}}
        ]
    }).limit(10)
    
    files = await cursor.to_list(length=10)
    
    # DEBUG: കണ്ടെത്തിയ ഫയലുകളുടെ എണ്ണം ലോഗിൽ കാണിക്കുന്നു
    print(f"DEBUG: Found {len(files)} files for query: '{query}'")
    
    return files

# --- Handlers ---

@app.on_message(filters.command("start") & filters.private)
async def start_command(client, message: Message):
    await message.reply_text(
        "👋 ഹായ്! ഞാൻ ഒരു ഓട്ടോ-ഫിൽട്ടർ ബോട്ടാണ്. എന്നെ നിങ്ങളുടെ ഗ്രൂപ്പിൽ ചേർത്താൽ, ഗ്രൂപ്പിൽ തിരയുന്ന ഫയലുകൾ ഞാൻ അയച്ചുതരും. കൂടുതൽ വിവരങ്ങൾക്ക് ഡെവലപ്പറെ ബന്ധപ്പെടുക."
    )

@app.on_message(filters.command("dbcount") & filters.user(ADMINS))
async def db_count_command(client, message: Message):
    """ഡാറ്റാബേസിൽ എത്ര ഫയലുകൾ ഉണ്ടെന്ന് പരിശോധിക്കുന്നു."""
    try:
        count_message = await message.reply_text("ഡാറ്റാബേസ് കൗണ്ട് എടുക്കുന്നു, ദയവായി കാത്തിരിക്കുക...")
        files_count = await db.files_col.count_documents({})
        await count_message.edit_text(f"📊 ഡാറ്റാബേസിൽ നിലവിൽ ഇൻഡക്സ് ചെയ്ത ഫയലുകളുടെ എണ്ണം: **{files_count}**")
    except Exception as e:
        await message.reply_text(f"❌ ഡാറ്റാബേസ് കണക്ഷൻ പിശക് സംഭവിച്ചു: {e}")

def get_file_info(message: Message) -> tuple[str, str, Union[Document, Video, Audio, None]]:
    """മെസ്സേജിൽ നിന്ന് file_id, file_name, file_object എന്നിവ കണ്ടെത്തുന്നു."""
    # Note: message.document.file_name ഇല്ലെങ്കിൽ അത് ഒഴിവാക്കാൻ
    if message.document and message.document.file_name:
        return message.document.file_id, message.document.file_name, message.document
    if message.video:
        # വീഡിയോക്ക് file_name ഇല്ലെങ്കിൽ caption അല്ലെങ്കിൽ id ഉപയോഗിക്കുന്നു
        file_name = message.caption.strip() if message.caption else f"Video_{message.id}"
        return message.video.file_id, file_name, message.video
    if message.audio:
        # ഓഡിയോക്ക് file_name/title ഇല്ലെങ്കിൽ id ഉപയോഗിക്കുന്നു
        file_name = message.audio.file_name or message.audio.title or f"Audio_{message.id}"
        return message.audio.file_id, file_name, message.audio
    return None, None, None

@app.on_message(filters.command("index") & filters.user(ADMINS))
async def index_command(client, message: Message):
    """അഡ്മിൻമാർക്ക് ഫയൽ സ്റ്റോർ ചാനലിലെ ഫയലുകൾ ഇൻഡക്സ് ചെയ്യാനുള്ള കമാൻഡ്."""
    if PRIVATE_FILE_STORE == -100:
        await message.reply_text("PRIVATE_FILE_STORE ID ENV വേരിയബിളിൽ നൽകിയിട്ടില്ല. ഇൻഡക്സിംഗ് സാധ്യമല്ല.")
        return

    msg = await message.reply_text("ഫയലുകൾ ഇൻഡക്സ് ചെയ്യാൻ തുടങ്ങുന്നു... (ലോഗുകൾ പരിശോധിക്കുക)")
    
    total_files_indexed = 0
    total_messages_processed = 0
    
    try:
        # filter=MessagesFilter.ALL ഒഴിവാക്കി. കാരണം അതാണ് പിശകിന് കാരണം.
        # filter ആർഗ്യുമെൻ്റ് ഇല്ലാതെ, എല്ലാ സന്ദേശങ്ങളും (ടെക്സ്റ്റ്, മീഡിയ) fetch ചെയ്യും.
        async for chat_msg in client.search_messages(chat_id=PRIVATE_FILE_STORE, limit=1000):
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
                         await msg.edit_text(f"✅ ഇൻഡക്സ് ചെയ്ത ഫയലുകൾ: {total_files_indexed} / {total_messages_processed}")
                         # വിജയകരമായി ഇൻഡെക്സ് ചെയ്ത ഫയലിൻ്റെ ലോഗ്
                         print(f"INDEX_DEBUG: Successfully indexed {file_name}") 

                except Exception as db_error:
                    # ഡാറ്റാബേസ് എഴുതുമ്പോൾ പിശക് സംഭവിച്ചാൽ
                    print(f"INDEX_DEBUG: DB WRITE ERROR for file {file_name}: {db_error}")
            else:
                # ഫയൽ ടൈപ്പ് ഡോക്യുമെന്റോ വീഡിയോയോ ഓഡിയോയോ അല്ലെങ്കിൽ
                if chat_msg.text:
                     # ടെക്സ്റ്റ് മെസ്സേജുകൾ ഇൻഡെക്സ് ചെയ്യേണ്ടതില്ല
                    print(f"INDEX_DEBUG: Skipping Text message {chat_msg.id}")
                else:
                    # മറ്റ് മീഡിയാ ടൈപ്പുകൾ (ഫോട്ടോ, സ്റ്റിക്ക്, GIF)
                    print(f"INDEX_DEBUG: Skipping message {chat_msg.id} - Not a supported file type (Doc/Vid/Aud).")
            
        # ഇൻഡെക്സിംഗ് പൂർത്തിയായ ശേഷം ഫൈനൽ റിപ്പോർട്ട്
        await msg.edit_text(f"🎉 ഇൻഡക്സിംഗ് പൂർത്തിയായി! ആകെ {total_files_indexed} ഫയലുകൾ ചേർത്തു. ({total_messages_processed} മെസ്സേജുകൾ പരിശോധിച്ചു)")
        
    except Exception as general_error:
        # ചാനൽ ആക്സസ് പോലെയുള്ള വലിയ പിശകുകൾ
        await msg.edit_text(f"❌ ഇൻഡെക്സിംഗ് പിഴവ്: {general_error}. ബോട്ട് ചാനലിൽ മെമ്പറാണോ, ID ശരിയാണോ എന്ന് പരിശോധിക്കുക.")
        print(f"INDEX_DEBUG: FATAL INDEXING ERROR: {general_error}")


# Auto-Filter and Copyright Handler (Global)
@app.on_message(filters.text & filters.incoming & ~filters.command(["start", "index", "dbcount"])) 
async def global_handler(client, message: Message):
    """എല്ലാ ടെക്സ്റ്റ് മെസ്സേജുകളും കൈകാര്യം ചെയ്യുന്നു: കോപ്പിറൈറ്റ് ഡിലീറ്റ് & ഓട്ടോ-ഫിൽട്ടർ."""
    query = message.text.strip()
    chat_id = message.chat.id
    
    # DEBUG: മെസ്സേജ് ഹാൻഡ്ലറിൽ എത്തി എന്ന് ലോഗ് ചെയ്യുന്നു
    print(f"DEBUG: Incoming text from chat {chat_id}: '{query}'")
    
    # --- 1. കോപ്പിറൈറ്റ് മെസ്സേജ് ഡിലീറ്റ് ലോജിക് (എല്ലാ ചാറ്റുകളിലും) ---
    COPYRIGHT_KEYWORDS = ["copyright", "unauthorized", "DMCA", "piracy", "പകർപ്പവകാശം", "അനുമതിയില്ലാതെ", "copy right"] 
    
    is_copyright_message = any(keyword.lower() in query.lower() for keyword in COPYRIGHT_KEYWORDS)
    is_protected_chat = chat_id == PRIVATE_FILE_STORE or chat_id in ADMINS
    
    if is_copyright_message and is_protected_chat:
        try:
            await message.delete()
            await client.send_message(LOG_CHANNEL, f"🚫 **കോപ്പിറൈറ്റ് സന്ദേശം നീക്കം ചെയ്തു!**\n\n**ചാറ്റ് ID:** `{chat_id}`\n**യൂസർ:** {message.from_user.mention}\n**സന്ദേശം:** `{query}`")
            return
        except Exception as e:
            print(f"Error deleting copyright message in chat {chat_id}: {e}")
            return
    
    print(f"DEBUG: Passed copyright check. Proceeding to filter.")
            
    # --- 2. ഓട്ടോ-ഫിൽട്ടർ തിരയൽ (ഫയൽ സ്റ്റോർ ചാനലിൽ ഒഴികെ) ---
    
    if chat_id == PRIVATE_FILE_STORE:
        print("DEBUG: Message came from PRIVATE_FILE_STORE, skipping filter.")
        return
        
    is_private = message.chat.type == "private"
    
    # ഫോഴ്സ് സബ്സ്ക്രൈബ് ചെക്ക്
    if not is_private or await is_subscribed(client, message.from_user.id):
        
        files = await get_file_details(query)
        
        if files:
            # ഫയൽ കണ്ടെത്തിയാൽ ഇൻലൈൻ ബട്ടണുകൾ അയക്കുന്നു
            text = f"ഇതാ നിങ്ങൾ തിരഞ്ഞ **{query}**-യുമായി ബന്ധപ്പെട്ട ഫയലുകൾ:\n\n"
            buttons = []
            for file in files:
                media_icon = {"document": "📄", "video": "🎬", "audio": "🎶"}.get(file.get('media_type', 'document'), '❓')
                file_name = file.get("title", "File").rsplit('.', 1)[0].strip() 
                
                buttons.append([
                    InlineKeyboardButton(
                        text=f"{media_icon} {file_name}",
                        callback_data=f"getfile_{file.get('file_id')}" 
                    )
                ])
            
            if len(files) == 10:
                 buttons.append([InlineKeyboardButton("കൂടുതൽ ഫലങ്ങൾ", url="https://t.me/your_search_group")]) 

            sent_message = await message.reply_text(
                text=text,
                reply_markup=InlineKeyboardMarkup(buttons),
                disable_web_page_preview=True
            )
            
            print(f"DEBUG: Filter results sent for query '{query}'. Starting autodelete timer.")
            
            # --- Autodelete Logic (1 മിനിറ്റിന് ശേഷം) ---
            await asyncio.sleep(60)
            try:
                await sent_message.delete()
                print("DEBUG: Autodelete completed.")
            except Exception as e:
                print(f"Error during autodelete: {e}")
                
    elif is_private:
        # ഫോഴ്സ് സബ്സ്ക്രൈബ് ചെയ്തിട്ടില്ലെങ്കിൽ
        if not FORCE_SUB_CHANNEL: return
        
        join_button = [
            [InlineKeyboardButton("ചാനലിൽ ചേരുക", url=f"https://t.me/{FORCE_SUB_CHANNEL.replace('@', '')}")]
        ]
        await message.reply_text(
            f"നിങ്ങൾക്ക് ഫയലുകൾ ലഭിക്കണമെങ്കിൽ ആദ്യം ഞങ്ങളുടെ ചാനലിൽ ചേരുക.",
            reply_markup=InlineKeyboardMarkup(join_button)
        )

# --- Callback Query Handler (Inline Button Click) ---

@app.on_callback_query(filters.regex("^getfile_"))
async def send_file_handler(client, callback):
    """ബട്ടണിൽ ക്ലിക്കുമ്പോൾ ഫയൽ അയക്കുന്നു."""
    
    # ഫോഴ്സ് സബ്സ്ക്രൈബ് ചെക്ക്
    if FORCE_SUB_CHANNEL and not await is_subscribed(client, callback.from_user.id):
        await callback.answer("ഫയൽ ലഭിക്കാൻ ചാനലിൽ ചേരുക.", show_alert=True)
        return

    file_id = callback.data.split("_")[1]
    file = await db.files_col.find_one({"file_id": file_id}) 
    
    if file:
        try:
            # ഫയൽ ഒറിജിനൽ സ്റ്റോർ ചാനലിൽ നിന്ന് ഫോർവേഡ് ചെയ്യുന്നു
            await client.forward_messages(
                chat_id=callback.message.chat.id,
                from_chat_id=file['chat_id'],
                message_ids=file['message_id']
            )
            await callback.answer("ഫയൽ അയച്ചിരിക്കുന്നു.", show_alert=False)
        except Exception as e:
            await callback.answer("ഫയൽ അയക്കുന്നതിൽ ഒരു പിഴവ് സംഭവിച്ചു. ബോട്ടിന് ആക്സസ് ഉണ്ടോയെന്ന് പരിശോധിക്കുക.", show_alert=True)
            print(f"File forward error: {e}")
    else:
        await callback.answer("ഫയൽ ഡാറ്റാബേസിൽ നിന്ന് നീക്കം ചെയ്യപ്പെട്ടു.", show_alert=True)
    
    try:
        await callback.message.delete()
    except Exception as e:
        print(f"Error deleting inline message: {e}")

# --- Render Webhook Setup (FastAPI for a scalable deployment) ---

# --- STARTUP/SHUTDOWN Lifecycle ---
async def startup_initial_checks():
    """തുടങ്ങുമ്പോൾ ചെയ്യേണ്ട ചെക്കുകൾ."""
    print("Running initial startup checks...")
    try:
        files_count = await db.files_col.count_documents({})
        print(f"Database check completed. Found {files_count} files in the database.")
    except Exception as e:
        print(f"Warning: Database check failed during startup: {e}")


@asynccontextmanager
async def lifespan(web_app: FastAPI):
    await startup_initial_checks()
    
    if WEBHOOK_URL_BASE:
        await app.start() 
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
    """Telegram അപ്ഡേറ്റുകൾ സ്വീകരിക്കുന്നു."""
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
    """Render-ന്റെ Health Check."""
    return {"status": "ok"}

# --- Main Entry Point ---

if __name__ == "__main__":
    if WEBHOOK_URL_BASE:
        uvicorn.run("main:api_app", host="0.0.0.0", port=PORT, log_level="info")
    else:
        print("Starting Pyrogram in Polling Mode...")
        asyncio.run(startup_initial_checks())
        app.run()
