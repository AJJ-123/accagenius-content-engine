"""
AccaGenius Content Decision Engine v2
Growth-optimised: every caption has a conversion path.
"""

BIG_CLUBS = {
    "manchester city","manchester united","liverpool","arsenal","chelsea",
    "tottenham","newcastle","aston villa","west ham","real madrid","barcelona",
    "atletico madrid","juventus","ac milan","inter milan","bayern munich",
    "borussia dortmund","paris saint-germain","psg","galatasaray","fenerbahce",
}

DERBY_PAIRS = [
    {"manchester city","manchester united"}, {"liverpool","everton"},
    {"arsenal","tottenham"}, {"chelsea","arsenal"}, {"chelsea","tottenham"},
    {"rangers","celtic"}, {"atletico madrid","real madrid"},
    {"barcelona","real madrid"}, {"ac milan","inter milan"},
    {"juventus","inter milan"}, {"barcelona","espanyol"},
]

def _is_derby(home, away):
    h,a = home.lower(), away.lower()
    for pair in DERBY_PAIRS:
        if any(p in h for p in pair) and any(p in a for p in pair):
            return True
    return False

def _is_big(home, away):
    h,a = home.lower(), away.lower()
    return any(b in h for b in BIG_CLUBS) or any(b in a for b in BIG_CLUBS)

def _title(home, away, league, is_derby, is_big):
    ll = (league or "").lower()
    if is_derby: return "DERBY DAY!"
    if "champions" in ll: return "CHAMPIONS LEAGUE"
    if "premier"   in ll: return "TOP HALF CLASH" if is_big else "PREMIER LEAGUE"
    if "bundesliga" in ll: return "BUNDESLIGA CLASH"
    if "la liga"    in ll or "primera" in ll: return "LA LIGA CLASH"
    if "serie a"    in ll: return "SERIE A SHOWDOWN"
    if "ligue 1"    in ll: return "LIGUE 1 BATTLE"
    return "MATCHDAY"

def score_fixture(m, fbd_data=None):
    home=m.get("home",""); away=m.get("away","")
    league=m.get("league",""); time_=m.get("time","TBC")
    status=m.get("status","NS")
    if status in ("FT","AET","PEN"): return None

    score=0; is_derby=_is_derby(home,away); is_big_m=_is_big(home,away)
    if is_derby: score+=40
    if is_big_m: score+=20

    fbd_match=None
    if fbd_data:
        for ftype in ("btts","over25"):
            for item in fbd_data.get(ftype,[]):
                ih=item.get("home","").lower(); ia=item.get("away","").lower()
                if home.lower()[:5] in ih or ih[:5] in home.lower()[:5]:
                    fbd_match=item
                    prob=item.get("btts_prob") or item.get("over25_prob") or 0
                    if float(prob)>=65: score+=15
                    break

    if score < 15 and not is_derby and not is_big_m: return None

    return {
        "home":home,"away":away,"league":league,"time":time_,
        "title":_title(home,away,league,is_derby,is_big_m),
        "is_derby":is_derby,"is_big":is_big_m,"score":score,
        "fbd":fbd_match,"fixture_id":m.get("id"),
        "home_logo":m.get("home_logo",""),"away_logo":m.get("away_logo",""),
        "home_id":m.get("home_id",0),"away_id":m.get("away_id",0),
        "league_id":m.get("league_id",0),
        "fbd_prediction":m.get("fbd_prediction",""),
        "fbd_btts":m.get("fbd_btts"),"fbd_over25":m.get("fbd_over25"),
        # defaults — overridden by form enrichment
        "home_form":"WWWDLW","away_form":"LDWWDL",
        "home_xg":"1.8","away_xg":"1.1",
        "home_xg_up":True,"away_xg_up":False,
    }

# ── Growth-optimised captions ────────────────────────────────────
def _stat_line(brief):
    lines=[]
    if brief.get("fbd_btts"):   lines.append(f"BTTS: {int(float(brief['fbd_btts']))}%")
    if brief.get("fbd_over25"): lines.append(f"Over 2.5: {int(float(brief['fbd_over25']))}%")
    pred=brief.get("fbd_prediction","")
    if pred:
        home=brief.get("home",""); away=brief.get("away","")
        label={"H":f"{home} win","A":f"{away} win","D":"Draw"}.get(pred.upper(),pred)
        lines.append(f"AI tip: {label}")
    return " | ".join(lines) if lines else ""

def generate_captions(brief):
    home=brief.get("home",""); away=brief.get("away","")
    league=brief.get("league",""); time_=brief.get("time","TBC")
    title=brief.get("title","MATCHDAY"); is_derby=brief.get("is_derby",False)
    stat=_stat_line(brief)
    hxg=brief.get("home_xg","?"); axg=brief.get("away_xg","?")
    h_rank=brief.get("home_rank",""); a_rank=brief.get("away_rank","")
    h_pts=brief.get("home_pts",""); a_pts=brief.get("away_pts","")

    rank_line=""
    if h_rank and a_rank:
        rank_line=f"#{h_rank} {home} ({h_pts}pts) vs #{a_rank} {away} ({a_pts}pts)\n"

    # ── TikTok — hook → engagement → follow CTA ──────────────
    tiktok=(
        f"🔥 {title} — {home} vs {away}!\n"
        f"⚽ Kick off: {time_}\n"
        f"{stat}\n"
        f"xG: {home} {hxg} | {away} {axg}\n"
        f"{'Derby games always deliver 🔥' if is_derby else 'Who scores first?'}\n\n"
        f"💬 Drop your score below 👇\n"
        f"📊 Follow for daily xG & AI picks\n"
        f"🔗 Full stats in bio\n"
        f"#football #accagenius #footballtips #xG #matchday #premierleague"
    ).strip()

    # ── YouTube Shorts — urgency + subscribe ─────────────────
    youtube=(
        f"{'🔥 DERBY DAY! ' if is_derby else ''}{home} vs {away} — {league}\n"
        f"Kick-off: {time_}\n\n"
        f"{stat}\n"
        f"xG this season: {home} avg {hxg} | {away} avg {axg}\n\n"
        f"{'Derby history never lies 👀' if is_derby else 'Our AI has the full breakdown.'}\n\n"
        f"📊 Subscribe for daily xG analysis & value picks\n"
        f"🔗 Full AI picks in description — accagenius.com\n"
        f"#footballanalysis #accagenius #shorts #xG #matchprediction"
    ).strip()

    # ── Instagram — polished, full stats ─────────────────────
    instagram=(
        f"⚡ {title}\n\n"
        f"⚽ {home} vs {away}\n"
        f"🏆 {league}\n"
        f"🕐 Kick-off: {time_}\n\n"
        f"{rank_line}"
        f"📊 AI Stats:\n"
        f"  • {stat}\n"
        f"  • xG: {home} {hxg} | {away} {axg}\n\n"
        f"{'🔥 Derby days are unpredictable — history shows anything can happen.' if is_derby else '🤖 Our AI model has crunched the data — full breakdown available now.'}\n\n"
        f"🔗 Full AI predictions + value bets at accagenius.com (link in bio)\n"
        f"💬 Join our Telegram for daily picks — link in bio\n\n"
        f"#football #accagenius #footballstats #premierleague #footballbetting "
        f"#xG #matchday #footballanalysis #aiFootball #valuebets"
    ).strip()

    # ── Reddit — discussion first, no betting tone ────────────
    reddit=(
        f"**{home} vs {away} — {league} — Pre-Match Thread**\n\n"
        f"Kick-off: {time_}\n\n"
        f"{rank_line}"
        f"Some interesting data ahead of this one:\n\n"
        f"- {home} xG average: {hxg} per game\n"
        f"- {away} xG average: {axg} per game\n"
        f"{'- ' + stat if stat else ''}\n\n"
        f"{'This is always a spicy fixture — form goes out the window in derbies.' if is_derby else 'Looking at the numbers, this one could go either way.'}\n\n"
        f"What are your predictions? Anyone fancy an upset?\n\n"
        f"*Stats via AccaGenius AI model — accagenius.com*"
    ).strip()

    # ── X / Twitter — short, reactive ────────────────────────
    x=(
        f"{'🔥 DERBY DAY! ' if is_derby else '⚽ '}"
        f"{home} vs {away} | {time_}\n"
        f"{stat}\n"
        f"xG: {home} {hxg} | {away} {axg}\n"
        f"Full AI breakdown 👉 accagenius.com\n"
        f"#football #accagenius"
    ).strip()

    return {"tiktok":tiktok,"youtube":youtube,"instagram":instagram,"reddit":reddit,"x":x}

def find_content_opportunities(data):
    fbd_data=data.get("fbd",{})
    fixtures=data.get("fixtures",[])
    live=data.get("live",[])
    briefs=[]

    for m in fixtures:
        brief=score_fixture(m, fbd_data)
        if brief:
            brief["content_type"]="preview"
            brief["captions"]=generate_captions(brief)
            briefs.append(brief)

    briefs.sort(key=lambda x: x.get("score",0), reverse=True)
    return briefs
