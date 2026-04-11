"""
AccaGenius Content Engine — Main Job v2
Handles: match previews, in-play alerts, FT recaps, caption-only posts
"""
import os, asyncio, random, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from datetime import datetime
from pathlib import Path

from engine.data      import get_all_data, get_live_matches
from engine.decisions import find_content_opportunities, generate_captions
from engine.inplay    import (goal_alert, xg_pressure_alert, shock_result_alert,
                               halftime_drop, final_score_recap, site_feature_post)
from renderer.poster  import render_match_poster
from renderer.video   import render_video
from jobs.telegram_bot import send_draft, send_simple

OUTPUT_DIR = os.getenv("OUTPUT_DIR", "/tmp/accagenius-content")

# Track what we've already alerted on
_alerted = set()

async def run_morning_job(render_videos=False, max_posts=4):
    """08:30 run — match previews for today."""
    today = datetime.now().strftime("%Y-%m-%d")
    print(f"\n[job] Morning run — {today}")
    await send_simple(f"🌅 <b>Morning content run starting</b>\n📅 {today}")

    data   = get_all_data()
    briefs = find_content_opportunities(data)
    print(f"[job] {len(briefs)} opportunities found")

    if not briefs:
        await send_simple("📭 No strong content opportunities today.")
        return

    count = 0
    for brief in briefs[:max_posts]:
        home  = brief["home"]; away  = brief["away"]
        slug  = f"{home}_{away}_{today}".replace(" ","_")
        path  = f"{OUTPUT_DIR}/{slug}"
        Path(path).mkdir(parents=True, exist_ok=True)

        poster_path = None
        try:
            poster_path = render_match_poster(brief, f"{path}/poster.png")
        except Exception as e:
            print(f"[job] Poster error: {e}")

        video_path = None
        if render_videos:
            try:
                video_path = render_video(brief, f"{path}/video.mp4")
            except Exception as e:
                print(f"[job] Video error: {e}")

        try:
            await send_draft(brief, brief.get("captions",{}),
                             poster_path, video_path, content_id=slug)
            count += 1
        except Exception as e:
            print(f"[job] Send error: {e}")

    await send_simple(f"✅ Morning run done — {count} drafts sent")


async def run_inplay_scan():
    """
    Scan live matches every 3 mins.
    Fires goal alerts, xG alerts, HT drops, FT recaps.
    Caption-only — no image needed.
    """
    live = get_live_matches()
    if not live:
        return

    alerts = []
    for m in live:
        mid    = m.get("id", f"{m.get('home')}_{m.get('away')}")
        minute = m.get("minute", 0) or 0
        status = m.get("status","")
        hs     = m.get("home_score",0) or 0
        as_    = m.get("away_score",0) or 0
        h_xg   = float(m.get("h_xg", 0) or 0)
        a_xg   = float(m.get("a_xg", 0) or 0)

        # ── Goal alert ────────────────────────────────────────
        goal_key = f"goal_{mid}_{hs}_{as_}"
        if goal_key not in _alerted and (hs + as_ > 0):
            prev_key_base = f"goal_{mid}_"
            prev_goals = sum(1 for k in _alerted if k.startswith(prev_key_base))
            if prev_goals < (hs + as_):  # new goal scored
                alerts.append(goal_alert(m))
                _alerted.add(goal_key)

        # ── xG pressure ──────────────────────────────────────
        if h_xg > 0 and a_xg > 0 and minute >= 40:
            xg_gap    = abs(h_xg - a_xg)
            total_xg  = h_xg + a_xg
            total_goals = hs + as_
            xg_unscored = total_xg - total_goals
            xg_key = f"xg_{mid}_{hs}_{as_}_{int(xg_unscored*10)}"
            if (xg_unscored >= 1.0 and xg_key not in _alerted):
                alerts.append(xg_pressure_alert(m, h_xg, a_xg, xg_gap))
                _alerted.add(xg_key)

        # ── Shock result ──────────────────────────────────────
        shock_key = f"shock_{mid}_{hs}_{as_}"
        is_big = m.get("is_big", False)
        if (is_big and minute >= 60 and shock_key not in _alerted):
            if (hs < as_ and m.get("home_is_favorite")) or \
               (as_ < hs and m.get("away_is_favorite")):
                alerts.append(shock_result_alert(m))
                _alerted.add(shock_key)

        # ── Half time drop ────────────────────────────────────
        ht_key = f"ht_{mid}"
        if status == "HT" and ht_key not in _alerted:
            if h_xg > 0 or a_xg > 0:
                alerts.append(halftime_drop(m, h_xg, a_xg))
                _alerted.add(ht_key)

        # ── Full time recap ───────────────────────────────────
        ft_key = f"ft_{mid}"
        if status in ("FT","AET","PEN") and ft_key not in _alerted:
            alerts.append(final_score_recap(m, h_xg, a_xg))
            _alerted.add(ft_key)

    # Send all alerts
    for alert in alerts:
        try:
            brief    = alert.get("brief", {})
            captions = alert.get("captions", {})
            atype    = alert.get("type","alert")
            home     = brief.get("home",""); away=brief.get("away","")
            score    = f"{brief.get('home_score',0)}-{brief.get('away_score',0)}"
            minute   = brief.get("minute",0)

            msg = (
                f"🔴 <b>LIVE ALERT — {atype.upper().replace('_',' ')}</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"⚽ <b>{home} {score} {away}</b>  {minute}'\n\n"
            )
            for platform, cap in captions.items():
                if platform in ("tiktok","x","instagram","reddit"):
                    msg += f"<b>📱 {platform.upper()}:</b>\n{cap[:400]}\n\n"

            await send_simple(msg[:4096])
            print(f"[inplay] Sent {atype} alert: {home} vs {away} {minute}'")

        except Exception as e:
            print(f"[inplay] Alert send error: {e}")


async def run_organic_post():
    """
    Send a caption-only organic post once daily (no match needed).
    Rotates through: xG explainer, acca maths, feature CTAs, Telegram CTA.
    """
    features  = ["xg_explainer","acca_explained","telegram_cta"]
    day_index = datetime.now().weekday()  # 0=Monday
    feature   = features[day_index % len(features)]

    content = site_feature_post(feature)
    captions = content.get("captions", {})

    msg = (
        f"📝 <b>ORGANIC POST — {feature.upper().replace('_',' ')}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"No graphic needed — caption only\n\n"
    )
    for platform, cap in captions.items():
        msg += f"<b>📱 {platform.upper()}:</b>\n{cap}\n\n{'─'*16}\n\n"

    await send_simple(msg[:4096])
    print(f"[organic] Sent organic caption: {feature}")


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["morning","inplay","organic","test"], default="morning")
    parser.add_argument("--videos", action="store_true")
    args = parser.parse_args()

    if args.mode == "morning":
        asyncio.run(run_morning_job(render_videos=args.videos))
    elif args.mode == "inplay":
        asyncio.run(run_inplay_scan())
    elif args.mode == "organic":
        asyncio.run(run_organic_post())
    elif args.mode == "test":
        asyncio.run(send_simple("✅ AccaGenius Content Engine — test message OK"))

if __name__ == "__main__":
    main()


async def run_x_reply_scan():
    """
    Scan target accounts for tweetable moments.
    Fires reply drafts to Telegram — you approve before anything posts.
    Runs every 15 mins during peak hours (8am-11pm).
    Requires X_BEARER_TOKEN in Railway env vars.
    """
    bearer = os.getenv("X_BEARER_TOKEN","")
    if not bearer:
        return  # silently skip if no X API token set

    from engine.x_replies import (TARGET_ACCOUNTS, fetch_recent_tweets,
                                   build_reply, check_reply_safe)
    from jobs.telegram_bot import send_reply_draft

    # Track seen tweet IDs so we don't draft the same tweet twice
    seen_file = f"{OUTPUT_DIR}/seen_tweets.json"
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    try:
        seen = json.load(open(seen_file)) if Path(seen_file).exists() else []
    except: seen = []

    new_seen   = list(seen)
    drafts_sent = 0

    # Only scan priority 1 and 2 accounts per run (avoid hammering API)
    targets = [a for a in TARGET_ACCOUNTS if a["priority"] <= 2]

    for account_info in targets[:5]:  # max 5 accounts per scan
        account = account_info["handle"]
        safe, _ = check_reply_safe(account)
        if not safe: continue

        tweets = await fetch_recent_tweets(account, bearer)
        for tweet in tweets[:2]:  # max 2 tweets per account
            tid = tweet.get("id","")
            if tid in seen: continue

            # Only reply to tweets with decent engagement
            metrics = tweet.get("public_metrics",{})
            if metrics.get("like_count",0) < 50: continue

            text  = tweet.get("text","")
            draft = build_reply(text, account)
            await send_reply_draft(tweet, account, draft)
            new_seen.append(tid)
            drafts_sent += 1

            # Max 2 reply drafts per scan run
            if drafts_sent >= 2:
                break
        if drafts_sent >= 2:
            break

        await asyncio.sleep(2)  # small gap between account fetches

    # Save seen tweet IDs (keep last 500)
    try:
        with open(seen_file,"w") as f:
            json.dump(new_seen[-500:], f)
    except: pass
