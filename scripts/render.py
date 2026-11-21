"""Render frames from blender/huquq_maktabi.blend.

  python scripts/render.py --frames 1,300,700 --pct 50 --samples 32 --out DIR
  python scripts/render.py --range 145 1056 --step 2 --out DIR      (sequence; skips existing files)
  python scripts/render.py --still CAM_NAME FRAME --out file.png --samples 256  (hi-res still)
"""
import argparse, os, sys, time
import bpy

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ap = argparse.ArgumentParser()
ap.add_argument("--frames", default="")
ap.add_argument("--range", nargs=2, type=int)
ap.add_argument("--step", type=int, default=1)
ap.add_argument("--pct", type=int, default=100)
ap.add_argument("--samples", type=int, default=0)
ap.add_argument("--threshold", type=float, default=0)
ap.add_argument("--out", required=True)
ap.add_argument("--still", nargs=2)
ap.add_argument("--res", nargs=2, type=int)
ap.add_argument("--blend", default=os.path.join(ROOT, "blender", "huquq_maktabi.blend"))
a = ap.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:])

bpy.ops.wm.open_mainfile(filepath=a.blend)
sc = bpy.context.scene
sc.render.resolution_percentage = a.pct
if a.res: sc.render.resolution_x, sc.render.resolution_y = a.res
if a.samples: sc.cycles.samples = a.samples
if a.threshold: sc.cycles.adaptive_threshold = a.threshold
sc.cycles.device = "CPU"
sc.render.threads_mode = "AUTO"

def render(f, path):
    sc.frame_set(f)
    sc.render.filepath = path
    t = time.time()
    bpy.ops.render.render(write_still=True)
    print(f"FRAME {f} -> {path} {time.time() - t:.1f}s", flush=True)

if a.still:
    cam, f = a.still[0], int(a.still[1])
    for m in list(sc.timeline_markers):
        sc.timeline_markers.remove(m)
    sc.camera = bpy.data.objects[cam]
    render(f, a.out)
else:
    os.makedirs(a.out, exist_ok=True)
    frames = [int(x) for x in a.frames.split(",") if x] if a.frames else list(range(a.range[0], a.range[1] + 1, a.step))
    for f in frames:
        p = os.path.join(a.out, f"f{f:04d}.png")
        if os.path.exists(p) and os.path.getsize(p) > 0:
            continue
        render(f, p)
