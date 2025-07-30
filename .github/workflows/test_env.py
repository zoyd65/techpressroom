import os

def test_secrets():
    telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
    telegram_user = os.getenv("TELEGRAM_USER_ID")
    hf_key = os.getenv("HUGGINGFACE_API_KEY")

    print("🔍 Verifica variabili d'ambiente:")
    print("TELEGRAM_BOT_TOKEN:", "✅ OK" if telegram_token else "❌ MANCANTE")
    print("TELEGRAM_USER_ID:", "✅ OK" if telegram_user else "❌ MANCANTE")
    print("HUGGINGFACE_API_KEY:", "✅ OK" if hf_key else "❌ MANCANTE")

    if not (telegram_token and telegram_user and hf_key):
        exit("❌ Alcuni secret non sono presenti. Controlla i secrets di GitHub.")
    else:
        print("✅ Tutti i secret sono presenti e correttamente caricati.")

if __name__ == "__main__":
    test_secrets()
