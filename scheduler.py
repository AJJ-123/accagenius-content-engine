import asyncio
import logging
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, '/app')

from datetime import datetime

logging.basicConfig(level=logging.INFO, format="%(asctime)s [scheduler] %(message)s")
logger = logging.getLogger(__name__)


async def send_telegram(message):
    token   = os.getenv("CONTENT_BOT_TOKEN", "")
    chat_id = os.getenv("CONTENT_ADMIN_CHAT_ID", "")
    if not token or not chat_id:
        logger.warning("Telegram tokens not set")
        return
    try:
        import urllib.request, urllib.parse
        url  = f"https://api.telegram.org/bot{token}/sendMessage"
        data = urllib.parse.urlencode({
            "chat_id":    chat_id,
            "text":       message,
            "parse_mode": "HTML"
        }).encode()
        urllib.request.urlopen(urllib.request.Request(url, data=data), timeout=10)
        logger.info("Telegram message sent")
    except Exception as e:
        logger.error(f"Telegram send error: {e}")


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
            home = brief.get("home", "")
            away = brief.get("away", "")
            caps = brief.get("captions", {})

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

            try:
                import poster as poster_module
                output = f"/tmp/{home}_{away}_poster.png".replace(" ", "_")
                poster_module.render_match_poster(brief, output)
                logger.info(f"Poster rendered: {output}")
            except Exception as e:
                logger.warning(f"Poster skipped: {e}")

            count += 1

        await send_telegram(f"✅ <b>Done!</b> {count} content drafts sent.")

    except Exception as e:
        logger.error(f"Morning job error: {e}")
        await send_telegram(f"⚠️ Morning job error: {e}")


async def run_inplay_scan():
    try:
        import data as data_module
        live = data_module.get_live_matches()
        if not live:
            return
        for m in live[:3]:
            home   = m.get("home", "")
            away   = m.get("away", "")
            hs     = m.get("home_score", 0) or 0
            as_    = m.get("away_score", 0) or 0
            minute = m.get("minute", 0) or 0
            if minute >= 45:
                msg = (
                    f"⚽ <b>LIVE</b> — {home} {hs}-{as_} {away} ({minute}')\n"
                    f"Live xG tracking 👉 accagenius.com"
                )
                await send_telegram(msg)
    except Exception as e:
        logger.error(f"Inplay scan error: {e}")


async def run_organic_post():
    try:
        import inplay as inplay_module
        features = ["xg_explainer", "acca_explained", "telegram_cta"]
        feature  = features[datetime.now().weekday() % len(features)]
        content  = inplay_module.site_feature_post(feature)
        caps     = content.get("captions", {})
        msg = (
            f"📝 <b>ORGANIC POST — no graphic needed</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🎵 <b>TIKTOK:</b>\n{caps.get('tiktok','')}\n\n"
            f"🐦 <b>X:</b>\n{caps.get('x','')}\n\n"
            f"💬 <b>REDDIT:</b>\n{caps.get('reddit','')[:400]}"
        )
        await send_telegram(msg[:4096])
    except Exception as e:
        logger.error(f"Organic post error: {e}")


async def scheduler_loop():
    morning_done = organic_done = afternoon_done = ""

    await send_telegram(
        "✅ <b>AccaGenius Content Engine Started</b>\n\n"
        "Scheduler is running.\n"
        "Morning content fires at 08:30 UK time.\n"
        "Organic post fires at 12:00.\n"
        "Live alerts fire between 12:00–23:00."
    )

    logger.info("✅ AccaGenius scheduler started")

    while True:
        try:
            now    = datetime.utcnow()
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
