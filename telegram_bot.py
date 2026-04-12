"""
AccaGenius Telegram Approval Bot
Sends content drafts with approve/skip buttons.
Built-in anti-ban rate limiter — enforces safe posting gaps per platform.
"""
import os, json, asyncio, logging
from pathlib import Path
from datetime import datetime, timedelta
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CallbackQueryHandler, ContextTypes

TELEGRAM_TOKEN   = os.getenv("CONTENT_BOT_TOKEN","")
ADMIN_CHAT_ID    = os.getenv("CONTENT_ADMIN_CHAT_ID","")
PENDING_FILE     = "/tmp/pending_content.json"
RATE_FILE        = "/tmp/rate_limits.json"

logger = logging.getLogger(__name__)

# ── Anti-ban rate limits ─────────────────────────────────────────
# How many minutes must pass between posts on each platform
PLATFORM_COOLDOWNS = {
    "tiktok":    45,   # 45 min minimum gap
    "instagram": 180,  # 3 hours minimum gap
    "youtube":   360,  # 6 hours minimum gap
    "x":         25,   # 25 min minimum gap
    "reddit":    240,  # 4 hours minimum gap
}

# Max posts per day per platform (conservative safe limits)
DAILY_LIMITS = {
    "tiktok":    2,
    "instagram": 2,
    "youtube":   1,
    "x":         8,
    "reddit":    2,
}

PLATFORM_EMOJIS = {
    "tiktok": "🎵", "instagram": "📸",
    "youtube": "▶️", "x": "🐦", "reddit": "💬",
}

# ── Rate limit storage ───────────────────────────────────────────
def _load_rates() -> dict:
    try:
        if Path(RATE_FILE).exists():
            with open(RATE_FILE) as f:
                return json.load(f)
    except: pass
    return {}

def _save_rates(data: dict):
    try:
        with open(RATE_FILE,"w") as f:
            json.dump(data, f, indent=2)
    except: pass

def _get_today() -> str:
    return datetime.now().strftime("%Y-%m-%d")

def check_platform_safe(platform: str) -> tuple[bool, str]:
    """
    Returns (is_safe, reason_if_not).
    Checks both cooldown and daily limit.
    """
    rates   = _load_rates()
    today   = _get_today()
    p_data  = rates.get(platform, {})
    now     = datetime.now()

    # Check daily limit
    today_count = p_data.get(f"count_{today}", 0)
    daily_max   = DAILY_LIMITS.get(platform, 3)
    if today_count >= daily_max:
        return False, f"Daily limit reached ({today_count}/{daily_max} posts today)"

    # Check cooldown
    last_post = p_data.get("last_post")
    if last_post:
        last_dt  = datetime.fromisoformat(last_post)
        cooldown = PLATFORM_COOLDOWNS.get(platform, 30)
        elapsed  = (now - last_dt).total_seconds() / 60
        if elapsed < cooldown:
            wait     = int(cooldown - elapsed)
            wait_str = f"{wait}m" if wait < 60 else f"{wait//60}h {wait%60}m"
            return False, f"Too soon — wait {wait_str} (min gap: {cooldown}min)"

    return True, ""

def mark_posted(platform: str):
    """Record a post for rate limiting."""
    rates = _load_rates()
    today = _get_today()
    if platform not in rates:
        rates[platform] = {}
    rates[platform]["last_post"] = datetime.now().isoformat()
    count_key = f"count_{today}"
    rates[platform][count_key] = rates[platform].get(count_key, 0) + 1
    _save_rates(rates)

def get_platform_status() -> str:
    """Get a summary of all platform statuses for display."""
    rates = _load_rates()
    today = _get_today()
    now   = datetime.now()
    lines = ["📊 <b>Platform Status:</b>"]

    for platform in ["tiktok","instagram","youtube","x","reddit"]:
        emoji    = PLATFORM_EMOJIS.get(platform,"")
        p_data   = rates.get(platform, {})
        count    = p_data.get(f"count_{today}", 0)
        daily_max = DAILY_LIMITS[platform]
        last_str = "Never"
        next_str = "✅ Ready"

        last = p_data.get("last_post")
        if last:
            last_dt  = datetime.fromisoformat(last)
            mins_ago = int((now - last_dt).total_seconds() / 60)
            last_str = f"{mins_ago}m ago" if mins_ago < 60 else f"{mins_ago//60}h ago"
            cooldown = PLATFORM_COOLDOWNS[platform]
            elapsed  = (now - last_dt).total_seconds() / 60
            if elapsed < cooldown:
                wait = int(cooldown - elapsed)
                next_str = f"⏳ {wait}m wait"
            else:
                next_str = "✅ Ready"

        if count >= daily_max:
            next_str = f"🔴 Limit ({count}/{daily_max})"

        lines.append(f"{emoji} <b>{platform.upper()}</b>: {count}/{daily_max} today | Last: {last_str} | {next_str}")

    return "\n".join(lines)

# ── Pending content storage ──────────────────────────────────────
def _load_pending() -> dict:
    try:
        if Path(PENDING_FILE).exists():
            with open(PENDING_FILE) as f:
                return json.load(f)
    except: pass
    return {}

def _save_pending(data: dict):
    try:
        with open(PENDING_FILE,"w") as f:
            json.dump(data, f, indent=2)
    except: pass

# ── Send draft ───────────────────────────────────────────────────
async def send_draft(brief: dict, captions: dict, poster_path: str = None,
                     video_path: str = None, content_id: str = None):
    if not TELEGRAM_TOKEN or not ADMIN_CHAT_ID:
        print("[telegram] Tokens not set — skipping send")
        return

    bot        = Bot(token=TELEGRAM_TOKEN)
    content_id = content_id or f"content_{datetime.now().strftime('%H%M%S')}"
    home       = brief.get("home","")
    away       = brief.get("away","")
    league     = brief.get("league","")
    time_      = brief.get("time","TBC")
    content_type = brief.get("content_type","preview")

    # Save pending
    pending = _load_pending()
    pending[content_id] = {
        "brief": brief, "captions": captions,
        "poster": poster_path, "video": video_path, "status": "pending"
    }
    _save_pending(pending)

    # Get platform statuses
    status_block = get_platform_status()

    # Build caption preview
    cap_lines = []
    for platform in ["tiktok","instagram","x","reddit","youtube"]:
        cap = captions.get(platform,"")
        if cap:
            safe, reason = check_platform_safe(platform)
            safe_icon    = "✅" if safe else f"⏳ ({reason})"
            cap_lines.append(
                f"{PLATFORM_EMOJIS.get(platform,'')} <b>{platform.upper()}</b> {safe_icon}\n"
                f"<code>{cap[:280].strip()}</code>\n"
            )

    header = (
        f"📣 <b>NEW CONTENT DRAFT</b>\n"
        f"{'━'*22}\n"
        f"⚽ <b>{home} vs {away}</b>\n"
        f"🏆 {league}  |  🕐 {time_}\n"
        f"Type: {content_type}\n"
        f"{'━'*22}\n\n"
        + "\n".join(cap_lines) +
        f"\n{'━'*22}\n"
        + status_block
    )

    # Per-platform approve buttons (only shows if platform is ready)
    platform_btns = []
    for platform in ["tiktok","instagram","x","reddit","youtube"]:
        if captions.get(platform):
            safe, _ = check_platform_safe(platform)
            icon = PLATFORM_EMOJIS.get(platform,"")
            label = f"{icon} Post to {platform.title()}" if safe else f"⏳ {platform.title()} (wait)"
            platform_btns.append(
                InlineKeyboardButton(label, callback_data=f"post_{platform}_{content_id}")
            )

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Copy All Captions", callback_data=f"copyall_{content_id}"),
         InlineKeyboardButton("⏭ Skip",              callback_data=f"skip_{content_id}")],
        platform_btns[:2],
        platform_btns[2:4],
        platform_btns[4:],
        [InlineKeyboardButton("📊 Platform Status",  callback_data=f"status_{content_id}"),
         InlineKeyboardButton("🔄 Regenerate",       callback_data=f"regen_{content_id}")],
    ])

    # Send poster if exists
    if poster_path and Path(poster_path).exists():
        with open(poster_path,"rb") as img:
            await bot.send_photo(
                chat_id=ADMIN_CHAT_ID, photo=img,
                caption=f"🖼 {home} vs {away} — {league}"
            )

    await bot.send_message(
        chat_id=ADMIN_CHAT_ID, text=header[:4096],
        parse_mode="HTML", reply_markup=keyboard
    )

    if video_path and Path(video_path).exists():
        with open(video_path,"rb") as vid:
            await bot.send_video(
                chat_id=ADMIN_CHAT_ID, video=vid,
                caption=f"🎬 {home} vs {away}"
            )

    print(f"[telegram] Draft sent: {home} vs {away}")


# ── Callback handler ─────────────────────────────────────────────
async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query  = update.callback_query
    await query.answer()
    data   = query.data
    bot    = context.bot

    # parse action and content_id
    parts  = data.split("_", 2)
    action = parts[0]

    if action == "status":
        await bot.send_message(
            chat_id=ADMIN_CHAT_ID,
            text=get_platform_status(),
            parse_mode="HTML"
        )
        return

    if action == "skip":
        cid = parts[1] if len(parts) > 1 else ""
        pending = _load_pending()
        if cid in pending:
            pending[cid]["status"] = "skipped"
            _save_pending(pending)
        await query.edit_message_text("⏭ Skipped.")
        return

    if action == "copyall":
        cid     = parts[1] if len(parts) > 1 else ""
        pending = _load_pending()
        item    = pending.get(cid,{})
        caps    = item.get("captions",{})
        msg     = "📋 <b>All Captions — Copy &amp; Paste:</b>\n\n"
        for p,c in caps.items():
            msg += f"<b>━ {p.upper()} ━</b>\n{c}\n\n"
        # Send as new message (not edit — too long)
        await bot.send_message(chat_id=ADMIN_CHAT_ID, text=msg[:4096], parse_mode="HTML")
        return

    if action == "post":
        # post_{platform}_{content_id}
        platform = parts[1] if len(parts) > 1 else ""
        cid      = parts[2] if len(parts) > 2 else ""

        safe, reason = check_platform_safe(platform)
        if not safe:
            await bot.send_message(
                chat_id=ADMIN_CHAT_ID,
                text=(
                    f"⛔ <b>Can't post to {platform.upper()} yet</b>\n\n"
                    f"Reason: {reason}\n\n"
                    f"This protects your account from being flagged as a bot.\n"
                    f"I'll remind you when it's safe to post again."
                ),
                parse_mode="HTML"
            )
            return

        # It's safe — send the caption ready to copy
        pending = _load_pending()
        item    = pending.get(cid,{})
        caps    = item.get("captions",{})
        cap     = caps.get(platform,"Caption not found")
        brief   = item.get("brief",{})
        home    = brief.get("home",""); away=brief.get("away","")

        # Mark as posted
        mark_posted(platform)
        pending[cid].setdefault("approved_platforms",[]).append(platform)
        _save_pending(pending)

        # Work out next safe time
        cooldown   = PLATFORM_COOLDOWNS.get(platform,30)
        next_time  = (datetime.now() + timedelta(minutes=cooldown)).strftime("%H:%M")

        await bot.send_message(
            chat_id=ADMIN_CHAT_ID,
            text=(
                f"✅ <b>{platform.upper()} caption ready to post!</b>\n\n"
                f"<code>{cap}</code>\n\n"
                f"{'━'*22}\n"
                f"⏰ Next safe post time: <b>{next_time}</b>\n"
                f"📊 I'll remind you before then if you try again."
            ),
            parse_mode="HTML"
        )
        return

    await query.edit_message_text("✅ Done.")


# ── Simple message sender ────────────────────────────────────────
async def send_simple(message: str):
    if not TELEGRAM_TOKEN or not ADMIN_CHAT_ID: return
    bot = Bot(token=TELEGRAM_TOKEN)
    await bot.send_message(chat_id=ADMIN_CHAT_ID, text=message,
                           parse_mode="HTML")

async def send_rate_reminder():
    """Send a daily morning briefing on platform status."""
    if not TELEGRAM_TOKEN or not ADMIN_CHAT_ID: return
    bot = Bot(token=TELEGRAM_TOKEN)
    msg = (
        f"☀️ <b>Good morning — AccaGenius Content Engine</b>\n"
        f"{'━'*22}\n\n"
        + get_platform_status() +
        f"\n\n{'━'*22}\n"
        f"💡 Post checklist:\n"
        f"1. Reply to yesterday's comments first\n"
        f"2. Spend 5 mins engaging in your niche\n"
        f"3. Then approve today's content drafts\n\n"
        f"🤖 Morning match previews generating now..."
    )
    await bot.send_message(chat_id=ADMIN_CHAT_ID, text=msg, parse_mode="HTML")

def run_bot():
    if not TELEGRAM_TOKEN:
        print("[telegram] No CONTENT_BOT_TOKEN — bot disabled")
        return
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CallbackQueryHandler(handle_callback))
    print("[telegram] Bot running...")
    app.run_polling()

# ── X Reply approval flow ────────────────────────────────────────
async def send_reply_draft(tweet: dict, account: str, reply_draft: dict):
    """
    Send a reply draft to Telegram for approval.
    One-tap to approve and send, or skip.
    """
    if not TELEGRAM_TOKEN or not ADMIN_CHAT_ID: return
    from engine.x_replies import check_reply_safe, mark_reply_sent, get_reply_status

    bot      = Bot(token=TELEGRAM_TOKEN)
    reply    = reply_draft.get("reply","")
    ttype    = reply_draft.get("tweet_type","")
    original = reply_draft.get("original","")
    tweet_id = tweet.get("id","")
    chars    = len(reply)

    safe, reason = check_reply_safe(account)
    safe_line    = "✅ Safe to reply now" if safe else f"⛔ {reason}"

    msg = (
        f"🐦 <b>X REPLY OPPORTUNITY</b>\n"
        f"{'━'*22}\n"
        f"Account: <b>@{account}</b>\n"
        f"Tweet type: {ttype}\n\n"
        f"<b>Original tweet:</b>\n"
        f"<i>{original}</i>\n\n"
        f"{'━'*22}\n"
        f"<b>Your reply draft ({chars}/280):</b>\n\n"
        f"<code>{reply}</code>\n\n"
        f"{'━'*22}\n"
        f"{safe_line}\n\n"
        + get_reply_status()
    )

    reply_id = f"xreply_{tweet_id}_{account}"
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "✅ Post Reply" if safe else "⛔ Blocked",
                callback_data=f"xreply_post_{reply_id}"
            ),
            InlineKeyboardButton("⏭ Skip",
                callback_data=f"xreply_skip_{reply_id}"),
        ],
        [
            InlineKeyboardButton("✏️ Edit Reply",
                callback_data=f"xreply_edit_{reply_id}"),
            InlineKeyboardButton("🔄 New Draft",
                callback_data=f"xreply_regen_{reply_id}"),
        ],
    ])

    # Save pending reply
    pending = _load_pending()
    pending[reply_id] = {
        "type": "x_reply",
        "tweet_id": tweet_id,
        "account": account,
        "reply": reply,
        "safe": safe,
    }
    _save_pending(pending)

    await bot.send_message(
        chat_id=ADMIN_CHAT_ID,
        text=msg[:4096],
        parse_mode="HTML",
        reply_markup=keyboard
    )
    print(f"[telegram] X reply draft sent for @{account}")
