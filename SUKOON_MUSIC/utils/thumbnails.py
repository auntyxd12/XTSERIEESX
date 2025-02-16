import os
import re
import logging
import asyncio
from datetime import datetime, timedelta
import aiofiles
import aiohttp
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps
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
CACHE_EXPIRY_DAYS = 7  # Cache expiry in days

# Ensure cache directory exists
if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)

# Custom Exceptions
class ThumbnailError(Exception):
    pass

class VideoInfoError(Exception):
    pass

# Utility Functions
def clear(text):
    """Truncate text to fit within a certain length."""
    words = text.split(" ")
    title = ""
    for word in words:
        if len(title) + len(word) < 60:
            title += " " + word
    return title.strip()

def is_cache_valid(file_path):
    """Check if the cached file is still valid."""
    if not os.path.exists(file_path):
        return False
    file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
    return datetime.now() - file_time < timedelta(days=CACHE_EXPIRY_DAYS)

async def download_thumbnail(videoid, thumbnail_url):
    """Download the thumbnail image asynchronously."""
    file_path = f"{CACHE_DIR}/thumb{videoid}.png"
    async with aiohttp.ClientSession() as session:
        async with session.get(thumbnail_url) as resp:
            if resp.status == 200:
                async with aiofiles.open(file_path, mode="wb") as f:
                    await f.write(await resp.read())
                return file_path
    raise ThumbnailError("Failed to download thumbnail")

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
        raise VideoInfoError("Failed to fetch video info")

async def create_thumbnail(videoid, title, duration, views, channel):
    """Create a custom thumbnail image with advanced features."""
    try:
        # Open downloaded thumbnail
        youtube = Image.open(f"{CACHE_DIR}/thumb{videoid}.png")
        image = change_image_size(1280, 720, youtube)

        # Apply advanced image processing
        image = image.convert("RGBA")
        background = image.filter(filter=ImageFilter.GaussianBlur(10))
        enhancer = ImageEnhance.Brightness(background)
        background = enhancer.enhance(0.5)

        # Add gradient overlay
        gradient = Image.new("RGBA", image.size, color=(0, 0, 0, 0))
        draw_gradient = ImageDraw.Draw(gradient)
        for i in range(0, 720):
            alpha = int(255 * (i / 720))
            draw_gradient.line([(0, i), (1280, i)], fill=(0, 0, 0, alpha))
        background = Image.alpha_composite(background, gradient)

        # Draw text and shapes
        draw = ImageDraw.Draw(background)
        arial = ImageFont.truetype(FONT2_PATH, 30)
        font = ImageFont.truetype(FONT_PATH, 30)

        # Dynamic font sizing for title
        title_font_size = 30
        while draw.textsize(title, font=font)[0] > 1200:
            title_font_size -= 1
            font = ImageFont.truetype(FONT_PATH, title_font_size)

        # Draw text
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
        raise ThumbnailError("Failed to create thumbnail")

async def get_thumb(videoid):
    """Get the thumbnail for a given video ID."""
    cached_path = f"{CACHE_DIR}/{videoid}.png"
    if os.path.isfile(cached_path) and is_cache_valid(cached_path):
        return cached_path

    try:
        # Fetch video info and download thumbnail concurrently
        title, duration, thumbnail_url, views, channel = await get_video_info(videoid)
        thumb_path = await download_thumbnail(videoid, thumbnail_url)

        # Create and save the final thumbnail
        final_path = await create_thumbnail(videoid, title, duration, views, channel)

        # Clean up temporary files
        try:
            os.remove(thumb_path)
        except Exception as e:
            logger.error(f"Error removing temporary thumbnail: {e}")

        return final_path
    except (VideoInfoError, ThumbnailError) as e:
        logger.error(f"Error generating thumbnail: {e}")
        return YOUTUBE_IMG_URL
