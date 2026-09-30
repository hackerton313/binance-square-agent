
from groq import Groq
import feedparser
import requests
import time
import re
import json
import random
from datetime import datetime

GROQ_API_KEY = "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"
BINANCE_SQUARE_API_KEY = "92535fb0b59946a19670ae719386b017"

groq_client = Groq(api_key=GROQ_API_KEY)
MODEL = "qwen/qwen3.8-27b"

KNOWN_TICKERS = [
    'BTC', 'ETH', 'SOL', 'BNB', 'XRP', 'ADA', 'DOGE', 'AVAX',
    'DOT', 'MATIC', 'LINK', 'UNI', 'AAVE', 'CRO', 'SHIB', 'LTC',
    'TRX', 'ATOM', 'FIL', 'APT', 'ARB', 'OP', 'INJ', 'TIA',
    'HOOD', 'COIN', 'MSTR', 'SPY', 'QQQ', 'USDT', 'USDC',
    'XRP', 'XLM', 'ETC', 'ALGO', 'VET', 'HBAR', 'ICP',
]

FEEDS = {
    'CoinDesk': 'https://www.coindesk.com/arc/outboundfeeds/rss/',
    'CoinTelegraph': 'https://cointelegraph.com/rss',
    'CryptoSlate': 'https://cryptoslate.com/feed/',
}

try:
    with open('posted.json', 'r') as f:
        POSTED_NEWS = set(json.load(f))
except:
    POSTED_NEWS = set()

def save_posted():
    with open('posted.json', 'w') as f:
        json.dump(list(POSTED_NEWS), f)

def fetch_news(limit=20):
    all_news = []
    for source, url in FEEDS.items():
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries:
                news_id = entry.link
                if news_id in POSTED_NEWS:
                    continue
                all_news.append({
                    'id': news_id,
                    'source': source,
                    'title': entry.title,
                    'summary': entry.get('summary', '')[:400]
                })
        except:
            continue
    random.shuffle(all_news)
    return all_news[:limit]

def fix_tickers(post):
    def replace_ticker(match):
        ticker = match.group(1).upper()
        if ticker in KNOWN_TICKERS:
            return f"${ticker}"
        return ""
    post = re.sub(r'\$([A-Za-z]+)', replace_ticker, post)
    post = re.sub(r'\s+', ' ', post)
    return post.strip()

def is_good_quality(post):
    if not post:
        return False, "فارغ"
    if len(post) < 180:
        return False, f"قصير ({len(post)})"
    if len(post) > 280:
        return False, f"طويل ({len(post)})"
    if not re.search(r'\$[A-Z]{2,10}', post):
        return False, "لا cashtag"
    if not re.search(r'#[A-Za-z]+', post):
        return False, "لا hashtag"
    return True, "جيد"

def write_post(news, max_retries=3):
    tickers_str = ', '.join([f'${t}' for t in KNOWN_TICKERS[:25]])
    prompt = f"""Write a Binance Square post about this crypto news.

News: {news["title"]}
Details: {news["summary"]}

STRICT Rules:
- Length: 200-260 characters
- Start with emoji
- Include 1-2 $CASHTAGS ONLY from: {tickers_str}
- End with 2-3 #hashtags
- Add a question

OUTPUT ONLY THE POST TEXT."""

    for attempt in range(max_retries):
        try:
            response = groq_client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": "Output only the final post. Nothing else."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.8,
                max_tokens=400
            )
            content = response.choices[0].message.content
            if content and content.strip():
                post = fix_tickers(content.strip())
                is_good, reason = is_good_quality(post)
                if is_good:
                    return post
                print(f"  ⚠️ {reason}")
                time.sleep(2)
        except Exception as e:
            print(f"  ❌ {str(e)[:80]}")
            time.sleep(3)
    return None

def post_to_square(text):
    url = "https://www.binance.com/bapi/composite/v1/public/pgc/openApi/content/add"
    headers = {
        "X-Square-OpenAPI-Key": BINANCE_SQUARE_API_KEY,
        "Content-Type": "application/json",
        "clienttype": "binanceSkill"
    }
    body = {"bodyTextOnly": text}
    try:
        response = requests.post(url, json=body, headers=headers, timeout=30)
        data = response.json()
        if data.get("code") == "000000":
            content_id = data.get("data", {}).get("id", "unknown")
            return {"success": True, "url": f"https://www.binance.com/square/post/{content_id}"}
        return {"success": False, "error": data.get("message")}
    except Exception as e:
        return {"success": False, "error": str(e)[:100]}

def run_agent(max_posts=1, wait_between=7200):
    print(f"🚀 بدء - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    news_list = fetch_news(limit=20)
    print(f"📰 {len(news_list)} خبر جديد\n")
    
    posted_count = 0
    for news in news_list:
        if posted_count >= max_posts:
            break
        
        print(f"\n📌 {news['title'][:60]}...")
        post = write_post(news)
        if not post:
            continue
        
        print(f"✍️ {len(post)} حرف")
        result = post_to_square(post)
        if result['success']:
            print(f"  ✅ {result['url']}")
            POSTED_NEWS.add(news['id'])
            posted_count += 1
            if posted_count < max_posts:
                time.sleep(wait_between)
        else:
            print(f"  ❌ {result['error']}")
        time.sleep(3)
    
    save_posted()
    print(f"\n🎉 نشرنا {posted_count}")

if __name__ == "__main__":
    run_agent(max_posts=1)
