import os
import requests
import feedparser
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

RSS_FEED_URL = "https://www.wired.it/feed"

def get_articles():
    feed = feedparser.parse(RSS_FEED_URL)
    yesterday = datetime.utcnow() - timedelta(days=1)
    articles = []

    for entry in feed.entries:
        published = datetime(*entry.published_parsed[:6])
        if published > yesterday:
            content = entry.get("content", [{"value": ""}])[0]["value"]
            articles.append({
                "title": entry.title,
                "link": entry.link,
                "summary": entry.get("summary", ""),
                "content": content
            })

    return articles

def sintetizza_articolo(titolo, descrizione, contenuto):
    prompt = (
        f"Scrivi una sintesi in tono giornalistico della notizia:\n"
        f"TITOLO: {titolo}\n"
        f"DESCRIZIONE: {descrizione}\n"
        f"CONTENUTO: {contenuto}\n"
        f"Rispondi con un breve testo giornalistico."
    )

    response = requests.post(
        "https://api.openrouter.ai/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {os.getenv('HUGGINGFACE_API_KEY')}",
            "Content-Type": "application/json"
        },
        json={
            "model": "mistralai/mixtral-8x7b-instruct",
            "messages": [{"role": "user", "content": prompt}]
        }
    )

    response.raise_for_status()
    data = response.json()
    return data["choices"][0]["message"]["content"]

def invia_telegram(msg: str):
    url = f"https://api.telegram.org/bot{os.getenv('TELEGRAM_BOT_TOKEN')}/sendMessage"
    payload = {
        "chat_id": os.getenv("TELEGRAM_USER_ID"),
        "text": msg,
        "parse_mode": "HTML"
    }
    response = requests.post(url, json=payload)
    response.raise_for_status()

def main():
    articoli = get_articles()
    if not articoli:
        invia_telegram("Nessuna nuova notizia da Wired nelle ultime 24 ore.")
        return

    for art in articoli:
        try:
            sintesi = sintetizza_articolo(art["title"], art["summary"], art["content"])
            messaggio = f"<b>{art['title']}</b>\n{art['link']}\n\n{sintesi}"
            invia_telegram(messaggio)
        except Exception as e:
            invia_telegram(f"Errore durante l'elaborazione di un articolo: {e}")

if __name__ == "__main__":
    main()
