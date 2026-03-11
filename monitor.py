import feedparser
import requests
import re
import os
from deep_translator import GoogleTranslator

# ✅ ICT의 X 아이디 입력 (@ 제외)
X_USERNAME = "I_Am_The_ICT"

NITTER_INSTANCE = "https://nitter.poast.org"
DISCORD_WEBHOOK = os.environ.get("DISCORD_WEBHOOK_URL")
LAST_ID_FILE = "last_tweet_id.txt"

PROTECTED_TERMS = [
    "Buy-side Liquidity", "Sell-side Liquidity", "Buy-stop", "Sell-stop",
    "Liquidity Raid", "Rebalancing", "Higher High", "Lower Low",
    "Swing Low", "Swing High", "Short-term High", "STH", "Long-term High", "LTH",
    "Short-term Low", "STL", "Long-term Low", "LTL",
    "New York open kill zone", "Pre-market", "Fibonacci", "FIB", "Upper Quadrant",
    "NDOG", "NWOG", "Consequent Encroachment", "C.E", "Silver Bullet",
    "Optimal Trade Entry", "OTE", "Premium", "Discount", "Equilibrium", "EQ",
    "Reclaimed Order block", "MMBM", "MMSM", "Common Gap", "Breakaway Gap",
    "Immediate Rebalance", "RTH-ORG", "Opening Range Gap", "ORG",
    "Body", "Wick", "Range", "IOFED", "SIBI", "BISI", "CISD", "SMT",
    "MSS", "DOM", "Dynamic Price Range", "Draw on Liquidity", "DOL",
    "Counterparty", "Catalyst", "Price Action", "Session Bias",
    "Order Block", "Cookie Cutter", "Low Hanging Fruit", "Setup",
    "Kill Zone", "Sell-off", "Spoofing", "Stop Loss", "Stop Out",
    "Re-entry", "Open Interest", "Breakout Trader", "Forex",
    "Retail", "Smart Money", "HRLR", "LRLR",
    "Asia", "London", "Bias", "Narrative", "Tape Reading",
    "Rejection Block", "Displacement", "Volume Imbalance",
    "Protraction", "Grading", "Gradient", "Engineered",
    "Institutional Order Flow", "IOF", "Opening Range", "Crude Oil",
    "Intraday", "Minor Buy-side", "Long", "Short", "High", "Low", "FVG",
]

PROTECTED_TERMS = sorted(PROTECTED_TERMS, key=len, reverse=True)

def get_tweets():
    url = f"{NITTER_INSTANCE}/{X_USERNAME}/rss"
    feed = feedparser.parse(url)
    return feed.entries

def clean_text(text):
    return re.sub(r'<[^>]+>', '', text).strip()

def translate(text):
    try:
        placeholders = {}
        protected_text = text
        for i, term in enumerate(PROTECTED_TERMS):
            placeholder = f"__TERM{i}__"
            pattern = re.compile(re.escape(term), re.IGNORECASE)
            match = pattern.search(protected_text)
            if match:
                placeholders[placeholder] = match.group(0)
                protected_text = pattern.sub(placeholder, protected_text)
        translated = GoogleTranslator(source='auto', target='ko').translate(protected_text)
        for placeholder, original_term in placeholders.items():
            translated = translated.replace(placeholder, original_term)
        return translated
    except Exception as e:
        return f"(번역 실패: {e})"

def send_discord(original, translated, link):
    data = {
        "embeds": [{
            "title": "📢 ICT 새 트윗",
            "url": link,
            "fields": [
                {"name": "🔤 원문", "value": original[:1024], "inline": False},
                {"name": "🇰🇷 번역", "value": translated[:1024], "inline": False},
            ],
            "color": 1942002
        }]
    }
    requests.post(DISCORD_WEBHOOK, json=data)

def get_last_id():
    if os.path.exists(LAST_ID_FILE):
        with open(LAST_ID_FILE, 'r') as f:
            return f.read().strip()
    return None

def save_last_id(tweet_id):
    with open(LAST_ID_FILE, 'w') as f:
        f.write(tweet_id)

def main():
    tweets = get_tweets()
    if not tweets:
        print("트윗을 가져오지 못했습니다.")
        return
    last_id = get_last_id()
    new_tweets = [t for t in tweets if t.id != last_id]
    if not new_tweets:
        print("새 트윗 없음")
        return
    for tweet in reversed(new_tweets):
        original = clean_text(tweet.summary)
        translated = translate(original)
        send_discord(original, translated, tweet.link)
        print(f"전송 완료: {original[:50]}...")
    save_last_id(tweets[0].id)

if __name__ == "__main__":
    main()
