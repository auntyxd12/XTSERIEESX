from SUKOON_MUSIC.core.bot import PURVI
from SUKOON_MUSIC.core.dir import dirr
from SUKOON_MUSIC.core.git import git
from SUKOON_MUSIC.core.userbot import Userbot
from SUKOON_MUSIC.misc import dbb, heroku

from SafoneAPI import SafoneAPI
from .logging import LOGGER

dirr()
git()
dbb()
heroku()

app = PURVI()
api = SafoneAPI()
userbot = Userbot()


from .platforms import *

Apple = AppleAPI()
Carbon = CarbonAPI()
SoundCloud = SoundAPI()
Spotify = SpotifyAPI()
Resso = RessoAPI()
Telegram = TeleAPI()
YouTube = YouTubeAPI()
