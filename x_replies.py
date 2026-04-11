"""
AccaGenius X Reply Engine
Monitors big football accounts for tweetable moments,
drafts data-led replies, sends to Telegram for approval.
Uses Twitter/X API v2 (free tier is enough for read + reply).
"""
import os, re, json, asyncio
from datetime import datetime, timedelta
from pathlib import Path

# ── Target accounts to monitor ───────────────────────────────────
TARGET_ACCOUNTS = [
    {"handle": "OptaJoe",        "type": "stats",   "priority": 1},
    {"handle": "WhoScored",      "type": "stats",   "priority": 1},
    {"handle": "SkySportsPL",    "type": "news",    "priority": 2},
    {"handle": "FabrizioRomano", "type": "news",    "priority": 2},
    {"handle": "Football_Daily", "type": "general", "priority": 2},
    {"handle": "bbcsport",       "type": "news",    "priority": 2},
    {"handle": "premierleague",  "type": "official","priority": 1},
    {"handle": "goal",           "type": "general", "priority": 3},
    {"handle": "BleacherReport", "type": "general", "priority": 3},
    {"handle": "transfermarkt",  "type": "stats",   "priority": 2},
]

# ── Reply templates by tweet type ────────────────────────────────
# Each template adds VALUE first, then subtle brand mention
REPLY_TEMPLATES = {

    # Tweet mentions goals / scoring
    "goals": [
        "xG backs that up — {team} have been one of the most clinical sides this season. "
        "Full xG breakdown on accagenius.com 📊",

        "The xG numbers have been predicting this form for weeks. "
        "{team} averaging {xg} xG per game — well above their actual goals scored. "
        "accagenius.com tracks this live 📈",

        "Worth noting {team}'s xG per shot has been elite this season — "
        "not just volume, quality chances. Full data 👉 accagenius.com",
    ],

    # Tweet mentions a result / score
    "result": [
        "The xG actually told this story before FT — "
        "a classic case of the numbers being right. "
        "Live xG on all games at accagenius.com 📊",

        "Interesting one from an xG perspective — "
        "the underlying numbers will be worth checking after this. "
        "accagenius.com has the full breakdown 👀",

        "xG model had this one pretty close actually. "
        "Data is live at accagenius.com if anyone wants the full picture 📈",
    ],

    # Tweet mentions a player
    "player": [
        "The xG per 90 numbers for {player} this season are genuinely elite — "
        "not just goals, it's the quality of chances. accagenius.com 📊",

        "Form data backs this completely. "
        "{player} has been one of the standout performers by xG this season. "
        "Full stats 👉 accagenius.com",
    ],

    # Tweet mentions a derby or big match upcoming
    "upcoming_match": [
        "Our AI model has the full xG breakdown for this one ahead of kickoff. "
        "Form, table position, probability — all live at accagenius.com 🤖",

        "This one's fascinating from an xG perspective — "
        "both sides have very different underlying numbers to their league position. "
        "Full preview at accagenius.com 📊",

        "xG model is tracking this as one of the higher-variance games this week. "
        "Full AI breakdown at accagenius.com 👀",
    ],

    # Tweet mentions a shock result
    "shock": [
        "The xG model actually flagged this as higher variance than the odds suggested. "
        "Football never lies 😅 Full data at accagenius.com",

        "This is exactly what makes xG useful — "
        "the underlying numbers often tell a different story to the scoreline. "
        "accagenius.com tracks this live 📊",

        "xG said one thing, the result said another. "
        "Classic football 🤷 Live stats at accagenius.com",
    ],

    # Tweet is a general stat
    "stat": [
        "Great stat — the xG numbers paint an even more interesting picture. "
        "We track all of this live at accagenius.com 📊",

        "The underlying data backs this up completely. "
        "Full xG breakdown on accagenius.com 👀",
    ],

    # Generic fallback — safe for anything
    "general": [
        "Interesting — the xG numbers on accagenius.com tell a similar story. "
        "Full AI breakdown live 📊",

        "Worth checking the xG data on this one. "
        "All live at accagenius.com 📈",
    ],
}

# ── Tweet classifier ─────────────────────────────────────────────
GOAL_KEYWORDS    = ["goal","scored","hat-trick","brace","strike","finish","tapped in",
                    "header","penalty","free kick","goals","scorer","scoring"]
RESULT_KEYWORDS  = ["full time","ft:","final score","wins","beat","defeated","draw",
                    "result","scores","fixture","match ends","today's results"]
PLAYER_KEYWORDS  = ["player","transfer","signing","contract","debut","injury","return",
                    "back","fit","squad","lineup","xi","bench"]
SHOCK_KEYWORDS   = ["shock","upset","stunned","incredible","unbelievable","embarrassing",
                    "disaster","nightmare","bottled","crisis","sack"]
UPCOMING_KEYWORDS= ["today","tonight","tomorrow","kick off","kickoff","preview",
                    "vs","v ","ahead of","preview","fixtures","matchday","this weekend"]
STAT_KEYWORDS    = ["stats","data","numbers","per game","per 90","season","career",
                    "record","all-time","most","ever","passes","tackles","assists"]

def classify_tweet(text: str) -> tuple[str, dict]:
    """
    Classify tweet type and extract entities.
    Returns (type, entities_dict)
    """
    text_lower = text.lower()
    entities   = {}

    # Extract team names (simple — capitalised words)
    teams = re.findall(r'\b[A-Z][a-z]+ (?:City|United|FC|Town|Wednesday|Athletic|'
                       r'Rovers|County|Wanderers|Villa|Forest|Palace|Hotspur|'
                       r'Albion|Athletic)\b', text)
    if teams:
        entities["team"] = teams[0]

    # Extract player names (two capitalised words)
    players = re.findall(r'\b[A-Z][a-z]+\s[A-Z][a-z]+\b', text)
    if players:
        entities["player"] = players[0]

    # Classify by keywords
    if any(k in text_lower for k in SHOCK_KEYWORDS):
        return "shock", entities
    if any(k in text_lower for k in GOAL_KEYWORDS):
        return "goals", entities
    if any(k in text_lower for k in RESULT_KEYWORDS):
        return "result", entities
    if any(k in text_lower for k in UPCOMING_KEYWORDS):
        return "upcoming_match", entities
    if any(k in text_lower for k in STAT_KEYWORDS):
        return "stat", entities
    if any(k in text_lower for k in PLAYER_KEYWORDS):
        return "player", entities

    return "general", entities

def build_reply(tweet_text: str, account: str,
                xg_data: dict = None) -> dict:
    """
    Build a reply draft for a tweet.
    Returns dict with reply text + metadata.
    """
    import random
    tweet_type, entities = classify_tweet(tweet_text)
    templates = REPLY_TEMPLATES.get(tweet_type, REPLY_TEMPLATES["general"])
    template  = random.choice(templates)

    # Fill in template placeholders
    reply = template
    if "{team}" in reply:
        reply = reply.replace("{team}", entities.get("team","this side"))
    if "{player}" in reply:
        reply = reply.replace("{player}", entities.get("player","them"))
    if "{xg}" in reply:
        xg_val = (xg_data or {}).get("xg_avg", "1.8")
        reply  = reply.replace("{xg}", str(xg_val))

    # Safety check — keep under 280 chars
    if len(reply) > 275:
        reply = reply[:272] + "..."

    return {
        "reply":      reply,
        "tweet_type": tweet_type,
        "account":    account,
        "entities":   entities,
        "char_count": len(reply),
        "original":   tweet_text[:200],
    }

# ── Rate limiter for replies ──────────────────────────────────────
REPLY_RATE_FILE = "/tmp/x_reply_rates.json"

REPLY_LIMITS = {
    "per_account_per_hour": 1,    # max 1 reply per account per hour
    "total_per_hour":       3,    # max 3 replies total per hour
    "total_per_day":        8,    # max 8 replies per day
    "min_gap_mins":         12,   # min 12 mins between any two replies
}

def _load_reply_rates() -> dict:
    try:
        if Path(REPLY_RATE_FILE).exists():
            with open(REPLY_RATE_FILE) as f:
                return json.load(f)
    except: pass
    return {}

def _save_reply_rates(data: dict):
    try:
        with open(REPLY_RATE_FILE,"w") as f:
            json.dump(data, f, indent=2)
    except: pass

def check_reply_safe(account: str) -> tuple[bool, str]:
    """Check if it's safe to reply to this account right now."""
    rates = _load_reply_rates()
    now   = datetime.now()
    today = now.strftime("%Y-%m-%d")
    hour  = now.strftime("%Y-%m-%d-%H")

    # Daily total
    daily_count = rates.get(f"total_{today}", 0)
    if daily_count >= REPLY_LIMITS["total_per_day"]:
        return False, f"Daily reply limit reached ({daily_count}/day)"

    # Hourly total
    hourly_count = rates.get(f"hourly_{hour}", 0)
    if hourly_count >= REPLY_LIMITS["total_per_hour"]:
        return False, f"Hourly reply limit reached ({hourly_count}/hour)"

    # Per-account hourly
    acct_key = f"account_{account}_{hour}"
    if rates.get(acct_key, 0) >= REPLY_LIMITS["per_account_per_hour"]:
        return False, f"Already replied to @{account} this hour"

    # Minimum gap
    last_any = rates.get("last_reply_time")
    if last_any:
        last_dt  = datetime.fromisoformat(last_any)
        elapsed  = (now - last_dt).total_seconds() / 60
        min_gap  = REPLY_LIMITS["min_gap_mins"]
        if elapsed < min_gap:
            wait = int(min_gap - elapsed)
            return False, f"Too soon — wait {wait} more minutes"

    return True, ""

def mark_reply_sent(account: str):
    """Record that a reply was sent."""
    rates = _load_reply_rates()
    now   = datetime.now()
    today = now.strftime("%Y-%m-%d")
    hour  = now.strftime("%Y-%m-%d-%H")

    rates[f"total_{today}"]           = rates.get(f"total_{today}", 0) + 1
    rates[f"hourly_{hour}"]           = rates.get(f"hourly_{hour}", 0) + 1
    rates[f"account_{account}_{hour}"]= rates.get(f"account_{account}_{hour}",0)+1
    rates["last_reply_time"]          = now.isoformat()
    _save_reply_rates(rates)

def get_reply_status() -> str:
    """Get reply rate limit status summary."""
    rates = _load_reply_rates()
    now   = datetime.now()
    today = now.strftime("%Y-%m-%d")
    hour  = now.strftime("%Y-%m-%d-%H")

    daily_count  = rates.get(f"total_{today}", 0)
    hourly_count = rates.get(f"hourly_{hour}", 0)
    last_reply   = rates.get("last_reply_time","Never")

    if last_reply != "Never":
        last_dt  = datetime.fromisoformat(last_reply)
        mins_ago = int((now - last_dt).total_seconds() / 60)
        last_str = f"{mins_ago}m ago"
    else:
        last_str = "Never"

    return (
        f"🐦 <b>X Reply Status:</b>\n"
        f"Today: {daily_count}/{REPLY_LIMITS['total_per_day']} replies\n"
        f"This hour: {hourly_count}/{REPLY_LIMITS['total_per_hour']}\n"
        f"Last reply: {last_str}\n"
        f"Min gap: {REPLY_LIMITS['min_gap_mins']} mins"
    )

# ── X API integration ─────────────────────────────────────────────
async def fetch_recent_tweets(account: str, bearer_token: str) -> list:
    """Fetch recent tweets from a target account using X API v2."""
    import aiohttp
    headers = {"Authorization": f"Bearer {bearer_token}"}
    url     = f"https://api.twitter.com/2/tweets/search/recent"
    params  = {
        "query":       f"from:{account} -is:retweet lang:en",
        "max_results": 5,
        "tweet.fields":"created_at,text,public_metrics",
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers,
                                   params=params, timeout=10) as r:
                if r.status == 200:
                    data = await r.json()
                    return data.get("data", [])
    except Exception as e:
        print(f"[x_replies] Fetch error for @{account}: {e}")
    return []

async def post_reply(tweet_id: str, reply_text: str,
                     bearer_token: str, access_token: str,
                     access_secret: str, api_key: str,
                     api_secret: str) -> bool:
    """Post a reply to a tweet using X API v2."""
    import aiohttp, hmac, hashlib, base64, time, urllib.parse
    # OAuth 1.0a signing for write operations
    try:
        url         = "https://api.twitter.com/2/tweets"
        payload     = {"text": reply_text, "reply": {"in_reply_to_tweet_id": tweet_id}}
        nonce       = base64.b64encode(os.urandom(16)).decode()
        timestamp   = str(int(time.time()))
        oauth_params = {
            "oauth_consumer_key":     api_key,
            "oauth_nonce":            nonce,
            "oauth_signature_method": "HMAC-SHA1",
            "oauth_timestamp":        timestamp,
            "oauth_token":            access_token,
            "oauth_version":          "1.0",
        }
        base_string = "&".join([
            "POST",
            urllib.parse.quote(url, safe=""),
            urllib.parse.quote("&".join(
                f"{k}={urllib.parse.quote(str(v),safe='')}"
                for k,v in sorted(oauth_params.items())
            ), safe="")
        ])
        signing_key = f"{urllib.parse.quote(api_secret,safe='')}&{urllib.parse.quote(access_secret,safe='')}"
        sig = base64.b64encode(
            hmac.new(signing_key.encode(), base_string.encode(), hashlib.sha1).digest()
        ).decode()
        oauth_params["oauth_signature"] = sig
        auth_header = "OAuth " + ", ".join(
            f'{k}="{urllib.parse.quote(str(v),safe="")}"'
            for k,v in sorted(oauth_params.items())
        )
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url,
                json=payload,
                headers={"Authorization": auth_header,
                         "Content-Type": "application/json"},
                timeout=10
            ) as r:
                if r.status in (200, 201):
                    print(f"[x_replies] ✅ Reply posted to tweet {tweet_id}")
                    return True
                else:
                    text = await r.text()
                    print(f"[x_replies] Post failed {r.status}: {text[:200]}")
    except Exception as e:
        print(f"[x_replies] Post error: {e}")
    return False
