#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# (c) Shrimadhav U K | gautamajay52

import asyncio
import logging
import os
import sys
import time
import re
from re import search
import subprocess
import hashlib
import math

import aria2p
from pyrogram.errors import FloodWait, MessageNotModified
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from tobrot import (
    ARIA_TWO_STARTED_PORT,
    AUTH_CHANNEL,
    CUSTOM_FILE_NAME,
    DOWNLOAD_LOCATION,
    EDIT_SLEEP_TIME_OUT,
    LOGGER,
    MAX_TIME_TO_WAIT_FOR_TORRENTS_TO_START

)
from tobrot.helper_funcs.create_compressed_archive import (
    create_archive,
    get_base_name,
    unzip_me,
)
from tobrot.helper_funcs.extract_link_from_message import extract_link
from tobrot.helper_funcs.upload_to_tg import upload_to_gdrive, upload_to_tg
from tobrot.helper_funcs.download import download_tg

from tobrot.helper_funcs.direct_link_generator import direct_link_generator
from tobrot.helper_funcs.exceptions import DirectDownloadLinkException

sys.setrecursionlimit(10 ** 4)



async def aria_start():
    aria2_daemon_start_cmd = []
    # start the daemon, aria2c command
    aria2_daemon_start_cmd.append("aria2c")
    aria2_daemon_start_cmd.append("--conf-path=/app/tobrot/aria2/aria2.conf")
    aria2_daemon_start_cmd.append("--allow-overwrite=true")
    aria2_daemon_start_cmd.append("--daemon=true")
    # aria2_daemon_start_cmd.append(f"--dir={DOWNLOAD_LOCATION}")
    # TODO: this does not work, need to investigate this.
    # but for now, https://t.me/TrollVoiceBot?start=858
    aria2_daemon_start_cmd.append("--enable-rpc")
    aria2_daemon_start_cmd.append("--disk-cache=0")
    aria2_daemon_start_cmd.append("--follow-torrent=mem")
    aria2_daemon_start_cmd.append("--max-connection-per-server=16")
    aria2_daemon_start_cmd.append("--min-split-size=10M")
    aria2_daemon_start_cmd.append("--rpc-listen-all=false")
    aria2_daemon_start_cmd.append(f"--rpc-listen-port={ARIA_TWO_STARTED_PORT}")
    aria2_daemon_start_cmd.append("--rpc-max-request-size=1024M")
    aria2_daemon_start_cmd.append("--seed-ratio=0.01")
    aria2_daemon_start_cmd.append("--seed-time=1")
    aria2_daemon_start_cmd.append("--max-overall-upload-limit=2M")
    aria2_daemon_start_cmd.append("--split=16")
    aria2_daemon_start_cmd.append(f"--bt-stop-timeout={MAX_TIME_TO_WAIT_FOR_TORRENTS_TO_START}")
    #
    LOGGER.info(aria2_daemon_start_cmd)
    #
    process = await asyncio.create_subprocess_exec(
        *aria2_daemon_start_cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await process.communicate()
    LOGGER.info(stdout)
    LOGGER.info(stderr)
    aria2 = aria2p.API(
        aria2p.Client(host="http://localhost", port=ARIA_TWO_STARTED_PORT, secret="")
    )
    return aria2


def add_magnet(aria_instance, magnetic_link, c_file_name):
    options = None
    # if c_file_name is not None:
    #     options = {
    #         "dir": c_file_name
    #     }
    try:
        download = aria_instance.add_magnet(magnetic_link, options=options)
    except Exception as e:
        return (
            False,
            "**👺𝙁𝘼𝙄𝙇𝙀𝘿** \n" + str(e) + " \n𝙋𝙡𝙚𝙖𝙨𝙚 𝙙𝙤 𝙣𝙤𝙩 𝙨𝙚𝙣𝙙 𝙎𝙇𝙊𝙒/𝘿𝙀𝘼𝘿 𝙡𝙞𝙣𝙠𝙨 𝙤𝙧 𝙘𝙝𝙚𝙘𝙠 𝙨𝙥𝙖𝙘𝙚𝙨.👺",
        )
    else:
        return True, "" + download.gid + ""


def add_torrent(aria_instance, torrent_file_path):
    if torrent_file_path is None:
        return (
            False,
            "**🔴FAILED** \n"
            + str(e)
            + " \n𝙨𝙤𝙢𝙚𝙩𝙝𝙞𝙣𝙜 𝙬𝙧𝙤𝙣𝙜 𝙤𝙘𝙘𝙪𝙧𝙧𝙚𝙙 𝙬𝙝𝙚𝙣 𝙩𝙧𝙮𝙞𝙣𝙜 𝙩𝙤 𝙖𝙙𝙙 <u>𝙏𝙊𝙍𝙍𝙀𝙉𝙏</u> 𝙛𝙞𝙡𝙚❌",
        )
    if os.path.exists(torrent_file_path):
        # Add Torrent Into Queue
        try:
            download = aria_instance.add_torrent(
                torrent_file_path, uris=None, options=None, position=None
            )
        except Exception as e:
            return (
                False,
                "**👺𝙁𝘼𝙄𝙇𝙀𝘿** \n"
                + str(e)
                + " \n𝙋𝙡𝙚𝙖𝙨𝙚 𝙙𝙤 𝙣𝙤𝙩 𝙨𝙚𝙣𝙙 𝙎𝙇𝙊𝙒/𝘿𝙀𝘼𝘿 𝙡𝙞𝙣𝙠𝙨 𝙤𝙧 𝙘𝙝𝙚𝙘𝙠 𝙨𝙥𝙖𝙘𝙚𝙨.👺",
            )
        else:
            return True, "" + download.gid + ""
    else:
        return False, "**👺𝙁𝘼𝙄𝙇𝙀𝘿** \n𝙋𝙡𝙚𝙖𝙨𝙚 𝙩𝙧𝙮 𝙤𝙩𝙝𝙚𝙧 𝙨𝙤𝙪𝙧𝙘𝙚𝙨 𝙩𝙤 𝙜𝙚𝙩 𝙬𝙤𝙧𝙠𝙖𝙗𝙡𝙚 𝙡𝙞𝙣𝙠👺"


def add_url(aria_instance, text_url, c_file_name):
    options = None
    # if c_file_name is not None:
    #     options = {
    #         "dir": c_file_name
    #     }
    if "zippyshare.com" in text_url \
        or "osdn.net" in text_url \
        or "mediafire.com" in text_url \
        or "cloud.mail.ru" in text_url \
        or "github.com" in text_url \
        or "yadi.sk" in text_url  \
        or "racaty.net" in text_url:
            try:
                urisitring = direct_link_generator(text_url)
                uris = [urisitring]
            except DirectDownloadLinkException as e:
                LOGGER.info(f'{text_url}: {e}')
    else:
        uris = [text_url]
    # Add URL Into Queue
    try:
        download = aria_instance.add_uris(uris, options=options)
    except Exception as e:
        return (
            False,
            "**👺𝙁𝘼𝙄𝙇𝙀𝘿** \n" + str(e) + " \n𝙋𝙡𝙚𝙖𝙨𝙚 𝙙𝙤 𝙣𝙤𝙩 𝙨𝙚𝙣𝙙 𝙎𝙇𝙊𝙒/𝘿𝙀𝘼𝘿 𝙡𝙞𝙣𝙠𝙨 𝙤𝙧 𝙘𝙝𝙚𝙘𝙠 𝙨𝙥𝙖𝙘𝙚𝙨.👺",
        )
    else:
        return True, "" + download.gid + ""


async def call_apropriate_function(
    aria_instance,
    incoming_link,
    c_file_name,
    sent_message_to_update_tg_p,
    is_zip,
    cstom_file_name,
    is_cloud,
    is_unzip,
    is_file,
    user_message,
    client,
):
    if not is_file:
        if incoming_link.lower().startswith("magnet:"):
            sagtus, err_message = add_magnet(aria_instance, incoming_link, c_file_name)
        elif incoming_link.lower().endswith(".torrent"):
            sagtus, err_message = add_torrent(aria_instance, incoming_link)
        else:
            sagtus, err_message = add_url(aria_instance, incoming_link, c_file_name)
        if not sagtus:
            return sagtus, err_message
        LOGGER.info(err_message)
        # https://stackoverflow.com/a/58213653/4723940
        await check_progress_for_dl(
            aria_instance, err_message, sent_message_to_update_tg_p, None
        )
        if incoming_link.startswith("magnet:"):
            #
            err_message = await check_metadata(aria_instance, err_message)
            #
            await asyncio.sleep(1)
            if err_message is not None:
                await check_progress_for_dl(
                    aria_instance, err_message, sent_message_to_update_tg_p, None
                )
            else:
                return False, "🔴𝙘𝙖𝙣'𝙩 𝙜𝙚𝙩 𝙢𝙚𝙩𝙖𝙙𝙖𝙩𝙖 \n\n#DeadTorrent⚰️"
        await asyncio.sleep(1)
        try:
            file = aria_instance.get_download(err_message)
        except aria2p.client.ClientException as ee:
            LOGGER.error(ee)
            return True, None
        to_upload_file = file.name
        com_g = file.is_complete
    else:
        await sent_message_to_update_tg_p.delete()
        to_upload_file, sent_message_to_update_tg_p = await download_tg(client=client, message=user_message)
        com_g = False
        if to_upload_file:
            com_g = True

    if is_zip:
        check_if_file = await create_archive(to_upload_file)
        if check_if_file is not None:
            to_upload_file = check_if_file
    #
    if is_unzip:
        try:
            check_ifi_file = get_base_name(to_upload_file)
            await unzip_me(to_upload_file)
            if os.path.exists(check_ifi_file):
                to_upload_file = check_ifi_file
        except Exception as ge:
            LOGGER.info(ge)
            LOGGER.info(
                f"😐𝘾𝙖𝙣'𝙩 𝙚𝙭𝙩𝙧𝙖𝙘𝙩 {os.path.basename(to_upload_file)}, 𝙐𝙥𝙡𝙤𝙖𝙙𝙞𝙣𝙜 𝙩𝙝𝙚 𝙨𝙖𝙢𝙚 𝙛𝙞𝙡𝙚😐"
            )

    if to_upload_file:
        if CUSTOM_FILE_NAME:
            if os.path.isfile(to_upload_file):
                os.rename(to_upload_file, f"{CUSTOM_FILE_NAME}{to_upload_file}")
                to_upload_file = f"{CUSTOM_FILE_NAME}{to_upload_file}"
            else:
                for root, _, files in os.walk(to_upload_file):
                    LOGGER.info(files)
                    for org in files:
                        p_name = f"{root}/{org}"
                        n_name = f"{root}/{CUSTOM_FILE_NAME}{org}"
                        os.rename(p_name, n_name)
                to_upload_file = to_upload_file

    if cstom_file_name:
        os.rename(to_upload_file, cstom_file_name)
        to_upload_file = cstom_file_name
    #
    response = {}
    LOGGER.info(response)
    user_id = user_message.from_user.id
    if com_g:
        if is_cloud:
            await upload_to_gdrive(
                to_upload_file, sent_message_to_update_tg_p, user_message, user_id
            )
        else:
            final_response = await upload_to_tg(
                sent_message_to_update_tg_p, to_upload_file, user_id, response, client
            )
            if not final_response:
                return True, None
            try:
                message_to_send = ""
                for key_f_res_se in final_response:
                    local_file_name = key_f_res_se
                    message_id = final_response[key_f_res_se]
                    channel_id = str(sent_message_to_update_tg_p.chat.id)[4:]
                    private_link = f"https://t.me/c/{channel_id}/{message_id}"
                    message_to_send += "📦⬤ <a href='"
                    message_to_send += private_link
                    message_to_send += "'>"
                    message_to_send += local_file_name
                    message_to_send += "</a>"
                    message_to_send += "\n"
                if message_to_send != "":
                    mention_req_user = (
                        f"\n<a href='tg://user?id={user_id}'>🤗DONE📤</a>\n"
                    )
                    message_to_send = f"\n<code>{str(file.name)}</code>\n<b>📦 𝙏𝙤𝙩𝙖𝙡 𝙁𝙞𝙡𝙚 𝙎𝙞𝙯𝙚: {file.total_length_string()}</b>\n\n" + message_to_send 
                    message_to_send = message_to_send + "\n\n" + mention_req_user + f"<b>⭐#uploads⛳</b>"
                else:
                    message_to_send = "<i>🔴𝙁𝘼𝙄𝙇𝙀𝘿</i> 𝙩𝙤 𝙪𝙥𝙡𝙤𝙖𝙙 𝙛𝙞𝙡𝙚𝙨😞"
                await user_message.reply_text(
                    text=message_to_send, quote=True, disable_web_page_preview=True
                )
            except Exception as go:
                LOGGER.error(go)
    return True, None


#


# https://github.com/jaskaranSM/UniBorg/blob/6d35cf452bce1204613929d4da7530058785b6b1/stdplugins/aria.py#L136-L164

# todo- so much unwanted code, I will remove in future after some testing
async def check_progress_for_dl(aria2, gid, event, previous_message):
    while True:
        try:
            file = aria2.get_download(gid)
            complete = file.is_complete
            is_file = file.seeder
            if not complete:
                if not file.error_message:
                    if file.has_failed:
                        LOGGER.info(
                            f"🔴𝘾𝙖𝙣𝙘𝙚𝙡𝙡𝙞𝙣𝙜 𝙙𝙤𝙬𝙣𝙡𝙤𝙖𝙙𝙞𝙣𝙜 𝙤𝙛 {file.name} 𝙢𝙖𝙮 𝙗𝙚 𝙙𝙪𝙚 𝙩𝙤 𝙨𝙡𝙤𝙬 𝙩𝙤𝙧𝙧𝙚𝙣𝙩🐌"
                        )
                        await event.edit(
                            f"🔴𝘿𝙤𝙬𝙣𝙡𝙤𝙖𝙙 𝙘𝙖𝙣𝙘𝙚𝙡𝙡𝙚𝙙 :\n<code>{file.name}</code>\n\n #DeadTorrent⚰️"
                        )
                        file.remove(force=True, files=True)
                        return
                else:
                    msg = file.error_message
                    LOGGER.info(msg)
                    await asyncio.sleep(EDIT_SLEEP_TIME_OUT)
                    await event.reply(f"`{msg}`")
                    return
                await asyncio.sleep(EDIT_SLEEP_TIME_OUT)
                # await check_progress_for_dl(aria2, gid, event, previous_message)
            else:
                LOGGER.info(
                    f"Downloaded Successfully: `{file.name} ({file.total_length_string()})` 🤒"
                )
                # await asyncio.sleep(EDIT_SLEEP_TIME_OUT)
                if not file.is_metadata:
                    await event.edit(
                        f"Downloaded Successfully: `{file.name} ({file.total_length_string()})` 🤒"
                    )
                return
        except aria2p.client.ClientException:
            await event.reply(
                f"Download cancelled :\n""🟢𝘿𝙤𝙬𝙣𝙡𝙤𝙖𝙙𝙚𝙙 𝙎𝙪𝙘𝙘𝙚𝙨𝙨𝙛𝙪𝙡𝙡𝙮: `{file.name} ({file.total_length_string()})` 🤗", quote=True
            )
            return
        except MessageNotModified as ep:
            LOGGER.info(ep)
            await asyncio.sleep(EDIT_SLEEP_TIME_OUT)
            # await check_progress_for_dl(aria2, gid, event, previous_message)
            return
        except FloodWait as e:
            LOGGER.info(e)
            time.sleep(e.x)
        except Exception as e:
            LOGGER.info(str(e))
            if "not found" in str(e) or "'file'" in str(e):
                await event.edit(
                    f"🔴𝘿𝙤𝙬𝙣𝙡𝙤𝙖𝙙 𝙘𝙖𝙣𝙘𝙚𝙡𝙡𝙚𝙙 :\n<code>{file.name} ({file.total_length_string()})</code>❌"
                    )
                return
            else:
                LOGGER.info(str(e))
                await event.edit(
                    "<u>error</u> :\n<code>{}</code> \n\n#error".format(str(e))
                )
                return


# https://github.com/jaskaranSM/UniBorg/blob/6d35cf452bce1204613929d4da7530058785b6b1/stdplugins/aria.py#L136-L164


async def check_metadata(aria2, gid):
    file = aria2.get_download(gid)
    LOGGER.info(file)
    if not file.followed_by_ids:
        # https://t.me/c/1213160642/496
        return None
    new_gid = file.followed_by_ids[0]
    LOGGER.info("𝘾𝙝𝙖𝙣𝙜𝙞𝙣𝙜 𝙂𝙄𝘿 " + gid + " 𝙩𝙤 " + new_gid)
    return new_gid
