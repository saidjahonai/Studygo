"""Assemble rendered frames into the final film (MP4 / H.264, 1920x1080, 24 fps).

Frames were path-traced at 12 fps (every 2nd frame of the 24 fps timeline) and are
motion-interpolated back to 24 fps per shot, then joined with cross-dissolves.

  python scripts/assemble_video.py FRAMES_DIR
"""
import os, subprocess, sys, glob, shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FR = sys.argv[1]
WORK = os.path.join(FR, "_shots"); os.makedirs(WORK, exist_ok=True)
OUT = os.path.join(ROOT, "video", "HUQUQ_MAKTABI_walkthrough_1080p.mp4")
FONT = "/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf"
FONT2 = "/usr/share/fonts/opentype/inter/Inter-Medium.otf"
SHOTS = [("A", 1, 143), ("B", 145, 1055), ("C", 1057, 1223), ("D", 1225, 1391)]
XF = [0.8, 1.0, 1.2]          # dissolve lengths between consecutive shots (s)
NATIVE = {"B": (700, 970)}    # timeline range also rendered on even frames (fast pans) -> native 24 fps

def run(cmd):
    print(" ".join(cmd)[:220], flush=True); subprocess.run(cmd, check=True)

durs = []
for name, a, b in SHOTS:
    seq = os.path.join(WORK, name); os.makedirs(seq, exist_ok=True)
    frames = [os.path.join(FR, f"f{f:04d}.png") for f in range(a, b + 1, 2)]
    missing = [f for f in frames if not os.path.exists(f)]
    if missing: sys.exit(f"missing {len(missing)} frames for shot {name}, e.g. {missing[0]}")
    for i, f in enumerate(frames):
        dst = os.path.join(seq, f"{i:05d}.png")
        if not os.path.exists(dst): os.symlink(f, dst)
    out = os.path.join(WORK, f"{name}.mp4")
    if not os.path.exists(out):
        run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", "12", "-i", os.path.join(seq, "%05d.png"),
             "-vf", "minterpolate=fps=24:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1,format=yuv420p",
             "-c:v", "libx264", "-crf", "12", "-preset", "medium", out])
    # fast camera moves: replace interpolated frames with real path-traced 24 fps frames
    if name in NATIVE and not os.path.exists(out + ".native"):
        n0, n1 = NATIVE[name]
        dec = os.path.join(WORK, f"{name}_dec"); fin = os.path.join(WORK, f"{name}_fin")
        os.makedirs(dec, exist_ok=True); os.makedirs(fin, exist_ok=True)
        run(["ffmpeg", "-y", "-loglevel", "error", "-i", out, os.path.join(dec, "%05d.png")])
        decoded = sorted(os.listdir(dec)); used = 0
        for j, fn in enumerate(decoded):
            f = a + j; real = os.path.join(FR, f"f{f:04d}.png")
            src = real if (n0 <= f <= n1 and os.path.exists(real)) else os.path.join(dec, fn)
            used += src == real
            dst = os.path.join(fin, f"{j:05d}.png")
            if os.path.lexists(dst): os.remove(dst)
            os.symlink(src, dst)
        run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", "24", "-i", os.path.join(fin, "%05d.png"),
             "-vf", "format=yuv420p", "-c:v", "libx264", "-crf", "12", "-preset", "medium", out + ".tmp.mp4"])
        os.replace(out + ".tmp.mp4", out); open(out + ".native", "w").write(str(used))
        print(f"shot {name}: {used} native 24 fps frames patched in", flush=True)
    durs.append(len(frames) / 12.0)

# cross-dissolves + fades + end title
inputs = []
for name, _, _ in SHOTS: inputs += ["-i", os.path.join(WORK, f"{name}.mp4")]
fc = []; prev = "[0:v]"; t = durs[0]
for i in range(1, len(SHOTS)):
    off = t - XF[i - 1]
    lab = f"[x{i}]"
    fc.append(f"{prev}[{i}:v]xfade=transition=fade:duration={XF[i-1]}:offset={off:.3f}{lab}")
    prev = lab; t = off + durs[i]
total = t
title_in = total - 3.4
fc.append(f"{prev}fade=t=in:st=0:d=1.2,fade=t=out:st={total-1.4:.3f}:d=1.4,"
          f"drawtext=fontfile={FONT}:text='HUQUQ MAKTABI':fontcolor=white:fontsize=96:x=(w-text_w)/2:y=h*0.70:"
          f"alpha='if(lt(t,{title_in:.2f}),0,min(1,(t-{title_in:.2f})/0.8))':shadowcolor=black@0.6:shadowx=0:shadowy=3,"
          f"drawtext=fontfile={FONT2}:text='Huquq-tartibot va davlat xizmatiga tayyorlov markazi':fontcolor=0xE6D3A3:fontsize=34:x=(w-text_w)/2:y=h*0.70+118:"
          f"alpha='if(lt(t,{title_in+0.4:.2f}),0,min(1,(t-{title_in+0.4:.2f})/0.8))':shadowcolor=black@0.6:shadowx=0:shadowy=2,format=yuv420p[v]")
os.makedirs(os.path.dirname(OUT), exist_ok=True)
run(["ffmpeg", "-y", "-loglevel", "error", *inputs, "-filter_complex", ";".join(fc), "-map", "[v]",
     "-c:v", "libx264", "-profile:v", "high", "-level", "4.1", "-crf", "18", "-preset", "slow",
     "-pix_fmt", "yuv420p", "-r", "24", "-movflags", "+faststart", OUT])
print(f"VIDEO {OUT}  duration {total:.2f}s")
