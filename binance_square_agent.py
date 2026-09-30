import os
import re
import json
import time
import random
from datetime import datetime

import feedparser
import requests
from groq import Groq

# ===== المفاتيح =====
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
BINANCE_SQUARE_API_KEY = os.environ.get("BINANCE_SQUARE_API_KEY")

if not GROQ_API_KEY or not BINANCE_SQUARE_API_KEY:
    raise ValueError("❌ المفاتيح غير موجودة")

groq_client = Groq(api_key=GROQ_API_KEY)
MODEL = "qwen/qwen3.8-27b"

# ===== الرموز المعروفة =====
KNOWN_TICKERS = [
    'BTC', 'ETH', 'SOL', 'BNB', 'XRP', 'ADA', 'DOGE', 'AVAX',
    'DOT', 'MATIC', 'LINK', 'UNI', 'AAVE', 'CRO', 'SHIB', 'LTC',
    'TRX', 'ATOM', 'FIL', 'APT', 'ARB', 'OP', 'INJ', 'TIA',
    'HOOD', 'COIN', 'MSTR', 'SPY', 'QQQ', 'USDT', 'USDC',
    'XLM', 'ETC', 'ALGO', 'VET', 'HBAR', 'ICP', 'NEAR', 'SUI',
    'SEI', 'RNDR', 'FET', 'AGIX', 'IMX', 'STX', 'GRT',
]

# ===== مصادر الأخبار =====
FEEDS = {
    'CoinDesk': 'https://www.coindesk.com/arc/outboundfeeds/rss/',
    'CoinTelegraph': 'https://cointelegraph.com/rss',
    'CryptoSlate': 'https://cryptoslate.com/feed/',
}

# ===== المواضيع التعليمية (100) =====
EDUCATION_TOPICS = [
    # إدارة المخاطر (20)
    "What is a Stop Loss and why it's crucial for risk management",
    "Risk management: The 1% rule for trading",
    "Position sizing: How much to risk per trade",
    "Risk/Reward ratio: The golden rule of trading",
    "Take Profit vs Stop Loss: Complete guide",
    "Trailing Stop Loss: Locking in profits",
    "The importance of diversification in crypto",
    "Never invest more than you can afford to lose",
    "How to calculate your risk per trade",
    "Drawdown: What it is and how to manage it",
    "The psychological side of risk management",
    "Leverage risks: Why 100x is dangerous",
    "Liquidation: How to avoid it",
    "Hedging strategies for crypto portfolios",
    "When to cut losses and when to hold",
    "Managing emotions during volatility",
    "The power of cash reserves in crypto",
    "Portfolio rebalancing strategies",
    "Average down vs average up: Which is better?",
    "Setting realistic profit targets",
    # أساسيات التداول (20)
    "Spot vs Futures trading: Key differences",
    "Market orders vs Limit orders explained",
    "What is slippage in crypto trading?",
    "Understanding trading volume and liquidity",
    "Order book basics for beginners",
    "Spread: The hidden cost of trading",
    "Bid-Ask spread explained simply",
    "Candlestick patterns: Doji, Hammer, Engulfing",
    "Support and resistance levels",
    "Trend lines: Drawing and using them",
    "Moving Averages: SMA vs EMA",
    "RSI: Relative Strength Index explained",
    "MACD: Moving Average Convergence Divergence",
    "Bollinger Bands for volatility",
    "Fibonacci retracement levels",
    "Head and shoulders pattern",
    "Double top and double bottom",
    "Cup and handle pattern",
    "Breakout vs Fakeout: How to tell",
    "Timeframe analysis: Multi-timeframe trading",
    # الكريبتو الأساسي (20)
    "Understanding Bitcoin halving and its market impact",
    "What is a crypto wallet? Hot vs Cold storage",
    "Understanding Market Cap vs Fully Diluted Valuation",
    "What is a whale in crypto? Their market impact",
    "Stablecoins: USDT vs USDC vs DAI",
    "Layer 1 vs Layer 2 blockchains",
    "What is a blockchain? Simple explanation",
    "Proof of Work vs Proof of Stake",
    "What is gas fees in Ethereum?",
    "Understanding crypto mining basics",
    "Private keys vs Public keys",
    "Seed phrases: Protect them at all costs",
    "What is a smart contract?",
    "ERC-20 vs BEP-20 tokens",
    "Understanding tokenomics",
    "Circulating supply vs Total supply vs Max supply",
    "What is a token burn?",
    "Genesis block: The beginning of crypto",
    "Fork: Hard fork vs Soft fork",
    "What is a testnet vs mainnet?",
    # DeFi (15)
    "What is DeFi? Decentralized Finance explained",
    "What is staking? Earning passive income with crypto",
    "What is impermanent loss in DeFi?",
    "Yield farming: How it works",
    "Liquidity pools explained simply",
    "AMM: Automated Market Makers",
    "What is a DEX vs CEX?",
    "What is a lending protocol?",
    "Collateralized loans in DeFi",
    "Flash loans: Advanced DeFi",
    "What is a governance token?",
    "DAO: Decentralized Autonomous Organizations",
    "What is Total Value Locked (TVL)?",
    "Cross-chain bridges explained",
    "What is a wrapped token? (WBTC, WETH)",
    # الأمان (10)
    "What is a rug pull and how to avoid it",
    "Phishing attacks in crypto: How to spot them",
    "Fake tokens and how to verify legitimacy",
    "Smart contract audits: Why they matter",
    "Honeypot scams: Detect before you buy",
    "Pump and dump schemes exposed",
    "Fake giveaways: Don't fall for them",
    "2FA and security best practices",
    "Hardware wallets: Do you need one?",
    "Common crypto scams and how to avoid them",
    # استراتيجيات (10)
    "Dollar Cost Averaging (DCA): The beginner's best friend",
    "FOMO vs FUD: Emotional trading pitfalls",
    "The importance of DYOR (Do Your Own Research)",
    "Swing trading vs Day trading",
    "HODL strategy: Does it still work?",
    "Grid trading explained simply",
    "Arbitrage: Earning from price differences",
    "Scalping: High-frequency small profits",
    "Copy trading: Should you try it?",
    "Backtesting: Testing strategies before risking money",
    # الأسواق (5)
    "Understanding bull and bear markets",
    "Bull trap and bear trap: Avoid them",
    "Market cycles: Where are we now?",
    "Fear and Greed Index explained",
    "Correlation between BTC and altcoins",
]

# ===== قاعدة البيانات =====
try:
    with open('posted.json', 'r') as f:
        POSTED_NEWS = set(json.load(f))
except:
    POSTED_NEWS = set()

def save_posted():
    with open('posted.json', 'w') as f:
        json.dump(list(POSTED_NEWS), f)

# ===== 1. قراءة الأخبار =====
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

# ===== 2. جلب الأسعار =====
def fetch_prices():
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {
        'ids': 'bitcoin,ethereum,solana,binancecoin,ripple',
        'vs_currencies': 'usd',
        'include_24hr_change': 'true'
    }
    try:
        response = requests.get(url, params=params, timeout=15)
        data = response.json()
        result = []
        for coin, info in data.items():
            result.append({
                'coin': coin,
                'price': info['usd'],
                'change': info['usd_24h_change']
            })
        return result
    except:
        return []

# ===== 3. جلب المشاريع الرائجة =====
def fetch_trending():
    url = "https://api.coingecko.com/api/v3/search/trending"
    try:
        response = requests.get(url, timeout=15)
        data = response.json()
        projects = []
        for item in data.get('coins', [])[:5]:
            coin = item['item']
            projects.append({
                'name': coin['name'],
                'symbol': coin['symbol'],
                'rank': coin.get('market_cap_rank', 'N/A')
            })
        return projects
    except:
        return []

# ===== 4. تصحيح الرموز =====
def fix_tickers(post):
    def replace_ticker(match):
        ticker = match.group(1).upper()
        if ticker in KNOWN_TICKERS:
            return f"${ticker}"
        return ""
    post = re.sub(r'\$([A-Za-z]+)', replace_ticker, post)
    post = re.sub(r'\s+', ' ', post)
    return post.strip()

# ===== 5. فحص الجودة =====
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

# ===== 6. اختيار نوع المحتوى =====
def get_content_type():
    hour = datetime.utcnow().hour
    schedule = {
        0: 'news', 2: 'analysis', 4: 'project', 6: 'news',
        8: 'education', 10: 'news', 12: 'analysis', 14: 'promotion',
        16: 'news', 18: 'project', 20: 'education', 22: 'recap',
    }
    closest = min(schedule.keys(), key=lambda h: abs(h - hour))
    return schedule[closest]

# ===== 7. قوالب المحتوى =====
PROMPTS = {
    'news': """Write a Binance Square post about this crypto news.

News: {title}
Details: {summary}

Rules:
- Length: 200-260 characters
- Start with emoji
- Include 1-2 $CASHTAGS from: {tickers}
- End with 2-3 #hashtags
- Add a question

OUTPUT ONLY THE POST.""",

    'education': """Write an educational Binance Square post.

Topic: {title}

Rules:
- Length: 200-260 characters
- Start with 📚
- Teach ONE clear concept with 2-3 bullet points or tips
- Use simple language
- Include $CASHTAGS from: {tickers} (if relevant)
- End with 2-3 educational #hashtags
- Add engaging question

OUTPUT ONLY THE POST.""",

    'analysis': """Write a crypto market analysis for Binance Square.

Market Data: {title}

Rules:
- Length: 200-260 characters
- Start with 📊
- Mention trends or changes
- Include $BTC, $ETH CASHTAGS
- End with 2-3 #hashtags
- Add a question

OUTPUT ONLY THE POST.""",

    'project': """Write a crypto project spotlight.

Project: {title}

Rules:
- Length: 200-260 characters
- Start with 💡
- Highlight 2-3 features
- Include $CASHTAGS (use project symbol if known)
- End with 2-3 #hashtags
- Add a question

OUTPUT ONLY THE POST.""",

    'promotion': """Write a Binance promotional post.

Promotion: {title}

Rules:
- Length: 200-260 characters
- Start with 🎁
- Highlight benefit
- Include $BNB or $USDT
- End with 2-3 #hashtags
- Add urgency

OUTPUT ONLY THE POST.""",

    'recap': """Write a daily crypto recap.

Data: {title}

Rules:
- Length: 200-260 characters
- Start with 🌙
- Summarize sentiment
- Include $BTC, $ETH
- End with 2-3 #hashtags
- Add forward-looking line

OUTPUT ONLY THE POST.""",
}

# ===== 8. كتابة المنشور =====
def write_post_simple(prompt, max_retries=3):
    for attempt in range(max_retries):
        try:
            response = groq_client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": "You are a professional crypto content writer for Binance Square. Output only the post text, nothing else."},
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

# ===== 9. النشر =====
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

# ===== 10. التشغيل =====
def run_agent():
    content_type = get_content_type()
    print(f"🚀 بدء - {datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC")
    print(f"📝 نوع: {content_type}")
    print("=" * 60)
    
    post_content = None
    news_id = None
    
    # جلب المحتوى حسب النوع
    if content_type == 'news':
        news_list = fetch_news(limit=10)
        if news_list:
            news = news_list[0]
            news_id = news['id']
            post_content = f"{news['title']}\n{news['summary']}"
            print(f"📰 {news['title'][:55]}...")
    
    elif content_type == 'education':
        # نختار موضوعًا لم يُنشر
        available = [t for t in EDUCATION_TOPICS if f"edu_{t[:30]}" not in POSTED_NEWS]
        if not available:
            available = EDUCATION_TOPICS  # إذا انتهت، أعد
        topic = random.choice(available)
        news_id = f"edu_{topic[:30]}"
        post_content = topic
        print(f"📚 {topic[:55]}...")
    
    elif content_type == 'analysis':
        prices = fetch_prices()
        if prices:
            text = "\n".join([f"{p['coin'].title()}: ${p['price']:.2f} ({p['change']:+.2f}%)" for p in prices])
            news_id = f"analysis_{datetime.utcnow().strftime('%Y%m%d%H')}"
            post_content = text
            print(f"📊 {len(prices)} عملة")
    
    elif content_type == 'project':
        projects = fetch_trending()
        if projects:
            proj = random.choice(projects)
            news_id = f"project_{proj['symbol']}_{datetime.utcnow().strftime('%Y%m%d%H')}"
            post_content = f"{proj['name']} (${proj['symbol']}) - Rank {proj['rank']}"
            print(f"💡 {proj['name']}")
    
    elif content_type == 'promotion':
        promos = [
            "Binance Futures zero-fee for new users",
            "Binance Earn: 10% APY on stablecoins",
            "Binance Launchpool: New token farming",
            "Refer friends, earn 40% commission",
            "Binance Convert: Zero fees on swaps",
        ]
        promo = random.choice(promos)
        news_id = f"promo_{promo[:30]}_{datetime.utcnow().strftime('%Y%m%d')}"
        post_content = promo
        print(f"🎁 {promo[:55]}...")
    
    elif content_type == 'recap':
        prices = fetch_prices()
        if prices:
            btc = next((p for p in prices if p['coin'] == 'bitcoin'), None)
            eth = next((p for p in prices if p['coin'] == 'ethereum'), None)
            if btc and eth:
                post_content = f"BTC: ${btc['price']:.0f} ({btc['change']:+.1f}%), ETH: ${eth['price']:.0f} ({eth['change']:+.1f}%)"
                news_id = f"recap_{datetime.utcnow().strftime('%Y%m%d')}"
                print(f"🌙 ملخص")
    
    # احتياطي
    if not post_content:
        print("⚠️ احتياطي: أخبار")
        news_list = fetch_news(limit=10)
        if news_list:
            news = news_list[0]
            news_id = news['id']
            post_content = f"{news['title']}\n{news['summary']}"
            content_type = 'news'
    
    if not post_content or not news_id:
        print("❌ لا يوجد محتوى")
        return
    
    # الكتابة
    tickers_str = ', '.join([f'${t}' for t in KNOWN_TICKERS[:30]])
    template = PROMPTS.get(content_type, PROMPTS['news'])
    prompt = template.format(title=post_content, summary=post_content, tickers=tickers_str)
    
    post = write_post_simple(prompt)
    if not post:
        print("❌ فشل الكتابة")
        return
    
    print(f"✍️ {len(post)} حرف")
    print(f"   {post[:100]}...")
    
    # النشر
    result = post_to_square(post)
    if result['success']:
        print(f"  ✅ {result['url']}")
        POSTED_NEWS.add(news_id)
    else:
        print(f"  ❌ {result['error']}")
    
    save_posted()
    print(f"\n🎉 اكتمل")

if __name__ == "__main__":
    run_agent()
