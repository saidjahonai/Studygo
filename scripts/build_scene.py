"""HUQUQ MAKTABI — procedural Blender scene (Blender 5.2, Cycles).

Coordinate system (metres):
  X = building length 0..12   (Zone1 Law 0-4 | Zone2 Admin+Coworking 4-8 | Zone3 Languages 8-12)
  Y = building depth  0..6    (Y=0 is the street facade, exterior is Y<0)
  Z = up                      (finished floor 0, ceiling 3.2)

Run:  /opt/bvenv/bin/python scripts/build_scene.py   -> blender/huquq_maktabi.blend
"""
import bpy, bmesh, math, os, random
from mathutils import Vector, Matrix, Euler

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEX = os.path.join(ROOT, "assets", "textures")
TVDIR = os.path.join(ROOT, "assets", "tv_logo")
OUT = os.path.join(ROOT, "blender", "huquq_maktabi.blend")
FONT_XB = "/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf"
FONT_SB = "/usr/share/fonts/opentype/inter/Inter-SemiBold.otf"
FPS = 24
H = 3.2          # interior ceiling height
random.seed(11)

# ------------------------------------------------------------------ reset
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.name = "HUQUQ_MAKTABI"
scene.unit_settings.system = "METRIC"

def srgb(h):
    """hex -> linear rgba"""
    h = h.lstrip("#")
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    lin = [x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c]
    return (*lin, 1.0)

def coll(name):
    c = bpy.data.collections.new(name); scene.collection.children.link(c); return c

C_ARCH = coll("01_Architecture"); C_EXT = coll("02_Exterior"); C_ADMIN = coll("03_Admin_Coworking")
C_LAW = coll("04_Law_History"); C_LANG = coll("05_Foreign_Languages"); C_LIGHT = coll("06_Lighting")
C_CAM = coll("07_Cameras")

# ================================================================== MATERIALS
MATS = {}

def new_mat(name):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial"); out.location = (600, 0)
    MATS[name] = m
    return m, nt, out

def principled(name, color, rough=0.5, metal=0.0, coat=0.0, spec=0.5, sheen=0.0, ior=1.5):
    m, nt, out = new_mat(name)
    b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    b.inputs["Base Color"].default_value = color if len(color) == 4 else (*color, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    b.inputs["Coat Weight"].default_value = coat
    b.inputs["Specular IOR Level"].default_value = spec
    b.inputs["Sheen Weight"].default_value = sheen
    b.inputs["IOR"].default_value = ior
    nt.links.new(b.outputs[0], out.inputs[0])
    return m

def add_noise_bump(nt, bsdf, scale=60, strength=0.05, detail=6):
    tc = nt.nodes.new("ShaderNodeTexCoord")
    n = nt.nodes.new("ShaderNodeTexNoise"); n.inputs["Scale"].default_value = scale; n.inputs["Detail"].default_value = detail
    bp = nt.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = strength
    nt.links.new(tc.outputs["Object"], n.inputs["Vector"])
    nt.links.new(n.outputs["Fac"], bp.inputs["Height"])
    nt.links.new(bp.outputs["Normal"], bsdf.inputs["Normal"])
    return n

def textured(name, color, rough, bump_scale, bump_strength, metal=0.0, sheen=0.0, coat=0.0):
    m = principled(name, color, rough, metal, coat=coat, sheen=sheen)
    nt = m.node_tree; b = nt.nodes["Principled BSDF"]
    add_noise_bump(nt, b, bump_scale, bump_strength)
    return m

def oak(name, axis="X", light=True):
    """Procedural light-oak veneer; grain runs along `axis`."""
    m, nt, out = new_mat(name)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    sc = {"X": (0.6, 28, 28), "Y": (28, 0.6, 28), "Z": (28, 28, 0.6)}[axis]
    mp.inputs["Scale"].default_value = sc
    n1 = nt.nodes.new("ShaderNodeTexNoise"); n1.inputs["Scale"].default_value = 1.6; n1.inputs["Detail"].default_value = 10; n1.inputs["Distortion"].default_value = 0.6
    n2 = nt.nodes.new("ShaderNodeTexNoise"); n2.inputs["Scale"].default_value = 0.35; n2.inputs["Detail"].default_value = 3
    w = nt.nodes.new("ShaderNodeTexWave"); w.wave_type = "BANDS"; w.inputs["Scale"].default_value = 0.9; w.inputs["Distortion"].default_value = 9; w.inputs["Detail"].default_value = 4
    nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
    for t in (n1, w): nt.links.new(mp.outputs["Vector"], t.inputs["Vector"])
    nt.links.new(tc.outputs["Object"], n2.inputs["Vector"])
    mix = nt.nodes.new("ShaderNodeMix"); mix.data_type = "FLOAT"; mix.inputs["Factor"].default_value = 0.45
    nt.links.new(n1.outputs["Fac"], mix.inputs[2]); nt.links.new(w.outputs["Fac"], mix.inputs[3])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    if light:
        ramp.color_ramp.elements[0].color = srgb("#b98c5d"); ramp.color_ramp.elements[1].color = srgb("#e3c9a2")
    else:
        ramp.color_ramp.elements[0].color = srgb("#6e4a2c"); ramp.color_ramp.elements[1].color = srgb("#a77a4e")
    ramp.color_ramp.elements[0].position = 0.25; ramp.color_ramp.elements[1].position = 0.75
    nt.links.new(mix.outputs[0], ramp.inputs[0])
    # large scale tonal variation
    hsv = nt.nodes.new("ShaderNodeHueSaturation")
    nt.links.new(ramp.outputs[0], hsv.inputs["Color"])
    vr = nt.nodes.new("ShaderNodeMapRange"); vr.inputs[3].default_value = 0.9; vr.inputs[4].default_value = 1.1
    nt.links.new(n2.outputs["Fac"], vr.inputs[0]); nt.links.new(vr.outputs[0], hsv.inputs["Value"])
    b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(hsv.outputs[0], b.inputs["Base Color"])
    rr = nt.nodes.new("ShaderNodeMapRange"); rr.inputs[3].default_value = 0.32; rr.inputs[4].default_value = 0.5
    nt.links.new(mix.outputs[0], rr.inputs[0]); nt.links.new(rr.outputs[0], b.inputs["Roughness"])
    b.inputs["Coat Weight"].default_value = 0.15; b.inputs["Coat Roughness"].default_value = 0.25
    bp = nt.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.04; bp.inputs["Distance"].default_value = 0.002
    nt.links.new(mix.outputs[0], bp.inputs["Height"]); nt.links.new(bp.outputs[0], b.inputs["Normal"])
    nt.links.new(b.outputs[0], out.inputs[0])
    return m

def tiles(name, c1, c2, tile=(1.2, 0.6), mortar=0.003, rough=0.25, mortar_col="#9a958f", axis="XY"):
    """Brick-texture driven floor tiles / pavers / planks."""
    m, nt, out = new_mat(name)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(tc.outputs["Object"], sep.inputs[0])
    comb = nt.nodes.new("ShaderNodeCombineXYZ")
    a, bax = axis[0], axis[1]
    nt.links.new(sep.outputs[a], comb.inputs[0]); nt.links.new(sep.outputs[bax], comb.inputs[1])
    br = nt.nodes.new("ShaderNodeTexBrick")
    br.inputs["Scale"].default_value = 1.0
    br.inputs["Brick Width"].default_value = tile[0]; br.inputs["Row Height"].default_value = tile[1]
    br.inputs["Mortar Size"].default_value = mortar; br.inputs["Mortar Smooth"].default_value = 0.3
    br.offset = 0.5; br.offset_frequency = 2
    br.inputs["Color1"].default_value = srgb(c1); br.inputs["Color2"].default_value = srgb(c2)
    br.inputs["Mortar"].default_value = srgb(mortar_col)
    nt.links.new(comb.outputs[0], br.inputs["Vector"])
    n = nt.nodes.new("ShaderNodeTexNoise"); n.inputs["Scale"].default_value = 3; n.inputs["Detail"].default_value = 8
    nt.links.new(tc.outputs["Object"], n.inputs["Vector"])
    mx = nt.nodes.new("ShaderNodeMix"); mx.data_type = "RGBA"; mx.blend_type = "OVERLAY"; mx.inputs["Factor"].default_value = 0.12
    nt.links.new(br.outputs["Color"], mx.inputs[6]); nt.links.new(n.outputs["Color"], mx.inputs[7])
    b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(mx.outputs[2], b.inputs["Base Color"])
    rr = nt.nodes.new("ShaderNodeMapRange"); rr.inputs[3].default_value = rough; rr.inputs[4].default_value = min(1, rough + 0.5)
    nt.links.new(br.outputs["Fac"], rr.inputs[0]); nt.links.new(rr.outputs[0], b.inputs["Roughness"])
    bp = nt.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.25; bp.invert = True
    nt.links.new(br.outputs["Fac"], bp.inputs["Height"]); nt.links.new(bp.outputs[0], b.inputs["Normal"])
    nt.links.new(b.outputs[0], out.inputs[0])
    return m

def glass(name, tint="#f2f7f6", rough=0.0):
    """Architectural glass; shadow rays pass straight through (clean daylight, low noise)."""
    m, nt, out = new_mat(name)
    g = nt.nodes.new("ShaderNodeBsdfPrincipled")
    g.inputs["Base Color"].default_value = srgb(tint); g.inputs["Transmission Weight"].default_value = 1.0
    g.inputs["Roughness"].default_value = rough; g.inputs["IOR"].default_value = 1.52
    tr = nt.nodes.new("ShaderNodeBsdfTransparent"); tr.inputs[0].default_value = srgb(tint)
    lp = nt.nodes.new("ShaderNodeLightPath")
    mx = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(lp.outputs["Is Shadow Ray"], mx.inputs[0])
    nt.links.new(g.outputs[0], mx.inputs[1]); nt.links.new(tr.outputs[0], mx.inputs[2])
    nt.links.new(mx.outputs[0], out.inputs[0])
    m.use_transparent_shadow = True if hasattr(m, "use_transparent_shadow") else None
    return m

def emission(name, color, strength):
    m, nt, out = new_mat(name)
    e = nt.nodes.new("ShaderNodeEmission")
    e.inputs[0].default_value = srgb(color) if isinstance(color, str) else color
    e.inputs[1].default_value = strength
    nt.links.new(e.outputs[0], out.inputs[0])
    return m

def image_mat(name, path, emissive=0.0, rough=0.35, sequence_len=0, gloss_coat=0.0):
    m, nt, out = new_mat(name)
    tex = nt.nodes.new("ShaderNodeTexImage")
    img = bpy.data.images.load(path, check_existing=True)
    tex.image = img
    if sequence_len:
        img.source = "SEQUENCE"
        tex.image_user.frame_duration = sequence_len
        tex.image_user.frame_start = 1
        tex.image_user.frame_offset = 0
        tex.image_user.use_cyclic = True
        tex.image_user.use_auto_refresh = True
    b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    b.inputs["Roughness"].default_value = rough
    b.inputs["Coat Weight"].default_value = gloss_coat
    nt.links.new(tex.outputs["Color"], b.inputs["Base Color"])
    if emissive:
        nt.links.new(tex.outputs["Color"], b.inputs["Emission Color"])
        b.inputs["Emission Strength"].default_value = emissive
        b.inputs["Base Color"].default_value = (0.01, 0.01, 0.01, 1)
        nt.links.remove(b.inputs["Base Color"].links[0])
        b.inputs["Coat Weight"].default_value = 1.0; b.inputs["Coat Roughness"].default_value = 0.05
    nt.links.new(b.outputs[0], out.inputs[0])
    return m

def leaf_mat(name, col):
    m, nt, out = new_mat(name)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    n = nt.nodes.new("ShaderNodeTexNoise"); n.inputs["Scale"].default_value = 18
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = srgb(col); ramp.color_ramp.elements[1].color = srgb("#5c8a3a")
    nt.links.new(tc.outputs["Object"], n.inputs["Vector"]); nt.links.new(n.outputs["Fac"], ramp.inputs[0])
    b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(ramp.outputs[0], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.38
    b.inputs["Subsurface Weight"].default_value = 0.15
    b.inputs["Coat Weight"].default_value = 0.3
    tl = nt.nodes.new("ShaderNodeBsdfTranslucent"); tl.inputs[0].default_value = srgb("#7bbf3a")
    mx = nt.nodes.new("ShaderNodeMixShader"); mx.inputs[0].default_value = 0.18
    nt.links.new(b.outputs[0], mx.inputs[1]); nt.links.new(tl.outputs[0], mx.inputs[2])
    nt.links.new(mx.outputs[0], out.inputs[0])
    return m

# palette
M_WALL = textured("Paint_WarmWhite", srgb("#efece6"), 0.85, 80, 0.015)
M_ACC_LAW = textured("Paint_Accent_Navy", srgb("#243652"), 0.8, 80, 0.015)
M_ACC_LANG = textured("Paint_Accent_Teal", srgb("#2a5a63"), 0.8, 80, 0.015)
M_CEIL = textured("Ceiling_White", srgb("#f4f3f0"), 0.9, 80, 0.01)
M_NAVY = textured("Acoustic_Navy", srgb("#17233a"), 0.75, 200, 0.12, sheen=0.4)
M_NAVY_FELT = textured("Acoustic_Felt_Graphite", srgb("#1b1f27"), 0.95, 300, 0.2, sheen=0.6)
M_GRAPHITE = principled("Graphite_Panel", srgb("#22262d"), 0.6, 0.0, coat=0.0)
M_BLACK_AL = principled("Aluminium_Black", srgb("#121314"), 0.35, 1.0)
M_STEEL = principled("Brushed_Steel", srgb("#b8bcc0"), 0.22, 1.0)
M_BLACK_MET = principled("Powder_Black", srgb("#18191b"), 0.45, 0.6)
M_WHITE_MET = principled("Powder_White", srgb("#ecedeb"), 0.4, 0.0)
M_WHITE_GLOSS = principled("White_Gloss", srgb("#f3f3f1"), 0.18, 0.0, coat=0.5)
M_PLASTIC_DK = principled("Plastic_Dark", srgb("#1d1e20"), 0.4)
M_SCREEN_OFF = principled("Screen_Black", srgb("#050607"), 0.05, 0.0, coat=1.0)
M_CERAMIC = principled("Ceramic_White", srgb("#f2f1ee"), 0.22, coat=0.6)
M_SOIL = textured("Soil", srgb("#2e2218"), 0.95, 200, 0.4)
M_FABRIC_GR = textured("Fabric_Graphite", srgb("#3a3d42"), 0.95, 400, 0.25, sheen=1.0)
M_FABRIC_NAVY = textured("Fabric_Navy", srgb("#25324d"), 0.95, 400, 0.25, sheen=1.0)
M_FABRIC_OLIVE = textured("Fabric_Sage", srgb("#6f7a62"), 0.95, 400, 0.25, sheen=1.0)
M_LEATHER = textured("Leather_Black", srgb("#141414"), 0.5, 150, 0.08, coat=0.2)
M_RUG = textured("Rug_Wool", srgb("#8b8478"), 0.98, 500, 0.35, sheen=0.8)
M_WB = image_mat("Whiteboard_Law", os.path.join(TEX, "wb_law.png"), rough=0.12, gloss_coat=0.6)
M_WB2 = image_mat("Whiteboard_Lang", os.path.join(TEX, "wb_lang.png"), rough=0.12, gloss_coat=0.6)
M_OAK_X = oak("Oak_Light_X", "X"); M_OAK_Y = oak("Oak_Light_Y", "Y"); M_OAK_Z = oak("Oak_Light_Z", "Z")
M_GLASS = glass("Glass_Clear"); M_GLASS_BOTTLE = glass("Glass_Bottle_Blue", "#9fc9e8", 0.05)
M_LED_W = emission("LED_White_6500K", "#eef4ff", 12)
M_LED_COOL = emission("LED_Contour_Cool", "#d8e6ff", 18)
M_LED_WARM = emission("LED_Warm_3500K", "#ffd7a8", 10)
M_PANEL = emission("LED_Panel_4000K", "#fff3e4", 6)
M_LOGO = emission("Logo_White_Illuminated", "#ffffff", 9)
M_SPEC_TXT = emission("Specialisation_Text", "#e9eef7", 3.5)
M_GOLD = principled("Brass_Accent", srgb("#c9a45c"), 0.25, 1.0)
M_SKIRT = principled("Skirting_White", srgb("#f1f0ec"), 0.4)
M_PLANT_DK = leaf_mat("Leaf_Ficus", "#1f4a1c"); M_PLANT_LT = leaf_mat("Leaf_Monstera", "#2c5e22")
M_STEM = principled("Stem", srgb("#4a3a26"), 0.7)
M_FLOOR_ADMIN = tiles("Porcelain_1200x600", "#cfcac2", "#c7c2ba", (1.2, 0.6), 0.002, 0.18, "#a8a39b")
M_FLOOR_CLASS = tiles("Vinyl_Plank_Oak", "#c8b394", "#bfa886", (1.5, 0.2), 0.0015, 0.35, "#8f7d62")
M_FACADE = textured("Fibre_Cement_Anthracite", srgb("#2e3135"), 0.7, 40, 0.06)
M_PAVER = tiles("Concrete_Pavers", "#a9a59f", "#9d9993", (0.6, 0.3), 0.006, 0.7, "#6e6a64")
M_ASPHALT = textured("Asphalt", srgb("#3a3b3d"), 0.85, 300, 0.3)
M_GRASS = leaf_mat("Grass", "#3c5f22")
M_CURB = textured("Concrete_Curb", srgb("#b4b0aa"), 0.8, 80, 0.1)
M_ROADLINE = principled("Road_Paint", srgb("#e8e6df"), 0.6)
M_BG_BLDG = textured("Background_Plaster", srgb("#9c958c"), 0.85, 20, 0.05)
M_BG_WIN = principled("Background_Glass", srgb("#3c4a58"), 0.08, 0.3, coat=1.0)
M_TV = image_mat("TV_HuquqMaktabi_MotionGraphics", os.path.join(TVDIR, "tv_0001.png"), emissive=2.2, sequence_len=96)
M_SLIDE_LAW = image_mat("TV_Slide_Law", os.path.join(TEX, "slide_law.png"), emissive=1.6)
M_SLIDE_LANG = image_mat("TV_Slide_Lang", os.path.join(TEX, "slide_lang.png"), emissive=1.6)
M_PR = {k: image_mat("Print_" + k, os.path.join(TEX, f"print_{k}.png"), rough=0.6) for k in ("law", "history", "world", "hello")}
M_PAPER = principled("Paper", srgb("#f4f2ec"), 0.8)
M_BOOK = [principled(f"Book_{i}", srgb(c), 0.6) for i, c in enumerate(["#7d2a2a", "#1f3b63", "#2f5a3d", "#c9b27a", "#3b3b3b"])]

# ================================================================== GEOMETRY KIT
class Builder:
    """Accumulates boxes/cylinders (in world space) into one mesh object."""
    def __init__(self, name, collection):
        self.name, self.coll = name, collection
        self.v, self.f, self.mi, self.mats = [], [], [], []
        self.uvs = []

    def _mat(self, m):
        if m not in self.mats: self.mats.append(m)
        return self.mats.index(m)

    def box(self, x0, y0, z0, x1, y1, z1, mat, M=None):
        idx = self._mat(mat); o = len(self.v)
        pts = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0), (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
        if M is not None: pts = [tuple(M @ Vector(p)) for p in pts]
        self.v += pts
        for fc in [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]:
            self.f.append(tuple(o + i for i in fc)); self.mi.append(idx)

    def cyl(self, cx, cy, z0, z1, r0, mat, r1=None, n=24, M=None, caps=True):
        r1 = r0 if r1 is None else r1
        idx = self._mat(mat); o = len(self.v)
        for z, r in ((z0, r0), (z1, r1)):
            for i in range(n):
                a = 2 * math.pi * i / n
                p = Vector((cx + r * math.cos(a), cy + r * math.sin(a), z))
                self.v.append(tuple(M @ p) if M is not None else tuple(p))
        for i in range(n):
            j = (i + 1) % n
            self.f.append((o + i, o + j, o + n + j, o + n + i)); self.mi.append(idx)
        if caps:
            self.f.append(tuple(o + n + i for i in range(n))); self.mi.append(idx)
            self.f.append(tuple(o + i for i in reversed(range(n)))); self.mi.append(idx)

    def build(self, bevel=0.0, segs=1, smooth=False):
        me = bpy.data.meshes.new(self.name)
        me.from_pydata(self.v, [], self.f)
        me.update()
        for m in self.mats: me.materials.append(m)
        me.polygons.foreach_set("material_index", self.mi)
        if smooth: me.polygons.foreach_set("use_smooth", [True] * len(me.polygons))
        ob = bpy.data.objects.new(self.name, me); self.coll.objects.link(ob)
        if bevel > 0:
            md = ob.modifiers.new("Bevel", "BEVEL"); md.width = bevel; md.segments = segs
            md.limit_method = "ANGLE"; md.harden_normals = False
        return ob

def T(x=0, y=0, z=0, rz=0.0):
    return Matrix.Translation((x, y, z)) @ Matrix.Rotation(math.radians(rz), 4, "Z")

def plane_obj(name, coll, corners, mat, uv=((0, 0), (1, 0), (1, 1), (0, 1))):
    me = bpy.data.meshes.new(name); me.from_pydata(corners, [], [(0, 1, 2, 3)]); me.update()
    ul = me.uv_layers.new(name="UVMap")
    for i, l in enumerate(me.loops): ul.data[i].uv = uv[l.vertex_index]
    me.materials.append(mat)
    ob = bpy.data.objects.new(name, me); coll.objects.link(ob); return ob

def wall_plane(name, coll, axis, pos, a0, a1, z0, z1, mat, facing=1):
    """Vertical image plane. axis='X': plane at x=pos spanning y a0..a1, facing +X if facing=1."""
    if axis == "X":
        c = [(pos, a0, z0), (pos, a1, z0), (pos, a1, z1), (pos, a0, z1)] if facing > 0 else [(pos, a1, z0), (pos, a0, z0), (pos, a0, z1), (pos, a1, z1)]
    else:
        c = [(a1, pos, z0), (a0, pos, z0), (a0, pos, z1), (a1, pos, z1)] if facing > 0 else [(a0, pos, z0), (a1, pos, z0), (a1, pos, z1), (a0, pos, z1)]
    return plane_obj(name, coll, c, mat)

def text_obj(name, coll, body, font, size, mat, loc, rot, extrude=0.004, align="CENTER", spacing=1.0):
    cu = bpy.data.curves.new(name, "FONT"); cu.body = body
    cu.font = bpy.data.fonts.load(font, check_existing=True)
    cu.size = size; cu.extrude = extrude; cu.align_x = align; cu.align_y = "CENTER"
    cu.space_character = spacing; cu.bevel_depth = 0.0
    ob = bpy.data.objects.new(name, cu); ob.location = loc; ob.rotation_euler = rot
    ob.data.materials.append(mat); coll.objects.link(ob); return ob

# ================================================================== ARCHITECTURE
arch = Builder("Building_Shell", C_ARCH)
WT = 0.25; TOP = 3.85
# back wall (y 6..6.25) full length, end walls
arch.box(-WT, 6.0, 0, 12 + WT, 6.0 + WT, TOP, M_FACADE)
arch.box(-WT, -WT, 0, 0, 6.0, TOP, M_FACADE)
arch.box(12, -WT, 0, 12 + WT, 6.0, TOP, M_FACADE)
# front facade with windows (classrooms) and full glazing (admin)
def facade_zone(x0, x1):
    w1 = (x0 + 0.5, x0 + 1.9); w2 = (x0 + 2.1, x0 + 3.5)
    arch.box(x0, -WT, 0, w1[0], 0, TOP, M_FACADE)
    arch.box(w1[1], -WT, 0, w2[0], 0, TOP, M_FACADE)
    arch.box(w2[1], -WT, 0, x1, 0, TOP, M_FACADE)
    arch.box(w1[0], -WT, 0, w2[1], 0, 0.85, M_FACADE)
    arch.box(w1[0], -WT, 2.75, w2[1], 0, TOP, M_FACADE)
    return [w1, w2]
WINDOWS = facade_zone(0, 4) + facade_zone(8, 12)
arch.box(4, -WT, 3.2, 8, 0, TOP, M_FACADE)            # fascia over storefront
# roof slab
arch.box(0, 0, H, 12, 6, 3.6, M_FACADE)
arch.build()

# interior wall linings (paint) — separate so exterior stays anthracite
lin = Builder("Interior_Walls", C_ARCH)
T_IN = 0.01
lin.box(0, -0.0, 0, T_IN, 6, H, M_ACC_LAW)              # law end wall  (x=0) navy accent
lin.box(12 - T_IN, 0, 0, 12, 6, H, M_ACC_LANG)            # lang end wall (x=12) teal accent
lin.box(0, 6 - T_IN, 0, 4, 6, H, M_WALL)                 # back wall law
lin.box(8, 6 - T_IN, 0, 12, 6, H, M_WALL)                # back wall lang
for zx in (0, 8):                                        # front wall inner lining around windows
    w1 = (zx + 0.5, zx + 1.9); w2 = (zx + 2.1, zx + 3.5)
    lin.box(zx, 0, 0, w1[0], T_IN, H, M_WALL); lin.box(w1[1], 0, 0, w2[0], T_IN, H, M_WALL); lin.box(w2[1], 0, 0, zx + 4, T_IN, H, M_WALL)
    lin.box(w1[0], 0, 0, w2[1], T_IN, 0.85, M_WALL); lin.box(w1[0], 0, 2.75, w2[1], T_IN, H, M_WALL)
# partitions at x=4 and x=8 with door openings y 3.1..4.1 (h 2.2)
for px in (4.0, 8.0):
    a, b = px - 0.06, px + 0.06
    lin.box(a, 0, 0, b, 3.1, H, M_WALL); lin.box(a, 4.1, 0, b, 6, H, M_WALL); lin.box(a, 3.1, 2.2, b, 4.1, H, M_WALL)
lin.build()

# window reveals, sills, frames, glass (classrooms)
win = Builder("Windows_Frames", C_ARCH)
for (a, b) in WINDOWS:
    win.box(a, -0.25, 0.85, b, 0.04, 0.88, M_WHITE_MET)               # inner sill
    win.box(a - 0.01, -0.33, 0.83, b + 0.01, -0.25, 0.86, M_BLACK_AL)  # outer sill
    win.box(a, -0.17, 0.88, b, -0.11, 0.93, M_BLACK_AL); win.box(a, -0.17, 2.70, b, -0.11, 2.75, M_BLACK_AL)
    win.box(a, -0.17, 0.85, a + 0.05, -0.11, 2.75, M_BLACK_AL); win.box(b - 0.05, -0.17, 0.85, b, -0.11, 2.75, M_BLACK_AL)
    m = (a + b) / 2; win.box(m - 0.025, -0.17, 0.85, m + 0.025, -0.11, 2.75, M_BLACK_AL)
    win.box(a, -0.25, 0.85, a + 0.002, 0, 2.75, M_WALL); win.box(b - 0.002, -0.25, 0.85, b, 0, 2.75, M_WALL)
win.build(bevel=0.003)
gl = Builder("Window_Glass", C_ARCH)
for (a, b) in WINDOWS:
    gl.box(a + 0.03, -0.142, 0.9, b - 0.03, -0.138, 2.72, M_GLASS)
gl.build()

# ---- storefront: glass partition + separate glass entrance door (admin zone)
sf = Builder("Storefront_Frame", C_ARCH)
Y_G = -0.12
for (a, b) in [(4.0, 4.06), (5.40, 5.45), (6.55, 6.60), (7.94, 8.0)]:
    sf.box(a, Y_G - 0.04, 0, b, Y_G + 0.04, H, M_BLACK_AL)
sf.box(4.0, Y_G - 0.04, H - 0.06, 8.0, Y_G + 0.04, H, M_BLACK_AL)          # head
sf.box(4.0, Y_G - 0.04, 0, 5.45, Y_G + 0.04, 0.04, M_BLACK_AL)            # sills
sf.box(6.55, Y_G - 0.04, 0, 8.0, Y_G + 0.04, 0.04, M_BLACK_AL)
sf.box(5.40, Y_G - 0.04, 2.42, 6.60, Y_G + 0.04, 2.47, M_BLACK_AL)        # transom bar
sf.build(bevel=0.002)
sg = Builder("Storefront_Glass", C_ARCH)
sg.box(4.06, Y_G - 0.005, 0.04, 5.40, Y_G + 0.005, H - 0.06, M_GLASS)
sg.box(6.60, Y_G - 0.005, 0.04, 7.94, Y_G + 0.005, H - 0.06, M_GLASS)
sg.box(5.45, Y_G - 0.005, 2.47, 6.55, Y_G + 0.005, H - 0.06, M_GLASS)
sg.build()
# frosted manifestation band on glass (safety marking with logo-ish line)
man = Builder("Glass_Manifestation", C_ARCH)
man.box(4.06, Y_G - 0.007, 1.0, 5.40, Y_G - 0.006, 1.06, M_WHITE_MET)
man.box(6.60, Y_G - 0.007, 1.0, 7.94, Y_G - 0.006, 1.06, M_WHITE_MET)
man.build()

# entrance door (pivot at hinge x=5.45, y=Y_G) — animated
db = Builder("Entrance_Door_Leaf", C_ARCH)
db.box(0.005, -0.006, 0.01, 1.095, 0.006, 2.415, M_GLASS)
db.box(0.0, -0.02, 0.0, 1.10, 0.02, 0.06, M_BLACK_AL)       # bottom rail
db.box(0.0, -0.02, 2.36, 1.10, 0.02, 2.42, M_BLACK_AL)      # top rail
for sy in (-1, 1):                                           # pull handles both sides
    db.cyl(0.98, sy * 0.075, 0.55, 1.75, 0.016, M_STEEL, n=16)
    db.box(0.97, min(0, sy * 0.075), 0.62, 0.99, max(0, sy * 0.075), 0.64, M_STEEL)
    db.box(0.97, min(0, sy * 0.075), 1.66, 0.99, max(0, sy * 0.075), 1.68, M_STEEL)
DOOR = db.build(bevel=0.002)
DOOR.location = (5.45, Y_G, 0)
# door glass sign
text_obj("Door_Sign", C_ARCH, "HUQUQ MAKTABI", FONT_SB, 0.05, M_WHITE_MET, (0.55, -0.007, 1.45), (math.radians(90), 0, 0), extrude=0.0005).parent = DOOR

# classroom doors (oak frame, glass vision panel) — fixed open
def class_door(px, open_dir):
    fr = Builder(f"DoorFrame_x{px}", C_ARCH)
    a, b = px - 0.075, px + 0.075
    fr.box(a, 3.06, 0, b, 3.1, 2.24, M_OAK_Z); fr.box(a, 4.1, 0, b, 4.14, 2.24, M_OAK_Z); fr.box(a, 3.06, 2.2, b, 4.14, 2.24, M_OAK_X)
    fr.build(bevel=0.003)
    lf = Builder(f"ClassDoor_x{px}", C_ARCH)
    lf.box(0, -0.02, 0.005, 0.96, 0.02, 2.19, M_OAK_X)
    lf.cyl(0.85, -0.05, 0.98, 1.02, 0.01, M_STEEL, n=12)
    M = Matrix.Translation((px + open_dir * 0.02, 4.08, 0)) @ Matrix.Rotation(math.radians(-90 if open_dir < 0 else -90), 4, "Z")
    ob = lf.build(bevel=0.003)
    ob.location = (px + open_dir * 0.03, 4.08, 0); ob.rotation_euler = (0, 0, math.radians(90 if open_dir < 0 else 90))
    # rotate so the leaf lies flat against partition inside the classroom
    ob.rotation_euler = (0, 0, math.radians(180 - 90 * open_dir * -1)) if False else ob.rotation_euler
    return ob
d1 = class_door(4.0, -1); d1.location = (3.895, 4.12, 0); d1.rotation_euler = (0, 0, math.radians(90))
# leaf along -X from hinge at (3.92,4.08): lies inside law room perpendicular to partition
d2 = class_door(8.0, 1); d2.location = (8.105, 4.12, 0); d2.rotation_euler = (0, 0, math.radians(90))

# floors & ceiling
fl = Builder("Floor_Admin", C_ARCH); fl.box(3.94, 0, -0.05, 8.06, 6, 0, M_FLOOR_ADMIN); fl.build()
fc = Builder("Floor_Classrooms", C_ARCH); fc.box(0, 0, -0.05, 3.94, 6, 0, M_FLOOR_CLASS); fc.box(8.06, 0, -0.05, 12, 6, 0, M_FLOOR_CLASS); fc.build()
fe = Builder("Floor_Entrance_Threshold", C_ARCH); fe.box(5.40, -0.25, -0.05, 6.60, 0, 0.005, M_STEEL); fe.build()
ce = Builder("Ceiling", C_ARCH); ce.box(0, 0, H - 0.001, 12, 6, H, M_CEIL); ce.build()
sk = Builder("Skirting", C_ARCH)
for (x0, y0, x1, y1) in [(0.01, 5.975, 3.94, 5.99), (8.06, 5.975, 11.99, 5.99), (0.01, 0.01, 0.025, 5.99), (11.975, 0.01, 11.99, 5.99)]:
    sk.box(x0, y0, 0, x1, y1, 0.08, M_SKIRT)
for px in (4.0, 8.0):
    for side in (-1, 1):
        x0 = px + side * 0.06; x1 = x0 + side * 0.012
        sk.box(min(x0, x1), 0.01, 0, max(x0, x1), 3.06, 0.08, M_SKIRT); sk.box(min(x0, x1), 4.14, 0, max(x0, x1), 5.99, 0.08, M_SKIRT)
sk.build()

# ================================================================== FURNITURE LIBRARY
def chair(b, cushion, M, fabric, legs=M_BLACK_MET, arms=False):
    """Upholstered side chair; origin = floor centre of seat, facing -Y local (sitter looks to -Y)."""
    for (lx, ly) in [(-0.2, -0.19), (0.2, -0.19), (-0.2, 0.19), (0.2, 0.19)]:
        b.cyl(lx, ly, 0, 0.44, 0.011, legs, n=10, M=M)
    b.box(-0.21, -0.2, 0.42, 0.21, 0.2, 0.44, legs, M=M)
    cushion.box(-0.235, -0.235, 0.44, 0.235, 0.215, 0.52, fabric, M=M)
    back = M @ Matrix.Translation((0, 0.23, 0.52)) @ Matrix.Rotation(math.radians(-8), 4, "X")
    cushion.box(-0.235, -0.03, 0.04, 0.235, 0.035, 0.40, fabric, M=back)
    b.box(-0.2, 0.205, 0.44, -0.185, 0.225, 0.62, legs, M=M); b.box(0.185, 0.205, 0.44, 0.2, 0.225, 0.62, legs, M=M)
    if arms:
        for sx in (-1, 1):
            cushion.box(sx * 0.235 - 0.03, -0.18, 0.52, sx * 0.235 + 0.03, 0.2, 0.68, fabric, M=M)

def desk(b, x0, y0, x1, y1, top_mat, leg_mat=M_WHITE_MET, h=0.75, modesty=True):
    b.box(x0, y0, h - 0.025, x1, y1, h, top_mat)
    for (lx, ly) in [(x0 + 0.04, y0 + 0.04), (x1 - 0.07, y0 + 0.04), (x0 + 0.04, y1 - 0.07), (x1 - 0.07, y1 - 0.07)]:
        b.box(lx, ly, 0, lx + 0.03, ly + 0.03, h - 0.025, leg_mat)
    b.box(x0 + 0.05, y0 + 0.05, h - 0.085, x1 - 0.05, y0 + 0.07, h - 0.025, leg_mat)
    b.box(x0 + 0.05, y1 - 0.07, h - 0.085, x1 - 0.05, y1 - 0.05, h - 0.025, leg_mat)

def laptop(b, x, y, rz, open_deg=110):
    M = T(x, y, 0.75, rz)
    b.box(-0.155, -0.11, 0, 0.155, 0.11, 0.012, M_STEEL, M=M)
    S = M @ Matrix.Translation((0, 0.11, 0.012)) @ Matrix.Rotation(math.radians(open_deg - 90), 4, "X")
    b.box(-0.155, -0.006, 0, 0.155, 0.0, 0.21, M_STEEL, M=S)
    b.box(-0.145, -0.0075, 0.012, 0.145, -0.006, 0.2, M_SCREEN_OFF, M=S)

def books(b, x, y, z, rz, n=4):
    M = T(x, y, z, rz); zz = 0
    for i in range(n):
        th = random.uniform(0.02, 0.04); w = random.uniform(0.15, 0.2); d = random.uniform(0.21, 0.26)
        b.box(-w / 2, -d / 2, zz, w / 2, d / 2, zz + th, random.choice(M_BOOK), M=M @ Matrix.Rotation(math.radians(random.uniform(-8, 8)), 4, "Z")); zz += th

def mug(b, x, y, z):
    b.cyl(x, y, z, z + 0.095, 0.04, M_CERAMIC, n=20)

def plant(coll, name, x, y, pot_h=0.55, pot_r=0.22, height=1.25, leaves=110, mat=None, big_leaf=False):
    b = Builder(name + "_Pot", coll)
    b.cyl(x, y, 0, pot_h, pot_r * 0.82, M_CERAMIC, r1=pot_r, n=40)
    b.cyl(x, y, pot_h - 0.04, pot_h - 0.035, pot_r * 0.95, M_SOIL, n=40)
    b.build(bevel=0.006, segs=2, smooth=True)
    lb = Builder(name + "_Foliage", coll)
    mat = mat or M_PLANT_DK
    rnd = random.Random(hash(name) & 0xffff)
    # stems
    stems = []
    for s in range(5 if big_leaf else 3):
        ang = rnd.uniform(0, 2 * math.pi); lean = rnd.uniform(0.03, 0.12)
        top = Vector((x + math.cos(ang) * lean, y + math.sin(ang) * lean, pot_h + height * rnd.uniform(0.75, 1.0)))
        stems.append(top)
        base = Vector((x, y, pot_h - 0.04)); d = top - base
        M = Matrix.Translation(base) @ d.to_track_quat("Z", "Y").to_matrix().to_4x4()
        lb.cyl(0, 0, 0, d.length, 0.012, M_STEM, r1=0.006, n=8, M=M)
    for i in range(leaves):
        st = rnd.choice(stems)
        t = rnd.uniform(0.25, 1.0)
        base = Vector((x, y, pot_h)).lerp(st, t)
        ang = rnd.uniform(0, 2 * math.pi)
        L = (0.17 if not big_leaf else 0.3) * rnd.uniform(0.7, 1.2); Wd = L * (0.45 if not big_leaf else 0.75)
        out_r = (0.08 + 0.32 * (1 - abs(t - 0.6))) * (1.4 if big_leaf else 1)
        p = base + Vector((math.cos(ang) * out_r * rnd.uniform(0.3, 1), math.sin(ang) * out_r * rnd.uniform(0.3, 1), 0))
        M = Matrix.Translation(p) @ Matrix.Rotation(ang, 4, "Z") @ Matrix.Rotation(math.radians(rnd.uniform(-35, 25)), 4, "Y") @ Matrix.Rotation(math.radians(rnd.uniform(-25, 25)), 4, "X")
        # leaf: 8-vert folded ellipse (two triangles fans)
        o = len(lb.v); idx = lb._mat(mat)
        pts = [(0, 0, 0)]
        for k in range(1, 7):
            u = k / 7; w = math.sin(u * math.pi) * Wd / 2
            pts += [(u * L, -w, -0.15 * w), (u * L, w, -0.15 * w)]
        pts.append((L, 0, 0))
        for k in range(len(pts)):
            px_, py_, pz_ = pts[k]
            pz_ += -0.25 * (px_ / L) ** 2 * L  # droop
            pts[k] = tuple(M @ Vector((px_, py_, pz_ + (0.01 if k else 0))))
        lb.v += pts
        # spine verts: 0, then pairs, end
        spine = [o] + [None] * 6 + [o + 13]
        prev_l, prev_r, prev_c = o, o, o
        for k in range(6):
            l_, r_ = o + 1 + 2 * k, o + 2 + 2 * k
            lb.f.append((prev_c, l_, prev_l) if k else (o, l_, o + 2)) if False else None
        # simple strip triangulation
        lb.f.append((o, o + 1, o + 2)); lb.mi.append(idx)
        for k in range(5):
            a1, a2, b1, b2 = o + 1 + 2 * k, o + 2 + 2 * k, o + 3 + 2 * k, o + 4 + 2 * k
            lb.f.append((a1, b1, b2, a2)); lb.mi.append(idx)
        lb.f.append((o + 11, o + 13, o + 12)); lb.mi.append(idx)
    ob = lb.build(smooth=True)
    return ob

# ================================================================== ZONE 2 — ADMINISTRATION + COWORKING
adm = Builder("Admin_Furniture", C_ADMIN)
cush = Builder("Admin_Upholstery", C_ADMIN)
# left & right coworking counters (along partitions), y 0.6..2.4
adm.box(4.06, 0.6, 0.72, 4.70, 2.4, 0.75, M_OAK_Y)
adm.box(7.30, 0.6, 0.72, 7.94, 2.4, 0.75, M_OAK_Y)
for (x0, x1) in [(4.06, 4.70), (7.30, 7.94)]:
    for y in (0.62, 1.48, 2.36):
        adm.box(x0 + 0.02, y - 0.0, 0, x1 - 0.04, y + 0.02, 0.72, M_WHITE_MET)
    # power/USB rail
    adm.box(x0 + (0.0 if x0 < 6 else 0.6), 0.6, 0.75, x0 + (0.03 if x0 < 6 else 0.64), 2.4, 0.83, M_PLASTIC_DK) if False else None
# wall-mounted shelf above counters + pendant-free task lights (linear)
adm.box(4.06, 0.7, 1.55, 4.36, 2.3, 1.575, M_OAK_Y); adm.box(7.64, 0.7, 1.55, 7.94, 2.3, 1.575, M_OAK_Y)
books(adm, 4.2, 0.95, 1.575, 90, 3); books(adm, 7.8, 2.0, 1.575, 90, 4)
# coworking chairs at counters
for y in (1.05, 1.95):
    chair(adm, cush, T(5.05, y, 0, 90 + random.uniform(-8, 8)), M_FABRIC_NAVY)      # faces -X (towards left counter)
    chair(adm, cush, T(6.95, y, 0, -90 + random.uniform(-8, 8)), M_FABRIC_NAVY)
laptop(adm, 4.42, 1.05, 90 + 180 - 180, 112); laptop(adm, 7.58, 1.95, -90, 108)
mug(adm, 4.55, 1.5, 0.75); books(adm, 7.55, 1.1, 0.75, 15, 2)
# branded acoustic felt panels above the counters (left & right walls)
for (wx, face, txt) in [(4.06, 1, "COWORKING"), (7.94, -1, "BILIM  •  INTIZOM  •  ADOLAT")]:
    x0, x1 = (wx, wx + 0.035) if face > 0 else (wx - 0.035, wx)
    adm.box(x0, 0.75, 1.78, x1, 2.25, 2.62, M_NAVY_FELT)
    fx0, fx1 = (x1, x1 + 0.006) if face > 0 else (x0 - 0.006, x0)
    adm.box(fx0, 0.74, 1.77, fx1, 2.26, 1.785, M_OAK_Y); adm.box(fx0, 0.74, 2.615, fx1, 2.26, 2.63, M_OAK_Y)
    text_obj(f"Wall_Text_{txt[:4]}", C_ADMIN, txt, FONT_XB if face > 0 else FONT_SB, 0.15 if face > 0 else 0.085,
             M_SPEC_TXT, ((x1 + 0.004) if face > 0 else (x0 - 0.004), 1.5, 2.2), (math.radians(90), 0, math.radians(90 if face > 0 else -90)), extrude=0.003)
    adm.box(fx0, 1.1, 2.04, fx1 + (0.001 if face > 0 else -0.001), 1.9, 2.05, M_GOLD) if False else None
# central coworking table directly ahead: 1.6 x 0.8, y 2.8..3.6
desk(adm, 5.2, 2.8, 6.8, 3.6, M_OAK_X, M_BLACK_MET)
for x in (5.6, 6.4):
    chair(adm, cush, T(x, 2.42, 0, 180 + random.uniform(-6, 6)), M_FABRIC_OLIVE)    # front side, faces +Y
    chair(adm, cush, T(x, 3.98, 0, random.uniform(-6, 6)), M_FABRIC_OLIVE)          # back side, faces -Y
laptop(adm, 5.6, 3.05, 180, 105); laptop(adm, 6.4, 3.35, 0, 110)
mug(adm, 6.0, 3.2, 0.75); books(adm, 5.95, 2.95, 0.75, 75, 3)
# low pendant/power box on table
adm.box(5.92, 3.12, 0.75, 6.08, 3.28, 0.79, M_PLASTIC_DK)
# rug under central table
rug = Builder("Rug", C_ADMIN); rug.box(4.95, 2.05, 0, 7.05, 4.35, 0.008, M_RUG); rug.build(bevel=0.004)

# reception / administrator desk (y 4.6..5.3)
RX0, RX1 = 5.15, 6.85
adm.box(RX0, 4.62, 0, RX1, 4.66, 1.05, M_OAK_Z)                       # front panel (oak, vertical grain)
for i in range(18):                                                   # fluted oak slats on front
    x = RX0 + 0.04 + i * (RX1 - RX0 - 0.08) / 17
    adm.box(x - 0.018, 4.585, 0.06, x + 0.018, 4.62, 1.03, M_OAK_Z)
adm.box(RX0 - 0.02, 4.55, 1.05, RX1 + 0.02, 4.82, 1.08, M_WHITE_GLOSS)  # raised transaction top
adm.box(RX0, 4.62, 0.72, RX1, 5.32, 0.75, M_WHITE_GLOSS)               # work surface
adm.box(RX0, 4.66, 0, RX0 + 0.04, 5.32, 0.72, M_GRAPHITE); adm.box(RX1 - 0.04, 4.66, 0, RX1, 5.32, 0.72, M_GRAPHITE)
adm.box(RX1 - 0.46, 4.9, 0, RX1 - 0.04, 5.3, 0.6, M_GRAPHITE)           # pedestal drawers
adm.box(RX0 + 0.02, 4.56, 0.0, RX1 - 0.02, 4.585, 0.025, M_GRAPHITE)    # plinth
# monitor, keyboard, phone, documents
adm.box(6.25, 4.98, 0.75, 6.43, 5.12, 0.76, M_STEEL); adm.box(6.325, 5.06, 0.76, 6.355, 5.08, 1.0, M_STEEL)
MON = Matrix.Translation((6.34, 5.05, 1.12)) @ Matrix.Rotation(math.radians(-8), 4, "Z")
adm.box(-0.31, -0.012, -0.19, 0.31, 0.012, 0.19, M_PLASTIC_DK, M=MON)
adm.box(-0.30, -0.0135, -0.18, 0.30, -0.012, 0.18, M_SCREEN_OFF, M=MON)
adm.box(6.12, 4.78, 0.75, 6.52, 4.92, 0.765, M_WHITE_MET)
adm.box(5.45, 4.85, 0.75, 5.66, 5.15, 0.756, M_PAPER); books(adm, 5.42, 5.12, 0.75, 10, 2)
# executive chair
ex = T(6.0, 5.62, 0, 180 - 12)
for k in range(5):
    a = math.radians(72 * k)
    Mk = ex @ Matrix.Rotation(a, 4, "Z")
    adm.box(-0.02, 0, 0.05, 0.02, 0.33, 0.08, M_BLACK_MET, M=Mk); adm.cyl(0, 0.31, 0.0, 0.05, 0.025, M_PLASTIC_DK, n=10, M=Mk)
adm.cyl(0, 0, 0.08, 0.42, 0.025, M_STEEL, n=16, M=ex)
cush.box(-0.26, -0.25, 0.42, 0.26, 0.24, 0.52, M_LEATHER, M=ex)
eb = ex @ Matrix.Translation((0, 0.26, 0.55)) @ Matrix.Rotation(math.radians(-10), 4, "X")
cush.box(-0.25, -0.05, 0.0, 0.25, 0.04, 0.62, M_LEATHER, M=eb)
for sx in (-1, 1):
    adm.box(sx * 0.27 - 0.02, -0.15, 0.52, sx * 0.27 + 0.02, 0.15, 0.66, M_BLACK_MET, M=ex)
# visitor chairs flanking the transaction counter? (kept clear for circulation)

# water cooler (right side, near partition)
WC = (7.68, 4.62)
adm.box(WC[0] - 0.16, WC[1] - 0.16, 0, WC[0] + 0.16, WC[1] + 0.16, 1.0, M_WHITE_GLOSS)
adm.box(WC[0] - 0.165, WC[1] - 0.17, 0.62, WC[0] + 0.165, WC[1] - 0.07, 0.86, M_PLASTIC_DK)    # dispensing recess (faces -Y)
adm.box(WC[0] - 0.08, WC[1] - 0.18, 0.66, WC[0] + 0.08, WC[1] - 0.10, 0.68, M_STEEL)
adm.cyl(WC[0] - 0.05, WC[1] - 0.135, 0.80, 0.84, 0.012, M_STEEL, n=10); adm.cyl(WC[0] + 0.05, WC[1] - 0.135, 0.80, 0.84, 0.012, (M_LED_COOL), n=10)
adm.cyl(WC[0], WC[1], 1.0, 1.04, 0.07, M_WHITE_GLOSS, n=24)
bt = Builder("WaterCooler_Bottle", C_ADMIN)
bt.cyl(WC[0], WC[1], 1.04, 1.1, 0.05, M_GLASS_BOTTLE, r1=0.13, n=32)
bt.cyl(WC[0], WC[1], 1.1, 1.46, 0.135, M_GLASS_BOTTLE, n=32)
bt.cyl(WC[0], WC[1], 1.46, 1.5, 0.135, M_GLASS_BOTTLE, r1=0.08, n=32)
bt.build(bevel=0.01, segs=2, smooth=True)
adm.cyl(WC[0] + 0.24, WC[1], 0.0, 0.5, 0.05, M_WHITE_MET, n=16)  # cup bin

# credenza + TV on left partition (facing +X)
adm.box(4.06, 4.3, 0.08, 4.48, 5.5, 0.55, M_OAK_Y); adm.box(4.08, 4.32, 0, 4.44, 5.48, 0.08, M_GRAPHITE)
books(adm, 4.27, 5.2, 0.55, 90, 3)
adm.box(4.06, 4.40, 1.18, 4.11, 5.62, 1.88, M_PLASTIC_DK)   # TV body
TVA = wall_plane("TV_Admin_Screen", C_ADMIN, "X", 4.112, 4.415, 5.605, 1.195, 1.865, M_TV, facing=1)
adm.build(bevel=0.003)
cush.build(bevel=0.022, segs=3, smooth=True)

plant(C_ADMIN, "Plant_Left", 4.62, 5.6, pot_h=0.6, pot_r=0.22, height=1.15, leaves=130, mat=M_PLANT_DK)
plant(C_ADMIN, "Plant_Right", 7.38, 5.6, pot_h=0.6, pot_r=0.22, height=0.95, leaves=34, mat=M_PLANT_LT, big_leaf=True)
plant(C_ADMIN, "Plant_Counter", 7.75, 0.75, pot_h=0.0, pot_r=0.001, height=0.0, leaves=0) if False else None

# ---- signature wall (behind administrator desk, y = 6)
sig = Builder("Signature_Wall_Slats", C_ADMIN)
sig.box(4.06, 5.97, 0, 7.94, 5.99, H, M_NAVY_FELT)                     # felt backing
x = 4.08
while x < 7.92:
    # leave the logo field clear
    sig.box(x, 5.925, 0.08, x + 0.032, 5.97, H - 0.06, M_NAVY)
    x += 0.058
sig.build(bevel=0.002)
pan = Builder("Signature_Logo_Panel", C_ADMIN)
pan.box(4.42, 5.875, 1.55, 7.58, 5.925, 2.80, M_GRAPHITE)
pan.build(bevel=0.004)
led = Builder("Signature_LED_Contours", C_ADMIN)
# contour frame inset around logo panel
pan_led = [(4.40, 5.90, 1.53, 7.60, 5.92, 1.545), (4.40, 5.90, 2.805, 7.60, 5.92, 2.82),
           (4.40, 5.90, 1.53, 4.415, 5.92, 2.82), (7.585, 5.90, 1.53, 7.60, 5.92, 2.82)]
for bx in pan_led: led.box(*bx, M_LED_COOL)
for xx in (4.22, 7.78):                                                 # vertical podcast-style LED lines
    led.box(xx - 0.006, 5.915, 0.12, xx + 0.006, 5.93, H - 0.12, M_LED_COOL)
led.box(4.06, 5.90, 0.0, 7.94, 5.93, 0.015, M_LED_WARM)                 # floor grazer
led.build()
logo = text_obj("Logo_HUQUQ_MAKTABI", C_ADMIN, "HUQUQ MAKTABI", FONT_XB, 0.30, M_LOGO, (6.0, 5.86, 2.38), (math.radians(90), 0, 0), extrude=0.012, spacing=1.05)
gold = Builder("Logo_Gold_Line", C_ADMIN); gold.box(5.2, 5.862, 2.16, 6.8, 5.875, 2.172, M_GOLD); gold.build()
text_obj("Spec_Row1", C_ADMIN, "PROKURATURA   •   ICHKI ISHLAR ORGANLARI   •   ADLIYA", FONT_SB, 0.062, M_SPEC_TXT, (6.0, 5.868, 1.94), (math.radians(90), 0, 0), extrude=0.003)
text_obj("Spec_Row2", C_ADMIN, "SUD TIZIMI   •   YURIDIK KADRLAR   •   DAVLAT XIZMATI", FONT_SB, 0.062, M_SPEC_TXT, (6.0, 5.868, 1.78), (math.radians(90), 0, 0), extrude=0.003)

# ================================================================== CLASSROOMS
def classroom(mirror, coll, wb_mat, slide_mat, prints, tag):
    """Builds a classroom in the 0..3.94 frame, mirrored for x' = 12 - x."""
    def X(x): return 12 - x if mirror else x
    def box(b, x0, y0, z0, x1, y1, z1, m, M=None):
        a, c = sorted((X(x0), X(x1))); b.box(a, y0, z0, c, y1, z1, m, M)
    rz = 180 if mirror else 0
    f = Builder(f"{tag}_Furniture", coll); cu = Builder(f"{tag}_Upholstery", coll)
    # student desks: 2 rows x 2 columns, 3 seats each; students face the whiteboard (-X)
    for rx0 in (1.45, 2.6):
        for (y0, y1) in [(0.55, 2.15), (3.85, 5.45)]:
            a, c = sorted((X(rx0), X(rx0 + 0.55)))
            desk(f, a, y0, c, y1, M_OAK_Y, M_WHITE_MET)
            box(f, rx0 + 0.53, y0 + 0.05, 0.62, rx0 + 0.55, y1 - 0.05, 0.72, M_WHITE_MET)
            for k in range(3):
                yc = y0 + 0.27 + k * 0.53
                chair(f, cu, T(X(rx0 + 0.86), yc, 0, (-90 if not mirror else 90) + random.uniform(-7, 7)), M_FABRIC_GR)
                if random.random() < 0.6:
                    books(f, X(rx0 + 0.25), yc + random.uniform(-0.1, 0.1), 0.75, random.uniform(70, 110), random.randint(1, 2))
    # teacher desk + chair near window
    a, c = sorted((X(0.35), X(1.05)))
    desk(f, a, 0.5, c, 1.75, M_OAK_Y, M_WHITE_MET)
    box(f, 0.37, 0.52, 0.0, 0.39, 1.73, 0.72, M_OAK_Z)
    chair(f, cu, T(X(0.0 + 0.0) if False else X(0.75), 1.12, 0, 90 if not mirror else -90), M_LEATHER, arms=True) if False else None
    chair(f, cu, T(X(0.62) if mirror else X(0.62), 1.12, 0, (90 if not mirror else -90)), M_FABRIC_GR, arms=True)
    laptop(f, X(0.7), 1.0, 90 if mirror else -90, 108)
    books(f, X(0.6), 1.55, 0.75, 20, 3)
    # whiteboard (x=0 wall), aluminium frame, marker tray
    wx = X(0.012); s = -1 if mirror else 1
    box(f, 0.01, 1.68, 0.88, 0.035, 4.32, 2.12, M_STEEL)
    wall_plane(f"{tag}_Whiteboard", coll, "X", X(0.036), 1.71, 4.29, 0.91, 2.09, wb_mat, facing=-1 if mirror else 1)
    box(f, 0.03, 1.9, 0.86, 0.09, 4.1, 0.88, M_STEEL)
    for k, col in enumerate([M_BOOK[1], M_BOOK[0], M_PLASTIC_DK]):
        f.cyl(X(0.06), 2.2 + k * 0.08, 0.88, 0.895, 0.009, col, n=8, M=Matrix.Translation((0, 0, 0)))
    # wall-mounted TV (x=0 wall) right of whiteboard
    box(f, 0.01, 4.55, 1.22, 0.06, 5.77, 1.92, M_PLASTIC_DK)
    wall_plane(f"{tag}_TV_Screen", coll, "X", X(0.062), 4.565, 5.755, 1.235, 1.905, slide_mat, facing=-1 if mirror else 1)
    # framed prints on back wall (y = 6), facing -Y
    for k, (cx, pm) in enumerate(zip((1.35, 2.85), prints)):
        x0, x1 = sorted((X(cx - 0.33), X(cx + 0.33)))
        f.box(x0 - 0.035, 5.955, 1.18, x1 + 0.035, 5.99, 2.10, M_BLACK_MET)          # frame
        f.box(x0, 5.95, 1.215, x1, 5.956, 2.065, M_PAPER)                               # passe-partout
        plane_obj(f"{tag}_Print_{k}", coll, [(x1 - 0.05, 5.949, 1.29), (x0 + 0.05, 5.949, 1.29), (x0 + 0.05, 5.949, 1.99), (x1 - 0.05, 5.949, 1.99)], pm)
        gl2 = Builder(f"{tag}_PrintGlass_{k}", coll); gl2.box(x0, 5.946, 1.215, x1, 5.948, 2.065, M_GLASS); gl2.build()
    # wall clock above whiteboard
    f.cyl(0, 0, 0, 0.03, 0.16, M_WHITE_MET, n=32, M=Matrix.Translation((X(0.015), 3.0, 2.55)) @ Matrix.Rotation(math.radians(90 * s), 4, "Y"))
    # bookcase on back wall corner
    bx0, bx1 = sorted((X(3.0), X(3.85)))
    f.box(bx0, 5.62, 0, bx1, 5.99, 0.9, M_OAK_X)
    for k in range(3): books(f, (bx0 + bx1) / 2 + (k - 1) * 0.25, 5.8, 0.9, 90, 2)
    f.build(bevel=0.003); cu.build(bevel=0.02, segs=3, smooth=True)
    plant(coll, f"{tag}_Plant", X(3.65), 0.45, pot_h=0.45, pot_r=0.17, height=0.85, leaves=80, mat=M_PLANT_DK)

classroom(False, C_LAW, M_WB, M_SLIDE_LAW, (M_PR["law"], M_PR["history"]), "Law")
classroom(True, C_LANG, M_WB2, M_SLIDE_LANG, (M_PR["world"], M_PR["hello"]), "Lang")
# classroom name plates beside doors (admin side)
text_obj("Plate_Law", C_ADMIN, "HUQUQ VA TARIX", FONT_SB, 0.055, M_GRAPHITE, (4.07, 2.85, 1.6), (math.radians(90), 0, math.radians(90)), extrude=0.002)
text_obj("Plate_Lang", C_ADMIN, "XORIJIY TILLAR", FONT_SB, 0.055, M_GRAPHITE, (7.93, 2.85, 1.6), (math.radians(90), 0, math.radians(-90)), extrude=0.002)

# ================================================================== LIGHTING
def area(name, loc, size, energy, color=(1, 0.93, 0.85), rot=(0, 0, 0), sy=None, spread=180):
    L = bpy.data.lights.new(name, "AREA"); L.energy = energy; L.color = color
    L.shape = "RECTANGLE"; L.size = size[0]; L.size_y = size[1]
    L.spread = math.radians(spread)
    ob = bpy.data.objects.new(name, L); ob.location = loc; ob.rotation_euler = rot
    ob.visible_camera = False; ob.visible_glossy = False if spread < 180 else True
    C_LIGHT.objects.link(ob); return ob

fx = Builder("Light_Fixtures", C_LIGHT)
# classroom 600x600 LED panels (2 x 3 grid per room)
for zx0 in (0.0, 8.06):
    for cx in (zx0 + 1.2, zx0 + 2.75):
        for cy in (1.2, 3.0, 4.8):
            fx.box(cx - 0.31, cy - 0.31, H - 0.012, cx + 0.31, cy + 0.31, H - 0.001, M_WHITE_MET)
            fx.box(cx - 0.29, cy - 0.29, H - 0.014, cx + 0.29, cy + 0.29, H - 0.012, M_PANEL)
            area(f"Panel_{cx:.1f}_{cy:.1f}", (cx, cy, H - 0.02), (0.58, 0.58), 42, (1, 0.95, 0.88))
# admin: two linear slot lights + downlights
for cx in (5.0, 7.0):
    fx.box(cx - 0.04, 0.5, H - 0.012, cx + 0.04, 4.4, H - 0.001, M_BLACK_AL)
    fx.box(cx - 0.025, 0.52, H - 0.014, cx + 0.025, 4.38, H - 0.012, M_PANEL)
    area(f"Linear_{cx}", (cx, 2.45, H - 0.02), (0.06, 3.85), 68, (1, 0.94, 0.86))
for (cx, cy) in [(6.0, 1.0), (5.6, 4.9), (6.4, 4.9)]:
    fx.cyl(cx, cy, H - 0.012, H - 0.001, 0.05, M_BLACK_AL, n=24); fx.cyl(cx, cy, H - 0.013, H - 0.012, 0.035, M_LED_WARM, n=24)
    area(f"Down_{cx}_{cy}", (cx, cy, H - 0.02), (0.07, 0.07), 22, (1, 0.88, 0.74), spread=60)
# signature wall grazing light (from ceiling cove)
fx.box(4.06, 5.70, H - 0.06, 7.94, 5.75, H, M_CEIL)
area("Wall_Grazer", (6.0, 5.82, H - 0.03), (3.8, 0.06), 70, (0.86, 0.91, 1.0), spread=70)
area("Wall_Floor_Uplight", (6.0, 5.88, 0.02), (3.8, 0.04), 18, (1.0, 0.85, 0.66), rot=(math.radians(180), 0, 0), spread=60)
# entrance canopy downlights
for cx in (4.6, 6.0, 7.4):
    fx.cyl(cx, -0.75, 3.299, 3.31, 0.06, M_LED_WARM, n=24)
    area(f"Canopy_{cx}", (cx, -0.75, 3.29), (0.1, 0.1), 25, (1, 0.86, 0.7), spread=70)
fx.build()

# sun + sky (late afternoon, golden hour)
sun = bpy.data.lights.new("Sun", "SUN"); sun.energy = 0.6; sun.angle = math.radians(1.0); sun.color = (1.0, 0.62, 0.38)
so = bpy.data.objects.new("Sun", sun); so.rotation_euler = (math.radians(86), 0, math.radians(-38)); C_LIGHT.objects.link(so)
world = bpy.data.worlds.new("Sky"); scene.world = world; world.use_nodes = True
wn = world.node_tree; wn.nodes.clear()
sky = wn.nodes.new("ShaderNodeTexSky"); sky.sky_type = "MULTIPLE_SCATTERING"
try:
    sky.sun_disc = False; sky.sun_elevation = math.radians(0.8); sky.sun_rotation = math.radians(232)
    sky.altitude = 300; sky.air_density = 1.0; sky.aerosol_density = 0.8
except Exception as e:
    print("sky param", e)
bg = wn.nodes.new("ShaderNodeBackground"); bg.inputs[1].default_value = 0.3
wo = wn.nodes.new("ShaderNodeOutputWorld")
wn.links.new(sky.outputs[0], bg.inputs[0]); wn.links.new(bg.outputs[0], wo.inputs[0])

# ================================================================== EXTERIOR
ex_b = Builder("Exterior_Ground", C_EXT)
ex_b.box(-30, -30, -0.06, 45, 40, -0.05, M_GRASS)
ex_b.box(-4, -6.5, -0.05, 16, -0.25, 0.0, M_PAVER)
ex_b.box(-4, -0.25, -0.05, -0.25, 7.5, 0.0, M_PAVER); ex_b.box(12.25, -0.25, -0.05, 16, 7.5, 0.0, M_PAVER)        # plaza / sidewalk
ex_b.box(-30, -6.75, -0.05, 45, -6.5, 0.12, M_CURB)             # curb
ex_b.box(-30, -14.5, -0.08, 45, -6.75, -0.04, M_ASPHALT)        # road
for k in range(-10, 16):
    ex_b.box(k * 3.0, -10.68, -0.04, k * 3.0 + 1.6, -10.57, -0.038, M_ROADLINE)
ex_b.box(-30, -16.5, -0.05, 45, -14.5, 0.0, M_PAVER)            # far sidewalk
ex_b.build()
# entrance portal (oak-clad canopy + fins) and sign
po = Builder("Entrance_Portal", C_EXT)
po.box(3.80, -1.25, 0, 4.0, -0.25, TOP, M_OAK_Z)
po.box(8.0, -1.25, 0, 8.20, -0.25, TOP, M_OAK_Z)
po.box(3.80, -1.25, 3.30, 8.20, -0.25, TOP, M_OAK_X)
po.box(3.80, -1.27, 3.30, 8.20, -1.25, TOP, M_GRAPHITE)        # sign band
po.build(bevel=0.006)
text_obj("Exterior_Sign", C_EXT, "HUQUQ MAKTABI", FONT_XB, 0.30, M_LOGO, (6.0, -1.285, 3.58), (math.radians(90), 0, 0), extrude=0.02)
# planters by the entrance
pl = Builder("Planters", C_EXT)
for cx in (2.9, 9.1):
    pl.box(cx - 0.6, -1.2, 0, cx + 0.6, -0.6, 0.45, M_FACADE)
    pl.box(cx - 0.56, -1.16, 0.40, cx + 0.56, -0.64, 0.42, M_SOIL)
pl.build(bevel=0.01)
for cx in (2.9, 9.1):
    for dx in (-0.35, 0.0, 0.35):
        plant(C_EXT, f"Shrub_{cx}_{dx}", cx + dx, -0.9, pot_h=0.42, pot_r=0.001, height=0.5, leaves=70, mat=M_PLANT_DK)
# bollard lights along path
bl = Builder("Bollards", C_EXT)
for cx in (4.5, 7.5):
    for cy in (-3.0, -5.2):
        bl.cyl(cx, cy, 0, 0.8, 0.06, M_BLACK_AL, n=20); bl.cyl(cx, cy, 0.62, 0.72, 0.061, M_LED_WARM, n=20)
bl.build()
# background urban context (soft, far) — residential blocks with some lit windows at dusk
M_WIN_LIT = emission("Window_Lit_Warm", "#ffcf93", 2.2)
M_WIN_LIT2 = emission("Window_Lit_Cool", "#dfe8ff", 1.4)
bgb = Builder("Background_Buildings", C_EXT)
rb = random.Random(5)
for (x0, x1, y0, y1, h) in [(-16, 2, 15, 27, 15.5), (9, 31, 17, 29, 18.6), (-34, -18, 6, 18, 12.4)]:
    bgb.box(x0, y0, 0, x1, y1, h, M_BG_BLDG)
    for fl_ in range(int(h / 3.1)):
        z = fl_ * 3.1 + 0.9
        xx = x0 + 0.9
        while xx < x1 - 1.6:
            m = M_BG_WIN
            rr = rb.random()
            if rr < 0.33: m = M_WIN_LIT
            elif rr < 0.4: m = M_WIN_LIT2
            bgb.box(xx, y0 - 0.03, z, xx + 1.4, y0 + 0.02, z + 1.55, m)
            bgb.box(xx - 0.06, y0 - 0.12, z - 0.08, xx + 1.46, y0, z - 0.02, M_CURB)
            xx += 2.4
    bgb.box(x0 - 0.1, y0 - 0.15, h - 0.3, x1 + 0.1, y1 + 0.1, h, M_CURB)
bgb.build()
# trees (deciduous, clumped crowns) behind building and along street
def tree(name, x, y, h=6.5, r=2.2):
    rnd = random.Random(hash(name) & 0xffff)
    t = Builder(name + "_Trunk", C_EXT)
    t.cyl(x, y, 0, h * 0.5, 0.17, M_STEM, r1=0.11, n=14)
    clumps = []
    for k in range(7):
        a = rnd.uniform(0, 2 * math.pi); rr = r * rnd.uniform(0.25, 0.7)
        c = Vector((x + rr * math.cos(a), y + rr * math.sin(a), h * rnd.uniform(0.58, 0.85)))
        clumps.append((c, r * rnd.uniform(0.45, 0.7)))
        base = Vector((x, y, h * 0.45)); d = c - base
        M = Matrix.Translation(base) @ d.to_track_quat("Z", "Y").to_matrix().to_4x4()
        t.cyl(0, 0, 0, d.length * 0.85, 0.07, M_STEM, r1=0.025, n=8, M=M)
    t.build()
    cr = Builder(name + "_Crown", C_EXT)
    idx = cr._mat(M_PLANT_DK if rnd.random() < 0.5 else M_PLANT_LT)
    for (c, cr_r) in clumps:
        for i in range(520):
            u = rnd.uniform(-1, 1); th = rnd.uniform(0, 2 * math.pi); rr = cr_r * rnd.uniform(0.35, 1.0) ** 0.33
            p = c + Vector((rr * math.sqrt(1 - u * u) * math.cos(th), rr * math.sqrt(1 - u * u) * math.sin(th), rr * 0.75 * u))
            M = Matrix.Translation(p) @ Euler((rnd.uniform(0, 6.3), rnd.uniform(0, 6.3), rnd.uniform(0, 6.3))).to_matrix().to_4x4()
            sz = rnd.uniform(0.07, 0.12); o = len(cr.v)
            cr.v += [tuple(M @ Vector(q)) for q in [(-sz, 0, 0), (0, -sz * 0.5, 0.01), (sz, 0, 0), (0, sz * 0.5, 0.01)]]
            cr.f.append((o, o + 1, o + 2, o + 3)); cr.mi.append(idx)
    cr.build()
for i, (x, y) in enumerate([(-3.8, 9), (2.0, 11.0), (9.8, 10.5), (15.8, 8.5), (-6.5, -4.6), (18.5, -4.2), (-12, 4)]):
    tree(f"Tree_{i}", x, y, h=random.uniform(6.5, 8.5), r=random.uniform(2.2, 2.9))
# facade wall-washers (dusk) on the piers between windows + grazing on portal
for (cx, tgt) in [(-0.0, 0), (2.0, 0), (10.0, 0), (12.0, 0)]:
    area(f"Facade_Uplight_{cx}", (cx, -0.45, 0.05), (0.08, 0.08), 6, (1, 0.8, 0.58), rot=(math.radians(-12), 0, 0), spread=35)
fxe = Builder("Facade_Uplight_Fixtures", C_EXT)
for cx in (0.0, 2.0, 10.0, 12.0):
    fxe.box(cx - 0.06, -0.52, 0, cx + 0.06, -0.38, 0.05, M_BLACK_AL); fxe.box(cx - 0.04, -0.5, 0.05, cx + 0.04, -0.4, 0.052, M_LED_WARM)
fxe.build()
# street lamps
sl = Builder("Street_Lamps", C_EXT)
for cx in (-4.0, 16.0):
    sl.cyl(cx, -6.2, 0, 5.2, 0.07, M_BLACK_AL, r1=0.05, n=16)
    sl.box(cx - 0.05, -6.2, 5.1, cx + 0.05, -5.0, 5.18, M_BLACK_AL)
    sl.box(cx - 0.12, -5.25, 5.05, cx + 0.12, -4.75, 5.1, M_BLACK_AL); sl.box(cx - 0.1, -5.23, 5.045, cx + 0.1, -4.77, 5.05, M_LED_WARM)
    area(f"StreetLamp_{cx}", (cx, -5.0, 5.03), (0.2, 0.45), 260, (1, 0.82, 0.6), spread=120)
sl.build()

# roller blinds in classroom windows (partly lowered)
bln = Builder("Roller_Blinds", C_ARCH)
M_BLIND = textured("Blind_Fabric", srgb("#e9e5dc"), 0.9, 600, 0.05, sheen=0.3)
for (a, b) in WINDOWS:
    bln.box(a + 0.02, 0.02, 2.62, b - 0.02, 0.09, 2.72, M_WHITE_MET)
    bln.box(a + 0.04, 0.045, 2.18, b - 0.04, 0.05, 2.62, M_BLIND)
    bln.box(a + 0.04, 0.035, 2.16, b - 0.04, 0.06, 2.18, M_WHITE_MET)
bln.build()

# ================================================================== ANIMATION
scene.render.fps = FPS
SHOTS = {  # name: (start, end)
    "A_exterior": (1, 144),
    "B_entry_cowork_admin_law": (145, 1056),
    "C_languages": (1057, 1224),
    "D_final_wide": (1225, 1392),
}
scene.frame_start, scene.frame_end = 1, 1392

def key_path(ob, keys, prop="location"):
    for f, v in keys:
        setattr(ob, prop, v); ob.keyframe_insert(prop, frame=f)

def make_cam(name, lens, keys_pos, keys_tgt, fstop=8.0, focus_dist=None):
    cd = bpy.data.cameras.new(name); cd.lens = lens; cd.sensor_width = 36; cd.clip_start = 0.05; cd.clip_end = 300
    cd.dof.use_dof = True; cd.dof.aperture_fstop = fstop
    cam = bpy.data.objects.new(name, cd); C_CAM.objects.link(cam)
    tgt = bpy.data.objects.new(name + "_Target", None); tgt.empty_display_size = 0.2; C_CAM.objects.link(tgt)
    key_path(cam, keys_pos); key_path(tgt, keys_tgt)
    con = cam.constraints.new("TRACK_TO"); con.target = tgt; con.track_axis = "TRACK_NEGATIVE_Z"; con.up_axis = "UP_Y"
    cd.dof.focus_object = tgt
    return cam

E = 1.58  # eye height
# A — exterior establishing (6 s): sweeping arc from street towards the facade
camA = make_cam("CAM_A_Exterior", 28,
                [(1, (-5.5, -15.5, 1.9)), (144, (1.8, -11.0, 1.7))],
                [(1, (5.0, 0.0, 2.0)), (144, (6.0, 0.0, 1.9))], fstop=11)
# B — one continuous take: approach, door opens, enter, coworking reveal, pans, admin wall, details, law class
P = [
    (145, (6.0, -7.2, E)), (230, (6.0, -2.4, E)), (300, (6.0, -0.4, E)), (360, (6.0, 1.15, E)),     # approach + enter
    (552, (6.0, 1.45, E)),                                                                              # pan left/right (slow creep)
    (690, (6.0, 3.35, 1.62)),                                                                           # glide toward admin desk
    (760, (7.0, 3.5, 1.5)), (860, (5.05, 3.8, 1.5)),                                                  # details: cooler/plant -> TV
    (935, (3.75, 3.6, E)), (1000, (3.15, 2.9, E)), (1056, (3.0, 2.45, E)),                               # into Law & History
]
TG = [
    (145, (6.0, 0.0, 1.45)), (230, (6.0, 1.0, 1.35)), (300, (6.0, 4.0, 1.4)), (360, (6.0, 5.5, 1.4)),
    (400, (6.0, 5.5, 1.3)), (440, (4.4, 2.6, 1.3)), (470, (4.3, 1.5, 1.45)), (500, (7.7, 1.5, 1.45)), (530, (7.7, 2.6, 1.3)), (552, (6.0, 5.6, 1.6)),
    (690, (6.0, 6.0, 2.05)),
    (760, (7.62, 5.05, 1.0)), (800, (7.0, 6.0, 1.4)), (860, (4.1, 5.0, 1.45)),
    (935, (0.0, 3.4, 1.4)), (1000, (0.0, 3.6, 1.35)), (1056, (2.1, 6.0, 1.55)),
]
camB = make_cam("CAM_B_Walkthrough", 22, P, TG, fstop=8)
# C — Foreign languages classroom
camC = make_cam("CAM_C_Languages", 22,
                [(1057, (8.35, 3.65, E)), (1140, (9.3, 3.1, E)), (1224, (9.15, 2.3, E))],
                [(1057, (12.0, 3.2, 1.35)), (1140, (12.0, 3.4, 1.35)), (1224, (10.1, 6.0, 1.55))], fstop=8)
# D — final cinematic wide (crane up & pull back)
camD = make_cam("CAM_D_FinalWide", 26,
                [(1225, (6.0, -5.5, 1.5)), (1392, (3.6, -13.5, 3.6))],
                [(1225, (6.0, 0.0, 2.1)), (1392, (6.0, 0.0, 1.9))], fstop=11)
for cam, (s, e) in zip((camA, camB, camC, camD), SHOTS.values()):
    m = scene.timeline_markers.new(cam.name, frame=s); m.camera = cam
scene.camera = camA

# entrance door: closed until f236, swings inward (+90 deg) by f292 (only during the entry)
for f, a in [(1, 0), (236, 0), (292, 92), (1100, 92), (1225, 0)]:
    DOOR.rotation_euler = (0, 0, math.radians(a)); DOOR.keyframe_insert("rotation_euler", frame=f)
# exposure: auto-exposure style adaptation as the camera moves inside
vs = scene.view_settings
for f, ev in [(1, 0.0), (144, 0.0), (145, 0.0), (250, 0.0), (330, 0.0), (1056, 0.0), (1057, 0.0), (1224, 0.0), (1225, 0.0)]:
    vs.exposure = ev; vs.keyframe_insert("exposure", frame=f)

# ================================================================== RENDER SETTINGS
r = scene.render
r.engine = "CYCLES"; r.resolution_x, r.resolution_y, r.resolution_percentage = 1920, 1080, 100
r.use_persistent_data = True
cy = scene.cycles
cy.device = "CPU"; cy.samples = 12; cy.use_adaptive_sampling = True; cy.adaptive_threshold = 0.05; cy.adaptive_min_samples = 6
cy.use_denoising = True
try: cy.denoiser = "OPENIMAGEDENOISE"
except Exception: pass
try: cy.denoising_input_passes = "RGB_ALBEDO_NORMAL"
except Exception: pass
cy.max_bounces = 6; cy.diffuse_bounces = 2; cy.glossy_bounces = 2; cy.transmission_bounces = 4; cy.transparent_max_bounces = 6
cy.caustics_reflective = False; cy.caustics_refractive = False
cy.sample_clamp_indirect = 6.0; cy.blur_glossy = 1.0
cy.use_light_tree = False
try:
    vs.view_transform = "AgX"; vs.look = "AgX - Medium High Contrast"
except Exception as e:
    print("look", e)
r.image_settings.file_format = "PNG"; r.image_settings.color_depth = "8"
r.film_transparent = False

bpy.ops.file.pack_all() if False else None
os.makedirs(os.path.dirname(OUT), exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=OUT, relative_remap=True)
print("SAVED", OUT, "objects:", len(bpy.data.objects))
