"""
    █▀▀ ▄▀█ █▄▀ █▀▀ █▀ ▀█▀ █░█░█ █ ▀▄▀
    █▄▄ █▀█ █░█ ██▄ ▄█ ░█░ ▀▄▀▄▀ █ █░█

    Copyleft 2022 t.me/CakesTwix
    This program is free software; you can redistribute it and/or modify

"""

__version__ = (1, 2, 3)

# meta pic: https://img.icons8.com/bubbles/512/000000/youtube-play.png
# meta developer: @cakestwix_mods
# requires: yt_dlp aiohttp
# scope: hikka_min 1.1.11
# scope: hikka_only

import asyncio
import logging
import aiohttp
import os
import shutil  # Added for copying cookies.txt
from yt_dlp.utils import DownloadError
import yt_dlp
from telethon.tl.types import Message
from telethon import functions, types

from .. import loader, utils
from ..inline.types import InlineCall

logger = logging.getLogger(__name__)

# Add the path to your original cookies file
COOKIES_FILE = '/root/snap/cookies.txt'  # Adjust the path if your cookies file is elsewhere

# Temporary copy of the cookies file
TEMP_COOKIES_FILE = '/tmp/cookies_temp.txt'

# Copy the cookies.txt to a temporary file to prevent it from being overwritten
try:
    shutil.copyfile(COOKIES_FILE, TEMP_COOKIES_FILE)
    os.chmod(TEMP_COOKIES_FILE, 0o644)  # Ensure proper permissions for the temp file
except PermissionError:
    logger.error(f"Permission denied while copying cookies file: {COOKIES_FILE}")
except Exception as e:
    logger.error(f"Error copying cookies file: {str(e)}")


def bytes2human(num, suffix="B"):
    if not num:
        return 0
    for unit in ["", "Ki", "Mi", "Gi", "Ti", "Pi", "Ei", "Zi"]:
        if abs(num) < 1024.0:
            return f"{num:3.1f}{unit}{suffix}"
        num /= 1024.0
    return f"{num:.1f}Yi{suffix}"


def progressbar(iteration: int, length: int) -> str:
    percent = ("{0:." + str(1) + "f}").format(100 * (iteration / float(100)))
    filledLength = int(length * iteration // 100)
    return "█" * filledLength + "▒" * (length - filledLength)


@loader.tds
class YouTubeMod(loader.Module):
    """Download YouTube videos with video and audio quality selection"""

    strings = {
        "name": "InlinedadaYouTube",
        "args": "🎞 <b>You need to specify link</b>",
        "downloading": "🎞 <b>Downloading...</b>",
        "not_found": "🎞 <b>Video not found...</b>",
        "no_qualt": "No quality",
        "format": "<b>Format</b>:",
        "ext": "<b>Ext</b>:",
        "video_codec": "<b>Video codec</b>:",
        "audio": "Audio",
        "file_size": "<b>File size</b>:",
        "uploading": "🎞 <b>Uploading File...</b>",
        "getting_info": "ℹ️ <b>Getting information about the video...</b>",
    }

    strings_ru = {
        "name": "InlinedadaYouTube",
        "args": "🎞 <b>Вам необходимо указать ссылку</b>",
        "downloading": "🎞 <b>Скачиваю...</b>",
        "not_found": "🎞 <b>Видео не найдено...</b>",
        "no_qualt": "Нету такого качества",
        "format": "<b>Формат</b>:",
        "ext": "<b>Расширение</b>:",
        "video_codec": "<b>Видео кодек</b>:",
        "audio": "Аудио",
        "file_size": "<b>Размер</b>:",
        "uploading": "🎞 <b>Загружаю...</b>",
        "getting_info": "ℹ️ <bПолучаю информацию про видео...</b>",
    }

    async def client_ready(self, client, db):
        self._db = db
        self._client = client

    @loader.unrestricted
    async def ytcmd(self, message: Message):
        """[quality(144p/720p/etc)] <link> - Download video from youtube"""
        args = utils.get_args(message)
        await utils.answer(message, self.strings("getting_info"))

        if not args:
            return await utils.answer(message, self.strings("args"))

        # Ensure the temporary cookies file exists and is readable
        if not os.path.exists(TEMP_COOKIES_FILE):
            return await utils.answer(message, "Cookies file is missing or inaccessible.")

        ydl_opts = {
            'cookiefile': TEMP_COOKIES_FILE,  # Using the temp cookies file
            'outtmpl': '%(title)s.%(ext)s',
            'quiet': False,  # Enable output for debugging if needed
            'noprogress': True,  # Disable progress bar for simplicity
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                info_dict = ydl.extract_info(
                    args[1] if len(args) >= 2 else args[0], download=False
                )
            except DownloadError as e:
                return await utils.answer(message, e.msg)

            formats_list = [{
                "text": f"{item.get('format_note', 'Unknown format')} ({item.get('video_ext', 'Unknown')})",
                "callback": self.format_change,
                "args": (item, info_dict, message.chat.id, item["format_id"],),
            } for item in info_dict["formats"] if item["ext"] in ["mp4", "webm"] and item["vcodec"] != "none" and (len(args) >= 2 and args[0] == item.get("format_note", 'Unknown format') or len(args) < 2)]

            caption = f"<b>{info_dict.get('title', 'Unknown title')}</b>\n\n"

            await self.inline.form(
                text=caption if formats_list else self.strings["no_qualt"],
                photo=f"https://img.youtube.com/vi/{info_dict.get('id', '')}/0.jpg",
                message=message,
                reply_markup=utils.chunks(formats_list, 2)
            )

    async def format_change(
        self,
        call: InlineCall,
        quality: dict,
        info_dict: dict,
        chat_id: int,
        format_id: int):
        string = f"{self.strings['format']} {quality.get('format', 'Unknown')}\n"
        string += f"{self.strings['ext']} {quality.get('ext', 'Unknown')}\n"
        string += f"{self.strings['video_codec']} {quality.get('vcodec', 'Unknown codec')}\n"
        string += f"{self.strings['file_size']} {bytes2human(quality.get('filesize', 0))}\n"

        audio_keyboard = [{
            "text": f"{self.strings['audio']} ({audio.get('format_note', 'Unknown')})",
            "callback": self.download,
            "args": (info_dict["id"], quality["ext"], quality["format_id"], audio["format_id"], chat_id,),
        } for audio in info_dict["formats"] if audio["ext"] == "m4a"]

        audio_keyboard.append(
            {
                "text": "Back",
                "callback": self.back,
                "args": (
                    info_dict,
                    chat_id,
                ),
            },
        )

        await call.edit(
            text=string,
            reply_markup=audio_keyboard,
        )

    async def back(self, call: InlineCall, info_dict: dict, chat_id: int):
        formats_list = [{
            "text": f"{item.get('format_note', 'Unknown format')} ({item.get('video_ext', 'Unknown')})",
            "callback": self.format_change,
            "args": (item, info_dict, chat_id, item["format_id"]),
        } for item in info_dict["formats"] if item["ext"] in ["mp4", "webm"] and item["vcodec"] != "none"]

        caption = f"<b>{info_dict.get('title', '