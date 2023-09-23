import re, os
from os import environ
from Script import script

id_pattern = re.compile(r'^.\d+$')
def is_enabled(value, default):
    if value.lower() in ["true", "yes", "1", "enable", "y"]:
        return True
    elif value.lower() in ["false", "no", "0", "disable", "n"]:
        return False
    else:
        return default

# Bot information
SESSION = environ.get('SESSION', 'Media_search')
API_ID = int(environ.get('API_ID', '10261086'))
API_HASH = environ.get('API_HASH', '9195dc0591fbdb22b5711bcd1f437dab')
BOT_TOKEN = environ.get('BOT_TOKEN', "6515031193:AAHk-xf0BZLNKgK9ab6qRHN8_7hJcLQCRh4")

#Port
PORT = environ.get("PORT", "5151")

# Bot settings
CACHE_TIME = int(environ.get('CACHE_TIME', 300))
USE_CAPTION_FILTER = bool(environ.get('USE_CAPTION_FILTER', False))
PICS = (environ.get('PICS', 'https://graph.org/file/f2e803a1bbdc3f3729784.jpg')).split()
SETTINGS_PICS = (environ.get('SETTINGS_PICS', 'https://graph.org/file/73e4acd0a9f4425fd34be.jpg')).split()
CHANNEL_PICS = (environ.get('CHANNEL_PICS', 'https://telegra.ph/file/8a0c09d6ba4f1097b19f4.jpg')).split()
DELETE_PICS = (environ.get('DELETE_PICS', 'https://telegra.ph/file/f58fbfbf2774cc93f5e14.jpg')).split()
SUPPORT_PICS = (environ.get('SUPPORT_PICS', 'https://telegra.ph/file/3bb6c7a38cc3b353b0f1b.jpg')).split()
RULES_PICS = (environ.get('RULES_PICS', 'https://graph.org/file/4752441b16362f2df8e27.jpg https://graph.org/file/e5445f406f428b47556fc.jpg')).split()


# Admins, Channels & Users
ADMINS = [int(admin) if id_pattern.search(admin) else admin for admin in environ.get('ADMINS', '1426588906 1498007933').split()]
CHANNELS = [int(ch) if id_pattern.search(ch) else ch for ch in environ.get('CHANNELS', '-1001844726042').split()]
auth_users = [int(user) if id_pattern.search(user) else user for user in environ.get('AUTH_USERS', '').split()]
AUTH_USERS = (auth_users + ADMINS) if auth_users else []
auth_channel = environ.get('AUTH_CHANNEL', '')
support_chat_id = environ.get('SUPPORT_CHAT_ID', '')
FORCE_SUB   = os.environ.get("FORCE_SUB", "")
auth_grp = environ.get('AUTH_GROUP')
AUTH_CHANNEL = int(auth_channel) if auth_channel and id_pattern.search(auth_channel) else None
AUTH_GROUPS = [int(ch) for ch in auth_grp.split()] if auth_grp else None
PREMIUM_USER = [int(user) if id_pattern.search(user) else user for user in environ.get('PREMIUM_USER', '').split()]
SUPPORT_CHAT_ID = int(support_chat_id) if support_chat_id and id_pattern.search(support_chat_id) else None
NO_RESULTS_MSG = bool(environ.get("NO_RESULTS_MSG", False))

# MongoDB information
DATABASE_URI = environ.get('DATABASE_URI', "mongodb+srv://abdul:abdul@cluster0.zx3rrqx.mongodb.net/?retryWrites=true&w=majority")
DATABASE_NAME = environ.get('DATABASE_NAME', "abdul")
COLLECTION_NAME = environ.get('COLLECTION_NAME', 'Telegram_files')

# Others
MSG_LOG_CHANNEL = int(environ.get('MSG_LOG_CHANNEL', '-1001959246948'))
LOG_CHANNEL = int(environ.get('LOG_CHANNEL', '-1001959246948'))
SUPPORT_CHAT = environ.get('SUPPORT_CHAT', '@Hs_Botz_Discussion')
P_TTI_SHOW_OFF = is_enabled((environ.get('P_TTI_SHOW_OFF', "True")), True)
IMDB = is_enabled((environ.get('IMDB', "True")), False)
SINGLE_BUTTON = is_enabled((environ.get('SINGLE_BUTTON', "True")), False)
CUSTOM_FILE_CAPTION = environ.get("CUSTOM_FILE_CAPTION", f"{script.CAPTION}")
BATCH_FILE_CAPTION = environ.get("BATCH_FILE_CAPTION", CUSTOM_FILE_CAPTION)
IMDB_TEMPLATE = environ.get("IMDB_TEMPLATE", "<b>Your Query: {query}</b> \n‌‌‌‌IMDb: \n\n🏷 Title: {title}\n🌟 Rating : {rating}/10\n🎭 Genres: {genres}\n📆 Year: {year}\n⏰ Duration : {runtime}\n🎙️ Languages : {languages}\n🔖 Plot : {plot}\n\n♥️ we are nothing without you ♥️ \n\n💛 Please Share Us 💛\n\n⚠️Click on the button 👇 below to get your query privately")
LONG_IMDB_DESCRIPTION = is_enabled(environ.get("LONG_IMDB_DESCRIPTION", "False"), False)
SPELL_CHECK_REPLY = is_enabled(environ.get("SPELL_CHECK_REPLY", "True"), False)
MAX_LIST_ELM = environ.get("MAX_LIST_ELM", None)
MSG_ALRT = environ.get('MSG_ALRT', '🚀 ʜꜱ ᠰ ʙᴏᴛꜱ🛰️')
INDEX_REQ_CHANNEL = int(environ.get('INDEX_REQ_CHANNEL', LOG_CHANNEL))
FILE_STORE_CHANNEL = [int(ch) for ch in (environ.get('FILE_STORE_CHANNEL', '')).split()]
MELCOW_NEW_USERS = is_enabled((environ.get('MELCOW_NEW_USERS', "True")), True)
PROTECT_CONTENT = is_enabled((environ.get('PROTECT_CONTENT', "False")), False)
PUBLIC_FILE_STORE = is_enabled((environ.get('PUBLIC_FILE_STORE', "False")), True)


MAIN_CHANNEL = environ.get('MAIN_CHANNEL',"https://t.me/Siveroz_Linkzz")
FILE_CHANNEL = int(environ.get('FILE_CHANNEL', '-1001881460488'))
FILE_CHANNEL_LINK = environ.get('FILE_CHANNEL_LINK', 'https://t.me/+VEFK_LuwT-piNDBl')


LANGUAGES = ["malayalam", "tamil", "english", "hindi", "telugu", "kannada"]

LOG_STR = "Current Cusomized Configurations are:-\n"
LOG_STR += ("IMDB Results are enabled, Bot will be showing imdb details for you queries.\n" if IMDB else "IMBD Results are disabled.\n")
LOG_STR += ("P_TTI_SHOW_OFF found , Users will be redirected to send /start to Bot PM instead of sending file file directly\n" if P_TTI_SHOW_OFF else "P_TTI_SHOW_OFF is disabled files will be send in PM, instead of sending start.\n")
LOG_STR += ("SINGLE_BUTTON is Found, filename and files size will be shown in a single button instead of two separate buttons\n" if SINGLE_BUTTON else "SINGLE_BUTTON is disabled , filename and file_sixe will be shown as different buttons\n")
LOG_STR += (f"CUSTOM_FILE_CAPTION enabled with value {CUSTOM_FILE_CAPTION}, your files will be send along with this customized caption.\n" if CUSTOM_FILE_CAPTION else "No CUSTOM_FILE_CAPTION Found, Default captions of file will be used.\n")
LOG_STR += ("Long IMDB storyline enabled." if LONG_IMDB_DESCRIPTION else "LONG_IMDB_DESCRIPTION is disabled , Plot will be shorter.\n")
LOG_STR += ("Spell Check Mode Is Enabled, bot will be suggesting related movies if movie not found\n" if SPELL_CHECK_REPLY else "SPELL_CHECK_REPLY Mode disabled\n")
LOG_STR += (f"MAX_LIST_ELM Found, long list will be shortened to first {MAX_LIST_ELM} elements\n" if MAX_LIST_ELM else "Full List of casts and crew will be shown in imdb template, restrict them by adding a value to MAX_LIST_ELM\n")
LOG_STR += f"Your current IMDB template is {IMDB_TEMPLATE}"

## EXTRA FEATURES ##
    
      # URL Shortener #

SHORTLINK_URL = environ.get('SHORTLINK_URL', 'tnshort.net')
SHORTLINK_API = environ.get('SHORTLINK_API', '832ad5ffe369f8dbfcd785735cd76a2b53ee2c46')
IS_SHORTLINK = bool(environ.get('IS_SHORTLINK', 'True'))
P_TTI_SHOW_OFF = bool(environ.get('P_TTI_SHOW_OFF', 'True'))

     # Auto Delete For Group Message (Self Delete) #
SELF_DELETE_SECONDS = int(environ.get('SELF_DELETE_SECONDS', 300))
SELF_DELETE = environ.get('SELF_DELETE', True)
if SELF_DELETE == "True":
    SELF_DELETE = True

TUTORIAL = environ.get('TUTORIAL', 'https://t.me/How_to_download_linkzz/3')
IS_TUTORIAL = bool(environ.get('IS_TUTORIAL', True))
