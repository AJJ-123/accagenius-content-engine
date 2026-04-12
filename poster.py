"""
AccaGenius Poster Renderer v3
Matches the Barcelona vs Espanyol style:
- Stadium background with warm glow
- Form badges (W/D/L)
- Table positions with points
- Stat boxes per team
- Red kickoff pill
- Trophy element
- Growth-optimised CTAs
"""
import os, io, math, requests
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
from typing import Optional

# Colours
BG_DARK   = (8,   10,  18)
GOLD      = (240, 180, 41)
GOLD_LT   = (255, 210, 80)
WHITE     = (255, 255, 255)
OFF_WHITE = (225, 232, 248)
MUTED     = (140, 155, 185)
GREEN     = (30,  200, 90)
RED_FORM  = (220, 50,  50)
YELLOW_D  = (230, 180, 0)
BLUE      = (80,  180, 240)
RED_PILL  = (200, 40,  40)
DARK_CARD = (12,  18,  35)
CARD_BG   = (18,  26,  50)

W, H = 1080, 1920
FONT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "static", "fonts")

def _f(size, bold=False, display=False):
    c = []
    if display: c.append(os.path.join(FONT_DIR, "BebasNeue-Regular.ttf"))
    if bold:
        c += ["/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
              "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"]
    else:
        c += ["/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
              "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]
    for p in c:
        if os.path.exists(p):
            try: return ImageFont.truetype(p, size)
            except: pass
    return ImageFont.load_default()

def _tw(draw, text, font):
    return int(draw.textlength(text, font=font))

def _tc(draw, text, y, font, color, shadow=False):
    x = (W - _tw(draw, text, font)) // 2
    if shadow:
        draw.text((x+3, y+3), text, font=font, fill=(0,0,0,120))
    draw.text((x, y), text, font=font, fill=color)
    bb = font.getbbox(text)
    return y + (bb[3]-bb[1]) + 4

def _logo(url, size=200):
    if not url: return None
    try:
        r = requests.get(url, timeout=8)
        img = Image.open(io.BytesIO(r.content)).convert("RGBA")
        return img.resize((size, size), Image.LANCZOS)
    except: return None

def _make_stadium_bg():
    """Generate a fake stadium background with warm pitch glow."""
    arr = np.zeros((H, W, 3), dtype=np.uint8)
    # Base dark blue-black
    arr[:,:] = [8, 10, 18]
    
    # Warm amber glow from the pitch (center-bottom area)
    for y in range(H):
        for x in range(0, W, 4):  # step for speed
            # Distance from pitch glow center
            dist_y = abs(y - int(H*0.52)) / H
            dist_x = abs(x - W//2) / W
            dist   = math.sqrt(dist_x**2 + dist_y**2)
            # Warm glow falloff
            warmth = max(0, 1 - dist * 2.2) * 0.7
            glow_r = int(min(255, arr[y,x,0] + warmth * 180))
            glow_g = int(min(255, arr[y,x,1] + warmth * 90))
            glow_b = int(min(255, arr[y,x,2] + warmth * 20))
            arr[y, x:x+4] = [glow_r, glow_g, glow_b]

    # Add stadium light bokeh (small bright spots)
    import random
    random.seed(42)
    for _ in range(80):
        bx = random.randint(0, W)
        by = random.randint(int(H*0.05), int(H*0.45))
        br = random.randint(2, 8)
        ba = random.uniform(0.3, 0.9)
        for dy in range(-br, br+1):
            for dx in range(-br, br+1):
                if dx*dx+dy*dy <= br*br:
                    ny, nx = by+dy, bx+dx
                    if 0 <= ny < H and 0 <= nx < W:
                        blend = ba * (1 - math.sqrt(dx*dx+dy*dy)/br)
                        arr[ny,nx] = [
                            int(min(255, arr[ny,nx,0] + blend*220)),
                            int(min(255, arr[ny,nx,1] + blend*190)),
                            int(min(255, arr[ny,nx,2] + blend*130)),
                        ]

    img = Image.fromarray(arr)
    return img.filter(ImageFilter.GaussianBlur(2))

def _overlay_vignette(img):
    """Dark vignette top and bottom."""
    v = Image.new("RGBA", (W,H), (0,0,0,0))
    d = ImageDraw.Draw(v)
    for i in range(320):
        a = int((1-i/320)*200)
        d.line([(0,i),(W,i)], fill=(0,0,0,a))
    for i in range(420):
        a = int((1-i/420)*230)
        d.line([(0,H-i),(W,H-i)], fill=(0,0,0,a))
    return Image.alpha_composite(img.convert("RGBA"), v).convert("RGB")

def _draw_form_badges(draw, form_str, cx, y, badge_size=56, gap=8):
    """Draw W/D/L form badges centred at cx."""
    chars = list(form_str.upper()[-7:])
    total_w = len(chars)*(badge_size+gap) - gap
    x = cx - total_w//2
    font = _f(28, bold=True)
    cols = {"W": GREEN, "D": YELLOW_D, "L": RED_FORM}
    for ch in chars:
        col = cols.get(ch, MUTED)
        draw.rounded_rectangle([x, y, x+badge_size, y+badge_size], radius=10, fill=col)
        tw = _tw(draw, ch, font)
        draw.text((x+(badge_size-tw)//2, y+12), ch, font=font, fill=(10,10,10))
        x += badge_size + gap
    return y + badge_size + 6

def _stat_box(draw, img, x1, y1, x2, y2, team_name, form_str, wins_text, xg_val, xg_up=True):
    """Draw a team stat box like in the reference poster."""
    # Card background
    draw.rounded_rectangle([x1,y1,x2,y2], radius=18, fill=DARK_CARD, outline=(30,45,80), width=1)
    
    fb = lambda s: _f(s, bold=True)
    fr = lambda s: _f(s)
    
    pad = 22
    y = y1 + pad
    
    # Team label
    label = f"{team_name[:12].upper()}  LAST 7"
    lw = _tw(draw, label, fb(28))
    draw.text((x1 + (x2-x1-lw)//2, y), label, font=fb(28), fill=GOLD)
    y += 42
    
    # Form badges
    cx_box = (x1+x2)//2
    y = _draw_form_badges(draw, form_str, cx_box, y, badge_size=50, gap=6)
    y += 12
    
    # Wins text
    ww = _tw(draw, wins_text, fb(30))
    draw.text((x1+(x2-x1-ww)//2, y), wins_text, font=fb(30), fill=OFF_WHITE)
    y += 44
    
    # xG
    xg_text = f"xG/TEAM: {xg_val}"
    xw = _tw(draw, xg_text, fb(32))
    draw.text((x1+(x2-x1-xw)//2, y), xg_text, font=fb(32), fill=OFF_WHITE)
    # Arrow
    arrow = "▲" if xg_up else "▼"
    acol  = GREEN if xg_up else RED_FORM
    aw    = _tw(draw, arrow, fb(32))
    draw.text((x1+(x2-x1+xw)//2+6, y), arrow, font=fb(32), fill=acol)

def _table_row(draw, x, y, rank, team_short, pts, col):
    """Draw a table position row."""
    fb = lambda s: _f(s, bold=True)
    fr = lambda s: _f(s)
    # Rank badge
    draw.rounded_rectangle([x, y, x+52, y+52], radius=10, fill=col)
    rw = _tw(draw, f"#{rank}", fb(24))
    draw.text((x+(52-rw)//2, y+12), f"#{rank}", font=fb(24), fill=(10,10,10))
    # Team name
    draw.text((x+62, y+8), team_short.upper(), font=fb(30), fill=WHITE)
    # Points
    pts_text = f"{pts} PTS"
    draw.text((x+62, y+40), pts_text, font=fr(26), fill=MUTED)

def render_match_poster(brief, output_path):
    home      = brief.get("home","Home")
    away      = brief.get("away","Away")
    league    = brief.get("league","")
    time_     = brief.get("time","TBC")
    title     = brief.get("title","MATCHDAY")
    pred      = brief.get("fbd_prediction","")
    btts      = brief.get("fbd_btts")
    o25       = brief.get("fbd_over25")
    is_derby  = brief.get("is_derby",False)

    # Form data (brief can include these from API)
    home_form  = brief.get("home_form","WWWDLW")
    away_form  = brief.get("away_form","LDWDLW")
    home_wins  = brief.get("home_wins_text","")
    away_wins  = brief.get("away_wins_text","")
    home_xg    = brief.get("home_xg","1.8")
    away_xg    = brief.get("away_xg","1.1")
    home_xg_up = brief.get("home_xg_up",True)
    away_xg_up = brief.get("away_xg_up",False)
    home_rank  = brief.get("home_rank","")
    away_rank  = brief.get("away_rank","")
    home_pts   = brief.get("home_pts","")
    away_pts   = brief.get("away_pts","")

    # Derive wins text if not provided
    if not home_wins:
        w_count = home_form.upper().count("W")
        home_wins = f"{w_count} wins in last {len(home_form)}"
    if not away_wins:
        w_count = away_form.upper().count("W")
        away_wins = f"{w_count} wins in last {len(away_form)}"

    # ── Stadium background ────────────────────────────────────
    print("[renderer] Generating stadium background...")
    img = _make_stadium_bg()
    img = _overlay_vignette(img)
    draw = ImageDraw.Draw(img)

    # ── Header ────────────────────────────────────────────────
    y = 48
    # Orange icon box
    draw.rounded_rectangle([W//2-34, y, W//2+34, y+58], radius=10, fill=GOLD)
    bx,by = W//2,y+8
    draw.polygon([(bx+7,by),(bx-7,by+24),(bx+2,by+24),(bx-9,by+50),
                  (bx+13,by+26),(bx+3,by+26)], fill=(10,10,10))

    _tc(draw, "ACCAGENIUS",   y+66,  _f(42,bold=True),  GOLD,   shadow=True)
    _tc(draw, "AI FOOTBALL INTELLIGENCE", y+116, _f(26), MUTED)

    # ── League ────────────────────────────────────────────────
    y = y + 160
    if league:
        # Small league logo placeholder + text
        lw = _tw(draw, league.upper(), _f(34,bold=True))
        total = lw + 50
        lx = (W-total)//2
        # League circle
        draw.ellipse([lx, y-2, lx+38, y+38], fill=(20,35,70), outline=(50,80,140), width=1)
        draw.text((lx+8, y+4), "⚽", font=_f(22), fill=WHITE)
        draw.text((lx+48, y+2), league.upper(), font=_f(34,bold=True), fill=WHITE)
        y += 58

    # ── Big Title ─────────────────────────────────────────────
    y += 8
    fd_big = _f(148, display=True)
    fd_med = _f(108, display=True)
    if _tw(draw, title, fd_big) < W - 60:
        # Two-colour: first word gold, rest white
        words = title.split()
        if len(words) >= 2:
            w1 = words[0]
            w2 = " ".join(words[1:])
            tw1 = _tw(draw, w1+" ", fd_big)
            tw2 = _tw(draw, w2,     fd_big)
            total_tw = _tw(draw, w1+" "+w2, fd_big)
            sx = (W - total_tw)//2
            draw.text((sx,    y), w1,    font=fd_big, fill=GOLD,  stroke_width=2, stroke_fill=(80,50,0))
            draw.text((sx+tw1, y), w2,   font=fd_big, fill=WHITE, stroke_width=2, stroke_fill=(20,20,20))
        else:
            _tc(draw, title, y, fd_big, GOLD, shadow=True)
        y += 165
    else:
        words = title.split(); half=len(words)//2
        _tc(draw, " ".join(words[:half]), y,    fd_med, GOLD,  shadow=True); y+=120
        _tc(draw, " ".join(words[half:]), y-10, fd_med, WHITE, shadow=True); y+=115

    # ── Logos ─────────────────────────────────────────────────
    y += 10
    logo_size = 220
    hl = _logo(brief.get("home_logo",""), logo_size)
    al = _logo(brief.get("away_logo",""), logo_size)
    logo_y = y

    if hl:
        if pred=="H":
            gl = hl.filter(ImageFilter.GaussianBlur(20))
            img.paste(gl, (78,logo_y-14), gl)
        img.paste(hl, (90, logo_y), hl)
    if al:
        ax = W - 90 - logo_size
        if pred=="A":
            gl = al.filter(ImageFilter.GaussianBlur(20))
            img.paste(gl, (ax-14,logo_y-14), gl)
        img.paste(al, (ax, logo_y), al)

    # VS
    _tc(draw, "VS", logo_y + logo_size//2 - 55, _f(120,display=True), (200,210,230), shadow=True)
    y = logo_y + logo_size + 20

    # Team names
    hcol = GOLD if pred=="H" else OFF_WHITE
    acol = GOLD if pred=="A" else OFF_WHITE
    hw = _tw(draw, home, _f(52,bold=True))
    draw.text((max(55, 215-hw//2), y), home, font=_f(52,bold=True), fill=hcol,
              stroke_width=1, stroke_fill=(0,0,0))
    aw2 = _tw(draw, away, _f(52,bold=True))
    draw.text((min(W-55-aw2, W-215-aw2//2), y), away, font=_f(52,bold=True), fill=acol,
              stroke_width=1, stroke_fill=(0,0,0))
    y += 78

    # ── Kickoff pill ──────────────────────────────────────────
    ko_text = f"TODAY  {time_}  KICKOFF"
    kw = _tw(draw, ko_text, _f(40,bold=True))
    kpad = 40
    kx1 = (W - kw - kpad*2)//2
    kx2 = kx1 + kw + kpad*2
    draw.rounded_rectangle([kx1, y, kx2, y+68], radius=34, fill=RED_PILL)
    draw.text((kx1+kpad, y+14), ko_text, font=_f(40,bold=True), fill=WHITE)
    y += 90

    # ── Form/stat boxes ───────────────────────────────────────
    y += 14
    box_h   = 260
    box_gap = 18
    box_w   = (W - 60 - box_gap) // 2
    bx1 = 30; bx2 = bx1 + box_w
    ax1 = bx2 + box_gap; ax2 = ax1 + box_w

    _stat_box(draw, img, bx1, y, bx2, y+box_h,
              home, home_form, home_wins, home_xg, home_xg_up)
    _stat_box(draw, img, ax1, y, ax2, y+box_h,
              away, away_form, away_wins, away_xg, away_xg_up)
    y += box_h + 22

    # ── Table positions ───────────────────────────────────────
    if home_rank or away_rank:
        # Trophy in centre
        trophy_y = y + 10
        trophy_text = "🏆"
        tw_tr = _tw(draw, trophy_text, _f(72))
        draw.text(((W-tw_tr)//2, trophy_y), trophy_text, font=_f(72), fill=GOLD)

        # Left: home table
        if home_rank:
            hcol2 = GOLD if str(home_rank) in ("1","2","3") else (60,130,255)
            _table_row(draw, 48, y+14, home_rank, home[:10], home_pts, hcol2)

        # Right: away table
        if away_rank:
            acol2 = RED_FORM if int(str(away_rank).replace("#","")) > 16 else (60,130,255)
            aw_text = away[:10]
            aw_tw = _tw(draw, f"#{away_rank}", _f(24,bold=True))
            # Right-aligned
            rx2 = W - 48
            draw.rounded_rectangle([rx2-52, y+14, rx2, y+66], radius=10, fill=acol2)
            draw.text((rx2-52+(52-aw_tw)//2, y+26), f"#{away_rank}", font=_f(24,bold=True), fill=(10,10,10))
            atw = _tw(draw, aw_text.upper(), _f(30,bold=True))
            draw.text((rx2-62-atw, y+22), aw_text.upper(), font=_f(30,bold=True), fill=WHITE)
            if away_pts:
                apttw = _tw(draw, f"{away_pts} PTS", _f(26))
                draw.text((rx2-62-apttw, y+54), f"{away_pts} PTS", font=_f(26), fill=MUTED)
        y += 100

    # ── Hook question ─────────────────────────────────────────
    y += 12
    hooks = {
        True:  (f"Are {home} cruising to another win... ⚽", f"or is a derby shock on the cards? 👀"),
        False: (f"Can {home} take all 3 points? 🔥", f"Drop your score prediction below 👇"),
    }
    line1, line2 = hooks.get(is_derby, hooks[False])
    fb48 = _f(38,bold=True)
    _tc(draw, line1, y,    fb48, OFF_WHITE, shadow=True); y += 54
    _tc(draw, line2, y,    fb48, GOLD,      shadow=True); y += 60

    # ── Conversion CTA strip ──────────────────────────────────
    # Subtle bottom CTA bar — drives to link in bio
    cta_y = H - 140
    draw.rectangle([0, cta_y, W, H], fill=(0,0,0))
    draw.line([(0,cta_y),(W,cta_y)], fill=(35,50,90), width=1)
    
    cta_lines = [
        ("🔗  Full stats & AI picks at  accagenius.com", _f(30,bold=True), GOLD),
        ("Follow for daily data  •  Link in bio", _f(26), MUTED),
    ]
    cy = cta_y + 16
    for txt, fnt, col in cta_lines:
        _tc(draw, txt, cy, fnt, col)
        bb = fnt.getbbox(txt)
        cy += (bb[3]-bb[1]) + 10

    # ── Save ──────────────────────────────────────────────────
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    img.save(output_path, "PNG", optimize=True)
    print(f"[renderer] ✅ Saved: {output_path}")
    return output_path
