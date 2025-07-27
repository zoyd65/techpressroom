import feedparser
import os
import asyncio
import requests
from telegram import Bot
from dotenv import load_dotenv

load_dotenv()

telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
user_id = int(os.getenv("TELEGRAM_USER_ID"))
hf_api_key = os.getenv("HF_API_KEY")
bot = Bot(token=telegram_token)

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
    "https://www.inverse.com/rss"
]

async def fetch_and_summarize_articles():
    all_articles = []
    for url in RSS_FEEDS:
        feed = feedparser.parse(url)
        for entry in feed.entries:
            if "title" in entry and "link" in entry:
                all_articles.append({
                    "title": entry.title,
                    "link": entry.link
                })
    return all_articles[:15]

def summarize_with_huggingface(title, link):
    headers = {"Authorization": f"Bearer {hf_api_key}"}
    prompt = f"Scrivi una sintesi in tono giornalistico della notizia:
Titolo: {title}
Link: {link}"
    json_data = {
        "inputs": prompt,
        "parameters": {"max_new_tokens": 80}
    }
    try:
        response = requests.post(
            "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.1",
            headers=headers,
            json=json_data,
            timeout=20
        )
        response.raise_for_status()
        result = response.json()
        if isinstance(result, list) and "generated_text" in result[0]:
            return result[0]["generated_text"].strip()
        else:
            return "Errore nella sintesi HuggingFace."
    except Exception as e:
        return f"Errore: {e}"

async def send_rassegna():
    await bot.send_message(chat_id=user_id, text="🗞️ *Rassegna stampa tech di oggi:*", parse_mode="Markdown")
    articles = await fetch_and_summarize_articles()
    for art in articles:
        sintesi = summarize_with_huggingface(art["title"], art["link"])
        msg = f"*{art['title']}*
{sintesi}
🔗 {art['link']}"
        await bot.send_message(chat_id=user_id, text=msg, parse_mode="Markdown")

if __name__ == "__main__":
    asyncio.run(send_rassegna())
