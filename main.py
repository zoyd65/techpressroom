import feedparser
import requests
import os
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
    "https://thenextweb.com/feed/"
]

def sintetizza_articolo(titolo, descrizione, contenuto):
    prompt = f"""Scrivi una sintesi in tono giornalistico della notizia:
Titolo: {titolo}
Descrizione: {descrizione}
Contenuto: {contenuto}
Restituisci solo un paragrafo conciso in italiano."""

    headers = {
        "Authorization": f"Bearer {HUGGINGFACE_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "mistralai/Mixtral-8x7B-Instruct-v0.1",
        "messages": [
            {"role": "system", "content": "Sei un assistente esperto di giornalismo tecnologico."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7
    }

    response = requests.post("https://api.openrouter.ai/v1/chat/completions", headers=headers, json=payload)
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"].strip()

def invia_telegram(messaggio):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_USER_ID,
        "text": messaggio,
        "parse_mode": "Markdown"
    }
    response = requests.post(url, json=payload)
    response.raise_for_status()

def notizie_delle_ultime_24_ore(feed_url):
    feed = feedparser.parse(feed_url)
    notizie = []
    now = datetime.datetime.now(datetime.timezone.utc)
    ieri = now - datetime.timedelta(days=1)

    for entry in feed.entries:
        if hasattr(entry, 'published_parsed'):
            data_pubblicazione = datetime.datetime(*entry.published_parsed[:6], tzinfo=datetime.timezone.utc)
            if data_pubblicazione > ieri:
                notizie.append({
                    "title": entry.title,
                    "link": entry.link,
                    "summary": entry.get("summary", ""),
                    "content": entry.get("content", [{"value": ""}])[0]["value"] if "content" in entry else ""
                })
    return notizie

def main():
    tutte_le_notizie = []

    for feed_url in RSS_FEEDS:
        tutte_le_notizie.extend(notizie_delle_ultime_24_ore(feed_url))

    if not tutte_le_notizie:
        invia_telegram("Nessuna nuova notizia tecnologica trovata nelle ultime 24 ore.")
        return

    sintesi_finale = "*🗞️ Rassegna Tecnologica Quotidiana*\n\n"

    for art in tutte_le_notizie[:10]:  # max 10 articoli per non superare limiti Telegram
        try:
            sintesi = sintetizza_articolo(art["title"], art["summary"], art["content"])
            sintesi_finale += f"*{art['title']}*\n{sintesi}\n[Leggi di più]({art['link']})\n\n"
        except Exception as e:
            print(f"Errore durante la sintesi o l'invio dell'articolo: {e}")
            continue

    invia_telegram(sintesi_finale)

if __name__ == "__main__":
    main()
