"""
Cyclone EWS — Video Generator with Voiceover
Generates a 1920x1080 MP4 demo video with:
  - Slides with project content (title, problem, architecture, agents, features, demo, CTA)
  - gTTS voiceover synced to each slide
  - Background music from template video (optional)
  - Clean IBM-themed dark design (navy #0A1628, accent #4FC3F7, red #E53935)
Run: python generate_video.py
Output: d:\CycloneDetectionEarlyWarning\Cyclone_EWS_Demo.mp4
"""
import os
import sys
import math
import textwrap
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from gtts import gTTS
from moviepy import (
    VideoClip, AudioFileClip, CompositeAudioClip,
    concatenate_videoclips, ImageClip
)
from moviepy.audio.AudioClip import AudioArrayClip

# ── Constants ────────────────────────────────────────────────────────────────
W, H = 1920, 1080
FPS  = 30
OUT  = r"d:\CycloneDetectionEarlyWarning\Cyclone_EWS_Demo.mp4"
TMP  = r"d:\CycloneDetectionEarlyWarning\_video_tmp"
os.makedirs(TMP, exist_ok=True)

# Colours
BG_DARK   = (10,  22,  40)    # #0A1628
BG_CARD   = (22,  27,  34)    # #161B22
ACCENT    = (79, 195, 247)    # #4FC3F7
RED       = (229, 57, 53)     # #E53935
ORANGE    = (255,109,  0)     # #FF6D00
YELLOW    = (255,214,  0)     # #FFD600
GREEN     = (105,240,174)     # #69F0AE
WHITE     = (230,237,243)     # #E6EDF3
MUTED     = (139,148,158)     # #8B949E
NAVY_BAND = (31, 56,100)      # #1F3864


def load_font(size, bold=False):
    """Try to load a system font, fall back to default."""
    candidates_bold   = ["arialbd.ttf","Arial Bold.ttf","DejaVuSans-Bold.ttf","calibrib.ttf"]
    candidates_normal = ["arial.ttf","Arial.ttf","DejaVuSans.ttf","calibri.ttf"]
    candidates = candidates_bold if bold else candidates_normal
    dirs = [
        r"C:\Windows\Fonts",
        "/usr/share/fonts/truetype/dejavu",
        "/usr/share/fonts/truetype",
        "/System/Library/Fonts",
    ]
    for d in dirs:
        for c in candidates:
            p = os.path.join(d, c)
            if os.path.exists(p):
                try:
                    return ImageFont.truetype(p, size)
                except Exception:
                    pass
    return ImageFont.load_default()


def draw_text_wrapped(draw, text, x, y, max_width, font, color, line_spacing=1.4):
    """Draw text with automatic word-wrapping."""
    words = text.split()
    lines = []
    line  = ""
    for w in words:
        test = (line + " " + w).strip()
        bbox = draw.textbbox((0, 0), test, font=font)
        if bbox[2] <= max_width:
            line = test
        else:
            if line:
                lines.append(line)
            line = w
    if line:
        lines.append(line)
    for ln in lines:
        draw.text((x, y), ln, font=font, fill=color)
        bbox = draw.textbbox((0, 0), ln, font=font)
        y += int((bbox[3] - bbox[1]) * line_spacing)
    return y


def gradient_bg(img: Image.Image):
    """Fill image with dark-to-darker vertical gradient."""
    arr = np.zeros((H, W, 3), dtype=np.uint8)
    for row in range(H):
        t = row / H
        r = int(BG_DARK[0] * (1 - t) + 5 * t)
        g = int(BG_DARK[1] * (1 - t) + 8 * t)
        b = int(BG_DARK[2] * (1 - t) + 18 * t)
        arr[row, :] = [r, g, b]
    bg = Image.fromarray(arr)
    img.paste(bg)


def header_band(img: Image.Image, title: str, subtitle: str = ""):
    """Draw top navy band with slide title."""
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, 0, W, 110], fill=NAVY_BAND)
    draw.rectangle([0, 110, W, 115], fill=ACCENT)
    f_title = load_font(38, bold=True)
    f_sub   = load_font(22)
    draw.text((60, 18), title,    font=f_title, fill=WHITE)
    if subtitle:
        draw.text((60, 72), subtitle, font=f_sub,   fill=tuple(ACCENT))


def footer_band(img: Image.Image):
    """Draw bottom band with branding."""
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, H-60, W, H], fill=NAVY_BAND)
    f = load_font(20)
    draw.text((60,  H-42), "IBM Bob  ·  IBM Granite LLM  ·  IBM Cloud (watsonx.ai)", font=f, fill=tuple(MUTED))
    draw.text((W-420, H-42), "Cyclone Detection & Early Warning System", font=f, fill=tuple(ACCENT))


def pill(draw: ImageDraw.Draw, x, y, w, h, text, bg, fg, font):
    draw.rounded_rectangle([x, y, x+w, y+h], radius=10, fill=bg)
    bbox = draw.textbbox((0,0), text, font=font)
    tx = x + (w - (bbox[2]-bbox[0])) // 2
    ty = y + (h - (bbox[3]-bbox[1])) // 2
    draw.text((tx, ty), text, font=font, fill=fg)


# ── SLIDES ───────────────────────────────────────────────────────────────────

def slide_title() -> Image.Image:
    img  = Image.new("RGB", (W, H), BG_DARK)
    gradient_bg(img)
    draw = ImageDraw.Draw(img)

    # Cyclone spiral (decorative rings)
    cx, cy = W - 340, H // 2
    for r in range(50, 350, 60):
        alpha = 80 - r // 5
        c = tuple(int(ACCENT[i] * alpha / 80) for i in range(3))
        draw.ellipse([cx-r, cy-r, cx+r, cy+r], outline=c, width=2)
    # Eye
    draw.ellipse([cx-30, cy-30, cx+30, cy+30], fill=RED)

    # Title
    f_big  = load_font(72, bold=True)
    f_sub  = load_font(32)
    f_tag  = load_font(26)
    f_badge= load_font(22, bold=True)

    draw.text((80, 180), "🌀 Cyclone Detection &",      font=f_big, fill=WHITE)
    draw.text((80, 270), "   Early Warning System",     font=f_big, fill=WHITE)

    # Accent underline
    draw.rectangle([80, 365, 900, 370], fill=ACCENT)

    draw.text((80, 390), "Agentic AI for Disaster Management & Climate Resilience", font=f_sub, fill=tuple(ACCENT))
    draw.text((80, 450), "Powered by IBM Bob · IBM Granite LLM · IBM Cloud",        font=f_tag, fill=tuple(MUTED))

    # Badges
    badges = [
        ("IBM watsonx.ai", NAVY_BAND, ACCENT),
        ("7 AI Agents",    (40,80,40), GREEN),
        ("Streamlit",      (50,30,70), (200,150,255)),
        ("ReAct Loop",     (60,40,10), YELLOW),
    ]
    bx = 80
    for label, bg, fg in badges:
        bw = 180
        draw.rounded_rectangle([bx, 540, bx+bw, 590], radius=8, fill=bg, outline=tuple(fg), width=1)
        bf = load_font(18, bold=True)
        bbox = draw.textbbox((0,0), label, font=bf)
        draw.text((bx + (bw-(bbox[2]-bbox[0]))//2, 557), label, font=bf, fill=tuple(fg))
        bx += bw + 20

    # Team
    draw.text((80, H-170), "Team: Sushmitha MG", font=load_font(28,True), fill=WHITE)
    draw.text((80, H-130), "Domain: Disaster Management & Climate Resilience", font=load_font(22), fill=tuple(MUTED))
    draw.text((80, H-90),  "IBM SkillsBuild Hackathon 2026 — Bengaluru",        font=load_font(22), fill=tuple(MUTED))

    footer_band(img)
    return img


def slide_problem() -> Image.Image:
    img  = Image.new("RGB", (W, H), BG_DARK)
    gradient_bg(img)
    header_band(img, "The Problem", "Why India needs AI-powered cyclone detection")
    draw = ImageDraw.Draw(img)

    stats = [
        ("5–6",   "Cyclones hit India annually\nalong Bay of Bengal & Arabian Sea"),
        ("1M+",   "People affected by\nCyclone Biparjoy alone (2023)"),
        ("$8.1B", "Economic damage from\nCyclone Fani (2019)"),
        ("72h",   "Minimum warning time\nneeded to save lives"),
    ]

    card_w, card_h = 380, 240
    sx = 80
    sy = 200
    for num, label in stats:
        # Card
        draw.rounded_rectangle([sx, sy, sx+card_w, sy+card_h], radius=14, fill=BG_CARD,
                                outline=(*RED, 180), width=1)
        f_num = load_font(68, bold=True)
        f_lbl = load_font(22)
        bbox = draw.textbbox((0,0), num, font=f_num)
        nx = sx + (card_w - (bbox[2]-bbox[0])) // 2
        draw.text((nx, sy+16), num, font=f_num, fill=RED)
        # Divider
        draw.rectangle([sx+20, sy+100, sx+card_w-20, sy+102], fill=tuple(ACCENT))
        y = sy + 116
        for line in label.split("\n"):
            lb = draw.textbbox((0,0), line, font=f_lbl)
            lx = sx + (card_w - (lb[2]-lb[0])) // 2
            draw.text((lx, y), line, font=f_lbl, fill=WHITE)
            y += 32
        sx += card_w + 30

    # Challenge text
    fy = 490
    f_body = load_font(26)
    challenges = [
        "❌  Delayed identification of cyclone formation",
        "❌  Limited real-time monitoring of storm intensity changes",
        "❌  No location-specific early warnings for coastal communities",
        "❌  Lack of AI-driven impact assessment for rapid response decisions",
    ]
    for ch in challenges:
        draw.text((100, fy), ch, font=f_body, fill=WHITE)
        fy += 50

    draw.text((100, 760), "✅  Solution: AI-powered 7-agent system for 72h+ advance cyclone detection & warnings",
              font=load_font(28, bold=True), fill=tuple(GREEN))

    footer_band(img)
    return img


def slide_architecture() -> Image.Image:
    img  = Image.new("RGB", (W, H), BG_DARK)
    gradient_bg(img)
    header_band(img, "System Architecture", "4-Phase Supervised Multi-Agent Pipeline")
    draw = ImageDraw.Draw(img)

    phases = [
        ("Phase 1",  "Weather Analysis\n+\nCyclone Detection",  ACCENT,  "IBM watsonx\nLLaMA 3-70B"),
        ("Phase 2",  "Track & Prediction\n+\nIntensity Forecast", YELLOW,  "Gemini Pro\n+  Groq LLaMA"),
        ("Phase 3",  "Impact Assessment\n+\nEarly Warning",       ORANGE,  "Gemini Pro\n+  Groq LLaMA"),
        ("Phase 4",  "Disaster Response\nRecommendation",         RED,     "IBM watsonx\nLLaMA 3-70B"),
    ]

    box_w, box_h = 380, 280
    sy = 160
    px = 60
    for i, (ph, agents, color, llm) in enumerate(phases):
        # Arrow between boxes
        if i > 0:
            ax = px - 30
            ay = sy + box_h // 2
            draw.polygon([(ax, ay-10), (ax, ay+10), (ax+28, ay)], fill=tuple(MUTED))

        # Box
        draw.rounded_rectangle([px, sy, px+box_w, sy+box_h], radius=14,
                                fill=BG_CARD, outline=color, width=2)
        # Phase label band
        draw.rounded_rectangle([px, sy, px+box_w, sy+44], radius=14, fill=color)
        f_ph  = load_font(20, bold=True)
        f_ag  = load_font(22)
        f_llm = load_font(18)
        draw.text((px+14, sy+10), ph, font=f_ph, fill=BG_DARK if color!=RED else WHITE)

        # Agent names
        ay2 = sy + 58
        for line in agents.split("\n"):
            lbbox = draw.textbbox((0,0), line, font=f_ag)
            lx = px + (box_w-(lbbox[2]-lbbox[0]))//2
            draw.text((lx, ay2), line, font=f_ag, fill=WHITE)
            ay2 += 34

        # LLM badge
        for line in llm.split("\n"):
            lbbox = draw.textbbox((0,0), line, font=f_llm)
            lx2 = px + (box_w-(lbbox[2]-lbbox[0]))//2
            draw.text((lx2, ay2+6), line, font=f_llm, fill=tuple(MUTED))
            ay2 += 26

        px += box_w + 30

    # Bottom features row
    features = [
        ("🧠 ReAct Loop",    "Think → Act → Observe\n(max 3 iterations)"),
        ("🗄️ Memory",        "Short-term buffer\n+ ChromaDB vector store"),
        ("🔧 MCP Tools",     "weather, satellite,\nimpact, alert tools"),
        ("🛡️ Guardrails",   "9 categories\n40+ safety checks"),
        ("⚖️ Governance",   "15 policies\nImmutable audit trail"),
    ]

    fx = 60
    fy = 570
    fw, fh = 340, 170
    for icon_label, desc in features:
        draw.rounded_rectangle([fx, fy, fx+fw, fy+fh], radius=12, fill=BG_CARD,
                                outline=(*MUTED, 100), width=1)
        fi   = load_font(20, bold=True)
        fdesc= load_font(18)
        draw.text((fx+14, fy+12), icon_label, font=fi, fill=tuple(ACCENT))
        dy = fy + 50
        for ln in desc.split("\n"):
            draw.text((fx+14, dy), ln, font=fdesc, fill=tuple(MUTED))
            dy += 28
        fx += fw + 12

    footer_band(img)
    return img


def slide_agents() -> Image.Image:
    img  = Image.new("RGB", (W, H), BG_DARK)
    gradient_bg(img)
    header_band(img, "7 Specialized AI Agents", "Per-agent LLM routing — best model for each domain")
    draw = ImageDraw.Draw(img)

    agents = [
        ("🌦️", "Weather Analysis",       "IBM watsonx / LLaMA 3-70B", ACCENT,  "Pressure · Wind · SST · Humidity · Rainfall"),
        ("🔍", "Cyclone Detection",       "IBM watsonx / LLaMA 3-70B", ACCENT,  "Satellite imagery · Spiral bands · Eye formation"),
        ("🗺️", "Track & Prediction",     "Google Gemini Pro",          GREEN,   "72h trajectory · Landfall · Uncertainty cone"),
        ("💥", "Intensity Prediction",    "Groq / LLaMA 3-70B",        YELLOW,  "Rapid intensification · Wind forecast · Pressure drop"),
        ("⚠️", "Impact Assessment",      "Google Gemini Pro",          GREEN,   "Population risk · Infrastructure · Agriculture"),
        ("🚨", "Early Warning & Alerts", "Groq / LLaMA 3-70B",        ORANGE,  "RED / ORANGE / YELLOW district alerts"),
        ("🛟", "Disaster Response",      "IBM watsonx / LLaMA 3-70B", ACCENT,  "Evacuation plan · NDRF · Shelter allocation"),
    ]

    row_h = 92
    sy    = 150
    for icon, name, llm, color, desc in agents:
        draw.rounded_rectangle([60, sy, W-60, sy+row_h-8], radius=12,
                                fill=BG_CARD, outline=color, width=1)
        # Left color bar
        draw.rounded_rectangle([60, sy, 72, sy+row_h-8], radius=6, fill=color)

        f_icon = load_font(36)
        f_name = load_font(26, bold=True)
        f_llm  = load_font(20)
        f_desc = load_font(20)

        draw.text((90,  sy+12), icon, font=f_icon, fill=WHITE)
        draw.text((160, sy+10), name, font=f_name, fill=WHITE)
        draw.text((160, sy+48), llm,  font=f_llm,  fill=color)

        # Description right side
        bbox = draw.textbbox((0,0), desc, font=f_desc)
        dx   = W - 80 - (bbox[2]-bbox[0])
        draw.text((dx, sy+30), desc, font=f_desc, fill=tuple(MUTED))

        sy += row_h

    footer_band(img)
    return img


def slide_cyclone_map() -> Image.Image:
    """Slide showing the animated cyclone map concept."""
    img  = Image.new("RGB", (W, H), BG_DARK)
    gradient_bg(img)
    header_band(img, "Animated 72-Hour Cyclone Track Forecast", "Plotly frames animation · Play/Pause · Time slider")
    draw = ImageDraw.Draw(img)

    # Draw a stylized cyclone track on a mock map background
    # Ocean background
    draw.rectangle([80, 130, 1300, 950], fill=(8, 24, 56))

    # Draw Indian coastline approximate polygon
    coast_pts = [
        (580,950),(600,820),(580,750),(560,680),(540,620),(520,570),
        (510,510),(530,460),(550,410),(570,380),(600,340),(630,320),
        (660,310),(690,320),(720,340),(740,380),(760,420),(780,470),
        (800,520),(820,580),(840,640),(860,700),(870,760),(880,820),
        (900,880),(910,950),
    ]
    draw.polygon(coast_pts, fill=(30, 50, 40), outline=(60,90,70))

    # Cyclone track line
    track = [
        (1100, 820), (1060, 760), (1010, 690), (960, 620),
        (900, 550),  (840, 490),  (790, 440),  (750, 410),
        (720, 400),  (700, 405),  (685, 415),
    ]
    CAT_COLORS_RGB = [
        (100,221,23),(255,214,0),(255,109,0),(229,57,53),(229,57,53),
        (229,57,53),(229,57,53),(229,57,53),(229,57,53),(229,57,53),(229,57,53),
    ]

    # Draw uncertainty cone
    import random; random.seed(42)
    cone_pts_top = [(t[0]-int(i*8), t[1]-int(i*8)) for i,t in enumerate(track)]
    cone_pts_bot = [(t[0]+int(i*8), t[1]+int(i*8)) for i,t in enumerate(track)]
    cone_all     = cone_pts_top + list(reversed(cone_pts_bot))
    draw.polygon(cone_all, fill=(229,57,53,30))

    # Track line
    for i in range(len(track)-1):
        draw.line([track[i], track[i+1]], fill=ORANGE, width=3)

    # Track dots (sized by intensity)
    sizes = [8,10,12,14,18,20,22,22,20,18,14]
    for i,(pt, sz, c) in enumerate(zip(track, sizes, CAT_COLORS_RGB)):
        draw.ellipse([pt[0]-sz, pt[1]-sz, pt[0]+sz, pt[1]+sz], fill=c, outline=WHITE)

    # Landfall star
    lf = track[6]
    star_pts = []
    for k in range(10):
        angle = math.pi/2 + k * 2*math.pi/10
        r     = 24 if k % 2 == 0 else 12
        star_pts.append((lf[0]+int(r*math.cos(angle)), lf[1]-int(r*math.sin(angle))))
    draw.polygon(star_pts, fill=RED, outline=WHITE)

    # Pulsing cyclone eye at T+36h
    eye = track[6]
    for r in [45, 35, 25, 15]:
        alpha_c = tuple(int(RED[i]*0.3) + int(BG_DARK[i]*0.7) for i in range(3))
        draw.ellipse([eye[0]-r, eye[1]-r, eye[0]+r, eye[1]+r], outline=RED, width=2)
    draw.ellipse([eye[0]-8, eye[1]-8, eye[0]+8, eye[1]+8], fill=WHITE)

    # Time labels
    hours = ["T+0h","T+12h","T+24h","T+36h\nLANDFALL","T+48h","T+60h","T+72h"]
    label_pts = [track[0], track[2], track[4], track[6], track[8], track[9], track[10]]
    f_lbl = load_font(18, bold=True)
    for i,(pt, lbl) in enumerate(zip(label_pts, hours)):
        color = RED if "LAND" in lbl else tuple(MUTED)
        for j, line in enumerate(lbl.split("\n")):
            draw.text((pt[0]+14, pt[1]-12+j*20), line, font=f_lbl, fill=color)

    # Category legend (right side panel)
    lx, ly = 1340, 150
    draw.rounded_rectangle([lx, ly, W-40, 950], radius=12, fill=BG_CARD)
    f_h  = load_font(24, bold=True)
    f_l  = load_font(18)
    draw.text((lx+20, ly+16), "Intensity Scale", font=f_h, fill=WHITE)
    cats = [
        ("TD  (< 63 kt)",   (79,195,247)),
        ("TS  (63–88 kt)",  (100,221,23)),
        ("SCS (89–117 kt)", (255,214,0)),
        ("VSCS(118–167kt)", (255,109,0)),
        ("ESCS(>168 kt)",   (229,57,53)),
    ]
    cy2 = ly + 60
    for cat_name, cat_c in cats:
        draw.rounded_rectangle([lx+20, cy2, lx+50, cy2+28], radius=6, fill=cat_c)
        draw.text((lx+64, cy2+4), cat_name, font=f_l, fill=WHITE)
        cy2 += 44

    # Key features
    draw.text((lx+20, cy2+20), "Key Features:", font=f_h, fill=tuple(ACCENT))
    feats = ["▶ Play / ⏸ Pause", "⏱ Time slider T+0→T+72h",
             "Pulsing cyclone eye", "Rotating spiral bands",
             "Uncertainty cone", "Intensity color shift"]
    ky = cy2 + 60
    for feat in feats:
        draw.text((lx+20, ky), f"• {feat}", font=f_l, fill=tuple(MUTED))
        ky += 34

    footer_band(img)
    return img


def slide_features() -> Image.Image:
    img  = Image.new("RGB", (W, H), BG_DARK)
    gradient_bg(img)
    header_band(img, "Key Features & Capabilities", "Mission Control · Guardrails · Governance · Observability")
    draw = ImageDraw.Draw(img)

    feats = [
        ("🌀", "Mission Control\nDashboard",
         "Animated 72h cyclone map\n5 KPI cards · Agent pipeline\nstatus · Run pipeline button",
         ACCENT),
        ("🛡️", "9-Category\nGuardrails",
         "40+ checks: injection, hallucination,\ntoxicity, PII, jailbreak, HITL,\nloop detection, bias, cost",
         RED),
        ("🔬", "LLM Comparison\nBenchmark",
         "4-provider side-by-side test:\nwatsonx · Gemini · Groq · OpenRouter\nAccuracy, latency, cost metrics",
         YELLOW),
        ("🔭", "Agent Observability\nTraces",
         "ReAct step-by-step execution,\ntoken usage, confidence scores,\nshort-term + ChromaDB memory",
         GREEN),
        ("⚖️", "AI Governance\n& Compliance",
         "15 named policies · Audit trail\nNDMA / DMA 2005 / IMD SOP\nregulatory alignment",
         ORANGE),
        ("🌊", "Coastal Zone\nExplorer",
         "5 Indian coastal divisions\nDistrict-level risk scoring\nPopulation vulnerability maps",
         ACCENT),
    ]

    col_w = (W - 160) // 3
    col_h = 360
    sx, sy = 80, 150
    for i, (icon, title, desc, color) in enumerate(feats):
        col = i % 3
        row = i // 3
        fx = sx + col * (col_w + 30)
        fy = sy + row * (col_h + 20)

        draw.rounded_rectangle([fx, fy, fx+col_w, fy+col_h-10], radius=14,
                                fill=BG_CARD, outline=color, width=1)
        # Top color strip
        draw.rounded_rectangle([fx, fy, fx+col_w, fy+6], radius=6, fill=color)

        f_ic = load_font(44)
        f_t  = load_font(24, bold=True)
        f_d  = load_font(18)

        draw.text((fx+20, fy+18), icon, font=f_ic, fill=WHITE)
        ty = fy + 78
        for line in title.split("\n"):
            draw.text((fx+20, ty), line, font=f_t, fill=WHITE)
            ty += 34
        ty += 6
        for line in desc.split("\n"):
            draw.text((fx+20, ty), line, font=f_d, fill=tuple(MUTED))
            ty += 28

    footer_band(img)
    return img


def slide_demo() -> Image.Image:
    img  = Image.new("RGB", (W, H), BG_DARK)
    gradient_bg(img)
    header_band(img, "Live Demo — Cyclone VARUNA", "Extremely Severe Cyclonic Storm · Bay of Bengal · Landfall T+48h")
    draw = ImageDraw.Draw(img)

    # Alert banner
    draw.rounded_rectangle([60, 145, W-60, 210], radius=10,
                            fill=(26,5,5), outline=RED, width=2)
    f_alert = load_font(26, bold=True)
    draw.text((90, 160), "🔴  ACTIVE ALERT: ESCS-4 CYCLONE VARUNA — Bay of Bengal · "
              "Landfall near Visakhapatnam in ~48h · Wind: 130 kt",
              font=f_alert, fill=RED)

    # KPI row
    kpis = [
        ("🌀",  "Category",   "ESCS-4",   RED),
        ("💨",  "Max Wind",   "130 kt",   ORANGE),
        ("🌡️", "SST",        "30.2°C",   YELLOW),
        ("📍",  "Landfall",   "T+48h",    ACCENT),
        ("🛡️", "Alert Level","RED",       RED),
    ]
    kw = (W - 160) // 5
    kx = 80
    ky = 230
    for icon, label, value, color in kpis:
        draw.rounded_rectangle([kx, ky, kx+kw-10, ky+130], radius=12, fill=BG_CARD,
                                outline=color, width=1)
        fi = load_font(32)
        fv = load_font(34, bold=True)
        fl = load_font(18)
        ibb = draw.textbbox((0,0), icon, font=fi)
        draw.text((kx+(kw-10-(ibb[2]-ibb[0]))//2, ky+8), icon, font=fi, fill=WHITE)
        vbb = draw.textbbox((0,0), value, font=fv)
        draw.text((kx+(kw-10-(vbb[2]-vbb[0]))//2, ky+52), value, font=fv, fill=color)
        lbb = draw.textbbox((0,0), label, font=fl)
        draw.text((kx+(kw-10-(lbb[2]-lbb[0]))//2, ky+100), label, font=fl, fill=tuple(MUTED))
        kx += kw

    # Impact districts
    districts = [
        ("Visakhapatnam", "Andhra Pradesh", "95%", RED,    "890,000 at risk"),
        ("Srikakulam",    "Andhra Pradesh", "87%", ORANGE, "320,000 at risk"),
        ("East Godavari", "Andhra Pradesh", "78%", ORANGE, "280,000 at risk"),
        ("Ganjam",        "Odisha",         "65%", YELLOW, "190,000 at risk"),
        ("Puri",          "Odisha",         "60%", YELLOW, "150,000 at risk"),
    ]
    f_dh = load_font(22, bold=True)
    f_dd = load_font(18)
    draw.text((80, 390), "District Impact Assessment", font=load_font(26, bold=True), fill=tuple(ACCENT))

    dy = 430
    for dist, state, risk, color, pop in districts:
        # Risk bar
        bar_w = int(float(risk.strip("%")) / 100 * 900)
        draw.rounded_rectangle([80, dy, 980, dy+52], radius=8, fill=BG_CARD)
        draw.rounded_rectangle([80, dy, 80+bar_w, dy+52], radius=8, fill=(*color, 160))
        draw.text((96, dy+14), f"{dist}  ·  {state}", font=f_dh, fill=WHITE)
        draw.text((900, dy+14), f"{risk}  |  {pop}", font=f_dd, fill=tuple(MUTED))
        dy += 66

    # Response
    draw.rounded_rectangle([1040, 390, W-60, 930], radius=12, fill=BG_CARD)
    f_rh = load_font(22, bold=True)
    f_rb = load_font(18)
    draw.text((1060, 406), "🚀 Response Actions", font=f_rh, fill=tuple(ACCENT))
    actions = [
        "• Evacuate 847 coastal villages",
        "• Deploy 14 NDRF battalions",
        "• Activate 312 cyclone shelters",
        "• Emergency port closure",
        "• SMS alert to 3.2M residents",
        "• Pre-position 6,200 MT food grain",
        "• Mobile medical units deployed",
        "• Satellite phones to collectors",
    ]
    ry = 448
    for act in actions:
        draw.text((1060, ry), act, font=f_rb, fill=WHITE)
        ry += 34

    footer_band(img)
    return img


def slide_cta() -> Image.Image:
    """Call-to-action / Thank you slide."""
    img  = Image.new("RGB", (W, H), BG_DARK)
    gradient_bg(img)
    draw = ImageDraw.Draw(img)

    # Decorative cyclone rings
    for r in range(60, 500, 80):
        c = tuple(int(ACCENT[i] * (1 - r/500)) for i in range(3))
        draw.ellipse([W//2-r, H//2-r, W//2+r, H//2+r], outline=c, width=2)
    draw.ellipse([W//2-35, H//2-35, W//2+35, H//2+35], fill=RED)

    f_big  = load_font(60, bold=True)
    f_sub  = load_font(32)
    f_med  = load_font(26)
    f_sml  = load_font(22)

    draw.text((W//2 - 420, 120), "Thank You", font=f_big, fill=WHITE)
    draw.rectangle([W//2-420, 200, W//2+420, 205], fill=tuple(ACCENT))

    stats = [
        ("75",   "Python files\ngenerated by IBM Bob"),
        ("7",    "Specialized\nAI Agents"),
        ("40+",  "Guardrail\nsafety checks"),
        ("15",   "Governance\npolicies"),
    ]
    sx = W//2 - 680
    sy = H//2 - 80
    for num, label in stats:
        f_n = load_font(52, bold=True)
        f_l = load_font(20)
        bn  = draw.textbbox((0,0), num, font=f_n)
        draw.text((sx + (160-(bn[2]-bn[0]))//2, sy), num, font=f_n, fill=tuple(ACCENT))
        for i, ln in enumerate(label.split("\n")):
            bl = draw.textbbox((0,0), ln, font=f_l)
            draw.text((sx + (160-(bl[2]-bl[0]))//2, sy+68+i*24), ln, font=f_l, fill=tuple(MUTED))
        sx += 200

    draw.text((100, H-280), "🌀 Cyclone Detection & Early Warning System",
              font=f_sub, fill=WHITE)
    draw.text((100, H-230), "Agentic AI · IBM Bob · IBM Granite LLM · watsonx.ai · ChromaDB",
              font=f_med,  fill=tuple(MUTED))

    links = [
        ("Team:",    "Sushmitha MG"),
        ("Domain:",  "Disaster Management & Climate Resilience"),
        ("Tech:",    "Python 3.12 · Streamlit · IBM Cloud (eu-gb) · Plotly"),
        ("App:",     "http://localhost:8501"),
    ]
    lx = 100; ly = H - 170
    for label, val in links:
        draw.text((lx, ly), f"{label}", font=load_font(20,True), fill=tuple(ACCENT))
        draw.text((lx+140, ly), val, font=load_font(20), fill=WHITE)
        ly += 32

    footer_band(img)
    return img


# ── SCRIPT ────────────────────────────────────────────────────────────────────
SLIDES = [
    (slide_title,        25, "Welcome to Cyclone Guard AI — an Agentic AI-powered Cyclone Detection and Early Warning System, built using IBM Bob, IBM Granite Large Language Model, and IBM Cloud. This system protects millions of coastal residents across India from devastating cyclones along the Bay of Bengal and Arabian Sea."),

    (slide_problem,      28, "India faces 5 to 6 cyclones every year. Cyclone Biparjoy in 2023 alone affected over one million people. Cyclone Fani in 2019 caused 8.1 billion dollars in economic damage. The core challenge is delayed identification of cyclone formation, limited real-time monitoring, and the absence of location-specific early warnings for coastal communities. Our AI system solves this by detecting cyclones 72 hours in advance."),

    (slide_architecture, 30, "Our system uses a 4-phase supervised multi-agent pipeline. Phase 1 runs Weather Analysis and Cyclone Detection agents in parallel using IBM watsonx. Phase 2 runs Track Prediction using Google Gemini and Intensity Prediction using Groq. Phase 3 handles Impact Assessment and Early Warning generation. Phase 4 generates the final Disaster Response plan. Every agent uses a ReAct loop — Think, Act, Observe — with ChromaDB long-term memory and MCP registered tools."),

    (slide_agents,       28, "The system has 7 specialized AI agents. The Weather Analysis Agent processes atmospheric pressure, wind speed, sea surface temperature, and humidity. The Cyclone Detection Agent identifies formation signatures from satellite imagery. The Tracking Agent predicts the 72-hour trajectory. The Intensity Prediction Agent detects rapid intensification. The Impact Assessment Agent evaluates risk to 1.95 million coastal residents. The Early Warning Agent generates RED, ORANGE, and YELLOW district alerts. Finally, the Disaster Response Agent creates evacuation and resource allocation plans."),

    (slide_cyclone_map,  28, "The centerpiece of our Mission Control Dashboard is an animated 72-hour cyclone track forecast. Built using Plotly frames animation, the cyclone eye pulses with each frame, spiral wind bands rotate around the eye, and the track line draws itself step by step. The intensity color automatically shifts from green for Tropical Storm, through yellow, orange, and red as the storm reaches Extremely Severe Cyclonic Storm intensity. Users can play, pause, or manually scrub through the 72-hour forecast using a time slider."),

    (slide_features,     28, "The system offers 6 major features. The Mission Control Dashboard provides an animated cyclone map with 5 KPI cards and agent pipeline status. The 9-category Guardrails system runs 40 plus safety checks including injection detection, hallucination prevention, P-I-I masking, and human-in-the-loop escalation. The LLM Comparison Benchmark tests all 4 providers side by side. The Agent Observability page shows full ReAct execution traces. The AI Governance dashboard tracks 15 named policies with an immutable audit trail aligned with NDMA and IMD guidelines. Finally, the Coastal Zone Explorer maps risk across 5 Indian coastal divisions."),

    (slide_demo,         28, "Here is Cyclone VARUNA — an Extremely Severe Cyclonic Storm in the Bay of Bengal with maximum winds of 130 knots. The system has issued RED alerts for Visakhapatnam and Srikakulam districts, placing 890,000 and 320,000 residents respectively at critical risk. The Impact Assessment Agent identifies 1.95 million people at risk across 5 districts. The Disaster Response Agent has activated evacuation for 847 coastal villages, deployed 14 NDRF battalions, activated 312 cyclone shelters, and initiated SMS broadcast to 3.2 million coastal residents."),

    (slide_cta,          20, "Thank you for watching our demo. Cyclone Guard AI was built entirely using IBM Bob — with 75 Python files generated across 7 AI agents, a multi-LLM gateway, ChromaDB memory, MCP tools, guardrails, and governance modules. The system is live at localhost 8501 and ready for integration with real IMD and NOAA data feeds. Together, we can use Agentic AI to protect coastal communities and save lives. Thank you."),
]


def make_tts(text: str, idx: int) -> str:
    """Generate TTS audio file and return path."""
    path = os.path.join(TMP, f"voice_{idx:02d}.mp3")
    if os.path.exists(path):
        return path
    print(f"  Generating TTS for slide {idx+1}…")
    tts = gTTS(text=text, lang="en", slow=False)
    tts.save(path)
    return path


def make_slide_clip(img_func, duration: float, voice_path: str, idx: int):
    """Create a video clip for one slide: static image + voice audio."""
    print(f"  Building clip for slide {idx+1}/{len(SLIDES)}…")

    # Render image
    img = img_func()
    arr = np.array(img)  # (H, W, 3) uint8

    # Audio
    audio = AudioFileClip(voice_path)
    actual_dur = max(duration, audio.duration + 1.0)

    # Image clip
    clip = ImageClip(arr, duration=actual_dur)

    # Set audio (pad or trim)
    clip = clip.with_audio(audio)
    clip = clip.with_fps(FPS)
    return clip


def main():
    print("=" * 60)
    print("  Cyclone EWS — Video Generator")
    print("=" * 60)

    # Step 1: Generate all TTS files
    print("\n[1/3] Generating voiceovers…")
    voice_files = []
    for i, (_, _, script) in enumerate(SLIDES):
        vf = make_tts(script, i)
        voice_files.append(vf)

    # Step 2: Build slide clips
    print("\n[2/3] Rendering slides…")
    clips = []
    for i, ((img_func, dur, _), vf) in enumerate(zip(SLIDES, voice_files)):
        c = make_slide_clip(img_func, dur, vf, i)
        clips.append(c)

    # Step 3: Concatenate and export
    print("\n[3/3] Encoding final video…")
    final = concatenate_videoclips(clips, method="compose")

    print(f"\nWriting: {OUT}")
    print(f"Total duration: {final.duration:.1f}s")
    final.write_videofile(
        OUT,
        fps=FPS,
        codec="libx264",
        audio_codec="aac",
        preset="fast",
        ffmpeg_params=["-crf", "23"],
        logger="bar",
    )

    # Cleanup
    for c in clips:
        c.close()
    final.close()

    print(f"\n✅ Done! Video saved to:\n   {OUT}")


if __name__ == "__main__":
    main()
