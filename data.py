"""
AccaGenius Content Engine — Data Ingestion
Pulls from the existing Railway backend API.
"""
import os
import requests
from datetime import datetime
from typing import Optional

API_BASE = os.getenv("ACCAGENIUS_API", "https://fastapi-backend-production-cf57.up.railway.app")

HEADERS = {"Content-Type": "application/json"}

def _get(endpoint: str, params: dict = None) -> dict:
    try:
        r = requests.get(f"{API_BASE}{endpoint}", params=params, headers=HEADERS, timeout=15)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"[data] Error fetching {endpoint}: {e}")
        return {}

def get_today_fixtures() -> list:
    data = _get("/today")
    return data.get("matches", [])

def get_live_matches() -> list:
    data = _get("/live")
    return data.get("matches", [])

def get_fbd_value_bets() -> dict:
    return _get("/fbd/value-bets")

def get_all_data() -> dict:
    return {
        "fixtures":   get_today_fixtures(),
        "live":       get_live_matches(),
        "fbd":        get_fbd_value_bets(),
        "fetched_at": datetime.now().isoformat(),
    }

def get_team_form(home_id: int, away_id: int, league_id: int) -> dict:
    """Fetch form and standings for both teams."""
    out = {}
    try:
        hf = _get(f"/form/{home_id}/{league_id}")
        af = _get(f"/form/{away_id}/{league_id}")
        out["home_form_raw"] = hf
        out["away_form_raw"] = af
    except: pass
    return out

def get_standings(league_id: int) -> list:
    try:
        d = _get(f"/standings/{league_id}")
        return d.get("standings", [])
    except: return []

def enrich_brief_with_form(brief: dict) -> dict:
    """Add form strings, xG and table position to a brief."""
    home_id    = brief.get("home_id", 0)
    away_id    = brief.get("away_id", 0)
    league_id  = brief.get("league_id", 0)
    if not home_id or not away_id or not league_id:
        return brief

    # Try to get form from /form endpoint
    try:
        hf = _get(f"/form/{home_id}/{league_id}")
        af = _get(f"/form/{away_id}/{league_id}")

        def _extract_form(fd):
            results = fd.get("recent_results", fd.get("form",""))
            if isinstance(results, str): return results[-7:]
            if isinstance(results, list):
                return "".join(r.get("result","?")[:1].upper() for r in results[-7:])
            return "WWWDLW"

        brief["home_form"]    = _extract_form(hf)
        brief["away_form"]    = _extract_form(af)
        brief["home_xg"]      = str(round(float(hf.get("xg_avg", hf.get("gf_avg",1.5))),1))
        brief["away_xg"]      = str(round(float(af.get("xg_avg", af.get("gf_avg",1.0))),1))
        brief["home_xg_up"]   = float(brief["home_xg"]) >= 1.5
        brief["away_xg_up"]   = float(brief["away_xg"]) >= 1.5
        hw = hf.get("wins",0); hn = hf.get("games",7)
        aw = af.get("wins",0); an = af.get("games",7)
        brief["home_wins_text"] = f"{hw} wins in last {hn}  {brief['home_xg']}{'▲' if brief['home_xg_up'] else '▼'}"
        brief["away_wins_text"] = f"{aw} wins in last {an}  {brief['away_xg']}{'▲' if brief['away_xg_up'] else '▼'}"
    except Exception as e:
        print(f"[data] Form fetch error: {e}")

    # Try standings
    try:
        standings = get_standings(league_id)
        for entry in standings:
            tid = entry.get("team_id") or (entry.get("team",{}).get("id"))
            if tid == home_id:
                brief["home_rank"] = entry.get("position", entry.get("rank",""))
                brief["home_pts"]  = entry.get("points","")
            if tid == away_id:
                brief["away_rank"] = entry.get("position", entry.get("rank",""))
                brief["away_pts"]  = entry.get("points","")
    except Exception as e:
        print(f"[data] Standings fetch error: {e}")

    return brief
