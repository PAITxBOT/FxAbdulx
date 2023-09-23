import os
import logging
import random
import asyncio
from Script import script
from pyrogram import Client, filters, enums
from pyrogram.errors import ChatAdminRequired, FloodWait, UserNotParticipant
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from database.ia_filterdb import Media, get_file_details, unpack_new_file_id, hs_bad_files
from database.users_chats_db import db
from info import *
from utils import get_settings, get_size, is_subscribed, save_group_settings, temp, get_shortlink, get_tutorial
from database.connections_mdb import active_connection
import re
import json
import base64
logger = logging.getLogger(__name__)

BATCH_FILES = {}

async def not_subscribed(_, client, message):
    await db.add_user_hs(client, message)
    if not FORCE_SUB:
        return False
    try:             
        user = await client.get_chat_member(FORCE_SUB, message.from_user.id) 
        if user.status == enums.ChatMemberStatus.BANNED:
            return True 
        else:
            return False                
    except UserNotParticipant:
        pass
    return True


@Client.on_message(filters.group & filters.create(not_subscribed))
async def forces_sub(client, message):
    buttons = [[InlineKeyboardButton(text="🥀 ᴊᴏɪɴ ᴜᴘᴅᴀᴛᴇ ᴄʜᴀɴɴᴇʟ 🥀", url=f"https://t.me/{FORCE_SUB}") ]]
    text = "**ʜᴇʏ {}\n\nsᴏʀʀʏ ᴅᴜᴅᴇ ʏᴏᴜ'ʀᴇ ɴᴏᴛ ᴊᴏɪɴᴇᴅ ᴍʏ ᴄʜᴀɴɴᴇʟ 😐. sᴏ ᴘʟᴇᴀꜱᴇ ᴊᴏɪɴ ᴏᴜʀ ᴜᴩᴅᴀᴛᴇ ᴄʜᴀɴɴᴇʟ ᴛᴏ ᴄᴏɴᴛɪɴᴜᴇ**"
    try:
        user = await client.get_chat_member(FORCE_SUB, message.from_user.id)    
        if user.status == enums.ChatMemberStatus.BANNED:                                   
            return await client.send_message(message.from_user.id, text="Sᴏʀʀy Yᴏᴜ'ʀᴇ Bᴀɴɴᴇᴅ Tᴏ Uꜱᴇ Mᴇ")  
    except UserNotParticipant:                       
        return await message.reply_text(text=text.format(message.from_user.mention, temp.U_NAME, temp.B_NAME), reply_markup=InlineKeyboardMarkup(buttons))
    return await message.reply_text(text=text, reply_markup=InlineKeyboardMarkup(buttons))

@Client.on_message(filters.command("start") & filters.incoming)
async def start(client, message):
    if message.chat.type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        buttons = [[
            InlineKeyboardButton('ᴀᴅᴅ ᴍᴇ ᴛᴏ ʏᴏᴜʀ ɢʀᴏᴜᴘ', url=f'http://t.me/{temp.U_NAME}?startgroup=true')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await message.reply(script.HS_START_TXT.format(message.from_user.mention if message.from_user else message.chat.title, temp.U_NAME, temp.B_NAME), disable_web_page_preview=True, reply_markup=reply_markup)
        await asyncio.sleep(2) # 😢 https://github.com/EvamariaTG/EvaMaria/blob/master/plugins/p_ttishow.py#L17 😬 wait a bit, before checking.
        if not await db.get_chat(message.chat.id):
            total=await client.get_chat_members_count(message.chat.id)
            await client.send_message(LOG_CHANNEL, script.LOG_TEXT_G.format(message.chat.title, message.chat.id, total, "Unknown"))       
            await db.add_chat(message.chat.id, message.chat.title)
        return 
    if not await db.is_user_exist(message.from_user.id):
        await db.add_user(message.from_user.id, message.from_user.first_name)
        await client.send_message(LOG_CHANNEL, script.LOG_TEXT_P.format(message.from_user.id, message.from_user.mention))
    if len(message.command) != 2:
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
        await message.reply_photo(
            photo=random.choice(PICS),
            caption=script.START_TXT.format(message.from_user.mention, temp.U_NAME, temp.B_NAME),
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
        return
    if AUTH_CHANNEL and not await is_subscribed(client, message):
        try:
            invite_link = await client.create_chat_invite_link(int(AUTH_CHANNEL))
        except ChatAdminRequired:
            logger.error("Make sure Bot is admin in Force Sub channel")
            return
        btn = [
            [
                InlineKeyboardButton(
                    "🔥 ᴊᴏɪɴ ᴜᴘᴅᴛᴀᴇs ᴄʜᴀɴɴᴇʟ 🔥", url=invite_link.invite_link
                )
            ]
        ]

        if message.command[1] != "subscribe":
            try:
                kk, file_id = message.command[1].split("_", 1)
                pre = 'checksubp' if kk == 'filep' else 'checksub' 
                btn.append([InlineKeyboardButton("🔄 ᴛʀʏ ᴀɢᴀɪɴ 🔄", callback_data=f"{pre}#{file_id}")])
            except (IndexError, ValueError):
                btn.append([InlineKeyboardButton("🔄 ᴛʀʏ ᴀɢᴀɪɴ 🔄", url=f"https://t.me/{temp.U_NAME}?start={message.command[1]}")])
        await client.send_message(
            chat_id=message.from_user.id,
            text="**Please Join My Updates Channel to use this Bot!**",
            reply_markup=InlineKeyboardMarkup(btn),
            parse_mode=enums.ParseMode.MARKDOWN
            )
        return
    if len(message.command) == 2 and message.command[1] in ["subscribe", "error", "okay", "help"]:
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
        await message.reply_photo(
            photo=random.choice(PICS),
            caption=script.START_TXT.format(message.from_user.mention, temp.U_NAME, temp.B_NAME),
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
        return
    data = message.command[1]
    try:
        pre, file_id = data.split('_', 1)
    except:
        file_id = data
        pre = ""
    if data.split("-", 1)[0] == "BATCH":
        sts = await message.reply("<b>𝙰𝙲𝙲𝙴𝚂𝚂𝙸𝙽𝙶 𝙵𝙸𝙻𝙴𝚂.../</b>")
        file_id = data.split("-", 1)[1]
        msgs = BATCH_FILES.get(file_id)
        if not msgs:
            file = await client.download_media(file_id)
            try: 
                with open(file) as file_data:
                    msgs=json.loads(file_data.read())
            except:
                await sts.edit("FAILED")
                return await client.send_message(LOG_CHANNEL, "UNABLE TO OPEN FILE.")
            os.remove(file)
            BATCH_FILES[file_id] = msgs
        for msg in msgs:
            title = msg.get("title")
            size=get_size(int(msg.get("size", 0)))
            f_caption=msg.get("caption", "")
            if BATCH_FILE_CAPTION:
                try:
                    f_caption=BATCH_FILE_CAPTION.format(file_name= '' if title is None else title, file_size='' if size is None else size, file_caption='' if f_caption is None else f_caption)
                except Exception as e:
                    logger.exception(e)
                    f_caption=f_caption
            if f_caption is None:
                f_caption = f"{title}"
            try:
                await client.send_cached_media(
                    chat_id=message.from_user.id,
                    file_id=msg.get("file_id"),
                    caption=f_caption,
                    protect_content=msg.get('protect', False),
                    )
            except FloodWait as e:
                await asyncio.sleep(e.x)
                logger.warning(f"Floodwait of {e.x} sec.")
                await client.send_cached_media(
                    chat_id=message.from_user.id,
                    file_id=msg.get("file_id"),
                    caption=f_caption,
                    protect_content=msg.get('protect', False),
                    )
            except Exception as e:
                logger.warning(e, exc_info=True)
                continue
            await asyncio.sleep(1) 
        await sts.delete()
        return
    elif data.split("-", 1)[0] == "DSTORE":
        sts = await message.reply("<b>𝙰𝙲𝙲𝙴𝚂𝚂𝙸𝙽𝙶 𝙵𝙸𝙻𝙴𝚂.../</b>")
        b_string = data.split("-", 1)[1]
        decoded = (base64.urlsafe_b64decode(b_string + "=" * (-len(b_string) % 4))).decode("ascii")
        try:
            f_msg_id, l_msg_id, f_chat_id, protect = decoded.split("_", 3)
        except:
            f_msg_id, l_msg_id, f_chat_id = decoded.split("_", 2)
            protect = "/pbatch" if PROTECT_CONTENT else "batch"
        diff = int(l_msg_id) - int(f_msg_id)
        async for msg in client.iter_messages(int(f_chat_id), int(l_msg_id), int(f_msg_id)):
            if msg.media:
                media = getattr(msg, msg.media.value)
                if BATCH_FILE_CAPTION:
                    try:
                        f_caption=BATCH_FILE_CAPTION.format(file_name=getattr(media, 'file_name', ''), file_size=getattr(media, 'file_size', ''), file_caption=getattr(msg, 'caption', ''))
                    except Exception as e:
                        logger.exception(e)
                        f_caption = getattr(msg, 'caption', '')
                else:
                    media = getattr(msg, msg.media.value)
                    file_name = getattr(media, 'file_name', '')
                    f_caption = getattr(msg, 'caption', file_name)
                try:
                    await msg.copy(message.chat.id, caption=f_caption, protect_content=True if protect == "/pbatch" else False)
                except FloodWait as e:
                    await asyncio.sleep(e.x)
                    await msg.copy(message.chat.id, caption=f_caption, protect_content=True if protect == "/pbatch" else False)
                except Exception as e:
                    logger.exception(e)
                    continue
            elif msg.empty:
                continue
            else:
                try:
                    await msg.copy(message.chat.id, protect_content=True if protect == "/pbatch" else False)
                except FloodWait as e:
                    await asyncio.sleep(e.x)
                    await msg.copy(message.chat.id, protect_content=True if protect == "/pbatch" else False)
                except Exception as e:
                    logger.exception(e)
                    continue
            await asyncio.sleep(1) 
        return await sts.delete()

    elif data.startswith("short"):
        user = message.from_user.id
        chat_id = temp.SHORT.get(user)
        files_ = await get_file_details(file_id)
        files = files_[0]
        hs = await get_shortlink(chat_id, f"https://telegram.me/{temp.U_NAME}?start=file_{file_id}")
        x = k = await client.send_photo(chat_id=user,photo=random.choice(CHANNEL_PICS),caption=f"<b>📝 ɴᴀᴍᴇ » : <code>{files.file_name}</code> \n\n🔖 sɪᴢᴇ » : {get_size(files.file_size)}\n\n🔗 ᴅᴏᴡɴʟᴏᴀᴅ ʟɪɴᴋ » : {hs}\n\n⚠️ ɴᴏᴛᴇ: ᴛʜɪꜱ ᴍᴇꜱꜱᴀɢᴇ ɪꜱ ᴅᴇʟᴇᴛᴇᴅ ɪɴ 𝟻 ᴍɪɴꜱ ᴛᴏ ᴀᴠᴏɪᴅ ᴄᴏᴘʏʀɪɢʜᴛꜱ. sᴀᴠᴇ ᴛʜᴇ ʟɪɴᴋ ᴛᴏ sᴏᴍᴇᴡʜᴇʀᴇ ᴇʟꜱᴇ</b>", reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton('📂 ᴅᴏᴡɴʟᴏᴀᴅ ɴᴏᴡ 📂', url=hs)
                    ], [
                        InlineKeyboardButton('⁉️ ʜᴏᴡ ᴛᴏ ᴅᴏᴡɴʟᴏᴀᴅ ⁉️', url=await get_tutorial(chat_id))
                    ]
                ]
            )
        )
        await asyncio.sleep(13)
        await k.delete()
        #await x.delete()
        await k.reply_photo(
            photo=random.choice(DELETE_PICS),
            caption="<b>✏️ ʏᴏᴜʀ ᴍᴇꜱꜱᴀɢᴇ ɪꜱ ꜱᴜᴄᴄᴇꜱꜱғᴜʟʟʏ ᴅᴇʟᴇᴛᴇᴅ!!! 🗑️\n\n💥 ᴩᴏᴡᴇʀᴇᴅ ʙʏ - <a href=https://telegram.me/OMGxMovies>Oᴍɢ x Mᴏᴠɪᴇs</a></b>",
            parse_mode=enums.ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(
                [[
                    InlineKeyboardButton('✘ ᴄʟᴏsᴇ ✘', callback_data='close_data')
                ]]
            )
        )
        await asyncio.sleep(13)
        await x.delete()
        return
        

    

    elif data.startswith("files"):
        user = message.from_user.id
        if temp.SHORT.get(user)==None:
            await message.reply_text(text="<b>Please Search Again in Group</b>")
        else:
            chat_id = temp.SHORT.get(user)
        settings = await get_settings(chat_id)
        if settings['is_shortlink'] and user not in PREMIUM_USER:
            files_ = await get_file_details(file_id)
            files = files_[0]
            hs = await get_shortlink(chat_id, f"https://telegram.me/{temp.U_NAME}?start=file_{file_id}")
            x = k = await client.send_photo(chat_id=user,photo=random.choice(CHANNEL_PICS),caption=f"<b>📝 ɴᴀᴍᴇ » : <code>{files.file_name}</code> \n\n🔖 sɪᴢᴇ » : {get_size(files.file_size)}\n\n🔗 ᴅᴏᴡɴʟᴏᴀᴅ ʟɪɴᴋ » : {hs}\n\n⚠️ ɴᴏᴛᴇ: ᴛʜɪꜱ ᴍᴇꜱꜱᴀɢᴇ ɪꜱ ᴅᴇʟᴇᴛᴇᴅ ɪɴ 𝟻 ᴍɪɴꜱ ᴛᴏ ᴀᴠᴏɪᴅ ᴄᴏᴘʏʀɪɢʜᴛꜱ. sᴀᴠᴇ ᴛʜᴇ ʟɪɴᴋ ᴛᴏ sᴏᴍᴇᴡʜᴇʀᴇ ᴇʟꜱᴇ</b>", reply_markup=InlineKeyboardMarkup(
                    [
                       [
                            InlineKeyboardButton('📂 ᴅᴏᴡɴʟᴏᴀᴅ ɴᴏᴡ 📂', url=hs)
                       ], [
                            InlineKeyboardButton('⁉️ ʜᴏᴡ ᴛᴏ ᴅᴏᴡɴʟᴏᴀᴅ ⁉️', url=await get_tutorial(chat_id))
                       ]
                    ]
                )
            )
            await asyncio.sleep(13)
            await k.delete()
            #await x.delete()
            #del k, x
            await k.reply_photo(
            photo=random.choice(DELETE_PICS),
            caption="<b>✏️ ʏᴏᴜʀ ᴍᴇꜱꜱᴀɢᴇ ɪꜱ ꜱᴜᴄᴄᴇꜱꜱғᴜʟʟʏ ᴅᴇʟᴇᴛᴇᴅ!!! 🗑️\n\n💥 ᴩᴏᴡᴇʀᴇᴅ ʙʏ - <a href=https://telegram.me/OMGxMovies>Oᴍɢ x Mᴏᴠɪᴇs</a></b>",
            parse_mode=enums.ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(
                [[
                    InlineKeyboardButton('✘ ᴄʟᴏsᴇ ✘', callback_data='close_data')
                ]]
            )
        )
        await asyncio.sleep(13)
        await x.delete()
        return

    files_ = await get_file_details(file_id)           
    if not files_:
        pre, file_id = ((base64.urlsafe_b64decode(data + "=" * (-len(data) % 4))).decode("ascii")).split("_", 1)
        try:
            msg = await client.send_cached_media(
                chat_id=message.from_user.id,
                file_id=file_id,
                protect_content=True if pre == 'filep' else False,
                )
            filetype = msg.media
            file = getattr(msg, filetype.value)
            title = '@Siveroz_Linkzz - ' + ' '.join(filter(lambda x: not x.startswith('[') and not x.startswith('@'), file.file_name.split()))
            size=get_size(file.file_size)
            f_caption = f"<code>{title}</code>"
            if CUSTOM_FILE_CAPTION:
                try:
                    f_caption=CUSTOM_FILE_CAPTION.format(file_name= '' if title is None else title, file_size='' if size is None else size, file_caption='')
                except:
                    return
            await msg.edit_caption(f_caption)
            btn = [[
                InlineKeyboardButton("🔄 ᴄʟɪᴄᴋ ᴛᴏ ɢᴇᴛ ᴅᴇʟᴇᴛᴇ ғɪʟᴇ ᴀɢᴀɪɴ 🔄", callback_data=f'delfile#{file_id}')
            ]]
            hs = k = await msg.reply("<b>❗⚠️❗🚨 ɪᴍᴘᴏʀᴛᴀɴᴛ 🚨❗⚠️❗️\n\n🎭 ᴛʜɪꜱ ᴍᴏᴠɪᴇ ғɪʟᴇ/ᴠɪᴅᴇᴏ ᴡɪʟʟ ʙᴇ ᴅᴇʟᴇᴛᴇᴅ ɪɴ <code>𝟷𝟶 ᴍɪɴꜱ</code>\n\n🔎 ᴅᴜᴇ ᴛᴏ ᴄᴏᴘʏʀɪɢʜᴛ ɪsꜱᴜᴇꜱ 🔎\n\n🥀 ᴘʟᴇᴀꜱᴇ ғᴏʀᴡᴀʀᴅ ᴛʜɪꜱ ғɪʟᴇ/ᴠɪᴅᴇᴏ ᴛᴏ ʏᴏᴜʀ Sᴀᴠᴇᴅ ᴍᴇꜱꜱᴀɢᴇꜱ ᴀɴᴅ sᴛᴀʀᴛ ᴅᴏᴡɴʟᴏᴀᴅ ᴛʜᴇʀᴇ  📝</b>",quote=True)
            await asyncio.sleep(13)
            await msg.delete()
            await hs.delete()
            del msg, hs
            await k.reply_photo(photo=random.choice(DELETE_PICS),caption="<b>🥀 ʏᴏᴜʀ ғɪʟᴇ/ᴠɪᴅᴇᴏ ɪꜱ ꜱᴜᴄᴄᴇꜱꜱғᴜʟʟʏ ᴅᴇʟᴇᴛᴇᴅ!!!✅\n\n📝 ᴄʟɪᴄᴋ ʙᴇʟᴏᴡ ʙᴜᴛᴛᴏɴ ᴛᴏ ɢᴇᴛ ʏᴏᴜʀ ᴅᴇʟᴇᴛᴇᴅ ғɪʟᴇ 👇</b>",reply_markup=InlineKeyboardMarkup(btn))
            #await hs.del
            return
        except:
            pass
        return await message.reply('No such file exist.')
    files = files_[0]
    title = '@Siveroz_Linkzz - ' + ' '.join(filter(lambda x: not x.startswith('[') and not x.startswith('@'), files.file_name.split()))
    size=get_size(files.file_size)
    f_caption=files.caption
    if CUSTOM_FILE_CAPTION:
        try:
            f_caption=CUSTOM_FILE_CAPTION.format(file_name= '' if title is None else title, file_size='' if size is None else size, file_caption='' if f_caption is None else f_caption)
        except Exception as e:
            logger.exception(e)
            f_caption=f_caption
    if f_caption is None:
        f_caption = f"@Siveroz_Linkzz - {' '.join(filter(lambda x: not x.startswith('[') and not x.startswith('@'), files.file_name.split()))}"
    msg = await client.send_cached_media(
        chat_id=message.from_user.id,
        file_id=file_id,
        caption=f_caption,
        protect_content=True if pre == 'filep' else False,
        reply_markup=InlineKeyboardMarkup(
            [[
                InlineKeyboardButton('ᴊᴏɪɴ ᴛʜᴇ ᴄʜᴀɴɴᴇʟ', url=f'https://t.me/Siveroz_Linkzz')
            ]]
        ))
    btn = [[
        InlineKeyboardButton("🔄 ᴄʟɪᴄᴋ ᴛᴏ ɢᴇᴛ ᴅᴇʟᴇᴛᴇ ғɪʟᴇ ᴀɢᴀɪɴ 🔄", callback_data=f'delfile#{file_id}')
    ]]
    hs = k = await msg.reply("<b>❗⚠️❗🚨 ɪᴍᴘᴏʀᴛᴀɴᴛ 🚨❗⚠️❗️\n\n🎭 ᴛʜɪꜱ ᴍᴏᴠɪᴇ ғɪʟᴇ/ᴠɪᴅᴇᴏ ᴡɪʟʟ ʙᴇ ᴅᴇʟᴇᴛᴇᴅ ɪɴ <code>𝟷𝟶 ᴍɪɴꜱ</code>\n\n🔎 ᴅᴜᴇ ᴛᴏ ᴄᴏᴘʏʀɪɢʜᴛ ɪsꜱᴜᴇꜱ 🔎\n\n🥀 ᴘʟᴇᴀꜱᴇ ғᴏʀᴡᴀʀᴅ ᴛʜɪꜱ ғɪʟᴇ/ᴠɪᴅᴇᴏ ᴛᴏ ʏᴏᴜʀ Sᴀᴠᴇᴅ ᴍᴇꜱꜱᴀɢᴇꜱ ᴀɴᴅ sᴛᴀʀᴛ ᴅᴏᴡɴʟᴏᴀᴅ ᴛʜᴇʀᴇ  📝</b>",quote=True)
    await asyncio.sleep(13)
    await msg.delete()
    await hs.delete()
    del msg, hs
    await k.reply_photo(photo=random.choice(DELETE_PICS),caption="<b>🥀 ʏᴏᴜʀ ғɪʟᴇ/ᴠɪᴅᴇᴏ ɪꜱ ꜱᴜᴄᴄᴇꜱꜱғᴜʟʟʏ ᴅᴇʟᴇᴛᴇᴅ!!!✅\n\n📝 ᴄʟɪᴄᴋ ʙᴇʟᴏᴡ ʙᴜᴛᴛᴏɴ ᴛᴏ ɢᴇᴛ ʏᴏᴜʀ ᴅᴇʟᴇᴛᴇᴅ ғɪʟᴇ 👇</b>",reply_markup=InlineKeyboardMarkup(btn))
    #await hs.delete(13)
    return
                    

@Client.on_message(filters.command('channel') & filters.user(ADMINS))
async def channel_info(bot, message):
           
    """Send basic information of channel"""
    if isinstance(CHANNELS, (int, str)):
        channels = [CHANNELS]
    elif isinstance(CHANNELS, list):
        channels = CHANNELS
    else:
        raise ValueError("Unexpected type of CHANNELS")

    text = '📑 **Indexed channels/groups**\n'
    for channel in channels:
        chat = await bot.get_chat(channel)
        if chat.username:
            text += '\n@' + chat.username
        else:
            text += '\n' + chat.title or chat.first_name

    text += f'\n\n**Total:** {len(CHANNELS)}'

    if len(text) < 4096:
        await message.reply(text)
    else:
        file = 'Indexed channels.txt'
        with open(file, 'w') as f:
            f.write(text)
        await message.reply_document(file)
        os.remove(file)


@Client.on_message(filters.command('logs') & filters.user(ADMINS))
async def log_file(bot, message):
    """Send log file"""
    try:
        await message.reply_document('TelegramBot.log')
    except Exception as e:
        await message.reply(str(e))

@Client.on_message(filters.command('delete') & filters.user(ADMINS))
async def delete(bot, message):
    """Delete file from database"""
    reply = message.reply_to_message
    if reply and reply.media:
        msg = await message.reply("𝐃𝐞𝐥𝐞𝐭𝐢𝐧𝐠....🗑️", quote=True)
    else:
        await message.reply('Reply to file with /delete which you want to delete', quote=True)
        return

    for file_type in ("document", "video", "audio"):
        media = getattr(reply, file_type, None)
        if media is not None:
            break
    else:
        await msg.edit('This is not supported file format')
        return
    
    file_id, file_ref = unpack_new_file_id(media.file_id)

    result = await Media.collection.delete_one({
        '_id': file_id,
    })
    if result.deleted_count:
        await msg.edit('**𝙵𝙸𝙻𝙴 𝚂𝚄𝙲𝙲𝙴𝚂𝚂𝙵𝚄𝙻𝙻𝚈 𝙳𝙴𝙻𝙴𝚃𝙴𝙳**')
    else:
        file_name = re.sub(r"(_|\-|\.|\+)", " ", str(media.file_name))
        result = await Media.collection.delete_many({
            'file_name': file_name,
            'file_size': media.file_size,
            'mime_type': media.mime_type
            })
        if result.deleted_count:
            await msg.edit('**𝙵𝙸𝙻𝙴 𝚂𝚄𝙲𝙲𝙴𝚂𝚂𝙵𝚄𝙻𝙻𝚈 𝙳𝙴𝙻𝙴𝚃𝙴𝙳**')
        else:
            # files indexed before https://github.com/EvamariaTG/EvaMaria/commit/f3d2a1bcb155faf44178e5d7a685a1b533e714bf#diff-86b613edf1748372103e94cacff3b578b36b698ef9c16817bb98fe9ef22fb669R39 
            # have original file name.
            result = await Media.collection.delete_many({
                'file_name': media.file_name,
                'file_size': media.file_size,
                'mime_type': media.mime_type
            })
            if result.deleted_count:
                await msg.edit('**𝙵𝙸𝙻𝙴 𝚂𝚄𝙲𝙲𝙴𝚂𝚂𝙵𝚄𝙻𝙻𝚈 𝙳𝙴𝙻𝙴𝚃𝙴𝙳**')
            else:
                await msg.edit('File not found in database')


@Client.on_message(filters.command('deleteall') & filters.user(ADMINS))
async def delete_all_index(bot, message):
    await message.reply_text(
        '**𝚃𝙷𝙸𝚂 𝙿𝚁𝙾𝙲𝙴𝚂𝚂 𝚆𝙸𝙻𝙻 𝙳𝙴𝙻𝙴𝚃𝙴 𝙰𝙻𝙻 𝚃𝙷𝙴 𝙵𝙸𝙻𝙴𝚂 𝙵𝚁𝙾𝙼 𝚈𝙾𝚄𝚁 𝙳𝙰𝚃𝙰𝙱𝙰𝚂𝙴.\n𝙳𝙾 𝚈𝙾𝚄 𝚆𝙰𝙽𝚃 𝚃𝙾 𝙲𝙾𝙽𝚃𝙸𝙽𝚄𝙴 𝚃𝙷𝙸𝚂..??**',
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        text="⚡ 𝐘𝐞𝐬 ⚡", callback_data="autofilter_delete"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="❄ 𝐂𝐚𝐧𝐜𝐞𝐥 ❄", callback_data="close_data"
                    )
                ],
            ]
        ),
        quote=True,
    )


@Client.on_callback_query(filters.regex(r'^autofilter_delete'))
async def delete_all_index_confirm(bot, message):
    await Media.collection.drop()
    await message.answer('𝙿𝙻𝙴𝙰𝚂𝙴 𝚂𝙷𝙰𝚁𝙴 𝙰𝙽𝙳 𝚂𝚄𝙿𝙿𝙾𝚁𝚃')
    await message.message.edit('Succesfully Deleted All The Indexed Files.')


@Client.on_message(filters.command('settings'))
async def settings(client, message):
    userid = message.from_user.id if message.from_user else None
    if not userid:
        return await message.reply(f"You are anonymous admin. Use /connect {message.chat.id} in PM")
    chat_type = message.chat.type

    if chat_type == enums.ChatType.PRIVATE:
        grpid = await active_connection(str(userid))
        if grpid is not None:
            grp_id = grpid
            try:
                chat = await client.get_chat(grpid)
                title = chat.title
            except:
                await message.reply_text("Make sure I'm present in your group!!", quote=True)
                return
        else:
            await message.reply_text("I'm not connected to any groups!", quote=True)
            return

    elif chat_type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        grp_id = message.chat.id
        title = message.chat.title

    else:
        return

    st = await client.get_chat_member(grp_id, userid)
    if (
            st.status != enums.ChatMemberStatus.ADMINISTRATOR
            and st.status != enums.ChatMemberStatus.OWNER
            and str(userid) not in ADMINS
    ):
        return

    settings = await get_settings(grp_id)

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
        await message.reply_photo(
            photo=random.choice(SETTINGS_PICS),
            caption=f"<b>ᴄʜᴀɴɢᴇ ʏᴏᴜʀ sᴇᴛᴛɪɴɢꜱ ғᴏʀ {title}\n\nʏᴏᴜ ᴄᴀɴ ᴄʜᴀɴɢᴇ sᴇᴛᴛɪɴɢs ᴀs ʏᴏᴜʀ ᴡɪsʜ ʙʏ ᴜsɪɴɢ ʙᴇʟᴏᴡ ʙᴜᴛᴛᴏɴs.\n\nᴩᴏᴡᴇʀᴇᴅ ʙʏ - <a href=https://t.me/Hs_Botz>ʜꜱ ᠰ ʙᴏᴛꜱ</a></b>",
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML,
            reply_to_message_id=message.id
        )



@Client.on_message(filters.command('set_template'))
async def save_template(client, message):
    sts = await message.reply("**𝙲𝙷𝙴𝙲𝙺𝙸𝙽𝙶 𝙽𝙴𝚆 𝚃𝙴𝙼𝙿𝙻𝙰𝚃𝙴**")
    userid = message.from_user.id if message.from_user else None
    if not userid:
        return await message.reply(f"You are anonymous admin. Use /connect {message.chat.id} in PM")
    chat_type = message.chat.type

    if chat_type == enums.ChatType.PRIVATE:
        grpid = await active_connection(str(userid))
        if grpid is not None:
            grp_id = grpid
            try:
                chat = await client.get_chat(grpid)
                title = chat.title
            except:
                await message.reply_text("Make sure I'm present in your group!!", quote=True)
                return
        else:
            await message.reply_text("I'm not connected to any groups!", quote=True)
            return

    elif chat_type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        grp_id = message.chat.id
        title = message.chat.title

    else:
        return

    st = await client.get_chat_member(grp_id, userid)
    if (
            st.status != enums.ChatMemberStatus.ADMINISTRATOR
            and st.status != enums.ChatMemberStatus.OWNER
            and str(userid) not in ADMINS
    ):
        return

    if len(message.command) < 2:
        return await sts.edit("No Input!!")
    template = message.text.split(" ", 1)[1]
    await save_group_settings(grp_id, 'template', template)
    await sts.edit(f"𝚂𝚄𝙲𝙲𝙴𝚂𝚂𝙵𝚄𝙻𝙻𝚈 𝚄𝙿𝙶𝚁𝙰𝙳𝙴𝙳 𝚈𝙾𝚄𝚁 𝚃𝙴𝙼𝙿𝙻𝙰𝚃𝙴 𝙵𝙾𝚁 {title} to\n\n{template}")

@Client.on_message(filters.command("delete_files_name") & filters.user(ADMINS))
async def deletenamefiles(bot, message):
    chat_type = message.chat.type
    if chat_type != enums.ChatType.PRIVATE:
        return await message.reply_text(f"<b>Hey {message.from_user.mention}, This command won't work in groups. It only works on my PM !</b>")
    else:
        pass
    try:
        keyword = message.text.split(" ", 1)[1]
    except:
        return await message.reply_text(f"<b>Hey {message.from_user.mention}, Give me a keyword along with the command to delete files.</b>")
    k = await bot.send_message(chat_id=message.chat.id, text=f"<b>Fetching Files for your query {keyword} on DB... Please wait...</b>")
    files, total = await hs_bad_files(keyword)
    await k.edit_text(f"<b>Found {total} files for your query {keyword} !\n\nFile deletion process will start in 5 seconds !</b>")
    await asyncio.sleep(5)
    deleted = 0
    for file in files:
        await k.edit_text(f"<b>Process started for deleting files from DB. Successfully deleted {str(deleted)} files from DB for your query {keyword} !\n\nPlease wait...</b>")
        file_ids = file.file_id
        file_name = file.file_name
        result = await Media.collection.delete_one({
            '_id': file_ids,
        })
        if result.deleted_count:
            logger.info(f'File Found for your query {keyword}! Successfully deleted {file_name} from database.')
        deleted += 1
    await k.edit_text(text=f"<b>Process Completed for file deletion !\n\nSuccessfully deleted {str(deleted)} files from database for your query {keyword}.</b>")

@Client.on_message(filters.command("deletefiles") & filters.user(ADMINS))
async def deletemultiplefiles(bot, message):
    btn = [[
            InlineKeyboardButton("ᴅᴇʟᴇᴛᴇ ᴘʀᴇᴅᴠᴅs", callback_data="predvd"),
            InlineKeyboardButton("ᴅᴇʟᴇᴛᴇ ᴄᴀᴍʀɪᴘs", callback_data="camrip")
          ]]
    await message.reply_text(
        text="<b>✅ sᴇʟᴇᴄᴛ ᴛʜᴇ ᴛʏᴘᴇ ᴏғ ғɪʟᴇꜱ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ ᴅᴇʟᴇᴛᴇ !✨\n\n🥀 ᴛʜɪꜱ ᴡɪʟʟ ᴅᴇʟᴇᴛᴇ 𝟷𝟶𝟶 ғɪʟᴇꜱ ғʀᴏᴍ ᴛʜᴇ ᴅᴀᴛᴀʙᴀꜱᴇ ғᴏʀ ᴛʜᴇ ꜱᴇʟᴇᴄᴛᴇᴅ ᴛʏᴘᴇ 📂</b>",
        reply_markup=InlineKeyboardMarkup(btn)
    )


@Client.on_message(filters.command("setshortlinkoff") & filters.user(ADMINS))
async def offshortlink(bot, message):
    chat_type = message.chat.type
    if chat_type == enums.ChatType.PRIVATE:
        return await message.reply_text("I will Work Only in group")
    elif chat_type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        grpid = message.chat.id
        title = message.chat.title
    else:
        return
    await save_group_settings(grpid, 'is_shortlink', False)
    buttons = [[InlineKeyboardButton('⇇ ᴄʟᴏsᴇ ⇉', callback_data='close_data') ]]
    return await message.reply_text("**✅ sᴜᴄᴄᴇꜱꜱғᴜʟʟʏ ᴅɪꜱᴀʙʟᴇᴅ ꜱʜᴏʀᴛʟɪɴᴋ ✨\n\n🥀 ᴩᴏᴡᴇʀᴇᴅ ʙʏ - <a href=https://t.me/Hs_Botz>ʜꜱ ᠰ ʙᴏᴛꜱ</a>**", disable_web_page_preview=True, reply_markup=InlineKeyboardMarkup(buttons))
    
@Client.on_message(filters.command("setshortlinkon") & filters.user(ADMINS))
async def onshortlink(bot, message):
    chat_type = message.chat.type
    if chat_type == enums.ChatType.PRIVATE:
        return await message.reply_text("I will Work Only in group")
    elif chat_type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        grpid = message.chat.id
        title = message.chat.title
    else:
        return
    await save_group_settings(grpid, 'is_shortlink', True)
    buttons = [[InlineKeyboardButton('⇇ ᴄʟᴏsᴇ ⇉', callback_data='close_data') ]]
    return await message.reply_text("**✅ sᴜᴄᴄᴇꜱꜱғᴜʟʟʏ ᴇɴʙʟᴇᴅ ꜱʜᴏʀᴛʟɪɴᴋ ✨\n\n🥀 ᴩᴏᴡᴇʀᴇᴅ ʙʏ - <a href=https://t.me/Hs_Botz>ʜꜱ ᠰ ʙᴏᴛꜱ</a>**", disable_web_page_preview=True, reply_markup=InlineKeyboardMarkup(buttons))

@Client.on_message(filters.command("shortlink_info"))
async def showshortlink(bot, message):
    userid = message.from_user.id if message.from_user else None
    if not userid:
        buttons = [[InlineKeyboardButton('⇇ ᴄʟᴏsᴇ ⇉', callback_data='close_data') ]]
        return await message.reply_text(text="<b>🥀 ʏᴏᴜ ᴀʀᴇ ᴀɴᴏɴʏᴍᴏᴜꜱ ᴀᴅᴍɪɴ. ᴛᴜʀɴ ᴏғғ ᴀɴᴏɴʏᴍᴏᴜꜱ ᴀᴅᴍɪɴ ᴀɴᴅ ᴛʀʏ ᴀɢᴀɪɴ ᴛʜɪꜱ ᴄᴏᴍᴍᴀɴᴅ 🎭\n\n✨ ᴩᴏᴡᴇʀᴇᴅ ʙʏ - <a href=https://t.me/Hs_Botz>ʜꜱ ᠰ ʙᴏᴛꜱ</a></b>", disable_web_page_preview=True, reply_markup=InlineKeyboardMarkup(buttons))
    chat_type = message.chat.type
    if chat_type == enums.ChatType.PRIVATE:
        buttons = [[InlineKeyboardButton('⇇ ᴄʟᴏsᴇ ⇉', callback_data='close_data') ]]
        #text="<b>👋 ʜᴇʏ</b> {},<b>\n\n🥀 ᴛʜɪꜱ ᴄᴏᴍᴍᴀɴᴅ ᴏɴʟʏ ᴡᴏʀᴋꜱ ɪɴ ɢʀᴏᴜᴘ 📢\n\n✨ ᴛʀʏ ᴛʜɪꜱ ᴄᴏᴍᴍᴀɴᴅ ɪɴ ʏᴏᴜʀ ᴏᴡɴ ɢʀᴏᴜᴘ, ɪғ ʏᴏᴜ ᴀʀᴇ ᴜꜱɪɴɢ ᴍᴇ ɪɴ ʏᴏᴜʀ ɢʀᴏᴜᴘ 📢\n\n✨ ᴩᴏᴡᴇʀᴇᴅ ʙʏ - <a href=https://t.me/Hs_Botz>ʜꜱ ᠰ ʙᴏᴛꜱ</a></b>", disable_web_page_preview=True, reply_markup=InlineKeyboardMarkup(buttons)
        return await message.reply_text(text="<b>ʜᴇʏ 👋\n\n🥀 ᴛʜɪꜱ ᴄᴏᴍᴍᴀɴᴅ ᴏɴʟʏ ᴡᴏʀᴋꜱ ɪɴ ɢʀᴏᴜᴘ 📢\n\n✨ ᴛʀʏ ᴛʜɪꜱ ᴄᴏᴍᴍᴀɴᴅ ɪɴ ʏᴏᴜʀ ᴏᴡɴ ɢʀᴏᴜᴘ, ɪғ ʏᴏᴜ ᴀʀᴇ ᴜꜱɪɴɢ ᴍᴇ ɪɴ ʏᴏᴜʀ ɢʀᴏᴜᴘ 📢\n\n✨ ᴩᴏᴡᴇʀᴇᴅ ʙʏ - <a href=https://t.me/Hs_Botz>ʜꜱ ᠰ ʙᴏᴛꜱ</a></b>", disable_web_page_preview=True, reply_markup=InlineKeyboardMarkup(buttons))
    elif chat_type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        grpid = message.chat.id
        title = message.chat.title
    else:
        return
    chat_id=message.chat.id
    userid = message.from_user.id
    user = await bot.get_chat_member(grpid, userid)
    if user.status != enums.ChatMemberStatus.ADMINISTRATOR and user.status != enums.ChatMemberStatus.OWNER and str(userid) not in ADMINS:
        buttons = [[InlineKeyboardButton('⇇ ᴄʟᴏsᴇ ⇉', callback_data='close_data') ]]
        return await message.reply_text("<b>🥀 ᴛʜɪs ᴄᴏᴍᴍᴀɴᴅ ᴡᴏʀᴋs ᴏɴʟʏ ғᴏʀ ᴛʜɪs ɢʀᴏᴜᴘ ᴏᴡɴᴇʀ/ᴀᴅᴍɪɴ 📑\n\n✨ ᴛʀʏ ᴛʜɪs ᴄᴏᴍᴍᴀɴᴅ ɪɴ ʏᴏᴜʀ ᴏᴡɴ ɢʀᴏᴜᴘ, ɪғ ʏᴏᴜ ᴀʀᴇ ᴜsɪɴɢ ᴍᴇ ɪɴ ʏᴏᴜʀ ɢʀᴏᴜᴘ 📢\n\n✨ ᴩᴏᴡᴇʀᴇᴅ ʙʏ - <a href=https://t.me/Hs_Botz>ʜꜱ ᠰ ʙᴏᴛꜱ</a></b>", disable_web_page_preview=True, reply_markup=InlineKeyboardMarkup(buttons))
    else:
        settings = await get_settings(chat_id) #fetching settings for group
        if 'shortlink' in settings.keys() and 'tutorial' in settings.keys():
            su = settings['shortlink']
            sa = settings['shortlink_api']
            st = settings['tutorial']
            buttons = [[InlineKeyboardButton('⇇ ᴄʟᴏsᴇ ⇉', callback_data='close_data') ]]
            return await message.reply_text(f"<b>✨ sʜᴏʀᴛʟɪɴᴋ ᴡᴇʙsɪᴅᴇ : <code>{su}</code>\n\n💥 ᴀᴘɪ : <code>{sa}</code>\n\n🖇️ ᴛᴜᴛᴏʀɪᴀʟ : <code>{st}</code>\n\n✨ ᴩᴏᴡᴇʀᴇᴅ ʙʏ - <a href=https://t.me/Hs_Botz>ʜꜱ ᠰ ʙᴏᴛꜱ</a></b>", disable_web_page_preview=True, reply_markup=InlineKeyboardMarkup(buttons))
        elif 'shortlink' in settings.keys() and 'tutorial' not in settings.keys():
            su = settings['shortlink']
            sa = settings['shortlink_api']
            buttons = [[InlineKeyboardButton('⇇ ᴄʟᴏsᴇ ⇉', callback_data='close_data') ]]
            return await message.reply_text(f"<b>✨ sʜᴏʀᴛʟɪɴᴋ ᴡᴇʙsɪᴅᴇ : <code>{su}</code>\n\n💥 ᴀᴘɪ : <code>{sa}</code>\n\n🖇️ ᴛᴜᴛᴏʀɪᴀʟ ʟɪɴᴋ ɴᴏᴛ ᴄᴏɴɴᴇᴄᴛᴇᴅ\n\n✨ ᴩᴏᴡᴇʀᴇᴅ ʙʏ - <a href=https://t.me/Hs_Botz>ʜꜱ ᠰ ʙᴏᴛꜱ</a></b>", disable_web_page_preview=True, reply_markup=InlineKeyboardMarkup(buttons))
        elif 'shortlink' not in settings.keys() and 'tutorial' in settings.keys():
            st = settings['tutorial']
            buttons = [[InlineKeyboardButton('⇇ ᴄʟᴏsᴇ ⇉', callback_data='close_data') ]]
            return await message.reply_text(f"<b>🖇️ ᴛᴜᴛᴏʀɪᴀʟ: <code>{st}</code>\n\n✨ sʜᴏʀᴛᴇɴᴇʀ ᴜʀʟ ɴᴏᴛ ᴄᴏɴɴᴇᴄᴛᴇᴅ\n\n🥀 ʏᴏᴜ ᴄᴀɴ ᴄᴏɴɴᴇᴄᴛ ᴜꜱɪɴɢ /set_tutorial ᴄᴏᴍᴍᴀɴᴅ\n\n✨ ᴩᴏᴡᴇʀᴇᴅ ʙʏ - <a href=https://t.me/Hs_Botz>ʜꜱ ᠰ ʙᴏᴛꜱ</a></b>", disable_web_page_preview=True, reply_markup=InlineKeyboardMarkup(buttons))
        else:
            buttons = [[InlineKeyboardButton('⇇ ᴄʟᴏsᴇ ⇉', callback_data='close_data') ]]
            return await message.reply_text("<b>🥀 sʜᴏʀᴛᴇɴᴇʀ ᴜʀʟ ᴀɴᴅ ᴛᴜᴛᴏʀɪᴀʟ ʟɪɴᴋ ɴᴏᴛ ᴄᴏɴɴᴇᴄᴛᴇᴅ. ᴄʜᴇᴄᴋ ᴛʜɪꜱ ᴄᴏᴍᴍᴀɴᴅꜱ, /shortlink ᴀɴᴅ /set_tutorial\n\n✨ ᴩᴏᴡᴇʀᴇᴅ ʙʏ - <a href=https://t.me/Hs_Botz>ʜꜱ ᠰ ʙᴏᴛꜱ</a></b>", disable_web_page_preview=True, reply_markup=InlineKeyboardMarkup(buttons))

@Client.on_message(filters.command('set_shortner'))
async def set_shortner(bot, message):
    chat_type = message.chat.type
    if chat_type == enums.ChatType.PRIVATE:
        buttons = [[InlineKeyboardButton('⇇ ᴄʟᴏsᴇ ⇉', callback_data='close_data') ]]
        return await message.reply_text(text=f"<b>👋 ʜᴇʏ {message.from_user.mention},\n\n🥀 ᴛʜɪs ᴄᴏᴍᴍᴀɴᴅ ᴏɴʟʏ ᴡᴏʀᴋꜱ ᴏɴ ɢʀᴏᴜᴘꜱ !📢\n\n✨ ᴩᴏᴡᴇʀᴇᴅ ʙʏ - <a href=https://t.me/Hs_Botz>ʜꜱ ᠰ ʙᴏᴛꜱ</a></b>", disable_web_page_preview=True, reply_markup=InlineKeyboardMarkup(buttons))
    elif chat_type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        grpid = message.chat.id
        title = message.chat.title
    else:
        return
    data = message.text
    userid = message.from_user.id
    user = await bot.get_chat_member(grpid, userid)
    if user.status != enums.ChatMemberStatus.ADMINISTRATOR and user.status != enums.ChatMemberStatus.OWNER and str(userid) not in ADMINS:
        return await message.reply_text("<b>You don't have access to use this command !</b>")
    else:
        pass
    try:
        command, shortlink_url, api = data.split(" ")
    except:
        buttons = [[InlineKeyboardButton('⇇ ᴄʟᴏsᴇ ⇉', callback_data='close_data') ]]
        return await message.reply_text(text="<b>❗ ᴄᴏᴍᴍᴀɴᴅ ɪɴᴄᴏᴍᴘʟᴇᴛᴇ ❗\n\n🌿 ɢɪᴠᴇ ᴍᴇ ᴀ ꜱʜᴏʀᴛʟɪɴᴋ ᴀɴᴅ ᴀᴘɪ ᴀʟᴏɴɢ ᴡɪᴛʜ ᴛʜᴇ ᴄᴏᴍᴍᴀɴᴅ !🌲\n\n✨ ꜰᴏʀᴍᴀᴛ: <code>/set_shortner kpslink.in a33ce12542055ff79361d9bcc681ece612bdcaf8</code>\n\n🥀 ᴩᴏᴡᴇʀᴇᴅ ʙʏ - <a href=https://t.me/Hs_Botz>ʜꜱ ᠰ ʙᴏᴛꜱ</a></b>", disable_web_page_preview=True, reply_markup=InlineKeyboardMarkup(buttons))
    reply = await message.reply_text("<b>ᴘʟᴇᴀꜱᴇ ᴡᴀɪᴛ.....</b>")
    await save_group_settings(grpid, 'shortlink', shortlink_url)
    await save_group_settings(grpid, 'shortlink_api', api)
    await save_group_settings(grpid, 'is_shortlink', True)
    buttons = [[InlineKeyboardButton('⇇ ᴄʟᴏsᴇ ⇉', callback_data='close_data') ]]
    await reply.edit_text(text=f"<b>✅ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ ᴀᴅᴅᴇᴅ ꜱʜᴏʀᴛʟɪɴᴋ ᴀᴘɪ ꜰᴏʀ {title}.\n\n‣ ᴄᴜʀʀᴇɴᴛ ꜱʜᴏʀᴛʟɪɴᴋ ᴡᴇʙꜱɪᴛᴇ: <code>{shortlink_url}</code>\n‣ ᴄᴜʀʀᴇɴᴛ ᴀᴘɪ: <code>{api}</code>\n\n🥀 ᴩᴏᴡᴇʀᴇᴅ ʙʏ - <a href=https://t.me/Hs_Botz>ʜꜱ ᠰ ʙᴏᴛꜱ</a></b>", disable_web_page_preview=True, reply_markup=InlineKeyboardMarkup(buttons))

@Client.on_message(filters.command("set_tutorial"))
async def settutorial(bot, message):
    userid = message.from_user.id if message.from_user else None
    if not userid:
        return await message.reply(f"<b>✨ ʏᴏᴜ ᴀʀᴇ ᴀɴᴏɴʏᴍᴏᴜꜱ ᴀᴅᴍɪɴ🧑‍💻.ᴛᴜʀɴ ᴏғғ ᴀɴᴏɴʏᴍᴏᴜꜱ ᴀᴅᴍɪɴ ᴀɴᴅ ᴛʀʏ ᴀɢᴀɪɴ ᴛʜɪꜱ ᴄᴏᴍᴍᴀɴᴅ📝</b>")
    chat_type = message.chat.type
    if chat_type == enums.ChatType.PRIVATE:
        buttons = [[InlineKeyboardButton('⇇ ᴄʟᴏsᴇ ⇉', callback_data='close_data') ]]
        return await message.reply_text(text="<b>🥀 ᴛʜɪꜱ ᴄᴏᴍᴍᴀɴᴅ ᴡᴏʀᴋ ᴏɴʟʏ ɪɴ ɢʀᴏᴜᴘ🌲\n\n✨ ᴛʀʏ ɪᴛ ɪɴ ʏᴏᴜʀ ᴏᴡɴ ɢʀᴏᴜᴘ 📢</b>", reply_markup=InlineKeyboardMarkup(buttons))
    elif chat_type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        grpid = message.chat.id
        title = message.chat.title
    else:
        return
    userid = message.from_user.id
    user = await bot.get_chat_member(grpid, userid)
    if user.status != enums.ChatMemberStatus.ADMINISTRATOR and user.status != enums.ChatMemberStatus.OWNER and str(userid) not in ADMINS:
        return
    else:
        pass
    if len(message.command) == 1:
        buttons = [[InlineKeyboardButton('⇇ ᴄʟᴏsᴇ ⇉', callback_data='close_data') ]]
        return await message.reply_text(text="<b>🥀 ɢɪᴠᴇ ᴍᴇ ᴀ ᴛᴜᴛᴏʀɪᴀʟ ʟɪɴᴋ ᴀʟᴏɴɢ ᴡɪᴛʜ ᴛʜɪꜱ ᴄᴏᴍᴍᴀɴᴅ👇\n\nᴄᴏᴍᴍᴀɴᴅ ᴜꜱᴀɢᴇ : /set_tutorial ʏᴏᴜʀ ᴛᴜᴛᴏʀɪᴀʟ ʟɪɴᴋ 🖇️</b>", reply_markup=InlineKeyboardMarkup(buttons))
    elif len(message.command) == 2:
        reply = await message.reply_text("<b>💢 ᴘʟᴇᴀsᴇ ᴡᴀɪᴛ... 💢</b>")
        tutorial = message.command[1]
        await save_group_settings(grpid, 'tutorial', tutorial)
        await save_group_settings(grpid, 'is_tutorial', True)
        buttons = [[InlineKeyboardButton('⇇ ᴄʟᴏsᴇ ⇉', callback_data='close_data') ]]
        await reply.edit_text(f"<b>✅ sᴜᴄᴄᴇꜱꜱғᴜʟʟʏ ᴀᴅᴅᴇᴅ ᴛᴜᴛᴏʀɪᴀʟ 🥀\n\n❗ʜᴇʀᴇ ɪꜱ ʏᴏᴜʀ ᴛᴜᴛᴏʀɪᴀʟ ʟɪɴᴋ ғᴏʀ ʏᴏᴜʀ ɢʀᴏᴜᴘ</b>{title}\n\n<b>🖇️ ʏᴏᴜʀ ʟɪɴᴋ : <code>{tutorial}</code>\n\n🥀 ᴩᴏᴡᴇʀᴇᴅ ʙʏ - <a href=https://t.me/Hs_Botz>ʜꜱ ᠰ ʙᴏᴛꜱ</a></b>", disable_web_page_preview=True, reply_markup=InlineKeyboardMarkup(buttons))
    else:
        buttons = [[InlineKeyboardButton('⇇ ᴄʟᴏsᴇ ⇉', callback_data='close_data') ]]
        return await message.reply_text(f"<b>🎭 ʏᴏᴜ ᴇɴᴛᴇʀᴇᴅ ɪɴᴄᴏʀʀᴇᴄᴛ ғᴏʀᴍᴀᴛ👇\n\n🫴 ғᴏʀᴍᴀᴛ: /set_tutorial ʏᴏᴜʀ ᴛᴜᴛᴏʀɪᴀʟ ʟɪɴᴋ 🖇️</b>", reply_markup=InlineKeyboardMarkup(buttons))
        
