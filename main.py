import feedparser
import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

# Carica variabili d'ambiente
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
TELEGRAM_USER_ID = os.getenv("TELEGRAM_USER_ID", "").strip()
HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY", "").strip()

# Validazione minima
if not TELEGRAM_BOT_TOKEN or not TELEGRAM_USER_ID or not HUGGINGFACE_API_KEY:
    print("❌ Errore: Variabili d'ambiente mancanti.")
    exit(1)

# Lista RSS
RSS_FEEDS = [
    "https://www.hdblog.it/rss/",
    "https://www.smartworld.it/feed/rss",
    "https://techprincess.it/feed/",
    "https://www.tomshw.it/feed/",
    "https://www.hwupgrade.it/rss/all.xml",
    "https://www.wired.it/feed/",
]

def estrai_articoli_ultime_ore(url, ore=12):
    articoli = []
    ora_limite = datetime.now() - timedelta(hours=ore)
    try:
        feed = feedparser.parse(url)
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
    except Exception as e:
        print(f"⚠️ Errore nel parsing RSS: {url}\n{e}")
    return articoli

def sintetizza_articolo(titolo, riassunto, contenuto):
    prompt = f"""Scrivi una sintesi in tono giornalistico della notizia:
Titolo: {titolo}
Riassunto: {riassunto}
Contenuto: {contenuto}
Sintesi:"""

    try:
        response = requests.post(
            "https://api-inference.huggingface.co/models/mistralai/Mixtral-8x7B-Instruct-v0.1",
            headers={
                "Authorization": f"Bearer {HUGGINGFACE_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "inputs": prompt,
                "parameters": {"max_new_tokens": 300}
            },
            timeout=30
        )

        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list) and "generated_text" in data[0]:
                return data[0]["generated_text"].strip()
            elif isinstance(data, dict) and "generated_text" in data:
                return data["generated_text"].strip()
        else:
            print(f"⚠️ HuggingFace API error {response.status_code}: {response.text}")
    except Exception as e:
        print(f"❌ Errore durante la richiesta a HuggingFace:\n{e}")
    return "Sintesi non disponibile."

def invia_telegram(messaggio):
    if len(messaggio) > 4096:
        messaggio = messaggio[:4093] + "..."

    payload = {
        "chat_id": TELEGRAM_USER_ID,
        "text": messaggio,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }
    try:
        response = requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            json=payload,
            timeout=15
        )
        if not response.ok:
            print(f"⚠️ Errore invio Telegram: {response.status_code} - {response.text}")
        return response.ok
    except Exception as e:
        print(f"❌ Errore durante l'invio a Telegram:\n{e}")
        return False

def escape_markdown(text):
    # Escape per i caratteri riservati in Telegram Markdown
    for c in ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']:
        text = text.replace(c, f'\\{c}')
    return text

def main():
    print("🚀 Avvio raccolta notizie...")
    tutti_articoli = []
    for feed in RSS_FEEDS:
        articoli = estrai_articoli_ultime_ore(feed, ore=12)
        print(f"📡 {feed}: {len(articoli)} articoli trovati")
        tutti_articoli.extend(articoli)

    if not tutti_articoli:
        invia_telegram("🕓 Nessuna nuova notizia trovata nelle ultime 12 ore.")
        print("✅ Nessuna notizia trovata. Messaggio inviato.")
        return

    print(f"📰 Trovati {len(tutti_articoli)} articoli. Generazione sintesi...")

    for art in tutti_articoli[:10]:  # Limite a 10 articoli per messaggi brevi
        titolo = escape_markdown(art["title"])
        link = art["link"]
        sintesi = sintetizza_articolo(art["title"], art["summary"], art["content"])
        msg = f"*{titolo}*\n{sintesi}\n[Leggi di più]({link})"
        print("📨 Invio messaggio...")
        invia_telegram(msg)

    print("✅ Completato. Tutti i messaggi sono stati inviati.")

if __name__ == "__main__":
    main()
