"""
AccaGenius Video Renderer
5-slide vertical MP4 (1080x1920, 9:16) using Pillow + FFmpeg.
Each slide 2.5s, fade transitions. ~13s total — perfect for TikTok/Shorts/Reels.
"""
import os, subprocess, tempfile
from PIL import Image, ImageDraw, ImageFilter
from renderer.poster import (
    _font, _tw, _cx, _tc, _logo, _glow,
    W, H, BG_DARK, BG_CARD, GOLD, WHITE, OFF_WHITE, MUTED, GREEN, BLUE, RED
)

FPS   = 30
SLIDE_SECS  = 2.5
FADE_FRAMES = 12
FRAMES_SLIDE = int(SLIDE_SECS * FPS)

def _base(color1=(20,40,120), color2=(30,15,80)):
    img = Image.new("RGB",(W,H),BG_DARK)
    img = _glow(img, W//2, 650,  350, color1, 80)
    img = _glow(img, W//2, 1400, 280, color2, 55)
    return img

def _footer(draw):
    draw.line([(60,H-88),(W-60,H-88)],fill=(35,50,90),width=1)
    _tc(draw,"accagenius.com",H-70,_font(30),MUTED)

def s1_title(brief):
    img  = _base()
    draw = ImageDraw.Draw(img)
    title   = brief.get("title","MATCHDAY")
    league  = brief.get("league","")
    fd = lambda s: _font(s, display=True)
    fb = lambda s: _font(s, bold=True)
    _tc(draw,league.upper(),280,fb(34),MUTED)
    if _tw(draw,title,fd(148)) < W-80:
        _tc(draw,title, 360, fd(148), WHITE)
    else:
        ws=title.split(); half=len(ws)//2
        _tc(draw," ".join(ws[:half]),340,fd(118),WHITE)
        _tc(draw," ".join(ws[half:]),470,fd(118),GOLD)
    _tc(draw,"ACCAGENIUS",H-200,fb(44),GOLD)
    _tc(draw,"AI FOOTBALL INTELLIGENCE",H-142,_font(28),MUTED)
    _footer(draw)
    return img

def s2_teams(brief):
    img  = _base()
    draw = ImageDraw.Draw(img)
    home=brief.get("home",""); away=brief.get("away","")
    league=brief.get("league",""); pred=brief.get("fbd_prediction","")
    fd=lambda s:_font(s,display=True); fb=lambda s:_font(s,bold=True)
    if league:
        lw=_tw(draw,league.upper(),fb(34))
        bx1=(W-lw-60)//2
        draw.rounded_rectangle([bx1-10,210,bx1+lw+10,256],radius=23,fill=(18,30,65))
        _tc(draw,league.upper(),218,fb(34),BLUE)
    hl=_logo(brief.get("home_logo",""),210)
    al=_logo(brief.get("away_logo",""),210)
    logo_y=400
    if hl:
        if pred=="H": img.paste(hl.filter(ImageFilter.GaussianBlur(16)),(88,logo_y-12),hl)
        img.paste(hl,(100,logo_y),hl)
    if al:
        ax=W-310
        if pred=="A": img.paste(al.filter(ImageFilter.GaussianBlur(16)),(ax-12,logo_y-12),al)
        img.paste(al,(ax,logo_y),al)
    _tc(draw,"VS",logo_y+75,fd(128),(190,200,225))
    y=logo_y+235
    hcol=GOLD if pred=="H" else OFF_WHITE
    acol=GOLD if pred=="A" else OFF_WHITE
    hw=_tw(draw,home,fb(48)); draw.text((max(60,215-hw//2),y),home,font=fb(48),fill=hcol)
    aw=_tw(draw,away,fb(48)); draw.text((min(W-60-aw,W-215-aw//2),y),away,font=fb(48),fill=acol)
    y+=80
    t=brief.get("time","TBC")
    draw.rounded_rectangle([60,y,W-60,y+82],radius=41,fill=(14,22,50))
    ko=f"⏰  KICK-OFF  {t}"; kw=_tw(draw,ko,fb(40))
    draw.text(((W-kw)//2,y+20),ko,font=fb(40),fill=GOLD)
    _footer(draw)
    return img

def s3_stats(brief):
    img  = _base((15,25,60),(40,15,80))
    draw = ImageDraw.Draw(img)
    fb=lambda s:_font(s,bold=True); fr=lambda s:_font(s)
    _tc(draw,"TODAY'S AI STATS",260,fb(64),WHITE)
    _tc(draw,"Powered by FBD + AccaGenius",338,fr(30),MUTED)
    draw.line([(60,390),(W-60,390)],fill=(35,50,90),width=1)
    y=430
    stats=[]
    if brief.get("fbd_btts"):  stats.append(("⚽  BTTS PROBABILITY",f"{int(float(brief['fbd_btts']))}%",GREEN))
    if brief.get("fbd_over25"):stats.append(("📈  OVER 2.5 GOALS",  f"{int(float(brief['fbd_over25']))}%",BLUE))
    if brief.get("fbd_prediction"):
        p=brief["fbd_prediction"]; home=brief.get("home",""); away=brief.get("away","")
        lm={"H":f"{home[:12].upper()} WIN","A":f"{away[:12].upper()} WIN","D":"DRAW"}
        stats.append(("🎯  AI PREDICTION",lm.get(p.upper(),p),GOLD))
    for lbl,val,col in stats:
        draw.rounded_rectangle([55,y,W-55,y+160],radius=16,fill=BG_CARD)
        draw.rounded_rectangle([55,y,70,y+160],radius=12,fill=col)
        draw.text((96,y+22),lbl,font=fr(32),fill=MUTED)
        fv=fb(80); vw=_tw(draw,val,fv)
        draw.text(((W-vw)//2,y+68),val,font=fv,fill=col)
        y+=180
    _footer(draw)
    return img

def s4_prediction(brief):
    img  = _base((10,40,15),(30,15,80))
    draw = ImageDraw.Draw(img)
    pred=brief.get("fbd_prediction",""); home=brief.get("home",""); away=brief.get("away","")
    fb=lambda s:_font(s,bold=True); fd=lambda s:_font(s,display=True)
    _tc(draw,"OUR PREDICTION",240,fb(40),MUTED)
    lm={"H":f"{home}\nWIN","A":f"{away}\nWIN","D":"DRAW"}
    text=lm.get(pred.upper(),"?")
    cx,cy,r=W//2,H//2-30,290
    draw.ellipse([cx-r,cy-r,cx+r,cy+r],fill=(18,38,18),outline=GREEN,width=5)
    lines=text.split("\n"); ystart=cy-len(lines)*55+20
    for line in lines:
        lw=_tw(draw,line,fd(100)); draw.text(((W-lw)//2,ystart),line,font=fd(100),fill=GREEN); ystart+=110
    _tc(draw,"AI-powered · FBD data",cy+r+44,fb(32),MUTED)
    _tc(draw,"Full stats at accagenius.com",cy+r+96,_font(30),MUTED)
    _footer(draw)
    return img

def s5_hook(brief):
    img  = _base((40,30,10),(20,10,60))
    draw = ImageDraw.Draw(img)
    fb=lambda s:_font(s,bold=True); fd=lambda s:_font(s,display=True); fr=lambda s:_font(s)
    is_derby=brief.get("is_derby",False)
    line1,line2 = ("WHO WINS THE","DERBY?") if is_derby else ("YOUR","PREDICTION?")
    _tc(draw,line1,300,fd(120),WHITE)
    _tc(draw,line2,430,fd(120),GOLD)
    sub="Drop your score below 👇" if is_derby else "Comment the score 👇"
    _tc(draw,sub,580,fb(40),MUTED)
    # CTA button
    y2=H-300
    draw.rounded_rectangle([70,y2,W-70,y2+80],radius=40,fill=GOLD)
    cta="🔗  Full stats at accagenius.com"
    cw=_tw(draw,cta,fb(36)); draw.text(((W-cw)//2,y2+20),cta,font=fb(36),fill=BG_DARK)
    _tc(draw,"Join our Telegram for daily picks",H-190,fr(32),MUTED)
    _footer(draw)
    return img

SLIDES = [s1_title, s2_teams, s3_stats, s4_prediction, s5_hook]

def render_video(brief, output_path):
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        n = 0
        for fn in SLIDES:
            slide = fn(brief)
            for i in range(FRAMES_SLIDE):
                if i < FADE_FRAMES:
                    a = int((i/FADE_FRAMES)*255)
                    ov = Image.new("RGBA",(W,H),(0,0,0,255-a))
                    fr2 = Image.alpha_composite(slide.convert("RGBA"),ov).convert("RGB")
                else:
                    fr2 = slide
                fr2.save(f"{tmp}/f{n:05d}.png")
                n += 1
        cmd = ["ffmpeg","-y","-framerate",str(FPS),"-i",f"{tmp}/f%05d.png",
               "-c:v","libx264","-pix_fmt","yuv420p","-crf","22","-preset","fast",output_path]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0:
            print(f"[video] FFmpeg error: {res.stderr[-300:]}")
        else:
            print(f"[video] ✅ {output_path}")
    return output_path
