"""Photoreal top-down plan render of the 3D model (orthographic, cut just below the ceiling)."""
import bpy, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
out = sys.argv[sys.argv.index("--") + 1] if "--" in sys.argv else os.path.join(ROOT, "renders", "stills", "00_topdown_plan.png")
samples = int(sys.argv[sys.argv.index("--") + 2]) if "--" in sys.argv and len(sys.argv) > sys.argv.index("--") + 2 else 32
bpy.ops.wm.open_mainfile(filepath=os.path.join(ROOT, "blender", "huquq_maktabi.blend"))
sc = bpy.context.scene
for m in list(sc.timeline_markers): sc.timeline_markers.remove(m)
for n in ("Light_Fixtures",):
    bpy.data.objects[n].hide_render = True
cd = bpy.data.cameras.new("CAM_TopDown"); cd.type = "ORTHO"; cd.ortho_scale = 13.0; cd.clip_start = 0.02; cd.clip_end = 10
cam = bpy.data.objects.new("CAM_TopDown", cd); sc.collection.objects.link(cam)
cam.location = (6.0, 2.6, 3.08); cam.rotation_euler = (0, 0, 0)
sc.camera = cam; sc.frame_set(1300)
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 2600, 1500, 100
sc.cycles.samples = samples; sc.view_settings.exposure = 0.3
sc.render.filepath = out
bpy.ops.render.render(write_still=True); print("TOPDOWN", out)
