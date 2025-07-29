import feedparser
import requests
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_USER_ID = os.getenv("TELEGRAM_USER_ID")
HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY")

RSS_FEEDS = [
    "https://techcrunch.com/feed/",
    "https://thenextweb.com/feed/",
    "https://www.theverge.com/rss/index.xml",
    "https://spectrum.ieee.org/rss/fulltext",
    "https://www.01net.it/feed/",
    "https://www.wired.it/feed/",
    "https://www.ictbusiness.it/feed",
]

def estrai_articoli(rss_url):
    feed = feedparser.parse(rss_url)
    articoli = []
    for entry in feed.entries[:2]:
        articoli.append({
            "title": entry.title,
            "link": entry.link,
            "summary": entry.summary if "summary" in entry else "",
            "content": entry.get("content", [{"value": ""}])[0]["value"]
        })
    return articoli

def sintetizza_articolo(title, summary, content):
    prompt = f"""Scrivi una sintesi in tono giornalistico della notizia:
{title}
{summary}
{content}
"""
    response = requests.post(
        "https://api.openrouter.ai/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {HUGGINGFACE_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": "openai/gpt-3.5-turbo",
            "messages": [{"role": "user", "content": prompt}]
        }
    )

    if response.status_code == 200:
        return response.json()['choices'][0]['message']['content'].strip()
    else:
        return f"Errore nella sintesi: {response.text}"

def invia_telegram(messaggio):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": TELEGRAM_USER_ID,
        "text": messaggio,
        "parse_mode": "Markdown",
        "disable_web_page_preview": False
    }
    requests.post(url, data=data)

def main():
    all_articles = []
    for feed in RSS_FEEDS:
        all_articles.extend(estrai_articoli(feed))

    oggi = datetime.now().strftime("%d/%m/%Y")
    invia_telegram(f"🗞️ *Rassegna stampa tech – {oggi}*")

    for art in all_articles[:10]:
        sintesi = sintetizza_articolo(art["title"], art["summary"], art["content"])
        msg = f"*{art['title']}*\n{sintesi}\n🔗 {art['link']}"
        invia_telegram(msg)

if __name__ == "__main__":
    main()
