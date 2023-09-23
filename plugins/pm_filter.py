import asyncio
import re
import ast
import math
import random
import pytz
from datetime import datetime, timedelta, date, time

from utils import get_shortlink
from pyrogram.errors.exceptions.bad_request_400 import MediaEmpty, PhotoInvalidDimensions, WebpageMediaEmpty
from Script import script
import pyrogram
from database.connections_mdb import active_connection, all_connections, delete_connection, if_active, make_active, \
    make_inactive
from info import *
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, InputMediaPhoto
from pyrogram import Client, filters, enums
from pyrogram.errors import FloodWait, UserIsBlocked, MessageNotModified, PeerIdInvalid
from utils import get_size, is_subscribed, get_poster, search_gagala, temp, get_settings, save_group_settings
from database.users_chats_db import db
from database.ia_filterdb import Media, get_file_details, get_search_results, get_bad_files, hs_bad_files
from database.filters_mdb import (
    del_all,
    find_filter,
    get_filters,
)
from database.gfilters_mdb import (
    find_gfilter,
    get_gfilters,
    del_allg
)
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)

BUTTONS = {}
FRESH = {}
SPELL_CHECK = {}
FILTER_MODE = {}

@Client.on_message(filters.group & filters.media)
async def media(client, message):
    userid = message.from_user.id        
    buttons = [[     
        InlineKeyboardButton("⚠️ ᴡᴀʀɴɪɴɢ ⚠️", callback_data="check_delete")
    ]]
    reply_markup = InlineKeyboardMarkup(buttons)
        
    k = await message.reply_photo(
        photo=random.choice(CHANNEL_PICS),
        caption=f"<b>ᴜsᴇʀ ɴᴀᴍᴇ: {message.from_user.mention} \nᴜsᴇʀ ɪᴅ:{userid} \n\nᴛʜɪs ɢʀᴏᴜᴘ ɴᴏᴛ ᴀʟʟᴏᴡᴇᴅ ʏᴏᴜʀ ғɪʟᴇs...ʟᴀsᴛ ᴡᴀʀɴɪɴɢ....</b>",
        reply_markup=reply_markup,
        parse_mode=enums.ParseMode.HTML
    )
    await asyncio.sleep(5)
    await k.delete()
    await message.delete()

@Client.on_message(filters.group & filters.text & filters.incoming)
async def give_filter(client, message):
    if message.chat.id != SUPPORT_CHAT_ID:
        glob = await global_filters(client, message)
        if glob == False:
            manual = await manual_filters(client, message)
            if manual == False:
                settings = await get_settings(message.chat.id)
                try:
                    if settings['auto_ffilter']:
                        await auto_filter(client, message)
                except KeyError:
                    grpid = await active_connection(str(message.from_user.id))
                    await save_group_settings(grpid, 'auto_ffilter', True)
                    settings = await get_settings(message.chat.id)
                    if settings['auto_ffilter']:
                        await auto_filter(client, message)
    else: #a better logic to avoid repeated lines of code in auto_filter function
        search = message.text
        temp_files, temp_offset, total_results = await get_search_results(chat_id=message.chat.id, query=search.lower(), offset=0, filter=True)
        if total_results == 0:
            return
        else:
            return await message.reply_text(f"<b>👋 ʜᴇʏ {message.from_user.mention},\n\n📂 ʀᴇsᴜʟᴛs ᴀʀᴇ ғᴏᴜɴᴅ {str(total_results)} ɪɴ ᴍʏ ᴅᴀᴛᴀʙᴀsᴇ ғᴏʀ ʏᴏᴜʀ ᴏ̨ᴜᴇʀʏ {search}.\n\n🌶️ ᴛʜɪs ɪs ᴀ sᴜᴘᴘᴏʀᴛ ɢʀᴏᴜᴘ sᴏ ᴛʜᴀᴛ ʏᴏᴜ ᴄᴀɴ'ᴛ ɢᴇᴛ ғɪʟᴇs ғʀᴏᴍ ʜᴇʀᴇ...\n\n📌 ᴊᴏɪɴ ᴀɴᴅ sᴇᴀʀᴄʜ ʜᴇʀᴇ - </b>",reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📝 ʀᴇǫᴜᴇsᴛ ʜᴇʀᴇ ", url=f"https://t.me/OMGxMovies/467")]]))

@Client.on_message(filters.private & filters.text & filters.incoming)
async def pm_text(bot, message):
    content = message.text
    user = message.from_user.first_name
    user_id = message.from_user.id
    if content.startswith("/") or content.startswith("#"): return  # ignore commands and hashtags
    await message.reply_text("<b>ʜᴇʏ ᴅᴜᴅᴇ 🥰,\n\nʏᴏᴜ ᴄᴀɴ'ᴛ ɢᴇᴛ ᴍᴏᴠɪᴇ ʜᴇʀᴇ........\nᴀꜱᴋ ᴍᴏᴠɪᴇ ᴏɴ ᴏᴜʀ ɢʀᴏᴜᴘ\nᴄʟɪᴄᴋ ᴏɴ ᴛʜᴇ ʙᴇʟᴏᴡ ʙᴜᴛᴛᴏɴ ᴛᴏ ᴊᴏɪɴ👇</b>",reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📝 ʀᴇǫᴜᴇsᴛ ʜᴇʀᴇ ", url=f"https://t.me/OMGxMovies/467")]]))
    await bot.send_message(
        chat_id=MSG_LOG_CHANNEL,
        text=f"<b>#ᴩᴍ_ᴍꜱɢ💌\n\nName : {user}\n\nID : {user_id}\n\nMessage : {content}</b>"
    )


@Client.on_callback_query(filters.regex(r"^next"))
async def next_page(bot, query):
    ident, req, key, offset = query.data.split("_")
    curr_time = datetime.now(pytz.timezone('Asia/Kolkata')).time()
    if int(req) not in [query.from_user.id, 0]:
        return await query.answer(script.ALRT_TXT.format(query.from_user.first_name), show_alert=True)
    try:
        offset = int(offset)
    except:
        offset = 0
    search = BUTTONS.get(key)
    if not search:
        await query.answer(script.OLD_ALRT_TXT.format(query.from_user.first_name),show_alert=True)
        return

    files, n_offset, total = await get_search_results(query.message.chat.id, search, offset=offset, filter=True)
    try:
        n_offset = int(n_offset)
    except:
        n_offset = 0

    if not files:
        return
    temp.GETALL[key] = files
    temp.SHORT[query.from_user.id] = query.message.chat.id
    settings = await get_settings(query.message.chat.id)
    pre = 'filep' if settings['file_secure'] else 'file'
    if settings['button']:
        btn = [
            [
                InlineKeyboardButton(
                    text=f"[{get_size(file.file_size)}] {' '.join(filter(lambda x: not x.startswith('[') and not x.startswith('@') and not x.startswith('www.'), file.file_name.split()))}", callback_data=f'{pre}#{file.file_id}'
                ),
            ]
            for file in files
        ]
    else:
        btn = []
        
    btn.insert(0,
        [
            InlineKeyboardButton("! ʟᴀɴɢᴜᴀɢᴇs !", callback_data=f"languages#{search.replace(' ', '_')}#{key}")
        ]
    )

    if 0 < offset <= 10:
        off_set = 0
    elif offset == 0:
        off_set = None
    else:
        off_set = offset - 10
    if n_offset == 0:
        btn.append(
            [InlineKeyboardButton("⇇ ʙᴀᴄᴋ", callback_data=f"next_{req}_{key}_{off_set}"),
             InlineKeyboardButton(f"📃 ᴩᴀɢᴇs {math.ceil(int(offset) / 10) + 1} / {math.ceil(total / 10)}",
                                  callback_data="pages")]
        )
    elif off_set is None:
        btn.append(
            [InlineKeyboardButton(f"🗓 {math.ceil(int(offset) / 10) + 1} / {math.ceil(total / 10)}", callback_data="pages"),
             InlineKeyboardButton("ɴᴇxᴛ ⇉", callback_data=f"next_{req}_{key}_{n_offset}")])
    else:
        btn.append(
            [
                InlineKeyboardButton("⇇ ʙᴀᴄᴋ", callback_data=f"next_{req}_{key}_{off_set}"),
                InlineKeyboardButton(f"🗓 {math.ceil(int(offset) / 10) + 1} / {math.ceil(total / 10)}", callback_data="pages"),
                InlineKeyboardButton("ɴᴇxᴛ ⇉", callback_data=f"next_{req}_{key}_{n_offset}")
            ],
        )
    cur_time = datetime.now(pytz.timezone('Asia/Kolkata')).time()
    time_difference = timedelta(hours=cur_time.hour, minutes=cur_time.minute, seconds=(cur_time.second+(cur_time.microsecond/1000000))) - timedelta(hours=curr_time.hour, minutes=curr_time.minute, seconds=(curr_time.second+(curr_time.microsecond/1000000)))
    remaining_seconds = "{:.2f}".format(time_difference.total_seconds())
    imdb = await get_poster(search, file=(files[0]).file_name) if settings["imdb"] else None
    if not settings["button"]:
        if settings["imdb"]:
            TEMPLATE = script.IMDB_TEMPLATE_TXT
            cap = TEMPLATE.format(
                qurey=search,
                title=imdb['title'],
                votes=imdb['votes'],
                aka=imdb["aka"],
                seasons=imdb["seasons"],
                box_office=imdb['box_office'],
                localized_title=imdb['localized_title'],
                kind=imdb['kind'],
                imdb_id=imdb["imdb_id"],
                cast=imdb["cast"],
                runtime=imdb["runtime"],
                countries=imdb["countries"],
                certificates=imdb["certificates"],
                languages=imdb["languages"],
                director=imdb["director"],
                writer=imdb["writer"],
                producer=imdb["producer"],
                composer=imdb["composer"],
                cinematographer=imdb["cinematographer"],
                music_team=imdb["music_team"],
                distributors=imdb["distributors"],
                release_date=imdb['release_date'],
                year=imdb['year'],
                genres=imdb['genres'],
                poster=imdb['poster'],
                plot=imdb['plot'],
                rating=imdb['rating'],
                url=imdb['url'],
                **locals()
            )
            cap+="<b>\n\n🔎 ʀᴇǫᴜᴇsᴛᴇᴅ ғɪʟᴇ 🥀</b>\n\n"
            for file in files:
                cap += f"<b>📁 <a href='https://telegram.me/{temp.U_NAME}?start=files_{file.file_id}'>[{get_size(file.file_size)}] {' '.join(filter(lambda x: not x.startswith('[') and not x.startswith('@') and not x.startswith('www.'), file.file_name.split()))}\n\n</a></b>"
        else:
            cap = f"<b>ʜᴇʏ {query.from_user.mention}👋, ғᴏᴜɴᴅ {total} 📂 ʀᴇsᴜʟᴛs ғᴏʀ ʏᴏᴜʀ ǫᴜᴇʀʏ <code>{search}</code>\n\n</b>"
            cap+="<b>🔎 ʀᴇǫᴜᴇsᴛᴇᴅ ғɪʟᴇ 🥀</b>\n\n"
            for file in files:
                cap += f"<b>📁 <a href='https://telegram.me/{temp.U_NAME}?start=files_{file.file_id}'>[{get_size(file.file_size)}] {' '.join(filter(lambda x: not x.startswith('[') and not x.startswith('@') and not x.startswith('www.'), file.file_name.split()))}\n\n</a></b>"
        try:
            cap += f"<b>⚠️ ᴛʜɪꜱ ᴍᴇꜱꜱᴀɢᴇ ᴡɪʟʟ ʙᴇ ᴀᴜᴛᴏ ᴅᴇʟᴇᴛᴇ ᴀғᴛᴇʀ 𝟷𝟶 ᴍɪɴᴜᴛᴇꜱ ᴛᴏ ᴀᴠᴏɪᴅ ᴄᴏᴘʏʀɪɢʜᴛ ɪꜱꜱᴜᴇꜱ</b>"
            await query.message.edit_text(text=cap, reply_markup=InlineKeyboardMarkup(btn), disable_web_page_preview=True)
        except MessageNotModified:
            pass
    else:
        try:
            await query.edit_message_reply_markup(
                reply_markup=InlineKeyboardMarkup(btn)
            )
        except MessageNotModified:
            pass
    await query.answer()


@Client.on_callback_query(filters.regex(r"^spol"))
async def advantage_spoll_choker(bot, query):
    _, user, movie_ = query.data.split('#')
    movies = SPELL_CHECK.get(query.message.reply_to_message.id)
    if not movies:
        return await query.answer(script.OLD_ALRT_TXT.format(query.from_user.first_name), show_alert=True)
    if int(user) != 0 and query.from_user.id != int(user):
        return await query.answer(script.ALRT_TXT.format(query.from_user.first_name), show_alert=True)
    if movie_ == "close_spellcheck":
        return await query.message.delete()
    movie = movies[(int(movie_))]
    await query.answer(script.TOP_ALRT_MSG, show_alert=True)
    gl = await global_filters(bot, query.message, text=movie)
    if gl == False:
        k = await manual_filters(bot, query.message, text=movie)
        if k == False:
            files, offset, total_results = await get_search_results(query.message.chat.id, movie, offset=0, filter=True)
            if files:
                k = (movie, files, offset, total_results)
                await auto_filter(bot, query, k)
            else:
                reqstr1 = query.from_user.id if query.from_user else 0
                reqstr = await bot.get_users(reqstr1)
                if NO_RESULTS_MSG:
                    await bot.send_message(chat_id=LOG_CHANNEL, text=(script.NORSLTS.format(reqstr.id, reqstr.mention, movie)))
                k = await query.message.edit(script.MVE_NT_FND)
                await asyncio.sleep(10)
                await k.delete()

@Client.on_callback_query(filters.regex(r"^languages#"))
async def languages_cb_handler(client: Client, query: CallbackQuery):

    if int(query.from_user.id) not in [query.message.reply_to_message.from_user.id, 0]:
        return await query.answer(
            f"⚠️ ʜᴇʟʟᴏ{query.from_user.first_name},\n\nᴛʜɪꜱ ɪꜱ ɴᴏᴛ ʏᴏᴜʀ ᴍᴏᴠɪᴇ ʀᴇǫᴜᴇꜱᴛ,\n\nʀᴇǫᴜᴇꜱᴛ ʏᴏᴜʀ'ꜱ...",
            show_alert=True,
        )
    
    _, search, key = query.data.split("#")

    btn = [
        [
            InlineKeyboardButton(
                text=lang.title(),
                callback_data=f"fl#{lang.lower()}#{search}#{key}"
                ),
        ]
        for lang in LANGUAGES
    ]

    btn.insert(
        0,
        [
            InlineKeyboardButton(
                text="⤵️ sᴇʟᴇᴄᴛ ʏᴏᴜʀ ʟᴀɴɢᴜᴀɢᴇs ⤵️", callback_data="ident"
            )
        ],
    )
    req = query.from_user.id
    offset = 0
    btn.append([InlineKeyboardButton(text="↭ ʙᴀᴄᴋ ᴛᴏ ꜰɪʟᴇs ​↭", callback_data=f"next_{req}_{key}_{offset}")])

    await query.edit_message_reply_markup(InlineKeyboardMarkup(btn))


@Client.on_callback_query(filters.regex(r"^fl#"))
async def filter_languages_cb_handler(client: Client, query: CallbackQuery):
    _, lang, search, key = query.data.split("#")

    search = search.replace("_", " ")
    req = query.from_user.id
    chat_id = query.message.chat.id
    message = query.message
    if int(req) not in [query.message.reply_to_message.from_user.id, 0]:
        return await query.answer(
            f"⚠️ ʜᴇʟʟᴏ{query.from_user.first_name},\n\nᴛʜɪꜱ ɪꜱ ɴᴏᴛ ʏᴏᴜʀ ᴍᴏᴠɪᴇ ʀᴇǫᴜᴇꜱᴛ,\n\nʀᴇǫᴜᴇꜱᴛ ʏᴏᴜʀ'ꜱ...",
            show_alert=True,
        )

    search = f"{search} {lang}" 

    files, _, _ = await get_search_results(chat_id, search, max_results=10)
    files = [file for file in files if re.search(lang, file.file_name, re.IGNORECASE)]
    if not files:
        await query.answer("✘ ɴᴏ ғɪʟᴇ ᴡᴇʀᴇ ғᴏᴜɴᴅ ✘", show_alert=1)
        return
    temp.GETALL[key] = files
    temp.SHORT[query.from_user.id] = query.message.chat.id
    settings = await get_settings(query.message.chat.id)
    curr_time = datetime.now(pytz.timezone('Asia/Kolkata')).time()
    pre = 'filep' if settings['file_secure'] else 'file'
    if settings['button']:
        btn = [
            [
                InlineKeyboardButton(
                    text=f"[{get_size(file.file_size)}] {' '.join(filter(lambda x: not x.startswith('[') and not x.startswith('@') and not x.startswith('www.'), file.file_name.split()))}", callback_data=f'{pre}#{file.file_id}'
                ),
            ]
            for file in files
        ]
    else:
        btn = []
        
    """btn.insert(0,
        [
            InlineKeyboardButton("! sᴇɴᴅ ᴀʟʟ ᴛᴏ ᴘᴍ !", callback_data=f"sendfiles#{key}")
        ]
    )"""
    total = 0
    cur_time = datetime.now(pytz.timezone('Asia/Kolkata')).time()
    time_difference = timedelta(hours=cur_time.hour, minutes=cur_time.minute, seconds=(cur_time.second+(cur_time.microsecond/1000000))) - timedelta(hours=curr_time.hour, minutes=curr_time.minute, seconds=(curr_time.second+(curr_time.microsecond/1000000)))
    remaining_seconds = "{:.2f}".format(time_difference.total_seconds())
    if settings["button"]:
        cap = f"<b>📟 ᴛɪᴛʟᴇ : {search} \n👩🏻‍💻 ʀᴇǫᴜᴇsᴛᴇᴅ ʙʏ : {query.from_user.mention} \n\n<code>⚠️ ᴛʜɪs ᴍᴇssᴀɢᴇ ᴡɪʟʟ ʙᴇ ᴀᴜᴛᴏ ᴅᴇʟᴇᴛᴇᴅ ᴀғᴛᴇʀ 𝟷𝟶 ᴍɪɴᴜᴛᴇs.</code></b>"
    else:
        cap = f"<b>👋 ʜᴇʏ {query.from_user.mention}\n\n🥀 ʜᴇʀᴇ ᴀʀᴇ ᴛʜᴇ ʀᴇꜱᴜʟᴛꜱ ꜰᴏʀ ʏᴏᴜʀ ǫᴜᴇʀʏ <code>{search}</code>\n\n</b>"
        for file in files:
            cap += f"<b>📁 <a href='https://telegram.me/{temp.U_NAME}?start=files_{file.file_id}'>[{get_size(file.file_size)}] {' '.join(filter(lambda x: not x.startswith('[') and not x.startswith('@') and not x.startswith('www.'), file.file_name.split()))}\n\n</a></b>"
            
    btn.insert(0, [
        InlineKeyboardButton("💢 ᴀᴅᴅ ᴍᴇ ᴛᴏ ɢʀᴏᴜᴘs 💢", url=f'http://t.me/{temp.U_NAME}?startgroup=true')
    ])
    offset = 0

    btn.append(
        [
            InlineKeyboardButton(text="⇇ ʙᴀᴄᴋ ᴛᴏ ғɪʟᴇs ⇉",callback_data=f"next_{req}_{key}_{offset}"),
        ])

    await query.message.edit_text(text=cap, reply_markup=InlineKeyboardMarkup(btn), disable_web_page_preview=True)

@Client.on_callback_query()
async def cb_handler(client: Client, query: CallbackQuery):
    if query.data == "close_data":
        await query.message.delete()
    elif query.data == "delallconfirm":
        userid = query.from_user.id
        chat_type = query.message.chat.type

        if chat_type == enums.ChatType.PRIVATE:
            grpid = await active_connection(str(userid))
            if grpid is not None:
                grp_id = grpid
                try:
                    chat = await client.get_chat(grpid)
                    title = chat.title
                except:
                    buttons = [[InlineKeyboardButton('⇇ ᴄʟᴏsᴇ ⇉', callback_data='close_data') ]]
                    await query.message.reply_text(text="<b>🥀 ᴍᴀᴋᴇ ꜱᴜʀᴇ I'ᴍ ᴘʀᴇꜱᴇɴᴛ ɪɴ ʏᴏᴜʀ ɢʀᴏᴜᴘ!! 📢</b>", reply_markup=InlineKeyboardMarkup(buttons), quote=True)
                    return await query.answer('𝙿𝙻𝙴𝙰𝚂𝙴 𝚂𝙷𝙰𝚁𝙴 𝙰𝙽𝙳 𝚂𝚄𝙿𝙿𝙾𝚁𝚃')
            else:
                buttons = [[InlineKeyboardButton('⇇ ᴄʟᴏsᴇ ⇉', callback_data='close_data') ]]
                await query.message.reply_text(text="<b>🥀 ɪ'ᴍ ɴᴏᴛ ᴄᴏɴɴᴇᴄᴛᴇᴅ ᴛᴏ ᴀɴʏ ɢʀᴏᴜᴘꜱ!!!📢\n\n✨ ᴄʜᴇᴄᴋ /connections ᴏʀ ᴄᴏɴɴᴇᴄᴛ ᴛᴏ ᴀɴʏ ɢʀᴏᴜᴘꜱ!!!📢</b>", reply_markup=InlineKeyboardMarkup(buttons) ,quote=True)
                return await query.answer(MSG_ALRT)

        elif chat_type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
            grp_id = query.message.chat.id
            title = query.message.chat.title

        else:
            return await query.answer('Piracy Is Crime')

        st = await client.get_chat_member(grp_id, userid)
        if (st.status == enums.ChatMemberStatus.OWNER) or (str(userid) in ADMINS):
            await del_all(query.message, grp_id, title)
        else:
            await query.answer("🥀 ʏᴏᴜ ɴᴇᴇᴅ ᴛᴏ ʙᴇ ɢʀᴏᴜᴘ ᴏᴡɴᴇʀ ᴏʀ ᴀɴ ᴀᴜᴛʜ ᴜꜱᴇʀ ᴛᴏ ᴅᴏ ᴛʜᴀᴛ !!! 📢", show_alert=True)
    elif query.data == "delallcancel":
        userid = query.from_user.id
        chat_type = query.message.chat.type

        if chat_type == enums.ChatType.PRIVATE:
            await query.message.reply_to_message.delete()
            await query.message.delete()

        elif chat_type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
            grp_id = query.message.chat.id
            st = await client.get_chat_member(grp_id, userid)
            if (st.status == enums.ChatMemberStatus.OWNER) or (str(userid) in ADMINS):
                await query.message.delete()
                try:
                    await query.message.reply_to_message.delete()
                except:
                    pass
            else:
                await query.answer("🥀 ʙᴜᴅᴅʏ ᴅᴏɴ'ᴛ ᴛᴏᴜᴄʜ ᴏᴛʜᴇʀꜱ ᴘʀᴏᴘᴇʀᴛʏ 🔎♻️", show_alert=True)
    elif "groupcb" in query.data:
        await query.answer()

        group_id = query.data.split(":")[1]

        act = query.data.split(":")[2]
        hr = await client.get_chat(int(group_id))
        title = hr.title
        user_id = query.from_user.id

        if act == "":
            stat = "ᴄᴏɴɴᴇᴄᴛ"
            cb = "connectcb"
        else:
            stat = "ᴅɪsᴄᴏɴɴᴇᴄᴛ"
            cb = "disconnect"

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(f"{stat}", callback_data=f"{cb}:{group_id}"),
             InlineKeyboardButton("⇇ ᴅᴇʟᴇᴛᴇ ⇉", callback_data=f"deletecb:{group_id}")],
            [InlineKeyboardButton("⇇ ʙᴀᴄᴋ ⇉", callback_data="backcb")]
        ])

        await query.message.edit_text(
            f"**📢 ɢʀᴏᴜᴘ ɴᴀᴍᴇ :- {title}\n\n✨ ɢʀᴏᴜᴘ ɪᴅ :- `{group_id}`**",
            reply_markup=keyboard,
            parse_mode=enums.ParseMode.MARKDOWN
        )
        return await query.answer(MSG_ALRT)
    elif "connectcb" in query.data:
        await query.answer()

        group_id = query.data.split(":")[1]

        hr = await client.get_chat(int(group_id))

        title = hr.title

        user_id = query.from_user.id

        mkact = await make_active(str(user_id), str(group_id))

        if mkact:
            buttons = [[InlineKeyboardButton('⇇ ᴄʟᴏsᴇ ⇉', callback_data='close_data') ]]
            await query.message.reply_text(f"**🛠️ ᴄᴏɴɴᴇᴄᴛᴇᴅ ᴛᴏ {title}**", parse_mode=enums.ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup(buttons))
        else:
            buttons = [[InlineKeyboardButton('⇇ ᴄʟᴏsᴇ ⇉', callback_data='close_data') ]]
            await query.message.reply_text(text='**🥀 sᴏᴍᴇ ᴇʀʀᴏʀ ᴏᴄᴄᴜʀʀᴇᴅ!!! 🥀**', parse_mode=enums.ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup(buttons))
        return await query.answer(MSG_ALRT)
    elif "disconnect" in query.data:
        await query.answer()

        group_id = query.data.split(":")[1]

        hr = await client.get_chat(int(group_id))

        title = hr.title
        user_id = query.from_user.id

        mkinact = await make_inactive(str(user_id))

        if mkinact:
            buttons = [[InlineKeyboardButton('⇇ ᴄʟᴏsᴇ ⇉', callback_data='close_data') ]]
            await query.message.reply_text(f"**⚒️ ᴅɪsᴄᴏɴɴᴇᴄᴛ ғʀᴏᴍ {title}**",parse_mode=enums.ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup(buttons))
        else:
            buttons = [[InlineKeyboardButton('⇇ ᴄʟᴏsᴇ ⇉', callback_data='close_data') ]]
            await query.message.reply_text(text="**🥀 sᴏᴍᴇ ᴇʀʀᴏʀ ᴏᴄᴄᴜʀʀᴇᴅ!!! 🥀**",parse_mode=enums.ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup(buttons))
        return await query.answer(MSG_ALRT)
    elif "deletecb" in query.data:
        await query.answer()

        user_id = query.from_user.id
        group_id = query.data.split(":")[1]

        delcon = await delete_connection(str(user_id), str(group_id))

        if delcon:
            buttons = [[InlineKeyboardButton('⇇ ᴄʟᴏsᴇ ⇉', callback_data='close_data') ]]
            await query.message.reply_text(text="**🥀 sᴜᴄᴄᴇssғᴜʟʟʏ ᴅᴇʟᴇᴛᴇᴅ ᴄᴏɴɴᴇᴄᴛɪᴏɴ !!!✅**", reply_markup=InlineKeyboardMarkup(buttons))
        else:
            buttons = [[InlineKeyboardButton('⇇ ᴄʟᴏsᴇ ⇉', callback_data='close_data') ]]
            await query.message.reply_text(text="**🥀 sᴏᴍᴇ ᴇʀʀᴏʀ ᴏᴄᴄᴜʀʀᴇᴅ!!! 🥀**", parse_mode=enums.ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup(buttons))
        return await query.answer(MSG_ALRT)
    elif query.data == "backcb":
        await query.answer()

        userid = query.from_user.id

        groupids = await all_connections(str(userid))
        if groupids is None:
            buttons = [[InlineKeyboardButton('⇇ ᴄʟᴏsᴇ ⇉', callback_data='close_data') ]]
            await query.message.reply_text(text="**🥀 ᴛʜᴇʀᴇ ᴀʀᴇ ɴᴏ ᴀᴄᴛɪᴠᴇ ᴄᴏɴɴᴇᴄᴛɪᴏɴs!!! ᴄᴏɴɴᴇᴄᴛ ᴛᴏ sᴏᴍᴇ ɢʀᴏᴜᴘs ғɪʀsᴛ...❗❗❗**", reply_markup=InlineKeyboardMarkup(buttons))
            return await query.answer(MSG_ALRT)
        buttons = []
        for groupid in groupids:
            try:
                ttl = await client.get_chat(int(groupid))
                title = ttl.title
                active = await if_active(str(userid), str(groupid))
                act = " - ACTIVE" if active else ""
                buttons.append(
                    [
                        InlineKeyboardButton(
                            text=f"{title}{act}", callback_data=f"groupcb:{groupid}:{act}"
                        )
                    ]
                )
            except:
                pass
        if buttons:
            await query.message.edit_text(
                "**🥀 ʏᴏᴜʀ ᴄᴏɴɴᴇᴄᴛᴇᴅ ɢʀᴏᴜᴘ ᴅᴇᴛᴀɪʟs ;✨**\n\n",
                reply_markup=InlineKeyboardMarkup(buttons)
            )
    elif "alertmessage" in query.data:
        grp_id = query.message.chat.id
        i = query.data.split(":")[1]
        keyword = query.data.split(":")[2]
        reply_text, btn, alerts, fileid = await find_filter(grp_id, keyword)
        if alerts is not None:
            alerts = ast.literal_eval(alerts)
            alert = alerts[int(i)]
            alert = alert.replace("\\n", "\n").replace("\\t", "\t")
            await query.answer(alert, show_alert=True)
            
    if query.data.startswith("file"):
        clicked = query.from_user.id
        try:
            typed = query.message.reply_to_message.from_user.id
        except:
            typed = query.from_user.id
        ident, file_id = query.data.split("#")
        files_ = await get_file_details(file_id)
        if not files_:
            return await query.answer('🥀 ɴᴏ sᴜᴄʜ ғɪʟᴇ ᴇxɪsᴛ ✨')
        files = files_[0]
        title = files.file_name
        size = get_size(files.file_size)
        f_caption = files.caption
        settings = await get_settings(query.message.chat.id)
        if CUSTOM_FILE_CAPTION:
            try:
                f_caption = CUSTOM_FILE_CAPTION.format(file_name='' if title is None else title,
                                                       file_size='' if size is None else size,
                                                       file_caption='' if f_caption is None else f_caption)
            except Exception as e:
                logger.exception(e)
            f_caption = f_caption
        if f_caption is None:
            f_caption = f"{files.file_name}"
        try:
            if AUTH_CHANNEL and not await is_subscribed(client, query):
                if clicked == typed:
                    await query.answer(url=f"https://telegram.me/{temp.U_NAME}?start={ident}_{file_id}")
                    return
                else:
                    await query.answer(f"Hᴇʏ {query.from_user.first_name}, Tʜɪs Is Nᴏᴛ Yᴏᴜʀ Mᴏᴠɪᴇ Rᴇǫᴜᴇsᴛ. Rᴇǫᴜᴇsᴛ Yᴏᴜʀ's !", show_alert=True)
            elif settings['botpm'] and settings['is_shortlink'] and clicked not in PREMIUM_USER:
                if clicked == typed:
                    temp.SHORT[clicked] = query.message.chat.id
                    await query.answer(url=f"https://telegram.me/{temp.U_NAME}?start=short_{file_id}")
                    return
                else:
                    await query.answer(f"Hᴇʏ {query.from_user.first_name}, Tʜɪs Is Nᴏᴛ Yᴏᴜʀ Mᴏᴠɪᴇ Rᴇǫᴜᴇsᴛ. Rᴇǫᴜᴇsᴛ Yᴏᴜʀ's !", show_alert=True)
            elif settings['is_shortlink'] and not settings['botpm'] and clicked not in PREMIUM_USER:
                if clicked == typed:
                    temp.SHORT[clicked] = query.message.chat.id
                    await query.answer(url=f"https://telegram.me/{temp.U_NAME}?start=short_{file_id}")
                    return
                else:
                    await query.answer(f"Hᴇʏ {query.from_user.first_name}, Tʜɪs Is Nᴏᴛ Yᴏᴜʀ Mᴏᴠɪᴇ Rᴇǫᴜᴇsᴛ. Rᴇǫᴜᴇsᴛ Yᴏᴜʀ's !", show_alert=True)
            elif settings['botpm'] or clicked in PREMIUM_USER:
                if clicked == typed:
                    await query.answer(url=f"https://telegram.me/{temp.U_NAME}?start={ident}_{file_id}")
                    return
                else:
                    await query.answer(f"Hᴇʏ {query.from_user.first_name}, Tʜɪs Is Nᴏᴛ Yᴏᴜʀ Mᴏᴠɪᴇ Rᴇǫᴜᴇsᴛ. Rᴇǫᴜᴇsᴛ Yᴏᴜʀ's !", show_alert=True)
            else:
                mh = await client.send_cached_media(
                    chat_id=FILE_CHANNEL,
                    file_id=file_id,
                    caption=script.CHANNEL_CAP.format(query.from_user.mention, title, size),
                    protect_content=True if ident == "filep" else False,
                    reply_markup=InlineKeyboardMarkup(
                            [[
                                InlineKeyboardButton("🎭 sɪᴠᴇʀᴏᴢ ʟɪɴᴋᴢᴢ 🎭", url=f"{MAIN_CHANNEL}")
                            ]]))
                mh8 = await query.message.reply(script.FILE_MSG.format(query.from_user.mention, title, size),
                True,
                enums.ParseMode.HTML,
                disable_web_page_preview=True,
                reply_markup=InlineKeyboardMarkup(
                    [[
                        InlineKeyboardButton('📂 ᴅᴏᴡɴʟᴏᴀᴅ ʟɪɴᴋ 📂', url=f"{mh.link}")
                    ],[
                        InlineKeyboardButton("⚠️ ᴄᴀɴ'ᴛ ᴀᴄᴄᴇss❓ ᴄʟɪᴄᴋ ʜᴇʀᴇ ⚠️", url=(FILE_CHANNEL_LINK))
                    ]]
                ))
            await asyncio.sleep(800)
            await mh8.delete()
            await mh.delete()
            del mh8, mh
        except Exception as e:
            logger.exception(e, exc_info=True)

    elif query.data.startswith("sendfiles"):
        clicked = query.from_user.id
        ident, key = query.data.split("#")
        settings = await get_settings(query.message.chat.id)
        try:
            if settings['botpm'] and settings['is_shortlink'] and clicked not in PREMIUM_USER:
                await query.answer(url=f"https://telegram.me/{temp.U_NAME}?start=sendfiles1_{key}")
                return
            elif settings['is_shortlink'] and not settings['botpm'] and clicked not in PREMIUM_USER:
                await query.answer(url=f"https://telegram.me/{temp.U_NAME}?start=sendfiles2_{key}")
                return
            else:
                await query.answer(url=f"https://telegram.me/{temp.U_NAME}?start=allfiles_{key}")
                return
        except UserIsBlocked:
            await query.answer('Uɴʙʟᴏᴄᴋ ᴛʜᴇ ʙᴏᴛ ᴍᴀʜɴ !', show_alert=True)
        except PeerIdInvalid:
            await query.answer(url=f"https://telegram.me/{temp.U_NAME}?start=sendfiles3_{key}")
        except Exception as e:
            logger.exception(e)
            await query.answer(url=f"https://telegram.me/{temp.U_NAME}?start=sendfiles4_{key}")

    elif query.data.startswith("del"):
        ident, file_id = query.data.split("#")
        files_ = await get_file_details(file_id)
        if not files_:
            return await query.answer('Nᴏ sᴜᴄʜ ғɪʟᴇ ᴇxɪsᴛ.')
        files = files_[0]
        title = files.file_name
        size = get_size(files.file_size)
        f_caption = files.caption
        settings = await get_settings(query.message.chat.id)
        if CUSTOM_FILE_CAPTION:
            try:
                f_caption = CUSTOM_FILE_CAPTION.format(file_name='' if title is None else title,
                                                       file_size='' if size is None else size,
                                                       file_caption='' if f_caption is None else f_caption)
            except Exception as e:
                logger.exception(e)
            f_caption = f_caption
        if f_caption is None:
            f_caption = f"{files.file_name}"
        await query.answer(url=f"https://telegram.me/{temp.U_NAME}?start=file_{file_id}")
            
    elif query.data.startswith("checksub"):
        if AUTH_CHANNEL and not await is_subscribed(client, query):
            await query.answer("I Like Your Smartness, But Don't Be Oversmart Okay 😒", show_alert=True)
            return
        ident, file_id = query.data.split("#")
        files_ = await get_file_details(file_id)
        if not files_:
            return await query.answer('No such file exist.')
        files = files_[0]
        title = files.file_name
        size = get_size(files.file_size)
        f_caption = files.caption
        if CUSTOM_FILE_CAPTION:
            try:
                f_caption = CUSTOM_FILE_CAPTION.format(file_name='' if title is None else title,
                                                       file_size='' if size is None else size,
                                                       file_caption='' if f_caption is None else f_caption)
            except Exception as e:
                logger.exception(e)
                f_caption = f_caption
        if f_caption is None:
            f_caption = f"{title}"
        await query.answer()
        await client.send_cached_media(
            chat_id=query.from_user.id,
            file_id=file_id,
            caption=f_caption,
            protect_content=True if ident == 'checksubp' else False
        )

    elif query.data == "predvd":
        k = await client.send_message(chat_id=query.message.chat.id, text="<b>Deleting PreDVDs... Please wait...</b>")
        files, next_offset, total = await get_bad_files(
                                                  'predvd',
                                                  offset=0)
        deleted = 0
        for file in files:
            file_ids = file.file_id
            result = await Media.collection.delete_one({
                '_id': file_ids,
            })
            if result.deleted_count:
                logger.info('PreDVD File Found ! Successfully deleted from database.')
            deleted+=1
        deleted = str(deleted)
        await k.edit_text(text=f"<b>Successfully deleted {deleted} PreDVD files.</b>")

    elif query.data == "camrip":
        k = await client.send_message(chat_id=query.message.chat.id, text="<b>Deleting CamRips... Please wait...</b>")
        files, next_offset, total = await get_bad_files(
                                                  'camrip',
                                                  offset=0)
        deleted = 0
        for file in files:
            file_ids = file.file_id
            result = await Media.collection.delete_one({
                '_id': file_ids,
            })
            if result.deleted_count:
                logger.info('CamRip File Found ! Successfully deleted from database.')
            deleted+=1
        deleted = str(deleted)
        await k.edit_text(text=f"<b>Successfully deleted {deleted} CamRip files.</b>")

    elif query.data.startswith("killfilesdq"):
        ident, keyword = query.data.split("#")
        await query.message.edit_text(f"<b>Fetching Files for your query {keyword} on DB... Please wait...</b>")
        files, total = await hs_bad_files(keyword)
        await query.message.edit_text(f"<b>Found {total} files for your query {keyword} !\n\nFile deletion process will start in 5 seconds !</b>")
        await asyncio.sleep(5)
        deleted = 0
        async with lock:
            try:
                for file in files:
                    file_ids = file.file_id
                    file_name = file.file_name
                    result = await Media.collection.delete_one({
                        '_id': file_ids,
                    })
                    if result.deleted_count:
                        logger.info(f'File Found for your query {keyword}! Successfully deleted {file_name} from database.')
                    deleted += 1
                    if deleted % 20 == 0:
                        await query.message.edit_text(f"<b>Process started for deleting files from DB. Successfully deleted {str(deleted)} files from DB for your query {keyword} !\n\nPlease wait...</b>")
            except Exception as e:
                logger.exception(e)
                await query.message.edit_text(f'Error: {e}')
            else:
                await query.message.edit_text(f"<b>Process Completed for file deletion !\n\nSuccessfully deleted {str(deleted)} files from database for your query {keyword}.</b>")
                
    elif query.data == "pages":
        await query.answer()

    elif query.data == "rendering_info":
        await query.answer(text=script.RENDERING_TXT, show_alert=True)

    elif query.data == "start":
        buttons = [[
            InlineKeyboardButton('〆 ᴀᴅᴅ ᴍᴇ ᴛᴏ ʏᴏᴜʀ ɢʀᴏᴜᴘ 〆', url=f'http://t.me/{temp.U_NAME}?startgroup=true')
            ],[
            InlineKeyboardButton('🧑‍💻 ᴏᴡɴᴇʀ', callback_data='owner_info'),
            InlineKeyboardButton('💡 sᴜᴘᴘᴏʀᴛ', callback_data='support')
            ],[
            InlineKeyboardButton('💠 ʜᴇʟᴘ 💠', callback_data='help'),
            InlineKeyboardButton('♻️ ᴀʙᴏᴜᴛ ♻️', callback_data='about')
            ],[
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await client.edit_message_media(
            query.message.chat.id, 
            query.message.id, 
            InputMediaPhoto(random.choice(PICS))
        )
        await query.message.edit_text(
            text=script.START_TXT.format(query.from_user.mention, temp.U_NAME, temp.B_NAME),
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
        await query.answer(MSG_ALRT)
    elif query.data == "help":
        buttons = [[
            InlineKeyboardButton('ғɪʟᴛᴇʀs', callback_data='filters'),
            InlineKeyboardButton('ғɪʟᴇ sᴛᴏʀᴇ', callback_data='store_file')
        ], [
            InlineKeyboardButton('ᴄᴏɴɴᴇᴄᴛɪᴏɴ', callback_data='coct'),
            InlineKeyboardButton('ᴇxᴛʀᴀ ᴍᴏᴅs', callback_data='extra')
        ], [
            InlineKeyboardButton('ʀᴏᴜʟs', callback_data='rule_btn'),
            InlineKeyboardButton('sᴇᴛᴛɪɴɢs', callback_data='setting_btn')
        ], [
            InlineKeyboardButton('⇇ ʙᴀᴄᴋ ᴛᴏ ʜᴏᴍᴇ ⇉', callback_data='start')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await client.edit_message_media(
            query.message.chat.id, 
            query.message.id, 
            InputMediaPhoto(random.choice(PICS))
        )
        await query.message.edit_text(
            text=script.HELP_TXT.format(query.from_user.mention),
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
    elif query.data == "about":
        buttons = [[
            InlineKeyboardButton('∙ sᴛᴀᴛᴜs ∙', callback_data='stats'),
            InlineKeyboardButton('∙ sᴏᴜʀᴄᴇ ᴄᴏᴅᴇ ∙', callback_data='source')
        ],[
            InlineKeyboardButton('📡 ʀᴇɴᴅᴇʀɪɴɢ ɪɴꜰᴏ ⛈️', callback_data='rendering_info')
        ],[
            InlineKeyboardButton('♙ ʜᴏᴍᴇ', callback_data='start'),
            InlineKeyboardButton('ᴄʟᴏsᴇ ⊝', callback_data='close_data')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await client.edit_message_media(
            query.message.chat.id, 
            query.message.id, 
            InputMediaPhoto(random.choice(PICS))
        )
        await query.message.edit_text(
            text=script.ABOUT_TXT.format(temp.B_NAME),
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
    elif query.data == "filters":
        buttons = [[
            InlineKeyboardButton('🍁 ᴍᴀɴᴜᴀʟ ғɪʟᴛᴇʀ 🍁', callback_data='manuelfilter'),
            InlineKeyboardButton('🍃 ᴀᴜᴛᴏ ғɪʟᴛᴇʀ 🍃', callback_data='autofilter')
        ],[
            InlineKeyboardButton('🥀 ɢʟᴏʙᴀʟ ғɪʟᴛᴇʀs 🥀', callback_data='global_filters')
        ],[
            InlineKeyboardButton('⇇ ʙᴀᴄᴋ ᴛᴏ ʜᴇʟᴘ ⇉', callback_data='help')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await client.edit_message_media(
            query.message.chat.id, 
            query.message.id, 
            InputMediaPhoto(random.choice(PICS))
        )
        await query.message.edit_text(
            text=script.ALL_FILTERS.format(query.from_user.mention),
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
    elif query.data == "setting_btn":
        buttons = [[
            InlineKeyboardButton('⇇ ʙᴀᴄᴋ ⇉', callback_data='help')
        ]]
        await client.edit_message_media(
            query.message.chat.id, 
            query.message.id, 
            InputMediaPhoto(random.choice(PICS))
        )
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.SETTING_TXT,
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
    elif query.data == "rule_btn":
        buttons = [[
            InlineKeyboardButton('⇇ ʙᴀᴄᴋ ⇉', callback_data='help')
        ]]
        await client.edit_message_media(
            query.message.chat.id, 
            query.message.id, 
            InputMediaPhoto(random.choice(RULES_PICS))
        )
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.RULE_TXT,
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
    elif query.data == "global_filters":
        buttons = [[
            InlineKeyboardButton('⇇ ʙᴀᴄᴋ ⇉', callback_data='filters')
        ]]
        await client.edit_message_media(
            query.message.chat.id, 
            query.message.id, 
            InputMediaPhoto(random.choice(PICS))
        )
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.GFILTER_TXT,
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
    elif query.data == "owner_info":
        buttons = [[
            InlineKeyboardButton('⇇ ʙᴀᴄᴋ ᴛᴏ ʜᴏᴍᴇ ⇉', callback_data='start')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await client.edit_message_media(
            query.message.chat.id, 
            query.message.id, 
            InputMediaPhoto(random.choice(PICS))
        )
        await query.message.edit_text(
            text=script.OWNER_TXT,
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
    elif query.data == "money_bot":
        buttons = [[
            InlineKeyboardButton('🔺 ᴄᴏɴɴᴇᴄᴛ ʏᴏᴜ sʜᴏʀᴛɴᴇʀ 🔻', callback_data='shorter')
        ],[
            InlineKeyboardButton('⇇ ʙᴀᴄᴋ', callback_data='start'),
            InlineKeyboardButton('ᴄʟᴏsᴇ ⊝', callback_data='close_data')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await client.edit_message_media(
            query.message.chat.id, 
            query.message.id, 
            InputMediaPhoto(random.choice(MONEY_PICS))
        )
        await query.message.edit_text(
            text=script.EARN_TXT,
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
    elif query.data == "shorter":
        buttons = [[
            InlineKeyboardButton('⇇ ʙᴀᴄᴋ ⇉', callback_data='money_bot')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await client.edit_message_media(
            query.message.chat.id, 
            query.message.id, 
            InputMediaPhoto(random.choice(SHORTER_PICS))
        )
        await query.message.edit_text(
            text=script.SHORTER_TXT,
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
    elif query.data == "support":
        buttons = [[
            InlineKeyboardButton('⇇ ʙᴀᴄᴋ ᴛᴏ ʜᴏᴍᴇ ⇉', callback_data='start')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await client.edit_message_media(
            query.message.chat.id, 
            query.message.id, 
            InputMediaPhoto(random.choice(SUPPORT_PICS))
        )
        await query.message.edit_text(
            text=script.SUPPORT_TXT,
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
    elif query.data == "source":
        buttons = [[
            InlineKeyboardButton('⇇ ʙᴀᴄᴋ ⇉', callback_data='about')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await client.edit_message_media(
            query.message.chat.id, 
            query.message.id, 
            InputMediaPhoto(random.choice(PICS))
        )
        await query.message.edit_text(
            text=script.SOURCE_TXT,
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
    elif query.data == "manuelfilter":
        buttons = [[
            InlineKeyboardButton('⚕️ ʙᴜᴛᴛᴏɴs ⚕️', callback_data='button')
        ],[
            InlineKeyboardButton('⇇ ʙᴀᴄᴋ ⇉', callback_data='filters')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await client.edit_message_media(
            query.message.chat.id, 
            query.message.id, 
            InputMediaPhoto(random.choice(PICS))
        )
        await query.message.edit_text(
            text=script.MANUELFILTER_TXT,
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
    elif query.data == "button":
        buttons = [[
            InlineKeyboardButton('⇇ ʙᴀᴄᴋ ⇉', callback_data='manuelfilter')
        ]]
        await client.edit_message_media(
            query.message.chat.id, 
            query.message.id, 
            InputMediaPhoto(random.choice(PICS))
        )
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.BUTTON_TXT,
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
    elif query.data == "autofilter":
        buttons = [[
            InlineKeyboardButton('⇇ ʙᴀᴄᴋ ⇉', callback_data='filters')
        ]]
        await client.edit_message_media(
            query.message.chat.id, 
            query.message.id, 
            InputMediaPhoto(random.choice(PICS))
        )
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.AUTOFILTER_TXT,
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
    elif query.data == "coct":
        buttons = [[
            InlineKeyboardButton('⇇ ʙᴀᴄᴋ ⇉', callback_data='help')
        ]]
        await client.edit_message_media(
            query.message.chat.id, 
            query.message.id, 
            InputMediaPhoto(random.choice(PICS))
        )
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.CONNECTION_TXT,
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
    elif query.data == "extra":
        buttons = [[
            InlineKeyboardButton('🧑‍💻 ᴀᴅᴍɪɴ 🧑‍💻', callback_data='admin')
        ],[
            InlineKeyboardButton('⇇ ʙᴀᴄᴋ ⇉', callback_data='help')
        ]]
        await client.edit_message_media(
            query.message.chat.id, 
            query.message.id, 
            InputMediaPhoto(random.choice(PICS))
        )
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.EXTRAMOD_TXT,
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
    
    elif query.data == "store_file":
        buttons = [[
            InlineKeyboardButton('⇇ ʙᴀᴄᴋ ⇉', callback_data='help')
        ]]
        await client.edit_message_media(
            query.message.chat.id, 
            query.message.id, 
            InputMediaPhoto(random.choice(PICS))
        )
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.FILE_STORE_TXT,
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
    
    elif query.data == "admin":
        buttons = [[
            InlineKeyboardButton('⇇ ʙᴀᴄᴋ ⇉', callback_data='extra')
        ]]
        await client.edit_message_media(
            query.message.chat.id, 
            query.message.id, 
            InputMediaPhoto(random.choice(PICS))
        )
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.ADMIN_TXT,
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
    elif query.data == "stats":
        buttons = [[
            InlineKeyboardButton('⇇ ʙᴀᴄᴋ', callback_data='about'),
            InlineKeyboardButton('ʀᴇғʀᴇsʜ ⟲', callback_data='rfrsh')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        total = await Media.count_documents()
        users = await db.total_users_count()
        chats = await db.total_chat_count()
        monsize = await db.get_db_size()
        free = 536870912 - monsize
        monsize = get_size(monsize)
        free = get_size(free)
        await query.message.edit_text(
            text=script.STATUS_TXT.format(total, users, chats, monsize, free),
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
    elif query.data == "rfrsh":
        await query.answer("Fetching MongoDb DataBase")
        buttons = [[
            InlineKeyboardButton('⇇ ʙᴀᴄᴋ', callback_data='help'),
            InlineKeyboardButton('ʀᴇғʀᴇsʜ ⟲', callback_data='rfrsh')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        total = await Media.count_documents()
        users = await db.total_users_count()
        chats = await db.total_chat_count()
        monsize = await db.get_db_size()
        free = 536870912 - monsize
        monsize = get_size(monsize)
        free = get_size(free)
        await query.message.edit_text(
            text=script.STATUS_TXT.format(total, users, chats, monsize, free),
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
    elif query.data.startswith("setgs"):
        ident, set_type, status, grp_id = query.data.split("#")
        grpid = await active_connection(str(query.from_user.id))

        if set_type == 'botpm' and query.from_user.id not in ADMINS:
            return await query.answer(text=f"🥀 ʜᴇʏ {query.from_user.first_name},\n\nʏᴏᴜ ᴄᴀɴ'ᴛ ᴄʜᴀɴɢᴇ ғɪʟᴇ sᴇɴᴅ ᴍᴏᴅᴇ sᴇᴛᴛɪɴɢs ғᴏʀ ʏᴏᴜʀ ɢʀᴏᴜᴘ !\n\nɪᴛ's ᴀɴ ᴀᴅᴍɪɴ ᴏɴʟʏ sᴇᴛᴛɪɴɢ !", show_alert=True)

        if set_type == 'is_shortlink' and query.from_user.id not in ADMINS:
            return await query.answer(text=f"🥀 ʜᴇʏ {query.from_user.first_name},\n\nʏᴏᴜ ᴄᴀɴ'ᴛ ᴄʜᴀɴɢᴇ sʜᴏʀᴛʟɪɴᴋ sᴇᴛᴛɪɴɢs ғᴏʀ ʏᴏᴜʀ ɢʀᴏᴜᴘ !\n\nɪᴛ's ᴀɴ ᴀᴅᴍɪɴ ᴏɴʟʏ sᴇᴛᴛɪɴɢ !", show_alert=True)

        if str(grp_id) != str(grpid):
            buttons = [[InlineKeyboardButton('⇇ ᴄʟᴏsᴇ ⇉', callback_data='close_data') ]]
            await query.message.edit("**🥀 ʏᴏᴜʀ ᴀᴄᴛɪᴠᴇ ᴄᴏɴɴᴇᴄᴛɪᴏɴ ʜᴀꜱ ʙᴇᴇɴ ᴄʜᴀɴɢᴇᴅ. ɢᴏ ᴛᴏ /settings ✨**", reply_markup=InlineKeyboardMarkup(buttons))
            return await query.answer('𝙿𝙻𝙴𝙰𝚂𝙴 𝚂𝙷𝙰𝚁𝙴 𝙰𝙽𝙳 𝚂𝚄𝙿𝙿𝙾𝚁𝚃')

        if status == "True":
            await save_group_settings(grpid, set_type, False)
        else:
            await save_group_settings(grpid, set_type, True)

        settings = await get_settings(grpid)

        if settings is not None:
            buttons = [
                [
                    InlineKeyboardButton('ʀᴇsᴜʟᴛ ᴘᴀɢᴇ 📃',
                                         callback_data=f'setgs#button#{settings["button"]}#{str(grp_id)}'),
                    InlineKeyboardButton('ʙᴜᴛᴛᴏɴ ⌨️' if settings["button"] else 'ᴛᴇxᴛ 📝',
                                         callback_data=f'setgs#button#{settings["button"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('ғɪʟᴇ sᴇɴᴅ ᴍᴏᴅᴇ 📂', callback_data=f'setgs#botpm#{settings["botpm"]}#{str(grp_id)}'),
                    InlineKeyboardButton('ʙᴏᴛ ᴘᴍ' if settings["botpm"] else 'ᴄʜᴀɴɴᴇʟ',
                                         callback_data=f'setgs#botpm#{settings["botpm"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('ғɪʟᴇ sᴇᴄᴜʀᴇ 🖌️',
                                         callback_data=f'setgs#file_secure#{settings["file_secure"]}#{str(grp_id)}'),
                    InlineKeyboardButton('✔ ᴇɴᴀʙʟᴇ' if settings["file_secure"] else '✘ ᴅɪsᴀʙʟᴇ',
                                         callback_data=f'setgs#file_secure#{settings["file_secure"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('ɪᴍᴅʙ ᴘᴏsᴛᴇʀ 🎭', callback_data=f'setgs#imdb#{settings["imdb"]}#{str(grp_id)}'),
                    InlineKeyboardButton('✔ ᴇɴᴀʙʟᴇ' if settings["imdb"] else '✘ ᴅɪsᴀʙʟᴇ',
                                         callback_data=f'setgs#imdb#{settings["imdb"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('sᴘᴇʟʟ ᴄʜᴇᴄᴋ 🔎',
                                         callback_data=f'setgs#spell_check#{settings["spell_check"]}#{str(grp_id)}'),
                    InlineKeyboardButton('✔ ᴇɴᴀʙʟᴇ' if settings["spell_check"] else '✘ ᴅɪsᴀʙʟᴇ',
                                         callback_data=f'setgs#spell_check#{settings["spell_check"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('ᴡᴇʟᴄᴏᴍᴇ ᴍᴇɢ 🥀', callback_data=f'setgs#welcome#{settings["welcome"]}#{str(grp_id)}'),
                    InlineKeyboardButton('✔ ᴇɴᴀʙʟᴇ' if settings["welcome"] else '✘ ᴅɪsᴀʙʟᴇ',
                                         callback_data=f'setgs#welcome#{settings["welcome"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('sʜᴏʀᴛɴᴇʀ ʟɪɴᴋ 🖇️',
                                         callback_data=f'setgs#is_shortlink#{settings["is_shortlink"]}#{str(grp_id)}'),
                    InlineKeyboardButton('✔ ᴇɴᴀʙʟᴇ' if settings["is_shortlink"] else '✘ ᴅɪsᴀʙʟᴇ',
                                         callback_data=f'setgs#is_shortlink#{settings["is_shortlink"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('✘ ᴄʟᴏsᴇ sᴇᴛᴛɪɴɢs ✘', callback_data='close_data')
                ]
            ]
            reply_markup = InlineKeyboardMarkup(buttons)
            await query.message.edit_reply_markup(reply_markup)
    await query.answer(MSG_ALRT)


async def auto_filter(client, msg, spoll=False):
    curr_time = datetime.now(pytz.timezone('Asia/Kolkata')).time()
    if not spoll:
        message = msg
        if message.text.startswith("/"): return  # ignore commands
        if re.findall("((^\/|^,|^!|^\.|^[\U0001F600-\U000E007F]).*)", message.text):
            return
        if len(message.text) < 100:
            search = message.text
            m=await message.reply_text(f"🔍")
            await m.delete()
            search = search.lower()
            find = search.split(" ")
            search = ""
            removes = ["in","upload", "series", "full", "horror", "thriller", "mystery", "print", "file"]
            for x in find:
                if x in removes:
                    continue
                else:
                    search = search + x + " "
            search = re.sub(r"\b(pl(i|e)*?(s|z+|ease|se|ese|(e+)s(e)?)|((send|snd|giv(e)?|gib)(\sme)?)|movie(s)?|new|latest|bro|bruh|broh|helo|that|find|dubbed|link|venum|iruka|pannunga|pannungga|anuppunga|anupunga|anuppungga|anupungga|film|undo|kitti|kitty|tharu|kittumo|kittum|movie|any(one)|with\ssubtitle(s)?)", "", search, flags=re.IGNORECASE)
            search = re.sub(r"\s+", " ", search).strip()
            search = search.replace("-", " ")
            search = search.replace(":","")
            files, offset, total_results = await get_search_results(message.chat.id ,search, offset=0, filter=True)
            settings = await get_settings(message.chat.id)
            if not files:
                #await m.delete()
                if settings["spell_check"]:
                    return await advantage_spell_chok(client, msg)
                else:
                    return
        else:
            return
    else:
        message = msg.message.reply_to_message  # msg will be callback query
        search, files, offset, total_results = spoll
        m=await message.reply_text(f"🔍")
        await m.delete()
        settings = await get_settings(message.chat.id)
        await msg.message.delete()
    pre = 'filep' if settings['file_secure'] else 'file'
    key = f"{message.chat.id}-{message.id}"
    FRESH[key] = search
    temp.GETALL[key] = files
    temp.SHORT[message.from_user.id] = message.chat.id
    if settings['button']:
        btn = [
            [
                InlineKeyboardButton(
                    text=f"[{get_size(file.file_size)}] {' '.join(filter(lambda x: not x.startswith('[') and not x.startswith('@') and not x.startswith('www.'), file.file_name.split()))}", callback_data=f'{pre}#{file.file_id}'
                ),
            ]
            for file in files
        ]
    else:
        btn = []
    
    btn.insert(0,
        [
            InlineKeyboardButton("! ʟᴀɴɢᴜᴀɢᴇs !", callback_data=f"languages#{search.replace(' ', '_')}#{key}")
        ]
    )

    if offset != "":
        key = f"{message.chat.id}-{message.id}"
        BUTTONS[key] = search
        req = message.from_user.id if message.from_user else 0
        btn.append(
            [InlineKeyboardButton(text=f"🗓 1/{math.ceil(int(total_results) / 10)}", callback_data="pages"),
             InlineKeyboardButton(text="ɴᴇxᴛ ⇉", callback_data=f"next_{req}_{key}_{offset}")]
        )
    else:
        btn.append(
            [InlineKeyboardButton(text="🗓 1/1", callback_data="pages")]
        )
    imdb = await get_poster(search, file=(files[0]).file_name) if settings["imdb"] else None
    cur_time = datetime.now(pytz.timezone('Asia/Kolkata')).time()
    time_difference = timedelta(hours=cur_time.hour, minutes=cur_time.minute, seconds=(cur_time.second+(cur_time.microsecond/1000000))) - timedelta(hours=curr_time.hour, minutes=curr_time.minute, seconds=(curr_time.second+(curr_time.microsecond/1000000)))
    remaining_seconds = "{:.2f}".format(time_difference.total_seconds())
    TEMPLATE = script.IMDB_TEMPLATE_TXT
    if imdb:
        cap = TEMPLATE.format(
            qurey=search,
            title=imdb['title'],
            votes=imdb['votes'],
            aka=imdb["aka"],
            seasons=imdb["seasons"],
            box_office=imdb['box_office'],
            localized_title=imdb['localized_title'],
            kind=imdb['kind'],
            imdb_id=imdb["imdb_id"],
            cast=imdb["cast"],
            runtime=imdb["runtime"],
            countries=imdb["countries"],
            certificates=imdb["certificates"],
            languages=imdb["languages"],
            director=imdb["director"],
            writer=imdb["writer"],
            producer=imdb["producer"],
            composer=imdb["composer"],
            cinematographer=imdb["cinematographer"],
            music_team=imdb["music_team"],
            distributors=imdb["distributors"],
            release_date=imdb['release_date'],
            year=imdb['year'],
            genres=imdb['genres'],
            poster=imdb['poster'],
            plot=imdb['plot'],
            rating=imdb['rating'],
            url=imdb['url'],
            **locals()
        )
        if not settings["button"]:
            cap+="<b>\n\n🔎 ʀᴇǫᴜᴇsᴛᴇᴅ ғɪʟᴇ 🥀</b>\n"
            for file in files:
                cap += f"<b>\n📁 <a href='https://telegram.me/{temp.U_NAME}?start=files_{file.file_id}'>[{get_size(file.file_size)}] {' '.join(filter(lambda x: not x.startswith('[') and not x.startswith('@') and not x.startswith('www.'), file.file_name.split()))}\n</a></b>"
    else:
        if settings["button"]:
            cap = f"<b>📟 ᴛɪᴛʟᴇ : {search} \n📂ᴛᴏᴛᴀʟ ꜰɪʟᴇs ꜰᴏᴜɴᴅᴇᴅ : {str(total_results)}\n👩🏻‍💻 ʀᴇǫᴜᴇsᴛᴇᴅ ʙʏ : {message.from_user.mention} \n\n<code>⚠️ ᴛʜɪs ᴍᴇssᴀɢᴇ ᴡɪʟʟ ʙᴇ ᴀᴜᴛᴏ ᴅᴇʟᴇᴛᴇᴅ ᴀғᴛᴇʀ 𝟷𝟶 ᴍɪɴᴜᴛᴇs.</code></b>"
        else:
            cap = f"<b>ʜᴇʏ {message.from_user.mention}👋, ғᴏᴜɴᴅ {total_results} 📂 ʀᴇsᴜʟᴛs ғᴏʀ ʏᴏᴜʀ ǫᴜᴇʀʏ <code>{search}</code>\n\n</b>"
            cap+="<b>🔎 ʀᴇǫᴜᴇsᴛᴇᴅ ғɪʟᴇ 🥀</b>\n\n"
            for file in files:
                cap += f"<b>📁 <a href='https://telegram.me/{temp.U_NAME}?start=files_{file.file_id}'>[{get_size(file.file_size)}] {' '.join(filter(lambda x: not x.startswith('[') and not x.startswith('@') and not x.startswith('www.'), file.file_name.split()))}\n\n</a></b>"

    if imdb and imdb.get('poster'):
        try:
            hehe =  await message.reply_photo(photo=imdb.get('poster'), caption=cap[:1024],
                                      reply_markup=InlineKeyboardMarkup(btn))
            if SELF_DELETE:
                await asyncio.sleep(SELF_DELETE_SECONDS)
                await hehe.delete()

        except (MediaEmpty, PhotoInvalidDimensions, WebpageMediaEmpty):
            pic = imdb.get('poster')
            poster = pic.replace('.jpg', "._V1_UX360.jpg")
            hmm = await message.reply_photo(photo=poster, caption=cap[:1024], reply_markup=InlineKeyboardMarkup(btn))
            if SELF_DELETE:
                await asyncio.sleep(SELF_DELETE_SECONDS)
                await hmm.delete()
        except Exception as e:
            logger.exception(e)
            fek = await message.reply_text(cap, reply_markup=InlineKeyboardMarkup(btn))
            if SELF_DELETE:
                await asyncio.sleep(SELF_DELETE_SECONDS)
                await fek.delete()
    else:
        fuk = await message.reply_text(cap, reply_markup=InlineKeyboardMarkup(btn))
        if SELF_DELETE:
            await asyncio.sleep(SELF_DELETE_SECONDS)
            await fuk.delete()

async def advantage_spell_chok(client, msg):
    mv_id = msg.id
    mv_rqst = msg.text
    reqstr1 = msg.from_user.id if msg.from_user else 0
    reqstr = await client.get_users(reqstr1)
    settings = await get_settings(msg.chat.id)
    query = re.sub(
        r"\b(pl(i|e)*?(s|z+|ease|se|ese|(e+)s(e)?)|((send|snd|giv(e)?|gib)(\sme)?)|movie(s)?|new|latest|br((o|u)h?)*|^h(e|a)?(l)*(o)*|mal(ayalam)?|t(h)?amil|file|that|find|und(o)*|kit(t(i|y)?)?o(w)?|thar(u)?(o)*w?|kittum(o)*|aya(k)*(um(o)*)?|full\smovie|any(one)|with\ssubtitle(s)?)",
        "", msg.text, flags=re.IGNORECASE)  # plis contribute some common words
    query = query.strip() + " movie"
    try:
        movies = await get_poster(mv_rqst, bulk=True)
    except Exception as e:
        logger.exception(e)
        reqst_gle = mv_rqst.replace(" ", "+")
        button = [[
                   InlineKeyboardButton("🔎 ɢᴏᴏɢʟᴇ 🔎", url=f"https://www.google.com/search?q={reqst_gle}")
        ]]
        if NO_RESULTS_MSG:
            await client.send_message(chat_id=LOG_CHANNEL, text=(script.NORSLTS.format(reqstr.id, reqstr.mention, mv_rqst)))
        k = await msg.reply_text( 
            text=script.I_CUDNT.format(mv_rqst),
            reply_markup=InlineKeyboardMarkup(button)
        )
        await asyncio.sleep(30)
        await k.delete()
        return
    movielist = []
    if not movies:
        reqst_gle = mv_rqst.replace(" ", "+")
        button = [[
                   InlineKeyboardButton("🔎 ɢᴏᴏɢʟᴇ 🔎", url=f"https://www.google.com/search?q={reqst_gle}")
        ]]
        if NO_RESULTS_MSG:
            await client.send_message(chat_id=LOG_CHANNEL, text=(script.NORSLTS.format(reqstr.id, reqstr.mention, mv_rqst)))
        k = await msg.reply_text( 
            text=script.I_CUDNT.format(mv_rqst),
            reply_markup=InlineKeyboardMarkup(button)
        )
        await asyncio.sleep(30)
        await k.delete()
        return
    movielist += [movie.get('title') for movie in movies]
    movielist += [f"{movie.get('title')} {movie.get('year')}" for movie in movies]
    SPELL_CHECK[mv_id] = movielist
    btn = [
        [
            InlineKeyboardButton(
                text=movie_name.strip(),
                callback_data=f"spol#{reqstr1}#{k}",
            )
        ]
        for k, movie_name in enumerate(movielist)
    ]
    btn.append([InlineKeyboardButton(text="⇇ ʙᴀᴄᴋ ⇉", callback_data=f'spol#{reqstr1}#close_spellcheck')])
    ki = await msg.reply_text(
        text=(script.CUDNT_FND.format(mv_rqst)),
        reply_markup=InlineKeyboardMarkup(btn)
    )
    await asyncio.sleep(30)
    await ki.delete()

async def manual_filters(client, message, text=False):
    group_id = message.chat.id
    name = text or message.text
    reply_id = message.reply_to_message.id if message.reply_to_message else message.id
    keywords = await get_filters(group_id)
    for keyword in reversed(sorted(keywords, key=len)):
        pattern = r"( |^|[^\w])" + re.escape(keyword) + r"( |$|[^\w])"
        if re.search(pattern, name, flags=re.IGNORECASE):
            reply_text, btn, alert, fileid = await find_filter(group_id, keyword)

            if reply_text:
                reply_text = reply_text.replace("\\n", "\n").replace("\\t", "\t")

            if btn is not None:
                try:
                    if fileid == "None":
                        if btn == "[]":
                            await client.send_message(
                                group_id, 
                                reply_text, 
                                disable_web_page_preview=True,
                                reply_to_message_id=reply_id)
                        else:
                            button = eval(btn)
                            await client.send_message(
                                group_id,
                                reply_text,
                                disable_web_page_preview=True,
                                reply_markup=InlineKeyboardMarkup(button),
                                reply_to_message_id=reply_id
                            )
                    elif btn == "[]":
                        await lient.send_cached_media(
                            group_id,
                            fileid,
                            caption=reply_text or "",
                            reply_to_message_id=reply_id
                        )
                    else:
                        button = eval(btn)
                        await message.reply_cached_media(
                            fileid,
                            caption=reply_text or "",
                            reply_markup=InlineKeyboardMarkup(button),
                            reply_to_message_id=reply_id
                        )
                except Exception as e:
                    logger.exception(e)
                break
    else:
        return False

async def global_filters(client, message, text=False):
    group_id = message.chat.id
    name = text or message.text
    reply_id = message.reply_to_message.id if message.reply_to_message else message.id
    keywords = await get_gfilters('gfilters')
    for keyword in reversed(sorted(keywords, key=len)):
        pattern = r"( |^|[^\w])" + re.escape(keyword) + r"( |$|[^\w])"
        if re.search(pattern, name, flags=re.IGNORECASE):
            reply_text, btn, alert, fileid = await find_gfilter('gfilters', keyword)

            if reply_text:
                reply_text = reply_text.replace("\\n", "\n").replace("\\t", "\t")

            if btn is not None:
                try:
                    if fileid == "None":
                        if btn == "[]":
                            knd3 = await client.send_message(
                                group_id, 
                                reply_text, 
                                disable_web_page_preview=True,
                                reply_to_message_id=reply_id
                            )
                            await asyncio.sleep(300)
                            await knd3.delete()
                            await message.delete()

                        else:
                            button = eval(btn)
                            knd2 = await client.send_message(
                                group_id,
                                reply_text,
                                disable_web_page_preview=True,
                                reply_markup=InlineKeyboardMarkup(button),
                                reply_to_message_id=reply_id
                            )
                            await asyncio.sleep(300)
                            await knd2.delete()
                            await message.delete()

                    elif btn == "[]":
                        knd1 = await client.send_cached_media(
                            group_id,
                            fileid,
                            caption=reply_text or "",
                            reply_to_message_id=reply_id
                        )
                        await asyncio.sleep(300)
                        await knd1.delete()
                        await message.delete()

                    else:
                        button = eval(btn)
                        knd4 = await message.reply_cached_media(
                            fileid,
                            caption=reply_text or "",
                            reply_markup=InlineKeyboardMarkup(button),
                            reply_to_message_id=reply_id
                        )
                        await asyncio.sleep(300)
                        await knd4.delete()
                        await message.delete()

                except Exception as e:
                    logger.exception(e)
                break
    else:
        return False
   
