"""Dimensioned top-down floor plan, generated from the same coordinates as build_scene.py.
Output: docs/floor_plan.png + docs/floor_plan.pdf (A3, mm)."""
import os, math
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Arc, Circle, Polygon

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "docs"); os.makedirs(OUT, exist_ok=True)
plt.rcParams["font.family"] = "DejaVu Sans"

# geometry (m) — identical to build_scene.py
WT = 0.20; IX0, IX1, IY0, IY1 = 0.2, 11.8, 0.2, 5.8
LAW = (0.20, 3.90); P1 = (3.90, 4.00); ADM = (4.00, 8.00); P2 = (8.00, 8.10); LANG = (8.10, 11.80)
CDY = (0.35, 1.35); WINDOWS = [(0.70, 2.00), (2.10, 3.40), (8.60, 9.90), (10.00, 11.30)]
ROWS_Y0 = (3.95, 2.75, 1.55); COLS = ((0.45, 1.65), (2.45, 3.65)); DESK_D = 0.5

fig, ax = plt.subplots(figsize=(16.5, 11.7))
ax.set_aspect("equal"); ax.axis("off"); ax.set_xlim(-1.7, 13.7); ax.set_ylim(-7.7, 8.5)
WALL = "#1d1f24"; OAK = "#e6d3b3"; FURN = "#8a7a64"; GLASS = "#3d9ad6"; CIRC = "#1aa36b"

def rect(x0, y0, x1, y1, fc="none", ec=FURN, lw=1, z=2, ls="-"):
    ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, fc=fc, ec=ec, lw=lw, zorder=z, ls=ls))

def chair(x, y, rz):
    """rz as in build_scene: 0 faces -Y, 180 faces +Y, -90 faces -X, 90 faces +X."""
    a = math.radians(rz)
    def tr(pts): return [(x + px * math.cos(a) - py * math.sin(a), y + px * math.sin(a) + py * math.cos(a)) for px, py in pts]
    ax.add_patch(Polygon(tr([(-0.235, -0.235), (0.235, -0.235), (0.235, 0.215), (-0.235, 0.215)]), fc="#c9ccd2", ec="#5a5e66", lw=0.7, zorder=3))
    ax.add_patch(Polygon(tr([(-0.235, 0.19), (0.235, 0.19), (0.235, 0.26), (-0.235, 0.26)]), fc="#5a5e66", ec="#5a5e66", lw=0.7, zorder=3))

def dim(p0, p1, txt, off, horiz=True, fs=9, col="#222"):
    (x0, y0), (x1, y1) = p0, p1
    if horiz:
        y = y0 + off
        ax.annotate("", (x0, y), (x1, y), arrowprops=dict(arrowstyle="<->", lw=0.8, color=col, shrinkA=0, shrinkB=0))
        for xx, yy in ((x0, y0), (x1, y1)): ax.plot([xx, xx], [yy, y], color="#999", lw=0.4)
        ax.text((x0 + x1) / 2, y + 0.06, txt, ha="center", va="bottom", fontsize=fs, color=col)
    else:
        x = x0 + off
        ax.annotate("", (x, y0), (x, y1), arrowprops=dict(arrowstyle="<->", lw=0.8, color=col, shrinkA=0, shrinkB=0))
        for xx, yy in ((x0, y0), (x1, y1)): ax.plot([xx, x], [yy, yy], color="#999", lw=0.4)
        ax.text(x - 0.07, (y0 + y1) / 2, txt, ha="right", va="center", fontsize=fs, rotation=90, color=col)

# floors
rect(*LAW[:1], IY0, LAW[1], IY1, fc="#f3ece0", ec="none", z=0) if False else None
rect(LAW[0], IY0, LAW[1], IY1, fc="#f3ece0", ec="none", z=0); rect(LANG[0], IY0, LANG[1], IY1, fc="#f3ece0", ec="none", z=0)
rect(ADM[0], IY0, ADM[1], IY1, fc="#ecebe8", ec="none", z=0)
# external walls
rect(0, IY1, 12, 6, fc=WALL, ec=WALL, z=5); rect(0, 0, WT, IY1, fc=WALL, ec=WALL, z=5); rect(IX1, 0, 12, IY1, fc=WALL, ec=WALL, z=5)
for (x0, x1, wins) in [(WT, 4.0, WINDOWS[:2]), (8.0, IX1, WINDOWS[2:])]:
    edges = [x0] + [v for w in wins for v in w] + [x1]
    for i in range(0, len(edges), 2): rect(edges[i], 0, edges[i + 1], WT, fc=WALL, ec=WALL, z=5)
    for (a, b) in wins:
        rect(a, 0, b, WT, fc="white", ec=WALL, lw=0.8, z=5); ax.plot([a, b], [0.1, 0.1], color=GLASS, lw=2, zorder=6)
# storefront (glass partition) + central entrance door
ax.plot([4.06, 5.40], [0.1, 0.1], color=GLASS, lw=3.2, zorder=6); ax.plot([6.60, 7.94], [0.1, 0.1], color=GLASS, lw=3.2, zorder=6)
for a in (4.0, 5.40, 6.55, 7.94): rect(a, 0.06, a + 0.06 if a not in (5.40,) else 5.45, 0.14, fc=WALL, ec=WALL, z=6)
ax.plot([5.45, 5.45], [0.1, 1.2], color=GLASS, lw=2.5, zorder=6)
ax.add_patch(Arc((5.45, 0.1), 2.2, 2.2, theta1=0, theta2=90, color=GLASS, lw=0.8, ls="--", zorder=6))
ax.plot([6.0, 6.0], [-0.35, 0.0], color="#d33", lw=0.8); ax.text(6.0, -0.42, "℄ entrance = ℄ facade (x = 6 000)", ha="center", va="top", fontsize=7.5, color="#d33")
# partitions + classroom doors
for (a, b) in (P1, P2):
    rect(a, IY0, b, CDY[0], fc="#4a4d55", ec="#4a4d55", z=5); rect(a, CDY[1], b, IY1, fc="#4a4d55", ec="#4a4d55", z=5)
ax.plot([3.86, 3.86], [CDY[1] + 0.02, CDY[1] + 0.98], color=FURN, lw=2.2, zorder=6)
ax.add_patch(Arc((3.86, CDY[1]), 1.92, 1.92, theta1=180, theta2=270, color=FURN, lw=0.8, ls="--"))
ax.plot([8.14, 8.14], [CDY[1] + 0.02, CDY[1] + 0.98], color=FURN, lw=2.2, zorder=6)
ax.add_patch(Arc((8.14, CDY[1]), 1.92, 1.92, theta1=270, theta2=360, color=FURN, lw=0.8, ls="--"))

# ---- ZONE 2 admin + coworking
rect(4.0, 1.5, 4.6, 3.7, fc=OAK); rect(7.4, 1.5, 8.0, 3.7, fc=OAK)
for y in (1.9, 2.6, 3.3): chair(4.95, y, -90); chair(7.05, y, 90)
rect(5.13, 4.48, 6.87, 5.2, fc="#f7f7f4", ec="#444", lw=1.2); rect(5.15, 4.515, 6.85, 4.59, fc=OAK, ec=FURN)
ax.add_patch(Circle((6.0, 5.33), 0.28, fc="#2a2a2a", ec="#2a2a2a", zorder=3))
rect(4.0, 4.0, 4.42, 5.2, fc=OAK); rect(4.0, 4.0, 4.05, 5.22, fc="#111", ec="#111", z=4)
for (px, py) in [(4.68, 5.4), (7.38, 5.4)]: ax.add_patch(Circle((px, py), 0.22, fc="white", ec="#3a7a3a", lw=1.6, zorder=3))
rect(7.52, 4.29, 7.84, 4.61, fc="white", ec="#3a6ea5", lw=1.2); ax.add_patch(Circle((7.68, 4.45), 0.12, fc="#bcdcf2", ec="#3a6ea5", zorder=4))
rect(4.0, 5.675, 8.0, 5.8, fc="#17233a", ec="#17233a", z=5); ax.plot([4.42, 7.58], [5.66, 5.66], color="#9fc2ff", lw=3, zorder=6)
# circulation
ax.annotate("", (6.0, 0.35), (6.0, 4.4), arrowprops=dict(arrowstyle="<-", lw=1.4, color=CIRC, ls="--"))
ax.annotate("", (3.6, 0.85), (5.4, 0.85), arrowprops=dict(arrowstyle="->", lw=1.0, color=CIRC, ls="--"))
ax.annotate("", (8.4, 0.85), (6.6, 0.85), arrowprops=dict(arrowstyle="->", lw=1.0, color=CIRC, ls="--"))
dim((5.2, 1.6), (6.8, 1.6), "aisle 1 600", 0, fs=7, col=CIRC)
lab_ = ax.text(6.0, 3.0, "open centre —\nclear view & access\nto administrator", ha="center", va="center", fontsize=7, color=CIRC, zorder=9)

# ---- classrooms
def classroom(mirror):
    X = (lambda x: 12 - x) if mirror else (lambda x: x)
    def R(x0, y0, x1, y1, **k):
        a, b = sorted((X(x0), X(x1))); rect(a, y0, b, y1, **k)
    for y0 in ROWS_Y0:
        for (c0, c1) in COLS:
            R(c0, y0, c1, y0 + DESK_D, fc=OAK)
            for dx in (0.3, 0.9): chair(X(c0 + dx), y0 - 0.30, 180)
    R(2.85, 4.8, 3.75, 5.3, fc=OAK); chair(X(3.3), 5.5, 0)
    R(0.58, 5.74, 2.62, 5.8, fc="white", ec="#222", lw=2, z=6)
    R(0.2, 4.0, 0.26, 5.22, fc="#111", ec="#111", z=6)
    for cy_ in (2.0, 3.15): R(0.2, cy_ - 0.365, 0.25, cy_ + 0.365, fc="#333", ec="#333", z=6)
    R(0.3, 0.21, 1.75, 0.52, fc=OAK)
    ax.annotate("", (X(2.05), 0.78), (X(3.6), 0.85), arrowprops=dict(arrowstyle="->", lw=1.0, color=CIRC, ls="--"))
    dm = lambda a, b, t, off, **k: dim((min(X(a), X(b)), 0) if False else (min(X(a), X(b)), k.pop("y", 0)), (max(X(a), X(b)), 0), t, off, **k)
classroom(False); classroom(True)
# classroom clearance dims (law; languages identical, mirrored)
dim((1.65, 4.6), (2.45, 4.6), "aisle 800", 0, fs=7, col=CIRC)
dim((3.2, 4.45), (3.2, 5.8), "1 350", 0, horiz=False, fs=7, col=CIRC)
dim((3.2, 0.2), (3.2, 1.0), "800", 0, horiz=False, fs=7, col=CIRC)
dim((0.3, 2.75), (0.3, 3.95), "pitch 1 200", 0, horiz=False, fs=7, col=CIRC)

def lab(x, y, t, s=11, w="bold", c="#1d1f24", **k): ax.text(x, y, t, ha="center", va="center", fontsize=s, fontweight=w, color=c, zorder=9, **k)
lab(2.05, 6.5, "LEFT — ZONE 1\nHUQUQ VA TARIX (Law & History)", 9.5)
lab(6.0, 6.75, "CENTRE — ZONE 2\nADMINISTRATION + COWORKING\n(one combined space)", 9.5)
lab(9.95, 6.5, "RIGHT — ZONE 3\nXORIJIY TILLAR (Foreign Languages)", 9.5)
lab(6.0, 6.12, "illuminated signature wall", 7, "normal", "#17233a")
lab(2.05, 5.95, "whiteboard (navy accent wall)", 6.5, "normal"); lab(9.95, 5.95, "whiteboard (teal accent wall)", 6.5, "normal")
lab(4.3, 2.6, "COWORKING (left)", 6.5, "normal", rotation=90); lab(7.7, 2.6, "COWORKING (right)", 6.5, "normal", rotation=90)
lab(6.0, 4.84, "ADMINISTRATOR DESK", 6.5); lab(7.68, 4.05, "water cooler", 6, "normal"); lab(4.55, 4.6, "TV +\ncredenza", 6, "normal")
lab(6.0, 1.15, "entry\nvestibule", 6.5, "normal", "#555")
for (x, t) in [(0.45, "TV"), (12 - 0.45, "TV")]: lab(x, 4.6, t, 6.5, "normal", rotation=90)
for (x, t) in [(0.45, "2 prints"), (12 - 0.45, "2 prints")]: lab(x, 2.58, t, 6.5, "normal", rotation=90)
lab(2.05, -0.75, "", 1); lab(6.0, -0.85, "GLASS PARTITION + CENTRAL GLASS ENTRANCE DOOR 1 100", 8, "bold", "#2a6fa0")

# dimension chains
dim((0, 0), (12, 0), "12 000 (external)", -2.55, fs=11)
for (a, b, t) in [(0, WT, "200"), (LAW[0], LAW[1], "3 700"), (P1[0], P1[1], "100"), (ADM[0], ADM[1], "4 000"), (P2[0], P2[1], "100"), (LANG[0], LANG[1], "3 700"), (IX1, 12, "200")]:
    dim((a, 0), (b, 0), t, -1.85, fs=8 if len(t) < 4 else 9)
dim((0, 0), (5.45, 0), "5 450", -1.25, fs=8); dim((5.45, 0), (6.55, 0), "1 100 door", -1.25, fs=8); dim((6.55, 0), (12, 0), "5 450", -1.25, fs=8)
dim((0, 0), (0, 6), "6 000 (external)", -0.55, horiz=False, fs=11)
dim((12, IY0), (12, IY1), "5 600 clear", 0.75, horiz=False, fs=8)
dim((12, IY0), (12, CDY[0]), "", 0.35, horiz=False); dim((12, CDY[0]), (12, CDY[1]), "door 1 000", 0.35, horiz=False, fs=7)
dim((12, CDY[1]), (12, IY1), "4 450", 0.35, horiz=False, fs=7)

ax.annotate("N", xy=(13.2, 7.6), xytext=(13.2, 6.9), ha="center", fontsize=12, fontweight="bold", arrowprops=dict(arrowstyle="-|>", lw=1.5, color="#111"))
for i in range(5): rect(8.9 + i, -4.35, 9.9 + i, -4.25, fc="#111" if i % 2 == 0 else "white", ec="#111", lw=0.6, z=8)
ax.text(8.9, -4.15, "0", fontsize=7); ax.text(13.9, -4.15, "5 m", fontsize=7, ha="right")
ax.text(-1.6, 8.3, "HUQUQ MAKTABI — Floor Plan", fontsize=18, fontweight="bold")
ax.text(-1.6, 7.92, "Footprint 12.0 × 6.0 m = 72 m² gross · external walls 200 · partitions 100 · ceiling 3 200 · dims in mm", fontsize=9.5, color="#444")
ax.text(-1.6, -3.0, "Net areas: Law & History 3.70×5.60 = 20.7 m²  ·  Admin + Coworking 4.00×5.60 = 22.4 m²  ·  Foreign Languages 20.7 m²", fontsize=8.5, color="#444")
ax.text(-1.6, -3.35, "Seats: 12 + 12 students, 2 teachers · 6 coworking seats (3 left + 3 right) · administrator  ·  green = circulation", fontsize=8.5, color="#444")
ax.text(-1.6, -0.6, "STREET ↓  (viewer outside\nfacing the entrance)", fontsize=8, color="#666")

# key plan: ground floor of the 75 m, 3-storey building (scale 1:4 of the main plan)
K = 0.16; KX, KY = -1.0, -7.1
def krect(x0, x1, fc, t, tc="white"):
    ax.add_patch(Rectangle((KX + (x0 + 10) * K, KY), (x1 - x0) * K, 12 * K, fc=fc, ec="#222", lw=0.7, zorder=7))
    ax.text(KX + ((x0 + x1) / 2 + 10) * K, KY + 6 * K, t, ha="center", va="center", fontsize=6.3, color=tc, zorder=8, rotation=0 if (x1 - x0) > 8 else 90)
krect(-10, -5, "#8d8478", "stair\n5 m"); krect(-5, 0, "#4a1420", "VINO\nVODKA\n5 m")
krect(0, 12, "#17233a", "HUQUQ MAKTABI 12 m")
krect(12, 62, "#6f757c", "SERVICES 50 m (apteka, market, kafe, sartaroshxona, notarius, maishiy xizmatlar)")
krect(62, 65, "#8d8478", "3 m")
ax.add_patch(Rectangle((KX, KY - 0.18), 75 * K, 0.1, fc="#d9d3c8", ec="none", zorder=6))
ax.text(KX, KY + 12 * K + 0.15, "KEY PLAN — ground floor of the 75 m long, 3-storey building (floors 2–3 above); HUQUQ MAKTABI canopy sign over its 12 m frontage", fontsize=8, color="#333")
ax.text(KX + 75 * K / 2, KY - 0.35, "street", ha="center", fontsize=7, color="#666")
fig.savefig(os.path.join(OUT, "floor_plan.png"), dpi=200, bbox_inches="tight", facecolor="white")
fig.savefig(os.path.join(OUT, "floor_plan.pdf"), bbox_inches="tight", facecolor="white")
print("floor plan saved")
