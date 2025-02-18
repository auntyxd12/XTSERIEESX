import os
import re
import logging
import aiofiles
import aiohttp
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont
from unidecode import unidecode
from youtubesearchpython.__future__ import VideosSearch

from SUKOON_MUSIC import app
from config import YOUTUBE_IMG_URL

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
CACHE_DIR = "cache"
FONT_PATH = "SUKOON_MUSIC/assets/font.ttf"
FONT2_PATH = "SUKOON_MUSIC/assets/font2.ttf"

def ensure_cache_dir():
    """Ensure the cache directory exists."""
    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR)

def change_image_size(max_width, max_height, image):
    """Resize the image while maintaining aspect ratio."""
    width_ratio = max_width / image.size[0]
    height_ratio = max_height / image.size[1]
    new_width = int(width_ratio * image.size[0])
    new_height = int(height_ratio * image.size[1])
    return image.resize((new_width, new_height))

def clear(text):
    """Truncate text to fit within a certain length."""
    words = text.split(" ")
    title = ""
    for word in words:
        if len(title) + len(word) < 60:
            title += " " + word
    return title.strip()

async def download_thumbnail(videoid, thumbnail_url):
    """Download the thumbnail image."""
    async with aiohttp.ClientSession() as session:
        async with session.get(thumbnail_url) as resp:
            if resp.status == 200:
                file_path = f"{CACHE_DIR}/thumb{videoid}.png"
                async with aiofiles.open(file_path, mode="wb") as f:
                    await f.write(await resp.read())
                return file_path
    return None

async def get_video_info(videoid):
    """Fetch video information from YouTube."""
    url = f"https://www.youtube.com/watch?v={videoid}"
    try:
        results = VideosSearch(url, limit=1)
        for result in (await results.next())["result"]:
            title = result.get("title", "Unsupported Title")
            title = re.sub("\W+", " ", title).title()
            duration = result.get("duration", "Unknown Mins")
            thumbnail = result["thumbnails"][0]["url"].split("?")[0]
            views = result.get("viewCount", {}).get("short", "Unknown Views")
            channel = result.get("channel", {}).get("name", "Unknown Channel")
            return title, duration, thumbnail, views, channel
    except Exception as e:
        logger.error(f"Error fetching video info: {e}")
    return None, None, None, None, None

async def create_thumbnail(videoid, title, duration, views, channel):
    """Create a custom thumbnail image."""
    try:
        youtube = Image.open(f"{CACHE_DIR}/thumb{videoid}.png")
        image1 = change_image_size(1280, 720, youtube)
        image2 = image1.convert("RGBA")
        background = image2.filter(filter=ImageFilter.BoxBlur(10))
        enhancer = ImageEnhance.Brightness(background)
        background = enhancer.enhance(0.5)
        draw = ImageDraw.Draw(background)
        arial = ImageFont.truetype(FONT2_PATH, 30)
        font = ImageFont.truetype(FONT_PATH, 30)

        # Draw text and shapes
        text_size = draw.textsize("T-SERIES MUSIC BOTS    ", font=font)
        draw.text((1280 - text_size[0] - 10, 10), "SUKOON MUSIC BOTS    ", fill="white", font=font)
        draw.text((55, 560), f"{channel} | {views[:23]}", (255, 255, 255), font=arial)
        draw.text((57, 600), clear(title), (255, 255, 255), font=font)
        draw.line([(55, 660), (1220, 660)], fill="white", width=5, joint="curve")
        draw.ellipse([(918, 648), (942, 672)], outline="white", fill="white", width=15)
        draw.text((36, 685), "00:00", (255, 255, 255), font=arial)
        draw.text((1185, 685), f"{duration[:23]}", (255, 255, 255), font=arial)

        # Save the final thumbnail
        final_path = f"{CACHE_DIR}/{videoid}.png"
        background.save(final_path)
        return final_path
    except Exception as e:
        logger.error(f"Error creating thumbnail: {e}")
        return None

async def get_thumb(videoid):
    """Get the thumbnail for a given video ID."""
    ensure_cache_dir()
    cached_path = f"{CACHE_DIR}/{videoid}.png"
    if os.path.isfile(cached_path):
        return cached_path

    title, duration, thumbnail_url, views, channel = await get_video_info(videoid)
    if not thumbnail_url:
        return YOUTUBE_IMG_URL

    thumb_path = await download_thumbnail(videoid, thumbnail_url)
    if not thumb_path:
        return YOUTUBE_IMG_URL

    final_path = await create_thumbnail(videoid, title, duration, views, channel)
    if not final_path:
        return YOUTUBE_IMG_URL

    try:
        os.remove(thumb_path)
    except Exception as e:
        logger.error(f"Error removing temporary thumbnail: {e}")

    return final_path
