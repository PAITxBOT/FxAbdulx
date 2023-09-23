from pyrogram import filters, Client, enums
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from database.connections_mdb import add_connection, all_connections, if_active, delete_connection
from info import ADMINS
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)


@Client.on_message((filters.private | filters.group) & filters.command('connect'))
async def addconnection(client, message):
    userid = message.from_user.id if message.from_user else None
    if not userid:
        buttons = [[InlineKeyboardButton('⇇ ᴄʟᴏsᴇ ⇉', callback_data='close_data') ]]
        return await message.reply_text(text="<b>🥀 ʏᴏᴜ ᴀʀᴇ ᴀɴᴏɴʏᴍᴏᴜꜱ ᴀᴅᴍɪɴ. ᴜꜱᴇ - /connect {message.chat.id} ɪɴ ᴘᴍ</b>", reply_markup=InlineKeyboardMarkup(buttons))
    chat_type = message.chat.type

    if chat_type == enums.ChatType.PRIVATE:
        try:
            cmd, group_id = message.text.split(" ", 1)
        except:
            buttons = [[InlineKeyboardButton('⇇ ᴄʟᴏsᴇ ⇉', callback_data='close_data') ]]
            await message.reply_text(
                "<b>💢 ᴇɴᴛᴇʀ ɪɴ ᴄᴏʀʀᴇᴄᴛ ғᴏʀᴍᴀᴛ !!!</b>\n\n"
                "<code>🔎 /connect ɢʀᴏᴜᴘ ɪᴅ</code>\n\n"
                "<b>🥀 ɢᴇᴛ ʏᴏᴜʀ ɢʀᴏᴜᴘ ɪᴅ ʙʏ ᴀᴅᴅɪɴɢ ᴛʜɪꜱ ʙᴏᴛ ᴛᴏ ʏᴏᴜʀ ɢʀᴏᴜᴘ ᴀɴᴅ ᴜꜱᴇ<code>/id</code></b>",
                reply_markup=InlineKeyboardMarkup(buttons),
                quote=True
            )
            return

    elif chat_type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        group_id = message.chat.id

    try:
        st = await client.get_chat_member(group_id, userid)
        if (
                st.status != enums.ChatMemberStatus.ADMINISTRATOR
                and st.status != enums.ChatMemberStatus.OWNER
                and userid not in ADMINS
        ):
            buttons = [[InlineKeyboardButton('⇇ ᴄʟᴏsᴇ ⇉', callback_data='close_data') ]]
            await message.reply_text(text="<b>🥀 ʏᴏᴜ ꜱʜᴏᴜʟᴅ ʙᴇ ᴀɴ ᴀᴅᴍɪɴ ɪɴ ɢɪᴠᴇɴ ɢʀᴏᴜᴘ!!!</b>", reply_markup=InlineKeyboardMarkup(buttons), quote=True)
            return
    except Exception as e:
        logger.exception(e)
        buttons = [[InlineKeyboardButton('⇇ ᴄʟᴏsᴇ ⇉', callback_data='close_data') ]]
        await message.reply_text(text="<b>🥀 ɪɴᴠᴀʟɪᴅ ɢʀᴏᴜᴘ ɪᴅ !!! 📢\n\n✨ ɪғ ᴄᴏʀʀᴇᴄᴛ, ᴍᴀᴋᴇ ꜱᴜʀᴇ ɪ'ᴍ ᴘʀᴇꜱᴇɴᴛ ɪɴ ʏᴏᴜʀ ɢʀᴏᴜᴘ !!!📢</b>", reply_markup=InlineKeyboardMarkup(buttons) ,quote=True,)
        return
    try:
        st = await client.get_chat_member(group_id, "me")
        if st.status == enums.ChatMemberStatus.ADMINISTRATOR:
            ttl = await client.get_chat(group_id)
            title = ttl.title

            addcon = await add_connection(str(group_id), str(userid))
            if addcon:
                buttons = [[InlineKeyboardButton('⇇ ᴄʟᴏsᴇ ⇉', callback_data='close_data') ]]
                await message.reply_text(
                    f"**✅ sᴜᴄᴄᴇꜱꜱғᴜʟʟʏ ᴄᴏɴɴᴇᴄᴛᴇᴅ ᴛᴏ {title}🥀\n\n✨ɴᴏᴡ ᴍᴀɴᴀɢᴇ ʏᴏᴜʀ ɢʀᴏᴜᴘ ғʀᴏᴍ ᴍʏ ᴘᴍ !🥀**",
                    quote=True,
                    reply_markup=InlineKeyboardMarkup(buttons),
                    parse_mode=enums.ParseMode.MARKDOWN
                )
                if chat_type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
                    await client.send_message(
                        userid,
                        f"**✅ ᴄᴏɴɴᴇᴄᴛᴇᴅ ᴛᴏ {title}** !",
                        parse_mode=enums.ParseMode.MARKDOWN
                    )
            else:
                buttons = [[InlineKeyboardButton('⇇ ᴄʟᴏsᴇ ⇉', callback_data='close_data') ]]
                await message.reply_text(text="<b>🥀 ʏᴏᴜ'ʀᴇ ᴀʟʀᴇᴀᴅʏ ᴄᴏɴɴᴇᴄᴛᴇᴅ ᴛᴏ ᴛʜɪꜱ ᴄʜᴀᴛ !!!</b>📢", reply_markup=InlineKeyboardMarkup(buttons) , quote=True)
        else:
            await message.reply_text("<b>🥀 ᴀᴅᴅ ᴍᴇ ᴀꜱ ᴀɴ ᴀᴅᴍɪɴ ɪɴ ɢʀᴏᴜᴘ 📢</b>", quote=True)
    except Exception as e:
        logger.exception(e)
        await message.reply_text(f"**🥀 sᴏᴍᴇ ᴇʀʀᴏʀ ᴏᴄᴄᴜʀʀᴇᴅ! ᴛʀʏ ᴀɢᴀɪɴ ʟᴀᴛᴇʀ. ✨**", quote=True)
        return


@Client.on_message((filters.private | filters.group) & filters.command('disconnect'))
async def deleteconnection(client, message):
    userid = message.from_user.id if message.from_user else None
    if not userid:
        return await message.reply(f"**🥀 ʏᴏᴜ ᴀʀᴇ ᴀɴᴏɴʏᴍᴏᴜꜱ ᴀᴅᴍɪɴ. Uꜱᴇ /connect {message.chat.id} ɪɴ ᴘᴍ 💥**")
    chat_type = message.chat.type

    if chat_type == enums.ChatType.PRIVATE:
        await message.reply_text("**🦸 ʀᴜɴ /connections ᴛᴏ ᴠɪᴇᴡ ᴏʀ ᴅɪꜱᴄᴏɴɴᴇᴄᴛ ғʀᴏᴍ ɢʀᴏᴜᴘꜱ!!! 📢**", quote=True)

    elif chat_type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        group_id = message.chat.id

        st = await client.get_chat_member(group_id, userid)
        if (
                st.status != enums.ChatMemberStatus.ADMINISTRATOR
                and st.status != enums.ChatMemberStatus.OWNER
                and str(userid) not in ADMINS
        ):
            return

        delcon = await delete_connection(str(userid), str(group_id))
        if delcon:
            buttons = [[InlineKeyboardButton('⇇ ᴄʟᴏsᴇ ⇉', callback_data='close_data') ]]
            await message.reply_text("**✅ sᴜᴄᴄᴇꜱꜱғᴜʟʟʏ ᴅɪꜱᴄᴏɴɴᴇᴄᴛᴇᴅ ғʀᴏᴍ ᴛʜɪꜱ ᴄʜᴀᴛ 📢\n\n🥀 ᴩᴏᴡᴇʀᴇᴅ ʙʏ - <a href=https://t.me/Hs_Botz>ʜꜱ ᠰ ʙᴏᴛꜱ</a>**", disable_web_page_preview=True, reply_markup=InlineKeyboardMarkup(buttons), quote=True)
        else:
            await message.reply_text("**🥀 ᴛʜɪꜱ ᴄʜᴀᴛ ɪꜱɴ'ᴛ ᴄᴏɴɴᴇᴄᴛᴇᴅ ᴛᴏ ᴍᴇ!\n\nᴅᴏ /connect ᴛᴏ ᴄᴏɴɴᴇᴄᴛ. ✨**", quote=True)


@Client.on_message(filters.private & filters.command(["connections"]))
async def connections(client, message):
    userid = message.from_user.id

    groupids = await all_connections(str(userid))
    if groupids is None:
        await message.reply_text(
            "**🥀 ᴛʜᴇʀᴇ ᴀʀᴇ ɴᴏ ᴀᴄᴛɪᴠᴇ ᴄᴏɴɴᴇᴄᴛɪᴏɴꜱ!! ᴄᴏɴɴᴇᴄᴛ ᴛᴏ ꜱᴏᴍᴇ ɢʀᴏᴜᴘꜱ ғɪʀꜱᴛ.💢**",
            quote=True
        )
        return
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
        await message.reply_text(
            "ᴄᴏɴɴᴇᴄᴛᴇᴅ ɢʀᴏᴜᴘs :-\n\n",
            reply_markup=InlineKeyboardMarkup(buttons),
            quote=True
        )
    else:
        await message.reply_text(
            "**🥀 ᴛʜᴇʀᴇ ᴀʀᴇ ɴᴏ ᴀᴄᴛɪᴠᴇ ᴄᴏɴɴᴇᴄᴛɪᴏɴꜱ!! ᴄᴏɴɴᴇᴄᴛ ᴛᴏ ꜱᴏᴍᴇ ɢʀᴏᴜᴘꜱ ғɪʀꜱᴛ. 💢**",
            quote=True
        )
