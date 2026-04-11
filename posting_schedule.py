"""
AccaGenius — Complete Posting Schedule & Anti-Ban Strategy
Platform-by-platform timings, content mix, and growth tactics.
"""

# ══════════════════════════════════════════════════════════════════
# THE GOLDEN RULES (read before anything else)
# ══════════════════════════════════════════════════════════════════
#
# 1. NEVER post the same caption on two platforms at the same time
# 2. NEVER post more than 3x per day when starting out (first 4 weeks)
# 3. ALWAYS wait 20-40 mins between posts on the SAME platform
# 4. ENGAGE before you post — reply to comments first, then post
# 5. Vary your wording even for the same match — bots repeat, humans don't
# 6. Your first comment on your own post should be a question
#    — this tricks algorithms into boosting it for "discussion"
# ══════════════════════════════════════════════════════════════════

SCHEDULE = {

    # ══════════════════════════════════════════════════════════════
    # TIKTOK
    # Best times: 7-9am, 12-2pm, 7-9pm UK
    # Safe daily limit: 1-3 posts
    # New account: max 1 post/day for first 2 weeks
    # Anti-ban: don't post same video twice, vary captions every time
    # ══════════════════════════════════════════════════════════════
    "tiktok": {
        "weekly_schedule": {
            "Monday":    ["07:30 — Weekly preview/stats post",
                          "20:00 — Monday Night Football live caption if applicable"],
            "Tuesday":   ["12:30 — xG explainer or educational post"],
            "Wednesday": ["07:30 — Midweek fixtures preview",
                          "20:30 — Champions League live caption"],
            "Thursday":  ["12:00 — Recap midweek results + xG verdict"],
            "Friday":    ["07:30 — Weekend preview — big fixtures",
                          "18:00 — Acca tip teaser"],
            "Saturday":  ["08:30 — Saturday matches preview",
                          "14:30 — Live caption during 3pm kickoffs",
                          "22:00 — Saturday results recap"],
            "Sunday":    ["11:30 — Sunday fixtures preview",
                          "20:00 — Sunday result recap"],
        },
        "content_mix": {
            "40%": "Match previews (stats, form, AI pick)",
            "25%": "Educational (xG explainer, how accas work, stat explainers)",
            "20%": "Live match captions (goals, HT stats, FT recap)",
            "15%": "CTA posts (join Telegram, link in bio)",
        },
        "anti_ban_rules": [
            "New account: max 1 post per day for first 14 days",
            "After 2 weeks: max 2 posts per day",
            "After 4 weeks: max 3 posts per day",
            "Wait 30+ mins between posts",
            "Don't post if you haven't been on the app for 2+ days",
            "Spend 10 mins watching/liking football content before posting",
            "Reply to ALL comments within 1 hour of posting",
            "Your first comment on your own post: ask a question",
            "Never use the same hashtag set twice in a row",
            "Vary caption slightly every time even same match",
        ],
        "first_comment_examples": [
            "What's your score prediction? 👇",
            "Who you backing here? 🤔",
            "Drop your acca below 👇",
            "Think the AI got this right?",
        ],
    },

    # ══════════════════════════════════════════════════════════════
    # INSTAGRAM
    # Best times: 8-10am, 12-1pm, 7-9pm UK
    # Safe daily limit: 1-2 posts + 3-5 Stories
    # Reels > carousels > single images for reach
    # ══════════════════════════════════════════════════════════════
    "instagram": {
        "weekly_schedule": {
            "Monday":    ["08:00 — Weekly fixtures graphic/caption",
                          "Story: Poll — who wins Monday Night?"],
            "Tuesday":   ["No main post — Stories only",
                          "Story: xG stat of the day"],
            "Wednesday": ["12:00 — Midweek preview post",
                          "Story: Champions League teams graphic"],
            "Thursday":  ["No main post — engage with comments/Stories only"],
            "Friday":    ["08:30 — Weekend preview post",
                          "Story: Acca of the day teaser"],
            "Saturday":  ["09:00 — Saturday matchday poster",
                          "Story: Live score updates during 3pm games",
                          "21:00 — Results recap caption"],
            "Sunday":    ["10:00 — Sunday feature match post",
                          "Story: FPL/stats content"],
        },
        "stories_schedule": {
            "daily": [
                "Morning: Today's top fixture stat (1 slide)",
                "Afternoon: Poll — who wins tonight?",
                "Evening: Result + xG verdict",
            ],
            "note": "Stories don't count toward post limits — use them daily"
        },
        "content_mix": {
            "35%": "Match previews with poster graphics",
            "30%": "Stories (polls, questions, live scores)",
            "20%": "Educational stat posts (xG, form, league tables)",
            "15%": "Telegram CTA + site traffic posts",
        },
        "anti_ban_rules": [
            "Never post more than 2 feed posts per day",
            "Gap between posts: minimum 3 hours",
            "Don't follow more than 20 new accounts per day",
            "Don't unfollow more than 20 per day",
            "Use 10-15 hashtags max (not 30 — that's a spam signal)",
            "Mix popular and niche hashtags: 3 big (1M+), 4 medium, 4 small",
            "Don't copy-paste the same caption twice",
            "Respond to comments within 2 hours",
            "Like 10-15 posts in your niche before posting",
            "Use Stories daily even when not posting to feed",
        ],
        "hashtag_sets": {
            "set_a_matchday": "#football #premierleague #footballstats #xG #accagenius #footballanalysis #matchday #footballdata #accas #footballbetting",
            "set_b_general": "#football #footballnerd #xG #accagenius #statsgeek #footballtips #soccer #footballlovers #dailytips #footballpredictions",
            "set_c_live": "#footballlive #goals #premierleague #football #xG #live #accagenius #inplay #footballscores #livefoootball",
        },
        "note": "Rotate hashtag sets — don't use same set twice in a row"
    },

    # ══════════════════════════════════════════════════════════════
    # X / TWITTER
    # Best times: 8-10am, 12-2pm, 5-7pm, 9-11pm UK
    # Safe daily limit: 5-10 tweets (platform expects high frequency)
    # Most forgiving platform for posting frequency
    # ══════════════════════════════════════════════════════════════
    "x": {
        "weekly_schedule": {
            "Monday":    ["08:00 — Week ahead fixtures",
                          "12:00 — xG fact/stat",
                          "20:30 — Live match updates"],
            "Tuesday":   ["09:00 — Yesterday's xG verdict",
                          "18:00 — Midweek preview"],
            "Wednesday": ["08:30 — Midweek matches",
                          "Live tweet CL match if big fixture",
                          "22:30 — FT reaction"],
            "Thursday":  ["10:00 — Stats recap",
                          "18:00 — Weekend teaser"],
            "Friday":    ["08:00 — Weekend big fixtures",
                          "12:00 — Acca tip",
                          "18:00 — AI pick reveal"],
            "Saturday":  ["08:30 — Morning picks",
                          "Live tweet 12:30 KO",
                          "14:45 — 3pm fixtures preview",
                          "Live tweet 3pm KOs",
                          "17:30 — 5:30 preview",
                          "22:00 — Day recap"],
            "Sunday":    ["10:00 — Sunday preview",
                          "Live tweet big game",
                          "22:00 — Weekend wrap"],
        },
        "content_mix": {
            "40%": "Live match reactions and stats",
            "25%": "Match previews (short, punchy)",
            "20%": "Stat facts / xG insights",
            "15%": "Replies to big football accounts",
        },
        "anti_ban_rules": [
            "X is most forgiving — 5-10 posts per day is fine",
            "NEVER automate follows/unfollows on X — instant ban",
            "Don't post same link more than 3x per day",
            "Engage with big football accounts daily (reply genuinely)",
            "Reply to trending football hashtags — this gets you seen",
            "Don't make every tweet a link — mix link and no-link posts",
            "Live-tweeting a match is fine and encouraged",
        ],
        "growth_hack": "Reply to viral football tweets with a stat or insight. Don't self-promo — just add value. People click your profile.",
    },

    # ══════════════════════════════════════════════════════════════
    # REDDIT
    # Strictest platform — needs most careful handling
    # Safe post limit: 1 per subreddit per day MAX
    # New account: lurk and comment for 2 weeks before any posts
    # ══════════════════════════════════════════════════════════════
    "reddit": {
        "weekly_schedule": {
            "Monday":    ["r/footballbetting — Weekly tips discussion (text only)",
                          "r/PremierLeague — Comment on match threads"],
            "Tuesday":   ["Comment only day — no posts",
                          "Reply to 5-10 threads genuinely"],
            "Wednesday": ["r/soccer — Midweek reaction/discussion post",
                          "r/AccaGenius — Post full analysis"],
            "Thursday":  ["Comment only day"],
            "Friday":    ["r/PremierLeague or r/Championship — Weekend preview"],
            "Saturday":  ["r/AccaGenius — Saturday results + xG breakdown",
                          "Comment in live match threads on r/PremierLeague"],
            "Sunday":    ["r/footballbetting or r/soccerbetting — Weekly reflection"],
        },
        "subreddits": {
            "r/PremierLeague":     "Big audience, post match discussions OK, no self-promo",
            "r/soccer":            "General football, stat posts do well, no self-promo",
            "r/footballbetting":   "Allows tips and analysis, but avoid hard sells",
            "r/Championship":      "Less saturated, good for EFL content",
            "r/AccaGenius":        "Your own sub — post everything here freely",
            "r/sportsbook":        "US-friendly, international bettors, allows site links",
            "r/fantasypremierleague": "xG and form stats VERY welcome here",
        },
        "anti_ban_rules": [
            "NEVER post a link on a new account — instant shadowban",
            "Build 100+ karma before ANY self-promotion",
            "Max 1 post per subreddit per day",
            "Always lead with VALUE — stat, analysis, discussion point",
            "Only mention AccaGenius naturally in comments when relevant",
            "Use text posts more than link posts on most subs",
            "Read each sub's rules before posting — every sub is different",
            "Don't delete and repost — Reddit penalises this",
            "Post at peak times: 8-10am or 7-9pm UK on weekdays",
            "Saturday 9am-12pm is peak Reddit football time",
        ],
        "safe_mention_template": (
            "End posts with: 'I track this using AccaGenius — accagenius.com' "
            "only after establishing value in the post. Never as the opener."
        ),
    },

    # ══════════════════════════════════════════════════════════════
    # YOUTUBE SHORTS
    # Best times: 8-10am, 12-2pm, 8-10pm UK
    # Safe daily limit: 1 Short per day
    # ══════════════════════════════════════════════════════════════
    "youtube": {
        "weekly_schedule": {
            "Monday":    ["09:00 — Weekly big fixtures Short"],
            "Wednesday": ["09:00 — Midweek preview Short"],
            "Friday":    ["09:00 — Weekend preview Short"],
            "Saturday":  ["22:00 — Results recap Short (after all games)"],
        },
        "content_mix": {
            "50%": "Match previews (poster-style video with stats)",
            "30%": "Educational (xG explainers, how AI picks work)",
            "20%": "Results recaps (FT score + xG verdict)",
        },
        "anti_ban_rules": [
            "1 Short per day MAX to start",
            "Title must contain searchable keywords: team names, league, 'xG'",
            "First line of description is critical for SEO",
            "Always add accagenius.com as first link in description",
            "Pin a comment with your Telegram link",
            "Use chapters if over 60 seconds",
            "Don't just repost TikTok watermarked videos to Shorts",
        ],
        "description_template": (
            "{HOME} vs {AWAY} — AI xG Preview | {LEAGUE}\n\n"
            "Full AI predictions and value bets: https://accagenius.com\n"
            "Join our free Telegram for daily picks: {TELEGRAM_LINK}\n\n"
            "{STATS_SUMMARY}\n\n"
            "Subscribe for daily xG analysis and AI-powered football predictions.\n\n"
            "#football #{HOME} #{AWAY} #{LEAGUE} #xG #accagenius #footballpredictions"
        ),
    },
}

# ══════════════════════════════════════════════════════════════════
# CAPTION-ONLY CONTENT IDEAS (no poster or video needed)
# These can be posted any time — pure text content for engagement
# ══════════════════════════════════════════════════════════════════
CAPTION_ONLY_IDEAS = [

    # Educational series — very high engagement
    {
        "title": "xG Explained",
        "platforms": ["tiktok","instagram","x","reddit"],
        "caption_tiktok": (
            "📊 Why xG is the most underrated football stat\n\n"
            "2019 Liverpool beat Barcelona 4-0\n"
            "xG said it should have been 3-1\n"
            "The numbers told the story before the game ended\n\n"
            "We track xG LIVE for every match at accagenius.com\n\n"
            "💬 What's your opinion on xG — useful or overrated?\n"
            "📊 Follow for daily xG breakdowns\n"
            "#football #xG #accagenius #footballstats #analytics"
        ),
    },
    {
        "title": "Acca Loss Maths",
        "platforms": ["tiktok","instagram","x"],
        "caption_tiktok": (
            "💸 Why your 5-fold acca always loses — the maths\n\n"
            "5 bets at 2.0 each = 32x return 🤩\n"
            "Actual probability of winning = 3.1% 😬\n\n"
            "Most people pick accas based on:\n"
            "❌ Their favourite teams\n"
            "❌ Recent memory\n"
            "❌ Gut feeling\n\n"
            "We use: form data + xG + table position + AI model\n\n"
            "💬 Biggest acca you've ever won? 👇\n"
            "🔗 Try our AI acca builder — link in bio\n"
            "#football #acca #accumulator #accagenius #footballtips"
        ),
    },
    {
        "title": "Live xG Alert Caption",
        "platforms": ["x","instagram","tiktok"],
        "caption_tiktok": (
            "🔴 LIVE — {HOME} vs {AWAY}\n\n"
            "Score: {SCORE} ({MINUTE}')\n"
            "xG: {HOME} {H_XG} | {AWAY} {A_XG}\n\n"
            "The numbers are saying a goal is coming ⚡\n\n"
            "Get live xG alerts on your phone 👉 link in bio\n"
            "#football #live #xG #accagenius #inplay"
        ),
    },
    {
        "title": "Derby Day Hype Caption",
        "platforms": ["all"],
        "caption_tiktok": (
            "🔥 DERBY DAY — {HOME} vs {AWAY}\n\n"
            "Stats don't matter today right? 😅\n\n"
            "Actually our AI says:\n"
            "📊 {HOME} xG avg: {H_XG}\n"
            "📊 {AWAY} xG avg: {A_XG}\n"
            "🎯 Prediction: {PREDICTION}\n\n"
            "💬 What's YOUR prediction? 👇\n"
            "📊 Full breakdown at accagenius.com — link in bio\n"
            "#football #derby #accagenius #xG #matchday"
        ),
    },
    {
        "title": "Site Feature CTA — No Match Needed",
        "platforms": ["tiktok","instagram"],
        "caption_tiktok": (
            "📱 What AccaGenius actually does:\n\n"
            "✅ AI-generated accas every morning\n"
            "✅ Live xG tracking mid-match\n"
            "✅ BTTS + Over 2.5 value picks daily\n"
            "✅ Form data across 34 leagues\n"
            "✅ Free Telegram with daily alerts\n\n"
            "All free. No spam.\n\n"
            "💬 What's your biggest football data need?\n"
            "🔗 Link in bio\n"
            "#football #accagenius #footballtips #xG #freetips"
        ),
    },
    {
        "title": "Shock Result Reaction",
        "platforms": ["x","tiktok","instagram"],
        "caption_tiktok": (
            "😱 {TEAM} just lost to {OPPONENT}?!\n\n"
            "xG said {XG_LINE}\n\n"
            "This is why football is football 🤷\n"
            "The AI doesn't always win — but the data is always honest\n\n"
            "💬 Did you have {TEAM} in your acca tonight?\n"
            "📊 Tomorrow's AI picks live at accagenius.com\n"
            "#football #shock #accagenius #footballresults"
        ),
    },
    {
        "title": "Weekend Acca Teaser",
        "platforms": ["tiktok","instagram","x"],
        "caption_tiktok": (
            "🤖 Our AI just built this weekend's acca...\n\n"
            "📊 Based on:\n"
            "Form across 34 leagues ✅\n"
            "xG averages ✅\n"
            "FBD probability model ✅\n"
            "Table position edge ✅\n\n"
            "Results Monday.\n\n"
            "💬 What's YOUR acca this weekend?\n"
            "🔗 Get the full AI pick — link in bio\n"
            "#football #acca #accagenius #weekendacca #footballtips"
        ),
    },
]

# ══════════════════════════════════════════════════════════════════
# WEEKLY GROWTH ROUTINE (what to do each day — 20 mins max)
# ══════════════════════════════════════════════════════════════════
DAILY_ROUTINE = {
    "7:00am": "Check content engine Telegram — approve morning drafts",
    "8:30am": "Post approved content (TikTok first, then Instagram, 20 min gap)",
    "9:00am": "Spend 10 mins engaging: reply to comments, like/reply in niche",
    "12:00pm": "Post X caption (match stat or xG fact — no graphic needed)",
    "1:00pm":  "Check for live matches starting — approve any live content drafts",
    "During match": "Post X live updates (goals, HT stats) — most engagement here",
    "Full time": "Post FT recap caption on X and Instagram Story",
    "9:00pm": "Reply to all comments from today's posts before sleeping",
    "Note": "Total active time per day: ~20-30 minutes",
}

# ══════════════════════════════════════════════════════════════════
# PLATFORM GROWTH SPEED EXPECTATIONS (realistic)
# ══════════════════════════════════════════════════════════════════
GROWTH_TIMELINE = {
    "Week 1-2": "Build posting habit. 0-50 followers. Focus on consistency not virality.",
    "Week 3-4": "First 100 followers. One post should do better than others — double down on that format.",
    "Month 2":  "100-500 followers if consistent. First viral post possible from a shock result or Derby Day post.",
    "Month 3":  "500-2000 followers. Algorithm starts recommending you. Telegram starts growing.",
    "Month 6":  "2000-10000+ followers. Content engine running daily. Some Telegram conversions to paid.",
    "Key insight": "Shock results and Derby Day posts get 10x the engagement of regular previews. Always post these.",
}
PYEOF
echo "✅ posting_schedule.py written"