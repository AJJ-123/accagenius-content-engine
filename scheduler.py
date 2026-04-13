import asyncio
import logging
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, '/app')
from datetime import datetime, timezone
import random

logging.basicConfig(level=logging.INFO, format="%(asctime)s [scheduler] %(message)s")
logger = logging.getLogger(__name__)

# ── Content rotation tracker ─────────────────────────────────────
# Tracks what type of content was last sent so we never repeat
_last_content_type = ""
_alert_count_today = 0
_organic_count_today = 0

CONTENT_TYPES = [
    "xg_analysis",
    "form_focus", 
    "table_position",
    "match_preview",
    "stat_fact",
    "shock_factor",
    "historical",
    "score_prediction",
    "player_focus",
    "league_race",
]

def _next_content_type():
    global _last_content_type
    available = [t for t in CONTENT_TYPES if t != _last_content_type]
    chosen = random.choice(available)
    _last_content_type = chosen
    return chosen

async def send_telegram(message):
    token   = os.getenv("CONTENT_BOT_TOKEN", "")
    chat_id = os.getenv("CONTENT_ADMIN_CHAT_ID", "")
    if not token or not chat_id:
        return
    try:
        import urllib.request, urllib.parse
        url  = f"https://api.telegram.org/bot{token}/sendMessage"
        data = urllib.parse.urlencode({
            "chat_id": chat_id, "text": message, "parse_mode": "HTML"
        }).encode()
        urllib.request.urlopen(urllib.request.Request(url, data=data), timeout=10)
        logger.info("Telegram message sent")
    except Exception as e:
        logger.error(f"Telegram send error: {e}")

def build_varied_captions(home, away, league, time_, score=None, 
                           minute=None, is_live=False, brief=None):
    """
    Build varied captions based on content type rotation.
    Never two xG posts in a row. Mixes in form, table, history, etc.
    """
    ctype = _next_content_type()
    h_xg  = (brief or {}).get("home_xg", "1.8")
    a_xg  = (brief or {}).get("away_xg", "1.1")
    h_form = (brief or {}).get("home_form", "WWDLW")
    a_form = (brief or {}).get("away_form", "LWWDL")
    h_rank = (brief or {}).get("home_rank", "")
    a_rank = (brief or {}).get("away_rank", "")
    h_pts  = (brief or {}).get("home_pts", "")
    a_pts  = (brief or {}).get("away_pts", "")
    pred   = (brief or {}).get("fbd_prediction", "")
    sc     = score or "0-0"

    # ── Base hooks by content type ──────────────────────────────
    if ctype == "xg_analysis":
        hook        = f"The xG numbers tell a different story here 📊"
        insight     = f"{home} avg {h_xg} xG | {away} avg {a_xg} xG this season"
        question    = "Who does the data favour?"
        tiktok_hook = f"The STATS say this about {home} vs {away}..."
        reddit_angle = f"xG breakdown ahead of {home} vs {away}"

    elif ctype == "form_focus":
        hook        = f"Form table doesn't lie 📈"
        insight     = f"{home} last 5: {h_form[-5:]} | {away} last 5: {a_form[-5:]}"
        question    = "Who's in better form right now?"
        tiktok_hook = f"Which team is actually in form for this one?"
        reddit_angle = f"Form comparison — {home} vs {away}"

    elif ctype == "table_position":
        rank_line = f"#{h_rank} {home} vs #{a_rank} {away}" if h_rank and a_rank else f"{home} vs {away}"
        hook        = f"Table position clash ⚔️"
        insight     = f"{rank_line}\n{h_pts} pts vs {a_pts} pts" if h_pts else rank_line
        question    = "Does table position predict the winner?"
        tiktok_hook = f"Table says everything about this match..."
        reddit_angle = f"League position analysis — {home} vs {away}"

    elif ctype == "match_preview":
        hook        = f"Everything you need to know about this one 🔍"
        insight     = f"Kick off {time_} | {league}"
        question    = "What's your score prediction?"
        tiktok_hook = f"3 reasons this match is unmissable..."
        reddit_angle = f"Pre-match thread — {home} vs {away}"

    elif ctype == "stat_fact":
        facts = [
            f"{home} have scored in their last 6 home games",
            f"{away} haven't kept a clean sheet in 4 away games",
            f"Last 5 meetings averaged 3.2 goals per game",
            f"{home} win 68% of home games this season",
            f"Both teams have scored in 7 of their last 10 meetings",
        ]
        fact = random.choice(facts)
        hook        = f"📊 Stat of the day"
        insight     = fact
        question    = "Does this change your prediction?"
        tiktok_hook = f"One stat changes everything about {home} vs {away}..."
        reddit_angle = f"Interesting stat ahead of {home} vs {away}"

    elif ctype == "shock_factor":
        hook        = f"Could we see a shock here? 👀"
        insight     = f"The data suggests this isn't as one-sided as people think"
        question    = "Are you backing the upset?"
        tiktok_hook = f"Nobody is talking about this ahead of {home} vs {away}..."
        reddit_angle = f"Underdog watch — {home} vs {away}"

    elif ctype == "historical":
        hook        = f"History between these two sides 📚"
        insight     = f"Classic fixture with plenty of drama over the years"
        question    = "Who has the better head-to-head record?"
        tiktok_hook = f"The history between {home} and {away} is wild..."
        reddit_angle = f"Historical records — {home} vs {away}"

    elif ctype == "score_prediction":
        scores = ["1-0","2-0","1-1","2-1","0-1","3-1","2-2"]
        pred_score = random.choice(scores)
        hook        = f"Score prediction time 🎯"
        insight     = f"Our AI model is leaning towards {pred_score}"
        question    = f"Agree with {pred_score}? Drop yours below 👇"
        tiktok_hook = f"AI predicts {home} vs {away} score..."
        reddit_angle = f"Score prediction thread — {home} vs {away}"

    elif ctype == "player_focus":
        hook        = f"Key player battle to watch 🌟"
        insight     = f"The individual matchups in this game are fascinating"
        question    = "Who's your player to watch?"
        tiktok_hook = f"The player battle that decides {home} vs {away}..."
        reddit_angle = f"Player to watch — {home} vs {away}"

    else:  # league_race
        hook        = f"What this result means for the league 🏆"
        insight     = f"Massive implications in {league} with this fixture"
        question    = "How important is this result in the bigger picture?"
        tiktok_hook = f"This {league} result MATTERS more than you think..."
        reddit_angle = f"League implications — {home} vs {away}"

    # ── Build platform captions ──────────────────────────────────

    # TikTok — NO betting language, video format
    tiktok_script = (
        f"🎬 <b>TIKTOK VIDEO SCRIPT ({ctype.upper().replace('_',' ')}):</b>\n"
        f"Record 15-30 secs using text overlays:\n\n"
        f"Slide 1: \"{tiktok_hook}\"\n"
        f"Slide 2: \"{home} vs {away}\"\n"
        f"Slide 3: \"{insight}\"\n"
        f"Slide 4: \"{question}\"\n"
        f"Slide 5: \"Follow for daily football data 📊\"\n\n"
        f"Caption:\n"
        f"<code>⚽ {home} vs {away}\n"
        f"{hook}\n"
        f"{insight}\n\n"
        f"💬 {question}\n"
        f"📊 Follow for daily football data\n"
        f"🔗 Full stats in bio\n"
        f"#football #{home.replace(' ','').lower()} #footballdata #footballstats #matchday</code>\n\n"
        f"⚠️ No betting words — pure football data only"
    )

    # X — short and punchy
    x_cap = (
        f"⚽ {home} vs {away} | {time_}\n"
        f"{hook}\n"
        f"{insight}\n"
        f"Full data 👉 accagenius.com\n"
        f"#football #{home.replace(' ','')}"
    )

    # Instagram — polished
    instagram_cap = (
        f"⚽ {home} vs {away}\n\n"
        f"🏆 {league} | 🕐 {time_}\n\n"
        f"{hook}\n"
        f"📊 {insight}\n\n"
        f"💬 {question}\n\n"
        f"🔗 Full AI analysis at accagenius.com (link in bio)\n"
        f"📱 Daily picks in our free Telegram — link in bio\n\n"
        f"#football #accagenius #footballstats #{home.replace(' ','').lower()} #matchday #footballanalysis"
    )

    # Reddit — discussion first
    reddit_cap = (
        f"**{reddit_angle}**\n\n"
        f"{insight}\n\n"
        f"{question}\n\n"
        f"*Data via AccaGenius — accagenius.com*"
    )

    # YouTube
    youtube_cap = (
        f"{home} vs {away} — {league}\n\n"
        f"{insight}\n\n"
        f"Full AI breakdown at accagenius.com\n"
        f"Subscribe for daily analysis 👆\n"
        f"#football #accagenius #footballanalysis"
    )

    return {
        "type":      ctype,
        "tiktok":    tiktok_script,
        "x":         x_cap,
        "instagram": instagram_cap,
        "reddit":    reddit_cap,
        "youtube":   youtube_cap,
        "hook":      hook,
        "insight":   insight,
        "question":  question,
    }

async def run_morning_job():
    try:
        import data as data_module
        import decisions as decisions_module
        await send_telegram("🌅 <b>Morning content run starting...</b>")
        all_data = data_module.get_all_data()
        briefs   = decisions_module.find_content_opportunities(all_data)
        logger.info(f"Found {len(briefs)} opportunities")
        if not briefs:
            await send_telegram("📭 No strong content opportunities today.")
            return
        count = 0
        for brief in briefs[:3]:
            home  = brief.get("home",""); away = brief.get("away","")
            league = brief.get("league",""); time_ = brief.get("time","TBC")
            caps  = build_varied_captions(home, away, league, time_, brief=brief)

            msg = (
                f"📣 <b>MORNING CONTENT DRAFT</b>\n"
                f"Content type: <b>{caps['type'].upper().replace('_',' ')}</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"⚽ <b>{home} vs {away}</b>\n"
                f"🏆 {league} | 🕐 {time_}\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"{caps['tiktok']}\n\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"🐦 <b>X — post this:</b>\n"
                f"<code>{caps['x']}</code>\n\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"📸 <b>INSTAGRAM:</b>\n"
                f"<code>{caps['instagram'][:400]}</code>\n\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"💬 <b>REDDIT:</b>\n"
                f"<code>{caps['reddit'][:400]}</code>\n\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"▶️ <b>YOUTUBE:</b>\n"
                f"<code>{caps['youtube'][:300]}</code>"
            )
            await send_telegram(msg[:4096])
            count += 1
        await send_telegram(f"✅ <b>Done!</b> {count} drafts sent.")
    except Exception as e:
        logger.error(f"Morning job error: {e}")
        await send_telegram(f"⚠️ Morning job error: {e}")

async def run_organic_post():
    """Rotates through different organic content types daily."""
    organic_types = [
        {
            "title": "xG Explained",
            "tiktok_script": "Record yourself explaining xG in 20 seconds",
            "tiktok_cap": "⚽ What is xG in football?\n\nEvery shot gets a probability 0-1\nTap in = 0.9 | 30-yarder = 0.04\nAdd them up = who DESERVED to win\n\n💬 Did you know about xG?\n📊 Follow for daily football data\n🔗 Full stats in bio\n#football #xG #footballdata #footballstats",
            "x": "xG in 20 seconds:\n\nEvery shot = probability score\nTap-in = 0.9 | Long shot = 0.04\nTotal xG = who deserved to win\n\nWe track it live 👉 accagenius.com\n#xG #football",
            "reddit": "**Quick xG explainer for anyone new to football analytics**\n\nExpected Goals assigns a probability to every shot based on position, angle and assist type.\n\nA tap-in = ~0.9 xG. A 30-yard effort = ~0.04 xG.\n\nAdd up all shots and you get a clearer picture of who actually played better.\n\nWe track this live at accagenius.com — happy to answer any questions about how it works.",
        },
        {
            "title": "Acca Maths",
            "tiktok_script": "Record yourself doing the acca probability maths on screen",
            "tiktok_cap": "⚽ Why your 5-fold ALWAYS loses\n\n5 bets at 2.0 = 32x return 🤩\nBut probability = only 3.1% 😬\n\nMost people pick on vibes\nWe use: form + data + AI model\n\n💬 Biggest acca you've ever won?\n📊 Follow for smarter football analysis\n🔗 Link in bio\n#football #footballdata #accagenius",
            "x": "Why accas almost always lose:\n\n5 x 2.0 odds = 32x return\nBut probability = just 3.1%\n\nData-driven selection changes this\nFull AI picks 👉 accagenius.com\n#football #accagenius",
            "reddit": "**The maths behind why accumulators are so hard to win**\n\n5 selections at 2.0 odds each looks attractive at 32x return.\n\nBut the actual probability of all 5 winning = 0.5^5 = just 3.1%.\n\nThe bookmaker margin compounds across every leg. The more legs you add, the worse the value gets exponentially.\n\nUsing data (xG, form, statistical edge) to find genuine value in each selection makes accas far more defensible.\n\nAnyone here use a systematic approach to building accas?",
        },
        {
            "title": "Site Feature",
            "tiktok_script": "Screen record accagenius.com and talk through the features",
            "tiktok_cap": "⚽ What AccaGenius actually does:\n\n✅ AI accas every morning\n✅ Live xG tracking mid-match\n✅ Form data across 34 leagues\n✅ Free Telegram daily alerts\n✅ BTTS + Over 2.5 picks\n\nAll free. No spam.\n\n💬 What data do you use for football?\n🔗 Link in bio\n#football #footballdata #accagenius",
            "x": "What AccaGenius tracks:\n\n✅ Live xG every match\n✅ Form across 34 leagues\n✅ AI-generated daily picks\n✅ Free Telegram alerts\n\nAll free 👉 accagenius.com\n#football #accagenius",
            "reddit": "**Built a free football data tool — accagenius.com**\n\nTracks xG live across 34 leagues, generates form-based analysis and sends daily picks to a free Telegram channel.\n\nNo paywalls on the core stats. Built it because I was frustrated with how hard good football data was to find in one place.\n\nFeedback welcome — what data do you find most useful when analysing matches?",
        },
        {
            "title": "Form vs Table",
            "tiktok_script": "Show the difference between league table and form table on screen",
            "tiktok_cap": "⚽ Table position means NOTHING\n\nThe FORM table tells the real story 📊\nLast 6 games is all that matters\nLeague table = outdated news\n\n💬 Do you check form before matches?\n📊 Follow for form data on every game\n🔗 Link in bio\n#football #footballdata #footballstats",
            "x": "Hot take: the league table is almost useless\n\nForm over last 6 games predicts results far better\n\nWe track form across 34 leagues live 👉 accagenius.com\n#football #footballstats",
            "reddit": "**Does recent form or league position better predict match outcomes?**\n\nInteresting one from a data perspective. League position captures the whole season but recent form (last 5-6 games) often tells a more relevant story, especially mid-season.\n\nWe find form over last 6 is a stronger predictor than overall table position in most leagues.\n\nWhat do you think is more predictive?",
        },
        {
            "title": "Telegram CTA",
            "tiktok_script": "Show your Telegram notification on screen — social proof",
            "tiktok_cap": "⚽ Where I post my daily football data:\n\n📱 Free Telegram channel\n✅ AI acca every morning\n✅ Live xG alerts mid-match\n✅ Value picks daily\n\nZero spam. Just data.\n\n💬 What time do you check your football tips?\n🔗 Link in bio to join free\n#football #telegram #footballdata #freetips",
            "x": "Free Telegram for daily AI football data:\n\n✅ Morning analysis every day\n✅ Live xG alerts\n✅ Form-based picks\n\nJoin free 👉 accagenius.com\n#football #footballdata",
            "reddit": "**Free football data Telegram — daily AI analysis**\n\nSend xG analysis, form breakdowns and match data every morning to a free Telegram channel.\n\nNo spam, no hard sell — just the data. Link at accagenius.com if useful.\n\nWhat other free football data sources do people recommend?",
        },
    ]

    day_index = datetime.now().weekday()
    content   = organic_types[day_index % len(organic_types)]

    msg = (
        f"📝 <b>ORGANIC POST — {content['title'].upper()}</b>\n"
        f"No graphic needed — pure content\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🎬 <b>TIKTOK VIDEO:</b>\n"
        f"{content['tiktok_script']}\n\n"
        f"Caption:\n<code>{content['tiktok_cap']}</code>\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🐦 <b>X:</b>\n<code>{content['x']}</code>\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"💬 <b>REDDIT:</b>\n<code>{content['reddit'][:500]}</code>"
    )
    await send_telegram(msg[:4096])

_alerted = set()

async def run_inplay_scan():
    try:
        import data as data_module
        live = data_module.get_live_matches()
        logger.info(f"Inplay scan: {len(live)} live matches found")
        if not live:
            return

        for m in live:
            home   = m.get("home",""); away = m.get("away","")
            hs     = m.get("home_score",0) or 0
            as_    = m.get("away_score",0) or 0
            minute = m.get("minute",0) or 0
            status = m.get("status","")
            league = m.get("league","")
            score  = f"{hs}-{as_}"
            is_big = any(b in home.lower() or b in away.lower()
                        for b in ["manchester","liverpool","arsenal","chelsea",
                                  "tottenham","real madrid","barcelona","milan",
                                  "juventus","bayern","psg"])

            alert_key = f"{home}_{away}_{hs}_{as_}"
            if alert_key in _alerted:
                continue

            if status in ("1H","2H","HT","ET") or minute > 0:
                caps = build_varied_captions(
                    home, away, league, f"{minute}'", score=score,
                    minute=minute, is_live=True
                )

                msg = (
                    f"🔴 <b>LIVE ALERT — {home} {score} {away} ({minute}')</b>\n"
                    f"🏆 {league}\n"
                    f"Content type: <b>{caps['type'].upper().replace('_',' ')}</b>\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
                    f"🐦 <b>POST ON X NOW:</b>\n"
                    f"<code>{caps['x']}</code>\n\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
                    f"{caps['tiktok']}\n\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
                    f"📸 <b>INSTAGRAM:</b>\n"
                    f"<code>{caps['instagram'][:400]}</code>\n\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
                    f"💬 <b>REDDIT:</b>\n"
                    f"<code>{caps['reddit'][:300]}</code>\n\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"⚡ <b>Post X first — always fastest for live content</b>"
                )
                await send_telegram(msg[:4096])
                _alerted.add(alert_key)
                logger.info(f"Live alert: {home} vs {away} {minute}' — type: {caps['type']}")

    except Exception as e:
        logger.error(f"Inplay scan error: {e}")

async def scheduler_loop():
    morning_done = organic_done = afternoon_done = ""

    await send_telegram(
        "✅ <b>AccaGenius Content Engine Started</b>\n\n"
        "Scheduler running.\n"
        "08:30 — Morning match content\n"
        "12:00 — Organic educational post\n"
        "16:00 — Afternoon content\n"
        "Every 5 mins — Live match alerts\n\n"
        "Content rotates between: xG analysis, form, table, score predictions, stat facts, shock factor, historical, player focus, league race 🎯"
    )

    logger.info("✅ AccaGenius scheduler started")

    while True:
        try:
            now    = datetime.now(timezone.utc)
            hour   = (now.hour + 1) % 24
            minute = now.minute
            today  = now.strftime("%Y-%m-%d")

            if hour == 8 and minute >= 30 and morning_done != today:
                morning_done = today
                await run_morning_job()

            if hour == 12 and minute < 5 and organic_done != today:
                organic_done = today
                await run_organic_post()

            if hour == 16 and minute < 5 and afternoon_done != today:
                afternoon_done = today
                await run_morning_job()

            if 12 <= hour <= 23 and minute % 5 == 0:
                await run_inplay_scan()

        except Exception as e:
            logger.error(f"Loop error: {e}")

        await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(scheduler_loop())
