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
BOT_TOKEN = environ.get('BOT_TOKEN', "6319930625:AAGs2mIczab1efdGqR0RXYNzBjmsNlawXEo")

#Port
PORT = environ.get("PORT", "8080")

# Bot settings
CACHE_TIME = int(environ.get('CACHE_TIME', 300))
USE_CAPTION_FILTER = bool(environ.get('USE_CAPTION_FILTER', False))
PICS = (environ.get('PICS', 'https://graph.org/file/630fd5fbc59fe83cefc34.jpg https://graph.org/file/5ed6c28c61ea6212e91f9.jpg https://graph.org/file/489c6b8058709c52ee31c.jpg https://graph.org/file/2c30c1452c2c4bccc3046.jpg https://graph.org/file/4f4c6bfc6a016b11ddef4.jpg https://graph.org/file/daf2b545d8b9b732b71d7.jpg https://graph.org/file/b711a112dc78f0bcc2cad.jpg https://graph.org/file/0858959a66bb00a29fd95.jpg https://graph.org/file/8ca62e6ad091a7cf4d86d.jpg https://graph.org/file/08ed0cd0bc6ac0bc37f49.jpg https://graph.org/file/4dc11ffde60a857316abe.jpg https://graph.org/file/3bce5258bede563a9c559.jpg https://graph.org/file/6cb914abbb21a755b601c.jpg https://graph.org/file/58a6861cf47953a596573.jpg https://graph.org/file/f7d482b08d48c2dc8a30a.jpg https://graph.org/file/a949483ebc4c3fe89bdc0.jpg https://graph.org/file/7b13e39550b56b82bd9f7.jpg https://graph.org/file/1cbe46cd74e11c704bbe2.jpg https://telegra.ph/file/e9c7a37f2522a1f4e494d.jpg')).split()
SETTINGS_PICS = (environ.get('SETTINGS_PICS', 'https://graph.org/file/73e4acd0a9f4425fd34be.jpg')).split()
CHANNEL_PICS = (environ.get('CHANNEL_PICS', 'https://graph.org/file/30fc6ea74df988db9b417.jpg')).split()
DELETE_PICS = (environ.get('DELETE_PICS', 'https://telegra.ph/file/f58fbfbf2774cc93f5e14.jpg')).split()
SUPPORT_PICS = (environ.get('SUPPORT_PICS', 'https://graph.org/file/30fc6ea74df988db9b417.jpg')).split()
RULES_PICS = (environ.get('RULES_PICS', 'https://graph.org/file/4752441b16362f2df8e27.jpg https://graph.org/file/e5445f406f428b47556fc.jpg')).split()


# Admins, Channels & Users
ADMINS = [int(admin) if id_pattern.search(admin) else admin for admin in environ.get('ADMINS', '1426588906').split()]
CHANNELS = [int(ch) if id_pattern.search(ch) else ch for ch in environ.get('CHANNELS', '-1001878854070').split()]
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
DATABASE_URI = environ.get('DATABASE_URI', "mongodb+srv://omg:omg@cluster0.cub5z0e.mongodb.net/?retryWrites=true&w=majority")
DATABASE_NAME = environ.get('DATABASE_NAME', "omg")
COLLECTION_NAME = environ.get('COLLECTION_NAME', 'Files')

# Others
MSG_LOG_CHANNEL = int(environ.get('MSG_LOG_CHANNEL', '-1001606248152'))
LOG_CHANNEL = int(environ.get('LOG_CHANNEL', '-1001606248152'))
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


MAIN_CHANNEL = environ.get('MAIN_CHANNEL',"https://t.me/OMGxMovies")
FILE_CHANNEL = int(environ.get('FILE_CHANNEL', '-1001606248152'))
FILE_CHANNEL_LINK = environ.get('FILE_CHANNEL_LINK', 'https://t.me/+SuuWzl_yiwllZDg1')


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

SHORTLINK_URL = environ.get('SHORTLINK_URL', 'v2.kpslink.in')
SHORTLINK_API = environ.get('SHORTLINK_API', 'ec8ba7deff6128848def53bf2d4e69608443cf27')
IS_SHORTLINK = bool(environ.get('IS_SHORTLINK', 'True'))
P_TTI_SHOW_OFF = bool(environ.get('P_TTI_SHOW_OFF', 'True'))

     # Auto Delete For Group Message (Self Delete) #
SELF_DELETE_SECONDS = int(environ.get('SELF_DELETE_SECONDS', 100))
SELF_DELETE = environ.get('SELF_DELETE', True)
if SELF_DELETE == "True":
    SELF_DELETE = True

TUTORIAL = environ.get('TUTORIAL', 'https://t.me/linkdownlos/12')
IS_TUTORIAL = bool(environ.get('IS_TUTORIAL', True))
