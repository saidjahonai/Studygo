"""Dimensioned floor plan (same coordinates as build_scene.py). Output: docs/floor_plan.png + .pdf"""
import os, math
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Arc, Circle, Polygon

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "docs")
os.makedirs(OUT, exist_ok=True)
plt.rcParams["font.family"] = "DejaVu Sans"

fig, ax = plt.subplots(figsize=(16.5, 11.7))  # A3 landscape
ax.set_aspect("equal"); ax.axis("off")
ax.set_xlim(-1.6, 13.6); ax.set_ylim(-3.6, 8.2)

WALL = "#1d1f24"; FURN = "#8a7a64"; OAK = "#e6d3b3"; GLASS = "#5aa7d6"

def rect(x0, y0, x1, y1, fc="none", ec=FURN, lw=1, z=2, hatch=None, alpha=1):
    ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, fc=fc, ec=ec, lw=lw, zorder=z, hatch=hatch, alpha=alpha))

def chair(x, y, rot):
    a = math.radians(rot)
    pts = [(-0.235, -0.235), (0.235, -0.235), (0.235, 0.235), (-0.235, 0.235)]
    P = [(x + px * math.cos(a) - py * math.sin(a), y + px * math.sin(a) + py * math.cos(a)) for px, py in pts]
    ax.add_patch(Polygon(P, closed=True, fc="#c9ccd2", ec="#5a5e66", lw=0.8, zorder=3))
    bx = [(-0.235, 0.2), (0.235, 0.2), (0.235, 0.26), (-0.235, 0.26)]
    B = [(x + px * math.cos(a) - py * math.sin(a), y + px * math.sin(a) + py * math.cos(a)) for px, py in bx]
    ax.add_patch(Polygon(B, closed=True, fc="#5a5e66", ec="#5a5e66", lw=0.8, zorder=3))

def dim(x0, y0, x1, y1, txt, off=0.0, horiz=True, fs=10):
    if horiz:
        y = y0 + off
        ax.annotate("", (x0, y), (x1, y), arrowprops=dict(arrowstyle="<->", lw=0.9, color="#333"))
        ax.plot([x0, x0], [y0, y], color="#777", lw=0.5); ax.plot([x1, x1], [y1, y], color="#777", lw=0.5)
        ax.text((x0 + x1) / 2, y + 0.08, txt, ha="center", va="bottom", fontsize=fs)
    else:
        x = x0 + off
        ax.annotate("", (x, y0), (x, y1), arrowprops=dict(arrowstyle="<->", lw=0.9, color="#333"))
        ax.plot([x0, x], [y0, y0], color="#777", lw=0.5); ax.plot([x1, x], [y1, y1], color="#777", lw=0.5)
        ax.text(x - 0.1, (y0 + y1) / 2, txt, ha="right", va="center", fontsize=fs, rotation=90)

# floors
rect(0, 0, 3.94, 6, fc="#f3ece0", ec="none", z=0); rect(8.06, 0, 12, 6, fc="#f3ece0", ec="none", z=0)
rect(3.94, 0, 8.06, 6, fc="#ecebe8", ec="none", z=0)
# exterior walls (250 mm), with windows / storefront
W = 0.25
rect(-W, 6, 12 + W, 6 + W, fc=WALL, ec=WALL, z=5); rect(-W, -W, 0, 6, fc=WALL, ec=WALL, z=5); rect(12, -W, 12 + W, 6, fc=WALL, ec=WALL, z=5)
for zx in (0, 8):
    segs = [(zx, zx + 0.5), (zx + 1.9, zx + 2.1), (zx + 3.5, zx + 4)]
    for a, b in segs: rect(a, -W, b, 0, fc=WALL, ec=WALL, z=5)
    for a, b in [(zx + 0.5, zx + 1.9), (zx + 2.1, zx + 3.5)]:
        rect(a, -W, b, 0, fc="white", ec=WALL, lw=0.8, z=5); ax.plot([a, b], [-0.14, -0.14], color=GLASS, lw=2, zorder=6)
# storefront glass partition + door
ax.plot([4.0, 5.40], [-0.12, -0.12], color=GLASS, lw=3, zorder=6); ax.plot([6.60, 8.0], [-0.12, -0.12], color=GLASS, lw=3, zorder=6)
for a in (4.0, 5.40, 6.55, 7.94): rect(a, -0.16, a + 0.06, -0.08, fc=WALL, ec=WALL, z=6)
ax.plot([5.45, 5.45], [-0.12, 0.98], color=GLASS, lw=2.5, zorder=6)
ax.add_patch(Arc((5.45, -0.12), 2.2, 2.2, theta1=0, theta2=90, color=GLASS, lw=0.8, ls="--", zorder=6))
# partitions (120 mm) with door openings
for px in (4.0, 8.0):
    rect(px - 0.06, 0, px + 0.06, 3.1, fc="#4a4d55", ec="#4a4d55", z=5); rect(px - 0.06, 4.1, px + 0.06, 6, fc="#4a4d55", ec="#4a4d55", z=5)
ax.plot([3.92, 3.92], [4.12, 5.08], color=FURN, lw=2, zorder=6); ax.add_patch(Arc((3.92, 4.12), 1.92, 1.92, theta1=180, theta2=270, color=FURN, lw=0.8, ls="--"))
ax.plot([8.08, 8.08], [4.12, 5.08], color=FURN, lw=2, zorder=6); ax.add_patch(Arc((8.08, 4.12), 1.92, 1.92, theta1=270, theta2=360, color=FURN, lw=0.8, ls="--"))

# ---- Admin + coworking
rect(4.06, 0.6, 4.70, 2.4, fc=OAK); rect(7.30, 0.6, 7.94, 2.4, fc=OAK)
for y in (1.05, 1.95): chair(5.05, y, 90); chair(6.95, y, -90)
rect(5.2, 2.8, 6.8, 3.6, fc=OAK)
for x in (5.6, 6.4): chair(x, 2.42, 180); chair(x, 3.98, 0)
rect(4.95, 2.05, 7.05, 4.35, fc="none", ec="#b0a89a", lw=0.8, z=1)
rect(5.13, 4.55, 6.87, 5.32, fc="#f5f5f2", ec="#555", lw=1.2); rect(5.15, 4.58, 6.85, 4.66, fc=OAK, ec=FURN)
ax.add_patch(Circle((6.0, 5.62), 0.3, fc="#2a2a2a", ec="#2a2a2a", zorder=3))
rect(4.06, 4.3, 4.48, 5.5, fc=OAK); rect(4.06, 4.40, 4.11, 5.62, fc="#111", ec="#111", z=4)
ax.add_patch(Circle((4.62, 5.6), 0.22, fc="white", ec="#3a7a3a", lw=1.5, zorder=3)); ax.add_patch(Circle((7.38, 5.6), 0.22, fc="white", ec="#3a7a3a", lw=1.5, zorder=3))
rect(7.52, 4.46, 7.84, 4.78, fc="white", ec="#3a6ea5", lw=1.2); ax.add_patch(Circle((7.68, 4.62), 0.12, fc="#bcdcf2", ec="#3a6ea5", zorder=4))
rect(4.06, 5.88, 7.94, 6.0, fc="#17233a", ec="#17233a", z=5)
ax.plot([4.42, 7.58], [5.86, 5.86], color="#9fc2ff", lw=3, zorder=6)
ax.annotate("", (6.0, 0.25), (6.0, 2.55), arrowprops=dict(arrowstyle="<-", lw=1.2, color="#2b7", ls="--"))
ax.text(6.0, 1.6, "circulation\n1500", ha="center", fontsize=7.5, color="#2b7", rotation=90, va="center")

# ---- classrooms
def classroom(mirror):
    X = (lambda x: 12 - x) if mirror else (lambda x: x)
    def R(x0, y0, x1, y1, **k):
        a, b = sorted((X(x0), X(x1))); rect(a, y0, b, y1, **k)
    for rx0 in (1.45, 2.6):
        for (y0, y1) in [(0.55, 2.15), (3.85, 5.45)]:
            R(rx0, y0, rx0 + 0.55, y1, fc=OAK)
            for k in range(3): chair(X(rx0 + 0.86), y0 + 0.27 + k * 0.53, 90 if mirror else -90)
    R(0.35, 0.5, 1.05, 1.75, fc=OAK); chair(X(0.62), 1.12, -90 if mirror else 90)
    R(0.0, 1.68, 0.05, 4.32, fc="white", ec="#333", lw=2)
    R(0.0, 4.55, 0.07, 5.77, fc="#111", ec="#111")
    R(3.0, 5.62, 3.85, 5.99, fc=OAK)
    for cx in (1.35, 2.85): R(cx - 0.36, 5.93, cx + 0.36, 6.0, fc="#222", ec="#222", z=6)
classroom(False); classroom(True)

# labels
def lab(x, y, t, s=12, w="bold", c="#1d1f24"): ax.text(x, y, t, ha="center", va="center", fontsize=s, fontweight=w, color=c, zorder=8)
lab(2.0, 3.0, "ZONE 1\nHUQUQ VA TARIX\nLaw & History", 11)
lab(10.0, 3.0, "ZONE 3\nXORIJIY TILLAR\nForeign Languages", 11)
lab(6.0, 1.5, "", 1)
ax.text(6.0, 6.55, "SIGNATURE WALL: illuminated logo,\nnavy acoustic slats, LED contours", ha="center", va="center", fontsize=7.5, color="#17233a")
lab(6.0, 3.2, "COWORKING\n(central table)", 7.5, "normal")
lab(4.38, 1.5, "cowork\ncounter", 7, "normal"); lab(7.62, 1.5, "cowork\ncounter", 7, "normal")
lab(6.0, 4.94, "ADMINISTRATOR / RECEPTION", 6.5, "bold")
lab(7.68, 4.2, "water\ncooler", 6.5, "normal"); lab(4.27, 4.0, "TV +\ncredenza", 6.5, "normal")
lab(6.0, -0.55, "GLASS PARTITION + GLASS ENTRANCE DOOR (1100)", 8, "bold", "#2a6fa0")
lab(6.0, 7.2, "ZONE 2 — ADMINISTRATION + COWORKING (one combined space)", 11)
lab(1.3, 4.95, "TV", 7, "normal"); lab(0.35, 3.0, "WB", 7, "normal"); lab(10.7, 4.95, "TV", 7, "normal"); lab(11.65, 3.0, "WB", 7, "normal")
ax.text(2.0, 5.7, "2 framed legal/history prints", ha="center", fontsize=6.5); ax.text(10.0, 5.7, "2 framed language prints", ha="center", fontsize=6.5)

# dimensions
dim(0, -W, 12, -W, "12 000", off=-2.35, fs=12)
dim(0, -W, 4, -W, "4 000", off=-1.6); dim(4, -W, 8, -W, "4 000", off=-1.6); dim(8, -W, 12, -W, "4 000", off=-1.6)
dim(4.0, -0.12, 5.45, -0.12, "1 450", off=-0.95, fs=8); dim(5.45, -0.12, 6.55, -0.12, "1 100", off=-0.95, fs=8); dim(6.55, -0.12, 8.0, -0.12, "1 450", off=-0.95, fs=8)
dim(-W, 0, -W, 6, "6 000", off=-0.75, horiz=False, fs=12)
dim(12.25, 3.1, 12.25, 4.1, "", off=0.0, horiz=False)
ax.text(12.55, 3.6, "door\n1000", fontsize=7.5, va="center")
dim(12 + W, 0, 12 + W, 3.1, "3 100", off=0.9, horiz=False, fs=8); dim(12 + W, 4.1, 12 + W, 6, "1 900", off=0.9, horiz=False, fs=8)
for zx in (0, 8):
    dim(zx + 0.5, 6.25, zx + 1.9, 6.25, "1 400 win", off=0.25, fs=7); dim(zx + 2.1, 6.25, zx + 3.5, 6.25, "1 400 win", off=0.25, fs=7) if False else None

# north arrow + scale + title
ax.annotate("N", xy=(13.1, 7.6), xytext=(13.1, 6.9), ha="center", fontsize=12, fontweight="bold", arrowprops=dict(arrowstyle="-|>", lw=1.5, color="#111"))
for i in range(5): rect(9.0 + i, -3.35, 10.0 + i, -3.25, fc="#111" if i % 2 == 0 else "white", ec="#111", lw=0.6, z=8)
ax.text(9.0, -3.15, "0", fontsize=7); ax.text(14.0, -3.15, "5 m", fontsize=7, ha="right")
ax.text(-1.5, 7.95, "HUQUQ MAKTABI — Floor Plan", fontsize=18, fontweight="bold")
ax.text(-1.5, 7.55, "Building 12.0 × 6.0 m = 72 m²  ·  ceiling height 3.20 m  ·  dimensions in mm  ·  scale 1:50 @ A3", fontsize=10, color="#444")
ax.text(-1.5, -3.3, "STREET / ENTRANCE PLAZA  ↓", fontsize=9, color="#666")
ax.text(-1.5, -2.95, "Zone areas (interior, to partition centre-lines): Z1 24.0 m² · Z2 24.0 m² · Z3 24.0 m²", fontsize=8.5, color="#444")

fig.savefig(os.path.join(OUT, "floor_plan.png"), dpi=200, bbox_inches="tight", facecolor="white")
fig.savefig(os.path.join(OUT, "floor_plan.pdf"), bbox_inches="tight", facecolor="white")
print("floor plan saved")
