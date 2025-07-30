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

def estrai_articoli_ultime_ore(url, ore=12):
    feed = feedparser.parse(url)
    articoli = []
    ora_limite = datetime.now() - timedelta(hours=ore)
    for entry in feed.entries:
        if "published_parsed" in entry:
            data = datetime(*entry.published_parsed[:6])
        elif "updated_parsed" in entry:
            data = datetime(*entry.updated_parsed[:6])
        else:
            continue
        if data > ora_limite:
            articoli.append({
                "title": entry.title,
                "link": entry.link,
                "summary": entry.get("summary", ""),
                "content": entry.get("content", [{"value": ""}])[0]["value"]
            })
    return articoli

def sintetizza_articolo(titolo, riassunto, contenuto):
    prompt = f"""Scrivi una sintesi in tono giornalistico della notizia:
Titolo: {titolo}
Riassunto: {riassunto}
Contenuto: {contenuto}
Sintesi:"""

    response = requests.post(
        "https://api-inference.huggingface.co/models/mistralai/Mixtral-8x7B-Instruct-v0.1",
        headers={
            "Authorization": f"Bearer {HUGGINGFACE_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "inputs": prompt,
            "parameters": {"max_new_tokens": 300}
        }
    )

    if response.status_code == 200:
        data = response.json()
        if isinstance(data, list) and "generated_text" in data[0]:
            return data[0]["generated_text"].strip()
        elif isinstance(data, dict) and "generated_text" in data:
            return data["generated_text"].strip()
    return "Sintesi non disponibile."

print("Messaggio inviato a Telegram:")
print(messaggio)


def invia_telegram(messaggio):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_USER_ID,
        "text": messaggio,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }
    response = requests.post(url, json=payload)
    return response.ok

def main():
    tutti_articoli = []
    for feed in RSS_FEEDS:
        tutti_articoli.extend(estrai_articoli_ultime_ore(feed, ore=12))

    if not tutti_articoli:
        invia_telegram("Nessuna nuova notizia trovata nelle ultime 12 ore.")
        return

    messaggi = []
    for art in tutti_articoli[:10]:
        sintesi = sintetizza_articolo(art["title"], art["summary"], art["content"])
        msg = f"*{art['title']}*\n{sintesi}\n[Leggi di più]({art['link']})"
        messaggi.append(msg)

    for m in messaggi:
        invia_telegram(m)

if __name__ == "__main__":
    main()
