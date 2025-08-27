import feedparser
import os
import requests
import datetime
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_USER_ID = os.getenv("TELEGRAM_USER_ID")
HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY")

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
    "https://thenextweb.com/feed/",
]

def sintetizza_articolo(titolo, descrizione, contenuto):
    """Sintetizza la notizia usando HuggingFace."""
    testo = f"TITOLO: {titolo}\n\nDESCRIZIONE: {descrizione}\n\nCONTENUTO: {contenuto}"
    try:
        response = requests.post(
            "https://api-inference.huggingface.co/models/facebook/bart-large-cnn",
            headers={"Authorization": f"Bearer {HUGGINGFACE_API_KEY}"},
            json={"inputs": testo, "parameters": {"min_length": 30, "max_length": 80}},
            timeout=60
        )
        if response.status_code == 200:
            return response.json()[0]["summary_text"]
        else:
            return f"(Sintesi non disponibile, errore HuggingFace {response.status_code})"
    except Exception as e:
        return f"(Errore sintesi: {e})"

def notizie_delle_ultime_24_ore(feed_url):
    feed = feedparser.parse(feed_url)
    notizie = []
    adesso = datetime.datetime.now(datetime.timezone.utc)
    limite = adesso - datetime.timedelta(days=1)

    for entry in feed.entries:
        data_pubblicazione = None

        if hasattr(entry, "published_parsed") and entry.published_parsed:
            data_pubblicazione = datetime.datetime(*entry.published_parsed[:6], tzinfo=datetime.timezone.utc)
        elif hasattr(entry, "updated_parsed") and entry.updated_parsed:
            data_pubblicazione = datetime.datetime(*entry.updated_parsed[:6], tzinfo=datetime.timezone.utc)

        # Se non c’è data, includiamo comunque la notizia
        if data_pubblicazione is None or data_pubblicazione > limite:
            notizie.append({
                "title": entry.get("title", "Senza titolo"),
                "link": entry.get("link", ""),
                "summary": entry.get("summary", ""),
                "content": entry.get("content", [{}])[0].get("value", "")
            })
    return notizie

def invia_telegram(messaggio):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_USER_ID, "text": messaggio, "parse_mode": "Markdown"}
    response = requests.post(url, data=payload)
    response.raise_for_status()

def main():
    tutte_le_notizie = []
    for feed_url in RSS_FEEDS:
        tutte_le_notizie.extend(notizie_delle_ultime_24_ore(feed_url))

    if not tutte_le_notizie:
        invia_telegram("⚠️ Nessuna notizia trovata nelle ultime 24 ore.")
        return

    invia_telegram("🗞️ *Rassegna Stampa Tech di oggi:*")

    for art in tutte_le_notizie[:15]:
        sintesi = sintetizza_articolo(art["title"], art["summary"], art["content"])
        msg = f"*{art['title']}*\n{sintesi}\n🔗 {art['link']}"
        invia_telegram(msg)

if __name__ == "__main__":
    main()
