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

MAX_LENGTH = 1800
MIN_LENGTH = 1000

# ===== قائمة العملات =====
ALL_COINS = [
    'BTC', 'ETH', 'BNB', 'SOL', 'XRP', 'ADA', 'DOGE', 'AVAX', 'DOT', 'TRX',
    'LINK', 'MATIC', 'LTC', 'BCH', 'UNI', 'ATOM', 'XLM', 'ETC', 'FIL', 'APT',
    'ARB', 'OP', 'INJ', 'TIA', 'SUI', 'SEI', 'NEAR', 'ICP', 'HBAR', 'VET',
    'ALGO', 'GRT', 'STX', 'IMX', 'FTM', 'SAND', 'MANA', 'AXS', 'CRO', 'AAVE',
    'MKR', 'SNX', 'COMP', 'CRV', '1INCH', 'SUSHI', 'ENJ', 'CHZ', 'ZIL', 'BAT',
    'RNDR', 'FET', 'AGIX', 'OCEAN', 'TAO', 'NMR', 'SHIB', 'PEPE', 'FLOKI', 'BONK',
    'AR', 'KSM', 'ZEC', 'DASH', 'WAVES', 'EGLD', 'THETA', 'CAKE', 'AXL', 'RUNE',
]

# ===== قائمة الهاشتاغات =====
ALL_TAGS = [
    'Crypto', 'Cryptocurrency', 'Blockchain', 'Web3', 'DeFi',
    'Trading', 'Investing', 'Altcoins', 'BullRun', 'BearMarket',
    'HODL', 'DYOR', 'TechnicalAnalysis', 'MarketUpdate',
    'CryptoEducation', 'LearnCrypto', 'CryptoBasics', 'RiskManagement',
    'TradingTips', 'Crypto101', 'CryptoNews', 'Breaking', 'MarketNews',
    'BitcoinNews', 'CryptoProject', 'Gem', 'Altcoin', 'LowCap',
    'Binance', 'BNB', 'BinanceSquare', 'NFT', 'Metaverse',
    'Layer2', 'Memecoins', 'AIcrypto', 'RWA', 'Bitcoin', 'Ethereum', 'Solana',
]

FEEDS = {
    'CoinDesk': 'https://www.coindesk.com/arc/outboundfeeds/rss/',
    'CoinTelegraph': 'https://cointelegraph.com/rss',
    'CryptoSlate': 'https://cryptoslate.com/feed/',
}

# ===== مواضيع تعليمية =====
EDUCATION_TOPICS = [
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

try:
    with open('recent_coins.json', 'r') as f:
        RECENT_COINS = json.load(f)
except:
    RECENT_COINS = []

try:
    with open('recent_tags.json', 'r') as f:
        RECENT_TAGS = json.load(f)
except:
    RECENT_TAGS = []

def save_posted():
    with open('posted.json', 'w') as f:
        json.dump(list(POSTED_NEWS), f)

def save_recent_coins(coins):
    global RECENT_COINS
    RECENT_COINS.extend(coins)
    RECENT_COINS = RECENT_COINS[-30:]
    with open('recent_coins.json', 'w') as f:
        json.dump(RECENT_COINS, f)

def save_recent_tags(tags):
    global RECENT_TAGS
    RECENT_TAGS.extend(tags)
    RECENT_TAGS = RECENT_TAGS[-30:]
    with open('recent_tags.json', 'w') as f:
        json.dump(RECENT_TAGS, f)

def pick_fresh_coins(count=2):
    recent = RECENT_COINS[-10:]
    available = [c for c in ALL_COINS if c not in recent]
    if len(available) < count:
        available = ALL_COINS
    return random.sample(available, min(count, len(available)))

def pick_fresh_tags(count=2):
    recent = RECENT_TAGS[-10:]
    available = [t for t in ALL_TAGS if t not in recent]
    if len(available) < count:
        available = ALL_TAGS
    return random.sample(available, min(count, len(available)))

# ===== قراءة الأخبار =====
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
                    'summary': entry.get('summary', '')[:600]
                })
        except:
            continue
    random.shuffle(all_news)
    return all_news[:limit]

def fetch_prices():
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {
        'ids': 'bitcoin,ethereum,solana,binancecoin,ripple',
        'vs_currencies': 'usd',
        'include_24hr_change': 'true'
    }
    try:
        return requests.get(url, params=params, timeout=15).json()
    except:
        return {}

def fetch_trending():
    try:
        return requests.get("https://api.coingecko.com/api/v3/search/trending", timeout=15).json().get('coins', [])[:5]
    except:
        return []

# ===== التصحيح والاستخراج =====
def fix_tickers(post):
    def replace_ticker(match):
        ticker = match.group(1).upper()
        if ticker in ALL_COINS:
            return f"${ticker}"
        return ""
    post = re.sub(r'\$([A-Za-z]+)', replace_ticker, post)
    post = re.sub(r'\s+', ' ', post)
    return post.strip()

def extract_coins(post):
    return list(set([c for c in re.findall(r'\$([A-Z]{2,10})', post) if c in ALL_COINS]))

def extract_tags(post):
    return list(set([t for t in re.findall(r'#([A-Za-z]+)', post) if t in ALL_TAGS]))

# ===== القص الإجباري =====
def force_trim(post, max_length):
    """قص إجباري: يقطع عند آخر نقطة، ويضمن وجود العملات والهاشتاغات"""
    if len(post) <= max_length:
        return post
    
    coins = re.findall(r'\$[A-Z]{2,10}', post)
    tags = re.findall(r'#[A-Za-z]+', post)
    
    post_body = re.sub(r'\$[A-Z]{2,10}', '', post)
    post_body = re.sub(r'#[A-Za-z]+', '', post_body)
    post_body = re.sub(r'\s+', ' ', post_body).strip()
    
    # هامش للعملات والهاشتاغات
    suffix = ""
    if coins:
        suffix += "\n\n" + " ".join(list(set(coins))[:2])
    if tags:
        suffix += "\n" + " ".join(list(set(tags))[:2])
    
    available = max_length - len(suffix) - 30
    
    if len(post_body) > available:
        truncated = post_body[:available]
        last_punct = max(
            truncated.rfind('.'),
            truncated.rfind('!'),
            truncated.rfind('?')
        )
        if last_punct > available * 0.5:
            post_body = post_body[:last_punct + 1]
        else:
            last_space = truncated.rfind(' ')
            if last_space > 0:
                post_body = post_body[:last_space] + "."
            else:
                post_body = truncated + "."
    
    return (post_body + suffix).strip()

# ===== ضمان العملات والهاشتاغات =====
def ensure_coins_tags(post):
    """يضمن وجود عملتين وهاشتاقين بالضبط (لا أكثر ولا أقل)"""
    coins = extract_coins(post)
    tags = extract_tags(post)
    
    # احذف الزائد
    if len(coins) > 2:
        for coin in coins[2:]:
            post = post.replace(f"${coin}", "")
        coins = coins[:2]
    
    if len(tags) > 2:
        for tag in tags[2:]:
            post = post.replace(f"#{tag}", "")
        tags = tags[:2]
    
    post = re.sub(r'\s+', ' ', post).strip()
    
    # أضف إذا نقص
    if len(coins) < 2:
        extra = pick_fresh_coins(2 - len(coins))
        post += "\n\n" + " ".join([f"${c}" for c in extra])
        coins.extend(extra)
    
    if len(tags) < 2:
        extra = pick_fresh_tags(2 - len(tags))
        post += "\n" + " ".join([f"#{t}" for t in extra])
        tags.extend(extra)
    
    save_recent_coins(coins)
    save_recent_tags(tags)
    
    return post

# ===== فحص الجودة =====
def is_good_quality(post):
    if not post:
        return False, "فارغ"
    if len(post) < MIN_LENGTH:
        return False, f"قصير ({len(post)})"
    if len(post) > MAX_LENGTH:
        return False, f"طويل ({len(post)})"
    
    coins = extract_coins(post)
    if len(coins) < 1:
        return False, "لا cashtag"
    if len(coins) > 2:
        return False, f"عملات كثيرة ({len(coins)})"
    
    tags = extract_tags(post)
    if len(tags) < 1:
        return False, "لا hashtag"
    if len(tags) > 2:
        return False, f"هاشتاغات كثيرة ({len(tags)})"
    
    return True, "جيد"

# ===== نوع المحتوى =====
def get_content_type():
    hour = datetime.utcnow().hour
    schedule = {
        0: 'news', 2: 'analysis', 4: 'project', 6: 'news',
        8: 'education', 10: 'news', 12: 'analysis', 14: 'promotion',
        16: 'news', 18: 'project', 20: 'education', 22: 'recap',
    }
    closest = min(schedule.keys(), key=lambda h: abs(h - hour))
    return schedule[closest]

# ===== القوالب =====
PROMPTS = {
    'news': """Write a DETAILED Binance Square post about this crypto news.

News: {title}
Details: {summary}

⚠️ ABSOLUTE MAXIMUM: 1800 CHARACTERS
⚠️ Use EXACTLY 2 $CASHTAGS maximum
⚠️ Use EXACTLY 2 #hashtags maximum

Rules:
- Target: 1400-1700 characters
- Start with emoji
- Structure: Headline + What happened + Why it matters + Market impact + Your take
- 2 $CASHTAGS MAX
- 2 #hashtags MAX
- Add engaging question

OUTPUT ONLY THE POST TEXT.""",

    'education': """Write a DETAILED educational post for Binance Square.

Topic: {title}

⚠️ ABSOLUTE MAXIMUM: 1800 CHARACTERS
⚠️ Use EXACTLY 2 $CASHTAGS maximum
⚠️ Use EXACTLY 2 #hashtags maximum

Rules:
- Target: 1400-1700 characters
- Start with 📚
- Structure: Hook + What it is + How it works + Benefits + Mistakes + Tip
- 2 $CASHTAGS MAX
- 2 #hashtags MAX
- Add engaging question

OUTPUT ONLY THE POST TEXT.""",

    'analysis': """Write a DETAILED crypto market analysis.

Market Data: {title}

⚠️ ABSOLUTE MAXIMUM: 1800 CHARACTERS
⚠️ Use ONLY $BTC and $ETH
⚠️ Use EXACTLY 2 #hashtags maximum

Rules:
- Target: 1400-1700 characters
- Start with 📊
- Structure: Current state + Key levels + Trends + Scenarios
- $BTC and $ETH ONLY
- 2 #hashtags MAX
- Add engaging question

OUTPUT ONLY THE POST TEXT.""",

    'project': """Write a DETAILED crypto project spotlight.

Project: {title}

⚠️ ABSOLUTE MAXIMUM: 1800 CHARACTERS
⚠️ Use EXACTLY 2 $CASHTAGS maximum
⚠️ Use EXACTLY 2 #hashtags maximum

Rules:
- Target: 1400-1700 characters
- Start with 💡
- Structure: What + Problem + How + Features + Risks
- 2 $CASHTAGS MAX
- 2 #hashtags MAX
- Add engaging question

OUTPUT ONLY THE POST TEXT.""",

    'promotion': """Write a promotional Binance post.

Promotion: {title}

⚠️ ABSOLUTE MAXIMUM: 1500 CHARACTERS
⚠️ Use ONLY $BNB and $USDT
⚠️ Use EXACTLY 2 #hashtags maximum

Rules:
- Target: 1000-1400 characters
- Start with 🎁
- Structure: Hook + Offer + How + Benefits + Urgency
- $BNB and $USDT ONLY
- 2 #hashtags MAX
- Add engaging question

OUTPUT ONLY THE POST TEXT.""",

    'recap': """Write a daily crypto recap.

Data: {title}

⚠️ ABSOLUTE MAXIMUM: 1800 CHARACTERS
⚠️ Use ONLY $BTC and $ETH
⚠️ Use EXACTLY 2 #hashtags maximum

Rules:
- Target: 1400-1700 characters
- Start with 🌙
- Structure: Summary + Movements + What mattered + Tomorrow + Final
- $BTC and $ETH ONLY
- 2 #hashtags MAX
- Add engaging question

OUTPUT ONLY THE POST TEXT.""",
}

# ===== الكتابة =====
def write_post(prompt, max_retries=2):
    for attempt in range(max_retries):
        try:
            response = groq_client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": f"Crypto writer for Binance Square. LIMIT: {MAX_LENGTH} chars. MAX 2 $CASHTAGS. MAX 2 #hashtags. Output ONLY post text."},
                    {"role": "user", "content": prompt[:2500]}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            
            content = response.choices[0].message.content
            if not content or not content.strip():
                continue
            
            post = fix_tickers(content.strip())
            
            # ⭐ القص الإجباري (لا إعادة محاولة)
            if len(post) > MAX_LENGTH:
                print(f"  🔧 قص إجباري: {len(post)} → {MAX_LENGTH}")
                post = force_trim(post, MAX_LENGTH)
            
            # ⭐ ضمان العملات والهاشتاغات
            post = ensure_coins_tags(post)
            
            # ⭐ فحص نهائي
            is_good, reason = is_good_quality(post)
            if is_good:
                return post
            
            print(f"  ⚠️ {reason}")
            time.sleep(2)
            
        except Exception as e:
            err = str(e)
            if "429" in err or "too large" in err or "rate" in err.lower():
                print(f"  ⏳ Rate limit، انتظار 30 ثانية...")
                time.sleep(30)
            else:
                print(f"  ❌ {err[:80]}")
                time.sleep(3)
    
    return None

# ===== النشر =====
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

# ===== التشغيل =====
def run_agent():
    content_type = get_content_type()
    print(f"🚀 بدء - {datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC")
    print(f"📝 نوع: {content_type}")
    print("=" * 60)
    
    post_content = None
    news_id = None
    
    if content_type == 'news':
        news_list = fetch_news(limit=10)
        if news_list:
            news = news_list[0]
            news_id = news['id']
            post_content = f"{news['title']}\n{news['summary']}"
            print(f"📰 {news['title'][:55]}...")
    
    elif content_type == 'education':
        available = [t for t in EDUCATION_TOPICS if f"edu_{t[:30]}" not in POSTED_NEWS]
        if not available:
            available = EDUCATION_TOPICS
        topic = random.choice(available)
        news_id = f"edu_{topic[:30]}"
        post_content = topic
        print(f"📚 {topic[:55]}...")
    
    elif content_type == 'analysis':
        prices = fetch_prices()
        if prices:
            text = "\n".join([f"{k.title()}: ${v['usd']:.2f} ({v['usd_24h_change']:+.2f}%)" for k, v in prices.items()])
            news_id = f"analysis_{datetime.utcnow().strftime('%Y%m%d%H')}"
            post_content = text
            print(f"📊 {len(prices)} عملة")
    
    elif content_type == 'project':
        projects = fetch_trending()
        if projects:
            proj = random.choice(projects)['item']
            news_id = f"project_{proj['symbol']}_{datetime.utcnow().strftime('%Y%m%d%H')}"
            post_content = f"{proj['name']} (${proj['symbol']}) - Rank {proj.get('market_cap_rank', 'N/A')}"
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
            btc = prices.get('bitcoin', {})
            eth = prices.get('ethereum', {})
            post_content = f"BTC: ${btc.get('usd', 0):.0f} ({btc.get('usd_24h_change', 0):+.1f}%), ETH: ${eth.get('usd', 0):.0f} ({eth.get('usd_24h_change', 0):+.1f}%)"
            news_id = f"recap_{datetime.utcnow().strftime('%Y%m%d')}"
            print(f"🌙 ملخص")
    
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
    
    template = PROMPTS.get(content_type, PROMPTS['news'])
    prompt = template.format(title=post_content, summary=post_content)
    
    post = write_post(prompt)
    if not post:
        print("❌ فشل الكتابة")
        return
    
    print(f"✍️ {len(post)} حرف")
    print(f"   {post[:150]}...")
    
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
