import os
import re
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import UserNotParticipant
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from typing import List, Dict, Any

# .env ഫയലിൽ നിന്ന് വേരിയബിളുകൾ ലോഡ് ചെയ്യുന്നു (ലോക്കൽ ടെസ്റ്റിങ്ങിന്)
load_dotenv()

# --- Config Variables ---
# env വേരിയബിളുകൾ ഇല്ലെങ്കിൽ default വാല്യൂ നൽകുന്നു
API_ID = int(os.environ.get("API_ID", 12345))
API_HASH = os.environ.get("API_HASH", "YOUR_API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "YOUR_BOT_TOKEN")
PRIVATE_FILE_STORE = int(os.environ.get("PRIVATE_FILE_STORE", -100))
ADMINS = [int(admin.strip()) for admin in os.environ.get("ADMINS", "").split(',') if admin.strip().isdigit()]
DATABASE_URL = os.environ.get("DATABASE_URL", "mongodb://localhost:27017")
FORCE_SUB_CHANNEL = os.environ.get("FORCE_SUB_CHANNEL", None)
LOG_CHANNEL = int(os.environ.get("LOG_CHANNEL", -100))

# Webhook Details
WEBHOOK_URL_BASE = os.environ.get("WEBHOOK_URL_BASE", None)
PORT = int(os.environ.get("PORT", 8080))
WEBHOOK_PATH = f"/{BOT_TOKEN}"

# --- MongoDB Setup (Updated to use a Database Class) ---

class Database:
    """ഡാറ്റാബേസ് പ്രവർത്തനങ്ങൾ കൈകാര്യം ചെയ്യുന്നു."""
    def __init__(self, uri: str, database_name: str):
        self._client = AsyncIOMotorClient(uri)
        self.db = self._client[database_name]
        self.files_col = self.db["files"] # ഫയൽ വിവരങ്ങൾ സൂക്ഷിക്കുന്ന Collection

    async def get_all_files(self) -> List[Dict[str, Any]]:
        """ഡാറ്റാബേസിലെ എല്ലാ ഫയൽ എൻട്രികളും ലിസ്റ്റ് ആയി തിരികെ നൽകുന്നു."""
        # Motor-ൽ നിന്നും Cursor-നെ ലിസ്റ്റ് ആയി മാറ്റാൻ to_list() ഉപയോഗിക്കുന്നു.
        cursor = self.files_col.find({})
        return await cursor.to_list(length=None)

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
            # 'sleep' argument removed (Fix 1)
        )

# --- Bot Instance ---
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
        return False
    except Exception as e:
        print(f"Error checking subscription: {e}")
        return True

async def get_file_details(query):
    """ഡാറ്റാബേസിൽ നിന്ന് ഫയൽ വിവരങ്ങൾ തിരയുന്നു."""
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
async def start_command(client, message: Message):
    await message.reply_text(
        "👋 ഹായ്! ഞാൻ ഒരു ഓട്ടോ-ഫിൽട്ടർ ബോട്ടാണ്. എന്നെ നിങ്ങളുടെ ഗ്രൂപ്പിൽ ചേർത്ത് പ്രവർത്തിപ്പിക്കാം."
    )

@app.on_message(filters.command("index") & filters.user(ADMINS))
async def index_command(client, message: Message):
    """അഡ്മിൻമാർക്ക് ഫയൽ സ്റ്റോർ ചാനലിലെ ഫയലുകൾ ഇൻഡക്സ് ചെയ്യാനുള്ള കമാൻഡ്."""
    if not PRIVATE_FILE_STORE:
        await message.reply_text("PRIVATE_FILE_STORE ID ENV വേരിയബിളിൽ നൽകിയിട്ടില്ല. ഇൻഡക്സിംഗ് സാധ്യമല്ല.")
        return

    msg = await message.reply_text("ഫയലുകൾ ഇൻഡക്സ് ചെയ്യാൻ തുടങ്ങുന്നു...")
    
    total_files = 0
    # msg.document ചെക്ക് ചെയ്യുന്നത് ആവശ്യമില്ല, filter="document" ഉള്ളതുകൊണ്ട്
    async for chat_msg in client.search_messages(chat_id=PRIVATE_FILE_STORE, filter="document"):
        if chat_msg.document:
            file_id = chat_msg.document.file_id
            file_name = chat_msg.document.file_name
            caption = chat_msg.caption.html if chat_msg.caption else None
            
            # ഡാറ്റാബേസിൽ ഫയൽ വിവരങ്ങൾ ചേർക്കുന്നു
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
                upsert=True
            )
            total_files += 1
            
            if total_files % 100 == 0:
                 # Original msg-യെ എഡിറ്റ് ചെയ്യുന്നു
                 await msg.edit_text(f"✅ ഇൻഡക്സ് ചെയ്ത ഫയലുകൾ: {total_files}")
                 
    await msg.edit_text(f"🎉 ഇൻഡക്സിംഗ് പൂർത്തിയായി! ആകെ {total_files} ഫയലുകൾ ചേർത്തു.")

# *** പ്രധാന ഫിൽട്ടർ ഫിക്സ്: filters.command() വിളിക്കുന്നു (Fix 3) ***
@app.on_message(filters.text & filters.private | filters.group & filters.text & filters.incoming & ~filters.command()) 
async def auto_filter_handler(client, message: Message):
    """ടെക്സ്റ്റ് മെസ്സേജുകൾ വരുമ്പോൾ ഫിൽട്ടർ ഫയലുകൾ തിരയുന്നു."""
    query = message.text.strip()
    
    # 1. ഫോഴ്സ് സബ്സ്ക്രൈബ് ചെക്ക്
    is_private = message.chat.type == "private"
    if not is_private or await is_subscribed(client, message.from_user.id):
        
        # 2. കോപ്പിറൈറ്റ് മെസ്സേജ് ഡിലീറ്റ് ലോജിക്
        COPYRIGHT_KEYWORDS = ["copyright", "unauthorized", "DMCA", "piracy", "പകർപ്പവകാശം", "അനുമതിയില്ലാതെ"] 
        if message.chat.id in ADMINS and any(keyword.lower() in query.lower() for keyword in COPYRIGHT_KEYWORDS):
             try:
                 await message.delete()
                 await client.send_message(LOG_CHANNEL, f"🚫 **കോപ്പിറൈറ്റ് സന്ദേശം നീക്കം ചെയ്തു!**\n\n**ചാറ്റ് ID:** `{message.chat.id}`\n**യൂസർ:** {message.from_user.mention}\n**സന്ദേശം:** `{query}`")
                 return
             except Exception as e:
                 print(f"Error deleting message: {e}")
        
        # 3. ഓട്ടോ-ഫിൽട്ടർ തിരയൽ
        files = await get_file_details(query)
        
        if files:
            text = f"ഇതാ നിങ്ങൾ തിരഞ്ഞ **{query}**-യുമായി ബന്ധപ്പെട്ട ഫയലുകൾ:\n\n"
            buttons = []
            for file in files:
                file_name = file.get("title", "File").rsplit('.', 1)[0].strip() # Extension ഒഴിവാക്കുന്നു
                
                buttons.append([
                    InlineKeyboardButton(
                        text=file_name,
                        callback_data=f"getfile_{file.get('file_id')}" 
                    )
                ])
            
            await message.reply_text(
                text=text,
                reply_markup=InlineKeyboardMarkup(buttons),
                disable_web_page_preview=True
            )

    elif is_private:
        # ഫോഴ്സ് സബ്സ്ക്രൈബ് ചെയ്തിട്ടില്ലെങ്കിൽ
        if not FORCE_SUB_CHANNEL: return # ചാനൽ ഇല്ലെങ്കിൽ ഒന്നും ചെയ്യേണ്ട
        
        join_button = [
            [InlineKeyboardButton("ചാനലിൽ ചേരുക", url=f"https://t.me/{FORCE_SUB_CHANNEL}")]
        ]
        await message.reply_text(
            f"നിങ്ങൾക്ക് ഫയലുകൾ ലഭിക്കണമെങ്കിൽ ആദ്യം ഞങ്ങളുടെ ചാനലിൽ (@{FORCE_SUB_CHANNEL}) ചേരുക.",
            reply_markup=InlineKeyboardMarkup(join_button)
        )

# --- Callback Query Handler (Inline Button Click) ---

@app.on_callback_query(filters.regex("^getfile_"))
async def send_file_handler(client, callback):
    """ബട്ടണിൽ ക്ലിക്കുമ്പോൾ ഫയൽ അയക്കുന്നു."""
    
    if FORCE_SUB_CHANNEL and not await is_subscribed(client, callback.from_user.id):
        join_button = [
            [InlineKeyboardButton("ചാനലിൽ ചേരുക", url=f"https://t.me/{FORCE_SUB_CHANNEL}")]
        ]
        await callback.answer("ഫയൽ ലഭിക്കാൻ ചാനലിൽ ചേരുക.", show_alert=True)
        await callback.message.reply_text(
            f"ഫയൽ ലഭിക്കണമെങ്കിൽ ആദ്യം ഞങ്ങളുടെ ചാനലിൽ (@{FORCE_SUB_CHANNEL}) ചേരുക.",
            reply_markup=InlineKeyboardMarkup(join_button)
        )
        return

    file_id = callback.data.split("_")[1]
    file = await db.files_col.find_one({"file_id": file_id}) 
    
    if file:
        try:
            await client.forward_messages(
                chat_id=callback.message.chat.id,
                from_chat_id=file['chat_id'],
                message_ids=file['message_id']
            )
            await callback.answer("ഫയൽ അയച്ചിരിക്കുന്നു.", show_alert=False)
        except Exception as e:
            await callback.answer("ഫയൽ അയക്കുന്നതിൽ ഒരു പിഴവ് സംഭവിച്ചു.", show_alert=True)
            print(f"File forward error: {e}")
    else:
        await callback.answer("ഫയൽ ഡാറ്റാബേസിൽ നിന്ന് നീക്കം ചെയ്യപ്പെട്ടു.", show_alert=True)
    
    try:
        await callback.message.delete()
    except Exception as e:
        print(f"Error deleting inline message: {e}")

# --- Render Webhook Setup (FastAPI for a scalable deployment) ---
from fastapi import FastAPI, Request, Response
import uvicorn
from http import HTTPStatus
from contextlib import asynccontextmanager

# *** STARTUP CHECKS ***
async def startup_initial_checks():
    """തുടങ്ങുമ്പോൾ ചെയ്യേണ്ട ചെക്കുകൾ."""
    print("Running initial startup checks...")
    try:
        files_count = len(await db.get_all_files())
        print(f"Database check completed. Found {files_count} files in the database.")
    except Exception as e:
        print(f"Warning: Database check failed during startup: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. പ്രധാനപ്പെട്ട startup ചെക്കുകൾ റൺ ചെയ്യുന്നു
    await startup_initial_checks()
    
    # 2. Bot തുടങ്ങുമ്പോൾ Webhook സജ്ജമാക്കുക അല്ലെങ്കിൽ Pooling തുടങ്ങുക
    if WEBHOOK_URL_BASE:
        # ഇത് Render-ൽ വെബ്ഹുക്ക് വഴി പ്രവർത്തിക്കാൻ
        await app.set_webhook(url=f"{WEBHOOK_URL_BASE}{WEBHOOK_PATH}")
        print(f"Webhook set successfully to: {WEBHOOK_URL_BASE}{WEBHOOK_PATH}")
        await app.start()
    else:
        # ലോക്കൽ ടെസ്റ്റിങ്ങിനായി പൂളിംഗ് (Pooling) രീതിയിൽ തുടങ്ങുക
        await app.start()
        print("Starting in Polling Mode (for local testing only).")
        
    yield
    # 3. Bot നിർത്തുക
    await app.stop()
    print("Application stopped.")

# FastAPI instance
api_app = FastAPI(lifespan=lifespan)

# Webhook endpoint for Telegram updates
@api_app.post(WEBHOOK_PATH)
async def process_update(request: Request):
    """Telegram അപ്ഡേറ്റുകൾ സ്വീകരിക്കുന്നു."""
    try:
        req = await request.json()
        await app.process_update(req) # Pyrogram അപ്ഡേറ്റ് പ്രോസസ്സ് ചെയ്യുന്നു
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
        # Render-ൽ Webhook മോഡിൽ പ്രവർത്തിപ്പിക്കാൻ
        uvicorn.run("main:api_app", host="0.0.0.0", port=PORT, log_level="info")
    else:
        # ലോക്കൽ ടെസ്റ്റിങ്ങിനായി പൂളിംഗ് മോഡ്
        print("Starting Pyrogram in Polling Mode...")
        asyncio.run(startup_initial_checks())
        app.run()
