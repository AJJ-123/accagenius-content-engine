import asyncio
import logging
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, '/app')
from datetime import datetime, timezone

logging.basicConfig(level=logging.INFO, format="%(asctime)s [scheduler] %(message)s")
logger = logging.getLogger(__name__)

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
            home = brief.get("home",""); away = brief.get("away","")
            caps = brief.get("captions", {})

            # TikTok for morning = video script instructions
            tiktok_video = (
                f"🎬 <b>TIKTOK VIDEO SCRIPT:</b>\n"
                f"Record a 15-30 second video saying:\n\n"
                f"Slide 1 title: \"{brief.get('title','MATCHDAY')}\"\n"
                f"Slide 2: \"{home} vs {away}\"\n"
                f"Slide 3: \"xG: {brief.get('home_xg','?')} vs {brief.get('away_xg','?')}\"\n"
                f"Slide 4: \"Kick off {brief.get('time','TBC')}\"\n"
                f"Slide 5: \"Who wins? Comment below!\"\n\n"
                f"Caption to use:\n"
                f"<code>{caps.get('tiktok','')[:300]}</code>"
            )

            msg = (
                f"📣 <b>MORNING CONTENT DRAFT</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"⚽ <b>{home} vs {away}</b>\n"
                f"🏆 {brief.get('league','')} | 🕐 {brief.get('time','TBC')}\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"{tiktok_video}\n\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"🐦 <b>X — post this now:</b>\n"
                f"<code>{caps.get('x','')}</code>\n\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"📸 <b>INSTAGRAM caption:</b>\n"
                f"<code>{caps.get('instagram','')[:400]}</code>\n\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"💬 <b>REDDIT post:</b>\n"
                f"<code>{caps.get('reddit','')[:400]}</code>\n\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"▶️ <b>YOUTUBE SHORTS caption:</b>\n"
                f"<code>{caps.get('youtube','')[:300]}</code>"
            )
            await send_telegram(msg[:4096])
            count += 1
        await send_telegram(f"✅ <b>Done!</b> {count} drafts sent.")
    except Exception as e:
        logger.error(f"Morning job error: {e}")
        await send_telegram(f"⚠️ Morning job error: {e}")

async def run_organic_post():
    try:
        import inplay as inplay_module
        features = ["xg_explainer","acca_explained","telegram_cta"]
        feature  = features[datetime.now().weekday() % len(features)]
        content  = inplay_module.site_feature_post(feature)
        caps     = content.get("captions",{})

        # TikTok organic = video script too
        tiktok_script = (
            f"🎬 <b>TIKTOK VIDEO SCRIPT:</b>\n"
            f"Record yourself saying:\n\n"
            f"{'\"What even is xG in football?\"' if feature == 'xg_explainer' else '\"Why do accas always lose?\"'}\n"
            f"Then explain using the stats below as talking points.\n"
            f"End with: \"Follow for daily football data\"\n\n"
            f"Caption:\n<code>{caps.get('tiktok','')}</code>"
        )

        msg = (
            f"📝 <b>ORGANIC POST — no graphic needed</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"{tiktok_script}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🐦 <b>X:</b>\n<code>{caps.get('x','')}</code>\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"💬 <b>REDDIT:</b>\n<code>{caps.get('reddit','')[:400]}</code>"
        )
        await send_telegram(msg[:4096])
    except Exception as e:
        logger.error(f"Organic post error: {e}")

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

                # ── TikTok: NO betting language, video instructions ──
                tiktok_video_script = (
                    f"🎬 <b>TIKTOK VIDEO — record this now:</b>\n"
                    f"Open your camera, use text overlay:\n\n"
                    f"Text on screen: \"{home} {score} {away}\"\n"
                    f"Text: \"{minute}' — LIVE RIGHT NOW\"\n"
                    f"Text: \"xG data tracking this live\"\n"
                    f"Text: \"Who scores next?\"\n\n"
                    f"Speak or caption:\n"
                    f"<code>⚽ {home} {score} {away} — {minute}' LIVE\n"
                    f"The xG numbers are telling a different story...\n"
                    f"Follow for live football data 📊\n"
                    f"#football #live #{home.replace(' ','').lower()} #footballdata #xG</code>\n\n"
                    f"⚠️ NO betting words — TikTok will remove it"
                )

                # ── X: short reactive ──
                x_cap = (
                    f"⚽ LIVE: {home} {score} {away} ({minute}')\n"
                    f"🏆 {league}\n"
                    f"Live xG data 👉 accagenius.com\n"
                    f"#football #{home.replace(' ','')}"
                )

                # ── Instagram: polished ──
                instagram_cap = (
                    f"🔴 LIVE — {home} {score} {away}\n\n"
                    f"⏱ {minute}' | 🏆 {league}\n\n"
                    f"📊 Our AI is tracking this live — xG, shots and pressure data all updating in real time.\n\n"
                    f"🔗 Full live stats at accagenius.com (link in bio)\n\n"
                    f"#football #live #accagenius #footballstats #xG #inplay"
                )

                # ── Reddit: discussion ──
                reddit_cap = (
                    f"**LIVE: {home} {score} {away} ({minute}') — {league}**\n\n"
                    f"Anyone watching? What are you seeing on the pitch?\n\n"
                    f"xG data live at accagenius.com if anyone wants the numbers.\n\n"
                    f"Score prediction from here?"
                )

                # ── YouTube: if big match ──
                youtube_cap = (
                    f"LIVE: {home} vs {away} — {league}\n\n"
                    f"Real-time xG breakdown at accagenius.com\n"
                    f"Subscribe for live match analysis 👆\n"
                    f"#football #live #xG #accagenius"
                ) if is_big else None

                msg = (
                    f"🔴 <b>LIVE ALERT — {home} {score} {away} ({minute}')</b>\n"
                    f"🏆 {league}\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
                    f"🐦 <b>POST ON X FIRST (do this now — takes 10 secs):</b>\n"
                    f"<code>{x_cap}</code>\n\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
                    f"{tiktok_video_script}\n\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
                    f"📸 <b>INSTAGRAM caption:</b>\n"
                    f"<code>{instagram_cap}</code>\n\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
                    f"💬 <b>REDDIT post:</b>\n"
                    f"<code>{reddit_cap}</code>"
                )

                if youtube_cap:
                    msg += f"\n\n━━━━━━━━━━━━━━━━━━━━━━\n\n▶️ <b>YOUTUBE:</b>\n<code>{youtube_cap}</code>"

                msg += "\n\n━━━━━━━━━━━━━━━━━━━━━━\n⚡ <b>Post X first — always fastest for live content</b>"

                await send_telegram(msg[:4096])
                _alerted.add(alert_key)
                logger.info(f"Live alert sent: {home} vs {away} {minute}'")

    except Exception as e:
        logger.error(f"Inplay scan error: {e}")

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
