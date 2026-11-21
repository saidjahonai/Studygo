# HUQUQ MAKTABI: architectural visualization

Photorealistic architectural walkthrough of the HUQUQ MAKTABI training centre,
a 12 × 6 m (72 m²) building split into three 4 × 6 m zones.

| # | Zone | Content |
|---|------|---------|
| 1 | **Law & History classroom** (4 × 6 m) | light-oak desks for 12, upholstered chairs, whiteboard, wall-mounted TV, 2 framed legal/history prints, navy accent wall |
| 2 | **Administration + Coworking** (4 × 6 m, **one combined space**) | glass partition with a separate glass entrance door. Coworking table straight ahead, coworking counters left and right, a 1.5 m circulation aisle, and the administrator/reception desk at the back in front of the illuminated signature wall |
| 3 | **Foreign Languages classroom** (4 × 6 m) | same light-oak furniture, whiteboard, wall-mounted TV, 2 framed international-education prints, teal accent wall |

**Signature wall** (behind the administrator): navy acoustic slats on a graphite felt backing,
a graphite logo panel with an illuminated white **HUQUQ MAKTABI** logo and a brass rule, and cool LED contour
lines in a podcast-studio style plus a warm floor grazer. It lists the specializations: PROKURATURA · ICHKI ISHLAR ORGANLARI ·
ADLIYA · SUD TIZIMI · YURIDIK KADRLAR · DAVLAT XIZMATI. It also includes a TV playing an animated HUQUQ MAKTABI
motion-graphics loop, two white planters, a water cooler and a fluted-oak reception desk.

## Deliverables

| File | What |
|------|------|
| `video/HUQUQ_MAKTABI_walkthrough_1080p.mp4` | **Final film**, 1920×1080, H.264, 24 fps, ~55 s |
| `blender/huquq_maktabi.blend` | Editable Blender 5.2 project (collections per zone, cameras, lights, materials) |
| `renders/stills/*.png` | High-resolution interior/exterior stills (2560×1440) |
| `docs/floor_plan.png` / `.pdf` | Dimensioned floor plan (mm), A3 |
| `scripts/` | Fully procedural pipeline (see below) |

## Film sequence

1. Exterior establishing shot at dusk (street → facade, illuminated sign)
2. Camera approaches the glass administration entrance; the glass door swings open
3. Camera enters; coworking is revealed directly ahead
4. Smooth pan left and right across the coworking counters
5. Glide toward the administrator's desk, revealing the illuminated signature wall
6. Details: water cooler and planters, then the TV with HUQUQ MAKTABI motion graphics
7. Through the door into the **Law & History** classroom (desks, whiteboard, TV, framed prints)
8. Dissolve to the **Foreign Languages** classroom
9. Final cinematic wide: crane up and pull back from the glowing facade, then the title card

Shots 2–7 are a single continuous camera take.

## Rendering pipeline

* **Blender 5.2.4 LTS** (`bpy` module) with **Cycles path tracing** (physically based materials, global illumination,
  real refraction and reflection on glass, Nishita-type multiple-scattering sky and sun, area lights)
* OpenImageDenoise (albedo + normal), AgX view transform (Medium High Contrast)
* Path-traced natively at 1920×1080 on every second frame of the 24 fps timeline (CPU only), then
  motion-compensated interpolation to 24 fps with ffmpeg `minterpolate`, cross-dissolves, H.264 encode

```bash
python -m venv /opt/bvenv && /opt/bvenv/bin/pip install bpy==5.2.4 pillow matplotlib
/opt/bvenv/bin/python scripts/make_textures.py      # TV loop, prints, whiteboards, slides
/opt/bvenv/bin/python scripts/build_scene.py        # -> blender/huquq_maktabi.blend
/opt/bvenv/bin/python scripts/render.py --range 1 1391 --step 2 --out /path/frames
/opt/bvenv/bin/python scripts/assemble_video.py /path/frames   # -> video/*.mp4
/opt/bvenv/bin/python scripts/floorplan.py          # -> docs/floor_plan.*
```

Opening `blender/huquq_maktabi.blend` in Blender 5.2+ gives the complete scene. Timeline markers switch between
the four cameras (`CAM_A_Exterior`, `CAM_B_Walkthrough`, `CAM_C_Languages`, `CAM_D_FinalWide`). For a final-quality
re-render on a GPU workstation, raise *Render → Sampling* to 128+ samples and render all frames
(`--step 1`); no interpolation is needed then.
