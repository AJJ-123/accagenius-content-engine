"""
AccaGenius Content Scheduler v2
"""
import asyncio, logging, sys, os

# Fix module path — must be before any local imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
import pytz

logging.basicConfig(level=logging.INFO, format="%(asctime)s [scheduler] %(message)s")
logger = logging.getLogger(__name__)
LONDON = pytz.timezone("Europe/London")

async def scheduler_loop():
    morning_done = afternoon_done = organic_done = ""
    logger.info("✅ AccaGenius scheduler started")

    while True:
        try:
            now   = datetime.now(LONDON)
            today = now.strftime("%Y-%m-%d")
            h, m  = now.hour, now.minute

            # 08:30 — Morning match previews
            if h==8 and m>=30 and morning_done != today:
                morning_done = today
                logger.info("Running morning job...")
                from jobs.run import run_morning_job
                await run_morning_job(render_videos=False, max_posts=4)

            # 12:00 — Organic caption post
            if h==12 and m<5 and organic_done != today:
                organic_done = today
                logger.info("Running organic post...")
                from jobs.run import run_organic_post
                await run_organic_post()

            # 16:00 — Afternoon with videos
            if h==16 and m<5 and afternoon_done != today:
                afternoon_done = today
                logger.info("Running afternoon job...")
                from jobs.run import run_morning_job
                await run_morning_job(render_videos=True, max_posts=2)

            # In-play scan every 3 mins 12:00-23:00
            if 12 <= h <= 23 and m % 3 == 0:
                try:
                    from jobs.run import run_inplay_scan
                    await run_inplay_scan()
                except Exception as e:
                    logger.error(f"Inplay scan error: {e}")

            # X reply scan every 15 mins 8:00-23:00
            if 8 <= h <= 23 and m % 15 == 0:
                try:
                    from jobs.run import run_x_reply_scan
                    await run_x_reply_scan()
                except Exception as e:
                    logger.error(f"X reply scan error: {e}")

        except Exception as e:
            logger.error(f"Scheduler loop error: {e}")

        await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(scheduler_loop())
