import os
import re
import asyncio
from pyrogram import Client, filters
from pyrogram.enums import MessagesFilter, ChatType
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, Document, Video, Audio
from pyrogram.errors import UserNotParticipant, MessageNotModified
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from typing import List, Dict, Any, Union
from fastapi import FastAPI, Request, Response
from contextlib import asynccontextmanager
from http import HTTPStatus
import uvicorn

# .env ഫയലിൽ നിന്നുള്ള വേരിയബിളുകൾ ലോഡ് ചെയ്യുന്നു
load_dotenv()

# --- ഗ്ലോബൽ സ്റ്റാറ്റസ് ഫ്ലാഗ് ---
# ഇൻഡെക്സിംഗ് നടക്കുന്നുണ്ടോ എന്ന് ട്രാക്ക് ചെയ്യുന്നു.
IS_INDEXING_RUNNING = False

# --- കോൺഫിഗ് വേരിയബിളുകൾ ---
API_ID = int(os.environ.get("API_ID", 12345))
API_HASH = os.environ.get("API_HASH", "YOUR_API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "YOUR_BOT_TOKEN")
PRIVATE_FILE_STORE = int(os.environ.get("PRIVATE_FILE_STORE", -100)) # ഫയലുകൾ സ്റ്റോർ ചെയ്തിട്ടുള്ള ചാനൽ ഐഡി
LOG_CHANNEL = int(os.environ.get("LOG_CHANNEL", -100))
# പ്രൈവറ്റ് ചാനൽ ഇൻഡെക്സ് ചെയ്യാൻ യൂസർ സെഷൻ സ്ട്രിംഗ് നിർബന്ധമാണ്
USER_SESSION_STRING = os.environ.get("USER_SESSION_STRING", None) 


# അഡ്മിൻ ലിസ്റ്റ്
ADMINS = []
admin_env = os.environ.get("ADMINS", "")
if admin_env:
    ADMINS = [int(admin.strip()) for admin in admin_env.split(',') if admin.strip().isdigit()]

DATABASE_URL = os.environ.get("DATABASE_URL", "mongodb://localhost:27017")
FORCE_SUB_CHANNEL = os.environ.get("FORCE_SUB_CHANNEL", None) # ഫോഴ്സ് സബ് ചാനൽ (ഉദാഹരണത്തിന് @MyChannel)

# വെബ്ഹുക്ക് വിശദാംശങ്ങൾ
WEBHOOK_URL_BASE = os.environ.get("WEBHOOK_URL_BASE", None)
PORT = int(os.environ.get("PORT", 8080))
WEBHOOK_PATH = f"/{BOT_TOKEN}"

# --- മോങ്കോഡിബി സജ്ജീകരണം ---

class Database:
    """ഡാറ്റാബേസ് ഓപ്പറേഷനുകൾ കൈകാര്യം ചെയ്യുന്നു."""
    def __init__(self, uri: str, database_name: str):
        self._client = AsyncIOMotorClient(uri)
        self.db = self._client[database_name]
        self.files_col = self.db["files"]

    async def get_all_files(self) -> List[Dict[str, Any]]:
        """എല്ലാ ഫയൽ എൻട്രികളും ലിസ്റ്റായി തിരികെ നൽകുന്നു."""
        cursor = self.files_col.find({})
        return await cursor.to_list(length=None)

    async def find_one(self, query: Dict[str, Any]) -> Dict[str, Any] | None:
        return await self.files_col.find_one(query)

    async def update_one(self, query: Dict[str, Any], update: Dict[str, Any], upsert: bool = False):
        await self.files_col.update_one(query, update, upsert=upsert)

# ഡാറ്റാബേസ് ഇൻസ്റ്റൻസ്
db = Database(DATABASE_URL, "AutoFilterBot")

# --- പൈറോഗ്രാം ക്ലൈന്റ് ---
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

# --- ബോട്ട് ഇൻസ്റ്റൻസ് (ഗ്ലോബൽ പൈറോഗ്രാം ക്ലൈന്റ്) ---
app = AutoFilterBot()

# --- സഹായികൾ ---

async def is_subscribed(client, user_id):
    """ഫോഴ്സ് സബ്സ്ക്രൈബ് ചാനലിൽ യൂസർ അംഗമാണോ എന്ന് പരിശോധിക്കുന്നു."""
    if not FORCE_SUB_CHANNEL:
        return True
    try:
        # ബോട്ടിൽ യൂസർ ചാനലിൽ ഉണ്ടോ എന്ന് പരിശോധിക്കുന്നു
        member = await client.get_chat_member(FORCE_SUB_CHANNEL, user_id) 
        if member.status in ["member", "administrator", "creator"]:
            return True
        return False
    except UserNotParticipant:
        print("DEBUG: യൂസർ ഫോഴ്സ് സബ് ചാനലിൽ അംഗമല്ല.")
        return False
    except Exception as e:
        print(f"സബ്സ്ക്രിപ്ഷൻ പരിശോധിക്കുന്നതിൽ പിശക്: {e}")
        return True 

async def get_file_details(query):
    """മെച്ചപ്പെടുത്തിയ റെഗുലർ എക്സ്പ്രഷൻ ഉപയോഗിച്ച് ഫയൽ വിവരങ്ങൾ ഡാറ്റാബേസിൽ തിരയുന്നു."""
    
    print(f"DEBUG: തിരയുന്ന വാക്ക്: '{query}'")

    # തിരയൽ വാചകത്തിലെ പ്രത്യേക ചിഹ്നങ്ങൾ കൈകാര്യം ചെയ്യുന്നു 
    escaped_query = re.escape(query)
    
    # ടൈറ്റിലിൻ്റെയോ ക്യാപ്ഷൻ്റെയോ ഏത് ഭാഗത്ത് വേണമെങ്കിലും തിരയാൻ സഹായിക്കുന്ന റെഗുലർ എക്സ്പ്രഷൻ
    regex_pattern = f".*{escaped_query}.*"
    
    # ടൈറ്റിലിലോ ക്യാപ്ഷനിലോ കേസ്-ഇൻസെൻസിറ്റീവായി ഭാഗികമായി പൊരുത്തപ്പെടുത്താൻ $regex ഉപയോഗിക്കുന്നു
    cursor = db.files_col.find({ 
        "$or": [
            {"title": {"$regex": regex_pattern, "$options": "i"}},
            {"caption": {"$regex": regex_pattern, "$options": "i"}}
        ]
    }).limit(10)
    
    files = await cursor.to_list(length=10)
    
    print(f"DEBUG: '{query}' എന്ന വാക്കിന് {len(files)} ഫയലുകൾ കണ്ടെത്തി")
    
    return files

# ഫയൽ വിവരങ്ങൾ വേർതിരിച്ചെടുക്കുന്ന ഫംഗ്ഷൻ
def get_file_info(message: Message) -> tuple[str, str, Union[Document, Video, Audio, None]]:
    """ഒരു സന്ദേശത്തിൽ നിന്ന് file_id, file_name, file_object എന്നിവ കണ്ടെത്തുന്നു."""
    if message.document and message.document.file_name:
        return message.document.file_id, message.document.file_name, message.document
    if message.video:
        file_name = message.caption.strip() if message.caption else f"Video_{message.id}"
        return message.video.file_id, file_name, message.video
    if message.audio:
        file_name = message.audio.file_name or message.audio.title or f"Audio_{message.id}"
        return message.audio.file_id, file_name, message.audio
    return None, None, None

# --- സ്റ്റാർട്ട് കമാൻഡ് ---
@app.on_message(filters.command("start") & filters.private)
async def start_command(client, message: Message):
    """പ്രൈവറ്റ് ചാറ്റിലെ /start കമാൻഡ് കൈകാര്യം ചെയ്യുന്നു."""
    global IS_INDEXING_RUNNING
    
    if IS_INDEXING_RUNNING:
        await message.reply_text("ഇൻഡെക്സിംഗ് നടന്നുകൊണ്ടിരിക്കുകയാണ്. അത് പൂർത്തിയാകുന്നതുവരെ ദയവായി കാത്തിരിക്കുക.")
        return
        
    await message.reply_text(
        f"ഹായ് {message.from_user.first_name}, ഞാൻ ഒരു ഓട്ടോ ഫിൽട്ടർ ബോട്ടാണ്. എന്നെ അഡ്മിനായി ചേർത്ത ഗ്രൂപ്പിലോ ചാനലിലോ നിങ്ങൾ ഫയലിൻ്റെ പേര് അയക്കുകയാണെങ്കിൽ, എനിക്ക് ഫയൽ ലിങ്ക് ചെയ്യാൻ കഴിയും.\n\n"
        "തിരയൽ ഫലം കാണുമ്പോൾ ബട്ടൺ ക്ലിക്ക് ചെയ്യുക, ഞാൻ ഫയൽ ഇവിടെ പ്രൈവറ്റായി അയച്ചുതരും.\n\n"
        "**അഡ്മിൻ കമാൻഡുകൾ:**\n"
        "• `/index` - ചാനലിലെ എല്ലാ ഫയലുകളും ഇൻഡെക്സ് ചെയ്യാൻ.\n"
        "• `/dbcount` - ഡാറ്റാബേസിലെ ഫയലുകളുടെ എണ്ണം പരിശോധിക്കാൻ."
    )
    print(f"DEBUG: {message.from_user.id} എന്ന ഐഡിയിൽ നിന്ന് സ്റ്റാർട്ട് കമാൻഡ് ലഭിച്ചു")

@app.on_message(filters.command("index") & filters.user(ADMINS))
async def index_command(client, message: Message):
    """
    യൂസർ സെഷൻ ഉപയോഗിച്ച് ഫയൽ സ്റ്റോർ ചാനലിൽ നിന്ന് എല്ലാ ഫയലുകളും ഇൻഡെക്സ് ചെയ്യുന്ന കമാൻഡ്.
    """
    global IS_INDEXING_RUNNING
    
    if IS_INDEXING_RUNNING:
        await message.reply_text("❌ മുന്നറിയിപ്പ്: ഇൻഡെക്സിംഗ് പ്രോസസ്സ് നിലവിൽ പ്രവർത്തിക്കുന്നു. ഇപ്പോഴത്തെ ജോലി പൂർത്തിയാക്കാൻ കാത്തിരിക്കുക.")
        return

    if PRIVATE_FILE_STORE == -100:
        await message.reply_text("PRIVATE_FILE_STORE ID ENV-യിൽ നൽകിയിട്ടില്ല. ഇൻഡെക്സിംഗ് സാധ്യമല്ല.")
        return
    
    if not USER_SESSION_STRING:
         await message.reply_text("❌ ഇൻഡെക്സിംഗ് പിശക്: **USER_SESSION_STRING** ENV-യിൽ നൽകിയിട്ടില്ല. യൂസർ സെഷൻ സ്ട്രിംഗ് ഉണ്ടാക്കി നൽകുക.")
         return

    IS_INDEXING_RUNNING = True # ഫ്ലാഗ് True ആക്കുന്നു
    
    msg = await message.reply_text("🔑 യൂസർ സെഷൻ ഉപയോഗിച്ച് പൂർണ്ണമായ ഓട്ടോമാറ്റിക് ഫയൽ ഇൻഡെക്സിംഗ് ആരംഭിക്കുന്നു... ഇതിന് സമയമെടുത്തേക്കാം. (ലോഗുകൾ പരിശോധിക്കുക)")
    
    total_files_indexed = 0
    total_messages_processed = 0
    
    # --- ഇൻഡെക്സിംഗിനായി യൂസർ ക്ലൈൻ്റ് ഇനിഷ്യലൈസ് ചെയ്യുന്നു ---
    user_client = Client(
        "indexer_session",
        api_id=API_ID,
        api_hash=API_HASH,
        session_string=USER_SESSION_STRING, # യൂസർ അക്കൗണ്ടായി ലോഗിൻ ചെയ്യുന്നു
    )

    try:
        await user_client.start() # യൂസർ ക്ലൈൻ്റ് ആരംഭിക്കുന്നു

        # Pyrogram-ൻ്റെ get_chat_history ഉപയോഗിച്ച് എല്ലാ സന്ദേശങ്ങളിലൂടെയും കടന്നുപോകുന്നു
        async for chat_msg in user_client.get_chat_history(chat_id=PRIVATE_FILE_STORE): 
            total_messages_processed += 1
            file_id, file_name, file_object = get_file_info(chat_msg)
            
            if file_id and file_name:
                caption = chat_msg.caption.html if chat_msg.caption else None 
                
                try:
                    # ഫയൽ വിവരങ്ങൾ MongoDB-യിൽ സേവ്/അപ്ഡേറ്റ് ചെയ്യുന്നു
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
                         # 50 ഫയലുകൾക്ക് ശേഷം സ്റ്റാറ്റസ് അപ്ഡേറ്റ് ചെയ്യുന്നു
                         try:
                             await msg.edit_text(f"✅ ഇൻഡെക്സ് ചെയ്ത ഫയലുകൾ: {total_files_indexed} / {total_messages_processed}")
                             print(f"INDEX_DEBUG: {file_name} വിജയകരമായി ഇൻഡെക്സ് ചെയ്തു") 
                         except MessageNotModified:
                             pass # ടെക്സ്റ്റ് ഒന്നുതന്നെയാണെങ്കിൽ അവഗണിക്കുക.

                except Exception as db_error:
                    print(f"INDEX_DEBUG: {file_name} എന്ന ഫയലിനുള്ള DB WRITE പിശക്: {db_error}")
            else:
                if chat_msg.text:
                    print(f"INDEX_DEBUG: ടെക്സ്റ്റ് മെസ്സേജ് {chat_msg.id} ഒഴിവാക്കുന്നു")
                else:
                    print(f"INDEX_DEBUG: മെസ്സേജ് {chat_msg.id} ഒഴിവാക്കുന്നു - പിന്തുണയ്ക്കുന്ന ഫയൽ തരം (Doc/Vid/Aud) അല്ല.")
            
        # ഇൻഡെക്സിംഗ് പൂർത്തിയാക്കിയതിന് ശേഷമുള്ള അന്തിമ റിപ്പോർട്ട്
        await msg.edit_text(f"🎉 ഇൻഡെക്സിംഗ് പൂർത്തിയായി! ആകെ {total_files_indexed} ഫയലുകൾ ചേർക്കുകയോ അപ്ഡേറ്റ് ചെയ്യുകയോ ചെയ്തു. ({total_messages_processed} സന്ദേശങ്ങൾ പ്രോസസ്സ് ചെയ്തു)")
        
    except Exception as general_error:
        # ചാനൽ ആക്സസ് ഇല്ലായ്മ പോലുള്ള വലിയ പിശകുകൾ പിടിക്കുന്നു
        await msg.edit_text(f"❌ ഇൻഡെക്സിംഗ് പിശക്: {general_error}. യൂസർ അക്കൗണ്ടിന് ചാനലിലേക്ക് ആക്സസ് ഉണ്ടോ എന്നും ഐഡി ശരിയാണോ എന്നും പരിശോധിക്കുക.")
        print(f"INDEX_DEBUG: മാരകമായ ഇൻഡെക്സിംഗ് പിശക്: {general_error}")
        
    finally:
        await user_client.stop() # യൂസർ ക്ലൈൻ്റ് നിർത്തുന്നു
        IS_INDEXING_RUNNING = False # ഫ്ലാഗ് False ആക്കുന്നു

@app.on_message(filters.command("dbcount") & filters.user(ADMINS))
async def dbcount_command(client, message: Message):
    """ഡാറ്റാബേസിലെ ആകെ ഫയലുകളുടെ എണ്ണം പരിശോധിക്കാനുള്ള കമാൻഡ്."""
    try:
        count = await db.files_col.count_documents({})
        await message.reply_text(f"📊 **ഡാറ്റാബേസ് ഫയൽ കൗണ്ട്:**\nനിലവിൽ ഇൻഡെക്സ് ചെയ്ത ആകെ ഫയലുകൾ: **{count}**")
    except Exception as e:
        await message.reply_text(f"❌ ഡാറ്റാബേസ് കൗണ്ട് എടുക്കുന്നതിൽ പിശക്: {e}")

# ഓട്ടോ-ഫിൽട്ടർ, കോപ്പിറൈറ്റ് ഹാൻഡ്ലർ (ഗ്ലോബൽ)
@app.on_message(filters.text & filters.incoming & ~filters.command(["start", "index", "dbcount"])) 
async def global_handler(client, message: Message):
    """വരുന്ന എല്ലാ ടെക്സ്റ്റ് സന്ദേശങ്ങളും കൈകാര്യം ചെയ്യുന്നു: കോപ്പിറൈറ്റ് ഡിലീറ്റും ഓട്ടോ-ഫിൽട്ടർ തിരയലും."""
    query = message.text.strip()
    chat_id = message.chat.id
    chat_type = message.chat.type
    
    # ഇൻഡെക്സിംഗ് നടക്കുന്നുണ്ടോ എന്ന് പരിശോധിക്കുന്നു
    global IS_INDEXING_RUNNING
    if IS_INDEXING_RUNNING:
        await message.reply_text("ഇൻഡെക്സിംഗ് നടന്നുകൊണ്ടിരിക്കുകയാണ്. പ്രോസസ്സ് പൂർത്തിയാകുമ്പോൾ വീണ്ടും ശ്രമിക്കുക.")
        return
    
    print(f"DEBUG: {chat_id} എന്ന ചാറ്റിൽ നിന്ന് വന്ന സന്ദേശം: '{query}'")
    
    # --- 1. കോപ്പിറൈറ്റ് സന്ദേശം ഇല്ലാതാക്കാനുള്ള ലോജിക് ---
    COPYRIGHT_KEYWORDS = ["copyright", "unauthorized", "DMCA", "piracy"] 
    
    is_copyright_message = any(keyword.lower() in query.lower() for keyword in COPYRIGHT_KEYWORDS)
    is_protected_chat = chat_id == PRIVATE_FILE_STORE or chat_id in ADMINS
    
    if is_copyright_message and is_protected_chat:
        try:
            await message.delete()
            # ലോഗ് ചെയ്യുന്നു
            await client.send_message(LOG_CHANNEL, f"🚫 **കോപ്പിറൈറ്റ് സന്ദേശം ഇല്ലാതാക്കി!**\n\n**ചാറ്റ് ഐഡി:** `{chat_id}`\n**യൂസർ:** {message.from_user.mention}\n**സന്ദേശം:** `{query}`")
            return
        except Exception as e:
            print(f"{chat_id} എന്ന ചാറ്റിൽ കോപ്പിറൈറ്റ് സന്ദേശം ഇല്ലാതാക്കുന്നതിൽ പിശക്: {e}")
            return
    
    print(f"DEBUG: കോപ്പിറൈറ്റ് പരിശോധന പാസായി. ഫിൽട്ടറിലേക്ക് പോകുന്നു.")
            
    # --- 2. ഓട്ടോ-ഫിൽട്ടർ തിരയൽ ---
    
    # **പുതിയ ലോജിക്:** പ്രൈവറ്റ് ചാറ്റിൽ (DM) ഫിൽട്ടറിംഗ് ഒഴിവാക്കുന്നു
    if chat_type == ChatType.PRIVATE:
        await message.reply_text("👋 ഫയലുകൾ തിരയുന്നതിന് എന്നെ അഡ്മിനായി ചേർത്ത **ഗ്രൂപ്പിലോ ചാനലിലോ** പേര് ടൈപ്പ് ചെയ്യുക. അവിടെ ബട്ടൺ ക്ലിക്ക് ചെയ്താൽ ഞാൻ ഇവിടെ (ഈ DM-ൽ) ഫയൽ അയച്ചുതരും.")
        return
        
    # ഫയൽ സ്റ്റോർ ചാനലിൽ നിന്നുള്ള സന്ദേശങ്ങൾ ഒഴിവാക്കുന്നു
    if chat_id == PRIVATE_FILE_STORE:
        print("DEBUG: സന്ദേശം PRIVATE_FILE_STORE-ൽ നിന്ന് വന്നതാണ്, ഫിൽട്ടർ ഒഴിവാക്കുന്നു.")
        return
        
    # --- ഗ്രൂപ്പിലും ചാനലിലും തിരച്ചിൽ നടത്തുന്നു ---
    
    # ഫോഴ്സ് സബ്സ്ക്രൈബ് പരിശോധന (ഇവിടെ ആവശ്യമില്ല, കാരണം ഫയൽ സ്വകാര്യമായാണ് അയക്കുന്നത്)
    
    files = await get_file_details(query)
    
    if files:
        # ഫയലുകൾ കണ്ടെത്തി: ഇൻലൈൻ ബട്ടണുകൾ അയയ്ക്കുന്നു
        text = f"**{query}** യുമായി ബന്ധപ്പെട്ട ഫയലുകൾ ഇതാ:\n\nഫയൽ ലഭിക്കുന്നതിനായി ബട്ടൺ ക്ലിക്ക് ചെയ്യുക. ഫയൽ നിങ്ങളുടെ പ്രൈവറ്റ് ചാറ്റിൽ ലഭിക്കുന്നതാണ്."
        buttons = []
        for file in files:
            media_icon = {"document": "📄", "video": "🎬", "audio": "🎶"}.get(file.get('media_type', 'document'), '❓')
            file_name = file.get("title", "File").rsplit('.', 1)[0].strip() 
            
            buttons.append([
                InlineKeyboardButton(
                    text=f"{media_icon} {file_name}",
                    # ഫയലിന്റെ message_id ഉപയോഗിച്ച് കോൾബാക്ക് ഡാറ്റ 64 ബൈറ്റിൽ കുറവാക്കുന്നു
                    callback_data=f"getmsg_{file.get('message_id')}" 
                )
            ])
        
        if len(files) == 10:
             buttons.append([InlineKeyboardButton("കൂടുതൽ ഫലങ്ങൾ", url="https://t.me/your_search_group")]) 

        sent_message = await message.reply_text(
            text=text,
            reply_markup=InlineKeyboardMarkup(buttons),
            disable_web_page_preview=True
        )
        
        print(f"DEBUG: '{query}' എന്ന തിരച്ചിലിനുള്ള ഫിൽട്ടർ ഫലങ്ങൾ അയച്ചു. ഓട്ടോഡിലീറ്റ് ടൈമർ ആരംഭിക്കുന്നു.")
        
        # --- ഓട്ടോഡിലീറ്റ് ലോജിക് (60 സെക്കൻഡിന് ശേഷം) ---
        await asyncio.sleep(60)
        try:
            await sent_message.delete()
            print("DEBUG: ഓട്ടോഡിലീറ്റ് പൂർത്തിയായി.")
        except Exception as e:
            print(f"ഓട്ടോഡിലീറ്റിനിടയിലെ പിശക്: {e}")
            
    # ഫയൽ ഗ്രൂപ്പിൽ/ചാനലിൽ കണ്ടെത്താനായില്ലെങ്കിൽ "നോട്ട് ഫൗണ്ട്" മെസ്സേജ് അയക്കുന്നത് ഒഴിവാക്കുന്നു.
                
# --- കോൾബാക്ക് ക്വറി ഹാൻഡ്ലർ (ഇൻലൈൻ ബട്ടൺ ക്ലിക്ക്) ---

@app.on_callback_query(filters.regex("^getmsg_")) 
async def send_file_handler(client, callback):
    """ഇൻലൈൻ ബട്ടൺ ക്ലിക്കുചെയ്യുമ്പോൾ ഫയൽ സ്വകാര്യമായി അയയ്ക്കുന്നു."""
    
    user_id = callback.from_user.id
    
    # ഫോഴ്സ് സബ്സ്ക്രൈബ് പരിശോധന
    if FORCE_SUB_CHANNEL and not await is_subscribed(client, user_id):
        # ഉപയോക്താവ് സബ്സ്ക്രൈബ് ചെയ്തിട്ടില്ലെങ്കിൽ
        join_button = [
            [InlineKeyboardButton("ചാനലിൽ അംഗമാകുക", url=f"https://t.me/{FORCE_SUB_CHANNEL.replace('@', '')}")]
        ]
        await callback.answer("ഫയൽ ലഭിക്കാൻ ചാനലിൽ അംഗമാകുക.", show_alert=True)
        # DM-ൽ സബ്സ്ക്രൈബ് ചെയ്യാൻ ആവശ്യപ്പെടുന്ന സന്ദേശം അയയ്ക്കുന്നു
        try:
            await client.send_message(
                chat_id=user_id,
                text=f"നിങ്ങൾ ചാനലിൽ അംഗമായിട്ടില്ല. ഫയൽ ലഭിക്കാൻ ദയവായി {FORCE_SUB_CHANNEL} എന്ന ചാനലിൽ ജോയിൻ ചെയ്യുക.",
                reply_markup=InlineKeyboardMarkup(join_button)
            )
        except Exception:
             # യൂസർ ബോട്ടിൽ start ചെയ്തിട്ടില്ലെങ്കിൽ സന്ദേശം അയക്കാൻ കഴിയില്ല
             pass 
        return

    # കോൾബാക്ക് ഡാറ്റയിൽ നിന്ന് message_id വേർതിരിച്ചെടുക്കുന്നു
    message_id_str = callback.data.split("_")[1]
    message_id = int(message_id_str)
    
    # message_id ഉപയോഗിച്ച് ഡാറ്റാബേസിൽ ഫയൽ കണ്ടെത്തുന്നു
    file = await db.files_col.find_one({"message_id": message_id}) 
    
    if file:
        try:
            # ഫയൽ ഒറിജിനൽ സ്റ്റോർ ചാനലിൽ നിന്ന് യൂസറിൻ്റെ പ്രൈവറ്റ് ചാറ്റിലേക്ക് ഫോർവേഡ് ചെയ്യുന്നു
            await client.forward_messages(
                chat_id=user_id, # <-- യൂസറിൻ്റെ പ്രൈവറ്റ് ചാറ്റ് ഐഡി
                from_chat_id=file['chat_id'],
                message_ids=file['message_id']
            )
            # യൂസറിൻ്റെ പ്രൈവറ്റ് ചാറ്റിൽ സ്ഥിരീകരണ സന്ദേശം അയയ്ക്കുന്നു
            await client.send_message(user_id, "✅ നിങ്ങൾ ആവശ്യപ്പെട്ട ഫയൽ ലഭിച്ചു.")
            
            await callback.answer("ഫയൽ നിങ്ങളുടെ പ്രൈവറ്റ് ചാറ്റിലേക്ക് അയച്ചിരിക്കുന്നു.", show_alert=True)
            
        except Exception as e:
            # ഫോർവേഡിംഗ് പരാജയപ്പെട്ടാൽ (ഉദാഹരണത്തിന്, യൂസർ ബോട്ടിനെ ബ്ലോക്ക് ചെയ്തു)
            await callback.answer("ഫയൽ അയക്കുന്നതിൽ പിശക് സംഭവിച്ചു. ദയവായി ബോട്ടിൽ /start കമാൻഡ് അയച്ച് പ്രൈവറ്റ് ചാറ്റ് ആരംഭിക്കുക.", show_alert=True)
            print(f"യൂസർക്ക് {user_id} ഫയൽ ഫോർവേഡ് ചെയ്യുന്നതിൽ പിശക്: {e}")
    else:
        await callback.answer("ഈ ഫയൽ ഡാറ്റാബേസിൽ നിന്ന് നീക്കം ചെയ്തിരിക്കുന്നു.", show_alert=True)
    
    # ഗ്രൂപ്പിലെ/ചാനലിലെ മെസ്സേജ് ഡിലീറ്റ് ചെയ്യുന്നു
    try:
        await callback.message.delete()
    except Exception as e:
        print(f"ഇൻലൈൻ മെസ്സേജ് ഡിലീറ്റ് ചെയ്യുന്നതിലെ പിശക്: {e}")

# --- റെൻഡർ വെബ്ഹുക്ക് സജ്ജീകരണം (FastAPI) ---

# --- സ്റ്റാർട്ടപ്പ്/ഷട്ട്ഡൗൺ ലൈഫ് സൈക്കിൾ ---
async def startup_initial_checks():
    """സ്റ്റാർട്ടപ്പിൽ പ്രവർത്തിപ്പിക്കേണ്ട പരിശോധനകൾ."""
    print("പ്രാരംഭ സ്റ്റാർട്ടപ്പ് പരിശോധനകൾ നടത്തുന്നു...")
    try:
        files_count = await db.files_col.count_documents({})
        print(f"ഡാറ്റാബേസ് പരിശോധന പൂർത്തിയായി. ഡാറ്റാബേസിൽ {files_count} ഫയലുകൾ കണ്ടെത്തി.")
    except Exception as e:
        print(f"മുന്നറിയിപ്പ്: സ്റ്റാർട്ടപ്പിൽ ഡാറ്റാബേസ് പരിശോധന പരാജയപ്പെട്ടു: {e}")


@asynccontextmanager
async def lifespan(web_app: FastAPI):
    await startup_initial_checks()
    
    if WEBHOOK_URL_BASE:
        await app.start() 
        await app.set_webhook(url=f"{WEBHOOK_URL_BASE}{WEBHOOK_PATH}")
        print(f"വെബ്ഹുക്ക് വിജയകരമായി സജ്ജീകരിച്ചു: {WEBHOOK_URL_BASE}{WEBHOOK_PATH}")
    else:
        await app.start()
        print("പോളിംഗ് മോഡിൽ ആരംഭിക്കുന്നു (ലോക്കൽ ടെസ്റ്റിംഗിന് മാത്രം).")
        
    yield
    await app.stop()
    print("ആപ്ലിക്കേഷൻ നിർത്തി.")

# FastAPI ഇൻസ്റ്റൻസ്
api_app = FastAPI(lifespan=lifespan)

# ടെലിഗ്രാം അപ്ഡേറ്റുകൾക്കായുള്ള വെബ്ഹുക്ക് എൻഡ്പോയിന്റ്
@api_app.post(WEBHOOK_PATH)
async def process_update(request: Request):
    """ടെലിഗ്രാം അപ്ഡേറ്റുകൾ സ്വീകരിക്കുകയും പ്രോസസ്സ് ചെയ്യുകയും ചെയ്യുന്നു."""
    try:
        req = await request.json()
        await app.process_update(req)
        return Response(status_code=HTTPStatus.OK)
    except Exception as e:
        print(f"അപ്ഡേറ്റ് പ്രോസസ്സ് ചെയ്യുന്നതിൽ പിശക്: {e}")
        return Response(status_code=HTTPStatus.INTERNAL_SERVER_ERROR)

# റെൻഡർ ഹെൽത്ത് ചെക്ക് എൻഡ്പോയിന്റ്
@api_app.get("/")
async def health_check():
    """റെൻഡർ ഹെൽത്ത് ചെക്ക്."""
    return {"status": "ok"}

# --- പ്രധാന എൻട്രി പോയിൻ്റ് ---

if __name__ == "__main__":
    if WEBHOOK_URL_BASE:
        # FastAPI ആപ്പ് നൽകാൻ uvicorn ഉപയോഗിക്കുന്നു (Render വിന്യാസത്തിനായി)
        uvicorn.run("main:api_app", host="0.0.0.0", port=PORT, log_level="info")
    else:
        # ലോക്കൽ പോളിംഗ് മോഡ് ടെസ്റ്റിംഗിനായി app.run() ഉപയോഗിക്കുന്നു
        print("പോളിംഗ് മോഡിൽ പൈറോഗ്രാം ആരംഭിക്കുന്നു...")
        asyncio.run(startup_initial_checks())
        app.run()
