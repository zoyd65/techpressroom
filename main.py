import feedparser
import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import traceback

load_dotenv()

# === Variabili d'ambiente ===
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
TELEGRAM_USER_ID = os.getenv("TELEGRAM_USER_ID", "").strip()
HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY", "").strip()

# === Controllo preliminare ===
if not TELEGRAM_BOT_TOKEN or not TELEGRAM_USER_ID or not HUGGINGFACE_API_KEY:
    raise EnvironmentError("❌ Variabili d'ambiente mancanti")

# === Configurazione ===
RSS_FEEDS = [
    "https://www.hdblog.it/rss/",
    "https://www.smartworld.it/feed/rss",
    "https://techprincess.it/feed/",
    "https://www.tomshw.it/feed/",
    "https://www.hwupgrade.it/rss/all.xml",
    "https://www.wired.it/feed/",
]

LOG_FILE = "log.txt"

# === Funzioni di supporto ===

def log(msg):
    timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    with open(LOG_FILE, "a") as f:
        f.write(f"{timestamp} {msg}\n")
    print(msg)

def escape_markdown(text):
    for c in ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']:
        text = text.replace(c, f'\\{c}')
    return text

def estrai_articoli_ultime_ore(url, ore=12):
    articoli = []
    try:
        feed = feedparser.parse(url)
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
    except Exception as e:
        log(f"⚠️ Errore nel parsing RSS da {url}: {e}")
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
            json={"inputs": prompt, "parameters": {"max_new_tokens": 300}},
            timeout=30
        )

        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list) and "generated_text" in data[0]:
                return data[0]["generated_text"].strip()
            elif isinstance(data, dict) and "generated_text" in data:
                return data["generated_text"].strip()
        else:
            log(f"⚠️ HuggingFace errore {response.status_code}: {response.text}")
    except Exception as e:
        log(f"❌ Errore HuggingFace: {e}")
    return "Sintesi non disponibile."

def invia_telegram(m_
