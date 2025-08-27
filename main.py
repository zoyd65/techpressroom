import os
import requests
import feedparser
import datetime

from dotenv import load_dotenv

# Carica eventuali variabili da file .env (solo in locale)
load_dotenv()

# Legge variabili da Secrets GitHub o da file .env
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_USER_ID = os.getenv("TELEGRAM_USER_ID")
HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY")

# Controllo per debug (stampa se manca qualcosa)
if not TELEGRAM_BOT_TOKEN:
    print("⚠️ Errore: TELEGRAM_BOT_TOKEN non trovato")
if not TELEGRAM_USER_ID:
    print("⚠️ Errore: TELEGRAM_USER_ID non trovato")
if not HUGGINGFACE_API_KEY:
    print("⚠️ Errore: HUGGINGFACE_API_KEY non trovato")


# === FEED RSS ===
RSS_FEEDS = [
    "https://techcrunch.com/feed/",
    "https://www.theverge.com/rss/index.xml",
    "http://feeds.arstechnica.com/arstechnica/index",
    "https://www.technologyreview.com/feed/",
    "https://www.agendadigitale.eu/feed/",
    "https://www.iltascabile.com/feed/",
    "https://www.valigiablu.it/feed/",
    "https://www.scienzainrete.it/rss",
    "https://aeon.co/feed.rss",
    "https://knowablemagazine.org/rss",
    "https://www.futurity.org/feed/",
    "https://www.inverse.com/rss",
    "https://thenextweb.com/feed/"
]

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

# === TELEGRAM ===
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_USER_ID = os.getenv("TELEGRAM_USER_ID")

def invia_telegram(messaggio: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_USER_ID, "text": messaggio, "parse_mode": "Markdown"}
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
    except Exception as e:
        print(f"❌ Errore invio Telegram: {e}")

# === RACCOLTA NOTIZIE ===
def notizie_delle_ultime_24_ore(feed_url):
    notizie = []
    try:
        resp = requests.get(feed_url, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        feed = feedparser.parse(resp.text)

        for entry in feed.entries:
            try:
                data_pubblicazione = None
                if hasattr(entry, "published_parsed") and entry.published_parsed:
                    data_pubblicazione = datetime.datetime(*entry.published_parsed[:6], tzinfo=datetime.timezone.utc)

                if data_pubblicazione and data_pubblicazione > datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=1):
                    notizie.append({
                        "title": entry.get("title", "Senza titolo"),
                        "link": entry.get("link", ""),
                        "published": entry.get("published", "Data non disponibile")
                    })
            except Exception as e:
                print(f"⚠️ Errore su entry di {feed_url}: {e}")
    except Exception as e:
        print(f"❌ Errore download feed {feed_url}: {e}")

    return notizie

def main():
    tutte_le_notizie = []
    for feed_url in RSS_FEEDS:
        tutte_le_notizie.extend(notizie_delle_ultime_24_ore(feed_url))

    if not tutte_le_notizie:
        invia_telegram("📰 Nessuna notizia trovata nelle ultime 24 ore.")
        return

    messaggio = "🗞️ *Rassegna Stampa Tech di oggi:*\n\n"
    for art in tutte_le_notizie[:15]:
        messaggio += f"• [{art['title']}]({art['link']})\n"

    invia_telegram(messaggio)

if __name__ == "__main__":
    main()
