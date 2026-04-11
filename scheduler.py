import asyncio
import logging
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime

logging.basicConfig(level=logging.INFO, format="%(asctime)s [scheduler] %(message)s")
logger = logging.getLogger(__name__)

async def send_telegram(message):
    """Send a message to Telegram."""
    token   = os.getenv("CONTENT_BOT_TOKEN", "")
    chat_id = os.getenv("CONTENT_ADMIN_CHAT_ID", "")
    if not token or not chat_id:
        logger.warning("CONTENT_BOT_TOKEN or CONTENT_ADMIN_CHAT_ID not set")
        return
    try:
        import urllib.request, urllib.parse, json
        url  = f"https://api.telegram.org/bot{token}/sendMessage"
        data = urllib.parse.urlencode({
            "chat_id":    chat_id,
            "text":       message,
            "parse_mode": "HTML"
        }).encode()
        req = urllib.request.Request(url, data=data)
        urllib.request.urlopen(req, timeout=10)
        logger.info("Telegram message sent")
    except Exception as e:
        logger.error(f"Telegram send error: {e}")

async def run_morning_job():
    try:
        from engine.data import get_all_data
        from engine.decisions import find_content_opportunities
        from renderer.poster import render_match_poster

        await send_telegram("🌅 <b>Morning content run starting...</b>")

        data   = get_all_data()
        briefs = find_content_opportunities(data)
        logger.info(f"Found {len(briefs)} opportunities")

        if not briefs:
            await send_telegram("📭 No strong content opportunities today.")
            return

        count = 0
        for brief in briefs[:3]:
            home  = brief.get("home","")
            away  = brief.get("away","")
            caps  = brief.get("captions", {})

            # Build caption message
            msg = (
                f"📣 <b>CONTENT DRAFT</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"⚽ <b>{home} vs {away}</b>\n"
                f"🏆 {brief.get('league','')} | 🕐 {brief.get('time','TBC')}\n\n"
                f"🎵 <b>TIKTOK:</b>\n{caps.get('tiktok','')[:300]}\n\n"
                f"🐦 <b>X:</b>\n{caps.get('x','')}\n\n"
                f"📸 <b>INSTAGRAM:</b>\n{caps.get('instagram','')[:300]}\n\n"
                f"💬 <b>REDDIT:</b>\n{caps.get('reddit','')[:300]}"
            )
            await send_telegram(msg[:4096])

            # Try poster
            try:
                output = f"/tmp/{home}_{away}_poster.png".replace(" ","_")
                render_match_poster(brief, output)
                logger.info(f"Poster rendered: {output}")
            except Exception as e:
                logger.warning(f"Poster error (non-fatal): {e}")

            count += 1

        await send_telegram(f"✅ <b>Done!</b> {count} content drafts sent.")

    except Exception as e:
        logger.error(f"Morning job error: {e}")
        await send_telegram(f"⚠️ Morning job error: {e}")

async def run_inplay_scan():
    try:
        from engine.data import get_live_matches
        live = get_live_matches()
        if not live:
            return
        for m in live[:3]:
            home   = m.get("home",""); away = m.get("away","")
            hs     = m.get("home_score",0); as_ = m.get("away_score",0)
            minute = m.get("minute",0)
            if minute and minute >= 45:
                msg = (
                    f"⚽ <b>LIVE</b> — {home} {hs}-{as_} {away} ({minute}')\n"
                    f"Full stats 👉 accagenius.com"
                )
                await send_telegram(msg)
    except Exception as e:
        logger.error(f"Inplay scan error: {e}")

async def scheduler_loop():
    morning_done = organic_done = afternoon_done = ""

    # Send startup message
    await send_telegram(
        "✅ <b>AccaGenius Content Engine Started</b>\n\n"
        "Scheduler is running.\n"
        "Morning content fires at 08:30 UK time.\n"
        "Live alerts fire between 12:00–23:00."
    )

    logger.info("✅ AccaGenius scheduler started")

    while True:
        try:
            now   = datetime.utcnow()
            # Convert to UK time (UTC+1 BST)
            hour  = (now.hour + 1) % 24
            minute = now.minute
            today = now.strftime("%Y-%m-%d")

            # 08:30 morning run
            if hour == 8 and minute >= 30 and morning_done != today:
                morning_done = today
                logger.info("Running morning job...")
                await run_morning_job()

            # 16:00 afternoon run
            if hour == 16 and minute < 5 and afternoon_done != today:
                afternoon_done = today
                logger.info("Running afternoon job...")
                await run_morning_job()

            # In-play scan every 5 mins 12:00-23:00
            if 12 <= hour <= 23 and minute % 5 == 0:
                await run_inplay_scan()

        except Exception as e:
            logger.error(f"Loop error: {e}")

        await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(scheduler_loop())
