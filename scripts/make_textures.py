"""Generate 2D graphics used inside the 3D scene:
 - TV motion-graphics loop (HUQUQ MAKTABI), image sequence
 - classroom TV slides
 - framed educational prints (law/history, languages)
 - whiteboard writing
Run with: python scripts/make_textures.py
"""
import math, os, random
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEX = os.path.join(ROOT, "assets", "textures")
TV = os.path.join(ROOT, "assets", "tv_logo")
os.makedirs(TEX, exist_ok=True); os.makedirs(TV, exist_ok=True)

F = "/usr/share/fonts/opentype/inter/"
def font(w, s): return ImageFont.truetype(F + f"Inter-{w}.otf", s)
def sfont(s): return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf", s)

NAVY = (14, 24, 44); GOLD = (214, 178, 102); WHITE = (245, 247, 250)
SPECS = ["PROKURATURA", "ICHKI ISHLAR ORGANLARI", "ADLIYA", "SUD TIZIMI",
         "YURIDIK KADRLAR", "DAVLAT XIZMATI"]

def ctext(d, xy, t, f, fill, anchor="mm", spacing=0):
    d.text(xy, t, font=f, fill=fill, anchor=anchor)

def scales_icon(d, cx, cy, s, col, w=6):
    """Simple scales-of-justice line icon."""
    d.line([(cx, cy - s), (cx, cy + s * 0.9)], fill=col, width=w)
    d.line([(cx - s * 0.9, cy - s * 0.6), (cx + s * 0.9, cy - s * 0.6)], fill=col, width=w)
    d.ellipse([cx - w * 1.5, cy - s - w * 1.5, cx + w * 1.5, cy - s + w * 1.5], fill=col)
    for sx in (-1, 1):
        px = cx + sx * s * 0.9
        d.line([(px, cy - s * 0.6), (px - s * 0.3, cy + s * 0.1)], fill=col, width=max(2, w // 2))
        d.line([(px, cy - s * 0.6), (px + s * 0.3, cy + s * 0.1)], fill=col, width=max(2, w // 2))
        d.chord([px - s * 0.36, cy - s * 0.1, px + s * 0.36, cy + s * 0.32], 0, 180, fill=col)
    d.rectangle([cx - s * 0.45, cy + s * 0.85, cx + s * 0.45, cy + s * 0.95], fill=col)

# ---------------------------------------------------------------- TV loop
def tv_frames(n=96, W=1280, H=720):
    random.seed(3)
    parts = [(random.random() * W, random.random() * H, random.uniform(.5, 2.2), random.random()) for _ in range(70)]
    for i in range(n):
        t = i / n
        im = Image.new("RGB", (W, H))
        px = im.load()
        # vertical gradient background
        g = Image.linear_gradient("L").resize((W, H))
        bg = Image.merge("RGB", [g.point(lambda v: int(8 + v * 0.06)), g.point(lambda v: int(16 + v * 0.08)), g.point(lambda v: int(34 + v * 0.12))])
        im.paste(bg)
        d = ImageDraw.Draw(im, "RGBA")
        # drifting particles
        for (x, y, r, ph) in parts:
            yy = (y - t * 120 * r) % H
            a = int(60 + 80 * (0.5 + 0.5 * math.sin(2 * math.pi * (t + ph))))
            d.ellipse([x - r, yy - r, x + r, yy + r], fill=(214, 178, 102, a))
        # rotating rings
        cx, cy = W // 2, 250
        for k, (rad, wid, sp) in enumerate([(150, 3, 1), (175, 2, -0.6), (200, 1, 0.35)]):
            a0 = 360 * t * sp
            d.arc([cx - rad, cy - rad, cx + rad, cy + rad], a0, a0 + 250, fill=GOLD + (220,), width=wid)
        scales_icon(d, cx, cy, 80, WHITE, 7)
        # sweeping light bar
        sx = int((t * 1.6 % 1.6 - 0.3) * W)
        glow = Image.new("L", (W, H), 0); gd = ImageDraw.Draw(glow)
        gd.polygon([(sx, 0), (sx + 90, 0), (sx - 110, H), (sx - 200, H)], fill=40)
        glow = glow.filter(ImageFilter.GaussianBlur(30))
        im = Image.composite(Image.new("RGB", (W, H), (255, 255, 255)), im, glow)
        d = ImageDraw.Draw(im, "RGBA")
        ctext(d, (W // 2, 480), "HUQUQ MAKTABI", font("ExtraBold", 92), WHITE)
        d.rectangle([W // 2 - 260, 540, W // 2 + 260, 543], fill=GOLD)
        # rotating specialization caption
        k = int(t * len(SPECS)) % len(SPECS)
        loc = (t * len(SPECS)) % 1
        alpha = int(255 * min(1, loc * 5, (1 - loc) * 5))
        ctext(d, (W // 2, 600), SPECS[k], font("SemiBold", 44), (214, 178, 102, alpha))
        ctext(d, (W // 2, 668), "Huquq-tartibot va davlat xizmatiga tayyorlov markazi", font("Regular", 26), (200, 208, 222, 200))
        im.save(os.path.join(TV, f"tv_{i + 1:04d}.png"))

# ---------------------------------------------------------------- slides
def slide(name, title, lines, accent):
    W, H = 1280, 720
    im = Image.new("RGB", (W, H), (248, 248, 246)); d = ImageDraw.Draw(im)
    d.rectangle([0, 0, W, 120], fill=accent)
    d.text((60, 60), title, font=font("Bold", 54), fill=WHITE, anchor="lm")
    for i, l in enumerate(lines):
        y = 200 + i * 95
        d.ellipse([70, y - 12, 94, y + 12], fill=accent)
        d.text((120, y), l, font=font("Medium", 42), fill=(40, 44, 52), anchor="lm")
    d.text((W - 50, H - 40), "HUQUQ MAKTABI", font=font("Bold", 28), fill=accent, anchor="rm")
    im.save(os.path.join(TEX, name))

# ---------------------------------------------------------------- prints
def print_scales():
    W, H = 900, 1200
    im = Image.new("RGB", (W, H), (236, 230, 216)); d = ImageDraw.Draw(im)
    d.rectangle([40, 40, W - 40, H - 40], outline=(60, 50, 40), width=4)
    scales_icon(d, W // 2, 470, 230, (52, 44, 36), 12)
    ctext(d, (W // 2, 860), "ADOLAT", sfont(110), (52, 44, 36))
    ctext(d, (W // 2, 960), "Qonun ustuvorligi — huquqiy davlat asosi", font("Medium", 32), (90, 76, 60))
    ctext(d, (W // 2, 1080), "LEX  •  IUS  •  IUSTITIA", font("SemiBold", 30), (120, 100, 78))
    im.save(os.path.join(TEX, "print_law.png"))

def print_history():
    W, H = 900, 1200
    im = Image.new("RGB", (W, H), (28, 34, 46)); d = ImageDraw.Draw(im)
    ctext(d, (W // 2, 120), "HUQUQ TARIXI", sfont(78), GOLD)
    ctext(d, (W // 2, 200), "Davlat va huquq tarixi xronologiyasi", font("Medium", 30), (200, 205, 215))
    d.line([(150, 280), (150, 1100)], fill=GOLD, width=5)
    ev = [("Mil. avv. XVIII", "Hammurapi qonunlari"), ("Mil. avv. V", "XII jadval qonunlari"),
          ("1215", "Buyuk erkinliklar xartiyasi"), ("XIV asr", "Temur tuzuklari"),
          ("1948", "Inson huquqlari deklaratsiyasi"), ("1992", "O'zbekiston Konstitutsiyasi")]
    for i, (y_, t_) in enumerate(ev):
        y = 320 + i * 135
        d.ellipse([136, y - 14, 164, y + 14], fill=GOLD)
        d.text((200, y - 22), y_, font=font("Bold", 36), fill=WHITE, anchor="lm")
        d.text((200, y + 24), t_, font=font("Regular", 32), fill=(190, 196, 208), anchor="lm")
    im.save(os.path.join(TEX, "print_history.png"))

def print_world():
    W, H = 900, 1200
    random.seed(7)
    im = Image.new("RGB", (W, H), (240, 242, 244)); d = ImageDraw.Draw(im)
    ctext(d, (W // 2, 110), "WORLD OF LANGUAGES", font("ExtraBold", 62), (24, 60, 110))
    # stylised dotted globe
    cx, cy, R = W // 2, 560, 330
    for lat in range(-80, 81, 8):
        for lon in range(-180, 180, 6):
            la, lo = math.radians(lat), math.radians(lon)
            x, y, z = math.cos(la) * math.sin(lo), math.sin(la), math.cos(la) * math.cos(lo)
            if z < 0: continue
            land = (math.sin(lo * 2.1 + 1) + math.cos(la * 3.3 - lo) + math.sin(lo * 5 + la * 2) * 0.5) > 0.4
            col = (32, 90, 160) if land else (180, 196, 214)
            r = 5.5 * (0.4 + 0.6 * z)
            d.ellipse([cx + x * R - r, cy - y * R - r, cx + x * R + r, cy - y * R + r], fill=col)
    ctext(d, (W // 2, 990), "English • Русский • Deutsch • Türkçe • Español", font("SemiBold", 34), (40, 50, 64))
    ctext(d, (W // 2, 1060), "Til — dunyoga ochilgan eshik", font("Medium", 32), (90, 100, 112))
    im.save(os.path.join(TEX, "print_world.png"))

def print_hello():
    W, H = 900, 1200
    im = Image.new("RGB", (W, H), (22, 74, 120)); d = ImageDraw.Draw(im)
    words = [("Hello", 120), ("Salom", 104), ("Привет", 92), ("Bonjour", 86), ("Hallo", 96), ("Merhaba", 84), ("Hola", 100)]
    y = 150
    for i, (w, s) in enumerate(words):
        col = WHITE if i % 2 == 0 else (250, 200, 90)
        ctext(d, (W // 2, y), w, font("ExtraBold", s), col); y += s + 38
    ctext(d, (W // 2, H - 90), "INTERNATIONAL EDUCATION", font("Bold", 36), (180, 210, 235))
    im.save(os.path.join(TEX, "print_hello.png"))

def whiteboard(name, lines, diagram):
    W, H = 2048, 1024
    im = Image.new("RGB", (W, H), (250, 251, 252)); d = ImageDraw.Draw(im)
    hf = ImageFont.truetype("/usr/share/fonts/truetype/freefont/FreeSansOblique.ttf", 74)
    bf = ImageFont.truetype("/usr/share/fonts/truetype/freefont/FreeSansOblique.ttf", 54)
    d.text((110, 110), lines[0], font=hf, fill=(20, 50, 140))
    d.line([(110, 205), (1000, 212)], fill=(20, 50, 140), width=6)
    for i, l in enumerate(lines[1:]):
        d.text((130, 270 + i * 100), l, font=bf, fill=(30, 30, 36) if i % 2 == 0 else (170, 30, 30))
    diagram(d)
    # faint ghosting of old erasures
    im = im.filter(ImageFilter.GaussianBlur(1.1))
    im.save(os.path.join(TEX, name))

def law_diag(d):
    bf = ImageFont.truetype("/usr/share/fonts/truetype/freefont/FreeSansOblique.ttf", 48)
    d.rectangle([1350, 180, 1780, 290], outline=(20, 50, 140), width=6); d.text((1565, 235), "Konstitutsiya", font=bf, fill=(20, 50, 140), anchor="mm")
    for i, t in enumerate(["Qonun", "Farmon", "Qaror"]):
        x = 1250 + i * 230
        d.line([(1565, 290), (x + 90, 430)], fill=(30, 30, 36), width=5)
        d.rectangle([x, 430, x + 190, 520], outline=(30, 30, 36), width=5); d.text((x + 95, 475), t, font=bf, fill=(30, 30, 36), anchor="mm")

def lang_diag(d):
    bf = ImageFont.truetype("/usr/share/fonts/truetype/freefont/FreeSansOblique.ttf", 52)
    rows = [("I", "am", "a student"), ("You", "are", "a lawyer"), ("She", "is", "a judge")]
    for i, r in enumerate(rows):
        for j, w in enumerate(r):
            d.text((1250 + j * 230, 220 + i * 110), w, font=bf, fill=[(20, 50, 140), (170, 30, 30), (30, 30, 36)][j])
    d.rectangle([1230, 190, 1900, 540], outline=(20, 120, 60), width=5)

if __name__ == "__main__":
    tv_frames()
    slide("slide_law.png", "Davlat va huquq nazariyasi", ["Huquq manbalari", "Konstitutsiyaviy tuzum", "Jinoyat huquqi asoslari", "Amaliy mashg'ulot: kazuslar"], (20, 40, 80))
    slide("slide_lang.png", "English for Law Enforcement", ["Legal vocabulary: 50 terms", "Speaking: court procedures", "Listening practice", "IELTS / CEFR B2 preparation"], (16, 92, 150))
    print_scales(); print_history(); print_world(); print_hello()
    whiteboard("wb_law.png", ["Huquq asoslari — 3-mavzu", "1. Normativ-huquqiy hujjatlar ierarxiyasi", "2. Qonun ustuvorligi tamoyili", "3. Huquqiy javobgarlik turlari", "Uyga vazifa: 12-15 betlar"], law_diag)
    whiteboard("wb_lang.png", ["English — Unit 7: The Courtroom", "judge • prosecutor • defendant", "witness • evidence • verdict", "Present Simple: to be", "Homework: p. 48, ex. 3-5"], lang_diag)
    print("textures done")
