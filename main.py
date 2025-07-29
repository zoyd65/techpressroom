import feedparser
import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_USER_ID = os.getenv("TELEGRAM_USER_ID")
HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY")

RSS_FEEDS = [
    "https://www.hdblog.it/rss/",
    "https://www.smartworld.it/feed/rss",
    "https://techprincess.it/feed/",
    "https://www.tomshw.it/feed/",
    "https://www.hwupgrade.it/rss/all.xml",
    "https://www.wired.it/feed/",
]

def estrai_articoli_ultime_ore(url, o_
