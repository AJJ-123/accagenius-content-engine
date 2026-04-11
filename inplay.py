"""
AccaGenius In-Play Content Engine
Monitors live matches and generates real-time content:
- Goal scored alerts
- xG pressure alerts  
- Shock result alerts
- Half-time stat drops
- Final score recaps
All with growth-optimised captions per platform.
"""

# ── In-play content types ────────────────────────────────────────
def goal_alert(m: dict) -> dict:
    home=m.get("home",""); away=m.get("away","")
    hs=m.get("home_score",0); as_=m.get("away_score",0)
    minute=m.get("minute",0); league=m.get("league","")
    scorer=m.get("scorer","")
    score=f"{hs}-{as_}"
    is_derby = m.get("is_derby",False)
    is_big   = m.get("is_big",False)

    captions = {
        "tiktok": (
            f"⚽ GOAL! {home} {hs}-{as_} {away}\n"
            f"🕐 {minute}' — {league}\n"
            f"{'🔥 Derby goal!' if is_derby else ''}\n"
            f"💬 Who wins from here? Comment 👇\n"
            f"📊 Follow for live xG alerts\n"
            f"#football #accagenius #goal #live{'#derby' if is_derby else ''}"
        ).strip(),

        "instagram": (
            f"⚽ GOAL — {minute}'\n\n"
            f"{home} {hs}-{as_} {away}\n"
            f"🏆 {league}\n\n"
            f"{'🔥 Derby drama!' if is_derby else '📊 Live xG tracking this one closely.'}\n\n"
            f"Get live xG alerts on all tonight's games 👉 accagenius.com\n"
            f"🔔 Follow for live match updates\n\n"
            f"#football #goal #live #accagenius #footballstats"
        ).strip(),

        "x": (
            f"⚽ GOAL! {home} {hs}-{as_} {away} ({minute}')\n"
            f"Live xG tracking 👉 accagenius.com\n"
            f"#football #goal #{home.replace(' ','')}"
        ).strip(),

        "reddit": (
            f"**GOAL — {home} {hs}-{as_} {away} ({minute}')**\n\n"
            f"{'Scorer: '+scorer if scorer else ''}\n\n"
            f"Who sees this one going from here? "
            f"xG stats are live on AccaGenius if anyone wants the full picture."
        ).strip(),

        "tiktok_caption": f"⚽ GOAL {minute}' — {home} {score} {away} 🔥",
    }
    return {
        "type":"goal","brief":m,"captions":captions,
        "priority":"HIGH","content_type":"live"
    }

def xg_pressure_alert(m: dict, h_xg: float, a_xg: float, xg_gap: float) -> dict:
    home=m.get("home",""); away=m.get("away","")
    hs=m.get("home_score",0); as_=m.get("away_score",0)
    minute=m.get("minute",0); league=m.get("league","")
    score=f"{hs}-{as_}"
    
    # Who's creating the pressure
    if h_xg > a_xg:
        pressure_team=home; other=away; team_xg=h_xg; team_goals=hs
    else:
        pressure_team=away; other=home; team_xg=a_xg; team_goals=as_
    
    unscored = round(team_xg - team_goals, 2)

    captions = {
        "tiktok": (
            f"🔴 XG ALERT — {minute}'\n"
            f"{home} {score} {away}\n"
            f"⚡ {pressure_team} xG: {team_xg:.1f} but only {team_goals} goal{'s' if team_goals!=1 else ''}\n"
            f"That's {unscored:.1f} xG unaccounted for 👀\n"
            f"💬 Goal coming? Drop your prediction 👇\n"
            f"📊 Follow for live xG • More in bio\n"
            f"#football #xG #accagenius #live #inplay"
        ).strip(),

        "instagram": (
            f"⚡ LIVE xG ALERT — {minute}'\n\n"
            f"⚽ {home} {score} {away}\n"
            f"🏆 {league}\n\n"
            f"📊 xG numbers:\n"
            f"  {home}: {h_xg:.1f} xG\n"
            f"  {away}: {a_xg:.1f} xG\n\n"
            f"🎯 {pressure_team} are creating chances but not converting.\n"
            f"That's {unscored:.1f} 'owed' goals based on xG model.\n\n"
            f"Live xG tracker on all tonight's games 👉 accagenius.com (link in bio)\n"
            f"#football #xG #accagenius #footballstats #live #inplay"
        ).strip(),

        "x": (
            f"⚡ xG ALERT ({minute}') — {home} {score} {away}\n"
            f"{pressure_team}: {team_xg:.1f} xG, {team_goals} goal\n"
            f"{unscored:.1f} xG unscored — goal overdue 👀\n"
            f"Live tracker 👉 accagenius.com\n"
            f"#xG #football #accagenius"
        ).strip(),

        "reddit": (
            f"**Live xG thread — {home} vs {away} ({minute}')**\n\n"
            f"Current score: {score}\n\n"
            f"xG breakdown so far:\n"
            f"- {home}: {h_xg:.1f} xG\n"
            f"- {away}: {a_xg:.1f} xG\n\n"
            f"{pressure_team} are massively underperforming their xG "
            f"({unscored:.1f} unscored). Does the model think a goal is coming?\n\n"
            f"Full live xG data on AccaGenius — accagenius.com"
        ).strip(),
    }
    return {
        "type":"xg_pressure","brief":m,"captions":captions,
        "priority":"MEDIUM","content_type":"live",
        "data":{"h_xg":h_xg,"a_xg":a_xg,"pressure_team":pressure_team,"unscored":unscored}
    }

def shock_result_alert(m: dict) -> dict:
    home=m.get("home",""); away=m.get("away","")
    hs=m.get("home_score",0); as_=m.get("away_score",0)
    minute=m.get("minute",0); league=m.get("league","")
    score=f"{hs}-{as_}"
    is_big=m.get("is_big",False)

    # Who's winning/losing unexpectedly
    if is_big and hs < as_:
        shock_line = f"{away} are WINNING at {home}!"
    elif is_big and hs > as_:
        shock_line = f"{home} dominating!"
    else:
        shock_line = f"Shock result on the cards!"

    captions = {
        "tiktok": (
            f"😱 SHOCK ALERT — {minute}'\n"
            f"{home} {score} {away}\n"
            f"⚡ {shock_line}\n"
            f"💬 Did anyone see this coming?!\n"
            f"📊 Follow + check bio for AI predictions\n"
            f"#football #shock #accagenius #live #{home.replace(' ','')}"
        ).strip(),

        "instagram": (
            f"😱 SHOCK IN PROGRESS — {minute}'\n\n"
            f"⚽ {home} {score} {away}\n"
            f"🏆 {league}\n\n"
            f"⚡ {shock_line}\n\n"
            f"Our AI model had the xG telling a different story...\n"
            f"Full live stats 👉 accagenius.com (link in bio)\n\n"
            f"#football #shock #upset #accagenius #live #footballstats"
        ).strip(),

        "x": (
            f"😱 SHOCK! {home} {score} {away} ({minute}')\n"
            f"{shock_line}\n"
            f"AI had this different 👉 accagenius.com\n"
            f"#football #{home.replace(' ','')} #shock"
        ).strip(),

        "reddit": (
            f"**[LIVE] {home} {score} {away} ({minute}') — Shock in progress?**\n\n"
            f"{shock_line}\n\n"
            f"Anyone watching? xG was pointing the other way before kick-off. "
            f"Classic case of the numbers not telling the whole story, or is this a genuine upset?\n\n"
            f"*Live xG data at accagenius.com*"
        ).strip(),
    }
    return {
        "type":"shock","brief":m,"captions":captions,
        "priority":"HIGH","content_type":"live"
    }

def halftime_drop(m: dict, h_xg: float, a_xg: float) -> dict:
    home=m.get("home",""); away=m.get("away","")
    hs=m.get("home_score",0); as_=m.get("away_score",0)
    league=m.get("league","")
    score=f"{hs}-{as_}"
    
    dominant = home if h_xg > a_xg else away
    dom_xg   = h_xg if h_xg > a_xg else a_xg
    other_xg = a_xg if h_xg > a_xg else h_xg

    captions = {
        "tiktok": (
            f"📊 HALF TIME — {home} {score} {away}\n"
            f"xG: {home} {h_xg:.1f} | {away} {a_xg:.1f}\n"
            f"⚡ {dominant} dominating on xG despite the score\n"
            f"💬 2nd half prediction? 👇\n"
            f"📊 Follow for 2nd half xG alerts\n"
            f"#football #halftime #xG #accagenius"
        ).strip(),

        "instagram": (
            f"📊 HALF TIME STATS\n\n"
            f"⚽ {home} {score} {away}\n"
            f"🏆 {league}\n\n"
            f"xG at the break:\n"
            f"  {home}: {h_xg:.1f}\n"
            f"  {away}: {a_xg:.1f}\n\n"
            f"{'⚡ ' + dominant + ' look the more dangerous side on xG despite the score.' if dom_xg > other_xg * 1.3 else '📊 Evenly matched on the numbers so far.'}\n\n"
            f"Full 2nd half AI analysis 👉 accagenius.com\n"
            f"#football #halftime #xG #accagenius #footballstats"
        ).strip(),

        "x": (
            f"📊 HT: {home} {score} {away}\n"
            f"xG: {home} {h_xg:.1f} | {away} {a_xg:.1f}\n"
            f"{dominant} look the better side on xG\n"
            f"Full stats 👉 accagenius.com\n"
            f"#football #xG #halftime"
        ).strip(),

        "reddit": (
            f"**Half time: {home} {score} {away}** — xG breakdown\n\n"
            f"45 minutes in:\n"
            f"- {home} xG: {h_xg:.1f}\n"
            f"- {away} xG: {a_xg:.1f}\n\n"
            f"{'**' + dominant + '** are creating the better chances despite what the score says.' if dom_xg > other_xg * 1.3 else 'Pretty even first half on xG.'}\n\n"
            f"What does everyone expect in the second half?\n\n"
            f"*xG data from AccaGenius live tracker — accagenius.com*"
        ).strip(),
    }
    return {
        "type":"halftime","brief":m,"captions":captions,
        "priority":"HIGH","content_type":"live",
        "data":{"h_xg":h_xg,"a_xg":a_xg,"dominant":dominant}
    }

def final_score_recap(m: dict, h_xg: float = 0, a_xg: float = 0) -> dict:
    home=m.get("home",""); away=m.get("away","")
    hs=m.get("home_score",0); as_=m.get("away_score",0)
    league=m.get("league","")
    score=f"{hs}-{as_}"
    
    # Result narrative
    if hs > as_:
        result_line=f"{home} win {score}"; winner=home
    elif as_ > hs:
        result_line=f"{away} win {score}"; winner=away
    else:
        result_line=f"Ends {score} — a draw"; winner=None

    # xG vs result verdict
    xg_verdict=""
    if h_xg > 0 and a_xg > 0:
        if hs > as_ and h_xg > a_xg: xg_verdict=f"xG backed the result — {home} {h_xg:.1f} vs {away} {a_xg:.1f}"
        elif as_ > hs and a_xg > h_xg: xg_verdict=f"xG called it — {away} {a_xg:.1f} vs {home} {h_xg:.1f}"
        elif hs > as_ and a_xg > h_xg: xg_verdict=f"Against the xG! {away} had {a_xg:.1f} xG vs {home} {h_xg:.1f}"
        elif as_ > hs and h_xg > a_xg: xg_verdict=f"Shock result — {home} had {h_xg:.1f} xG but lost"
        else: xg_verdict=f"xG: {home} {h_xg:.1f} | {away} {a_xg:.1f}"

    captions = {
        "tiktok": (
            f"🔴 FULL TIME — {home} {score} {away}\n"
            f"⚽ {result_line}\n"
            f"{'📊 ' + xg_verdict if xg_verdict else ''}\n\n"
            f"Did our AI call it? Check the full preview on accagenius.com\n"
            f"💬 Happy with the result? Comment 👇\n"
            f"📊 Follow for tomorrow's AI picks\n"
            f"#football #fulltime #accagenius #footballresults"
        ).strip(),

        "instagram": (
            f"🔴 FULL TIME\n\n"
            f"⚽ {home} {score} {away}\n"
            f"🏆 {league}\n\n"
            f"📊 Final xG: {xg_verdict}\n\n"
            f"{'Our AI model predicted this one correctly 🎯' if winner else 'The numbers had this one tight — draws happen!'}\n\n"
            f"Get tomorrow's AI predictions now 👉 accagenius.com (link in bio)\n"
            f"💬 Join our Telegram for daily picks — link in bio\n\n"
            f"#football #fulltime #accagenius #footballresults #xG #aiFootball"
        ).strip(),

        "x": (
            f"🔴 FT: {home} {score} {away}\n"
            f"{xg_verdict}\n"
            f"Tomorrow's AI picks 👉 accagenius.com\n"
            f"#football #{home.replace(' ','')} #FT"
        ).strip(),

        "reddit": (
            f"**Full Time: {home} {score} {away}** — {league}\n\n"
            f"{xg_verdict}\n\n"
            f"{'Result matched the xG model pretty well tonight.' if (hs>as_ and h_xg>a_xg) or (as_>hs and a_xg>h_xg) else 'The xG model had this going the other way — football never lies though.'}\n\n"
            f"Anyone watching? How did it feel?\n\n"
            f"*xG via AccaGenius — accagenius.com*"
        ).strip(),
    }
    return {
        "type":"final_score","brief":m,"captions":captions,
        "priority":"HIGH","content_type":"live"
    }

def site_feature_post(feature: str) -> dict:
    """Generate organic posts about AccaGenius features — no match needed."""
    
    features = {
        "xg_explainer": {
            "tiktok": (
                "📊 What even IS xG in football?\n\n"
                "xG = Expected Goals\n"
                "Every shot gets a probability score 0-1\n"
                "Based on: distance, angle, assist type, pressure\n\n"
                "A tap-in = 0.9 xG\n"
                "A 30-yard effort = 0.04 xG\n\n"
                "Add them up over 90 mins and you know who DESERVED to win 🧠\n\n"
                "💬 Did you know about xG before this?\n"
                "📊 We track xG live for every match — link in bio\n"
                "#football #xG #footballstats #accagenius #footballdata"
            ),
            "x": (
                "xG explained in 30 seconds:\n\n"
                "Every shot = probability score\n"
                "Tap-in = 0.9 | 30-yarder = 0.04\n"
                "Total xG = who deserved to win\n\n"
                "We track it live for every game 👉 accagenius.com\n"
                "#xG #football #footballstats"
            ),
            "reddit": (
                "**Quick explanation of xG for anyone new to football analytics**\n\n"
                "Expected Goals (xG) assigns a probability to every shot based on historical data:\n\n"
                "- Distance from goal\n"
                "- Angle of shot\n"
                "- Type of assist\n"
                "- Defensive pressure\n\n"
                "A penalty = ~0.76 xG. A header from 18 yards = ~0.09 xG.\n\n"
                "Add up all shots in a game and you get a much clearer picture of who actually played better than the scoreline suggests.\n\n"
                "We use this at AccaGenius to track live match quality — accagenius.com\n\n"
                "Any questions about how xG works?"
            ),
        },
        "acca_explained": {
            "tiktok": (
                "💰 Why do accas lose so much?\n\n"
                "5-fold at 2.0 odds each = 32x potential\n"
                "Probability of winning = 3.1%\n\n"
                "Most people pick accas on vibes 😅\n"
                "We use: form, xG, table position + AI model\n\n"
                "💬 Whats the biggest acca youve won?\n"
                "📊 Our AI builds smarter accas — link in bio\n"
                "#football #acca #accumulator #accagenius #footballtips"
            ),
            "x": (
                "Why accas almost always lose:\n\n"
                "5 selections at 2.0 = 32x return\n"
                "But probability = just 3.1%\n\n"
                "We built an AI that uses xG + form + table data\n"
                "to actually find value 👉 accagenius.com\n"
                "#football #acca #accagenius"
            ),
            "reddit": (
                "**Why do accumulators have such a bad reputation mathematically?**\n\n"
                "Quick maths: 5 selections at 2.0 odds each = 32x return\n\n"
                "But the actual probability of all 5 winning = 0.5^5 = 3.1%\n\n"
                "The bookmaker's margin compounds across every selection, meaning each leg you add makes the value worse exponentially.\n\n"
                "That said — if you can identify genuine value in individual selections (using xG, form, statistical edge), accas become more defensible.\n\n"
                "We try to do exactly that at AccaGenius — data-driven selection rather than gut feel. Anyone here build accas with a systematic approach?"
            ),
        },
        "telegram_cta": {
            "tiktok": (
                "📱 Where do I post my daily picks?\n\n"
                "✅ Free Telegram channel\n"
                "✅ AI-generated accas every morning\n"
                "✅ Live xG alerts mid-match\n"
                "✅ BTTS + Over 2.5 value picks\n\n"
                "Zero spam. Just data.\n\n"
                "💬 What time do you check your tips?\n"
                "🔗 Link in bio to join free\n"
                "#football #telegram #footballtips #accagenius #freetips"
            ),
            "x": (
                "Free Telegram for daily AI football picks:\n\n"
                "✅ Morning acca every day\n"
                "✅ Live xG alerts\n"
                "✅ BTTS/Over 2.5 value picks\n\n"
                "Join 👉 accagenius.com (link in bio)\n"
                "#football #footballtips #accagenius"
            ),
        },
    }

    content = features.get(feature, features["xg_explainer"])
    return {
        "type": "feature_post",
        "feature": feature,
        "captions": content,
        "priority": "LOW",
        "content_type": "organic",
    }
