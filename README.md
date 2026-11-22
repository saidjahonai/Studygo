# HUQUQ MAKTABI: architectural visualization

Photorealistic architectural walkthrough of the HUQUQ MAKTABI training centre.

**Context:** HUQUQ MAKTABI occupies 12 m of the **ground floor of a 75 m long, 3-storey building**. Its left neighbour is
a 5 m **VINO VODKA** shop, then a 5 m residential stair entrance; to its right are **50 m of services** (apteka, market, kafe, sartaroshxona,
notarius, maishiy xizmatlar), then a 3 m building end. The illuminated **HUQUQ MAKTABI** letters are mounted on a canopy (naves)
spanning the school's 12 m frontage.

**Footprint 12.0 × 6.0 m = 72 m² gross**, with 200 mm external walls and 100 mm partitions; the clear interior is 11.6 × 5.6 m.
The **main entrance is a glass door at the exact centre of the 12 m front facade** (x = 6 000 mm).
Standing outside and looking through the entrance:

| Position | Zone | Clear size | Content |
|---|------|-----|---------|
| **LEFT** | **Law & History classroom** | 3.70 × 5.60 m (20.7 m²) | 12 seats in light-oak desks (3 rows × 2 desks × 2), upholstered chairs, whiteboard on a navy accent wall, wall-mounted TV, 2 framed legal/history prints, teacher desk |
| **CENTRE** | **Administration + Coworking**, one combined space | 4.00 × 5.60 m (22.4 m²) | glass partition with a separate central glass door, entry vestibule, coworking ONLY on the LEFT and RIGHT sides (counters with 3 seats each), the centre kept open so nothing blocks the administrator desk at the back |
| **RIGHT** | **Foreign Languages classroom** | 3.70 × 5.60 m (20.7 m²) | same furniture, whiteboard on a teal accent wall, TV, 2 framed international-education prints |

There are only two classrooms. Room widths are derived from furniture and circulation, not from equal thirds:

* **Admin:** 0.6 m counters each side, a 1.6 m central aisle from the door, and an open centre leading straight to the administrator desk, water cooler and TV.
* **Classrooms:** students face the board along the 5.6 m axis. There is 1.35 m between the board and the first desk, an 0.8 m aisle, a 1.2 m row pitch and an 0.8 m rear circulation zone. Each classroom door (1 000 mm, in the partition next to the vestibule) opens into that rear zone.

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
| `renders/stills/01…07_*.png` | High-resolution stills (2560×1440): exterior at dusk, glass entrance, coworking + admin, signature wall, Law & History, Foreign Languages, building context |
| `docs/floor_plan.png` / `.pdf` | Dimensioned floor plan (mm), A3 |
| `renders/stills/00_topdown_plan.png` | Photoreal top-down plan render of the 3D model (ceiling cut away) |
| `scripts/` | Fully procedural pipeline (see below) |

## Film sequence

1. Exterior establishing shot at dusk: the 3-storey building, its neighbours, and the canopy with the illuminated HUQUQ MAKTABI letters
2. Camera approaches the glass administration entrance; the glass door swings open
3. Camera enters; coworking is revealed directly ahead
4. Smooth pan left and right across the coworking counters
5. Glide toward the administrator's desk, revealing the illuminated signature wall
6. Details: water cooler and planters, then the TV with HUQUQ MAKTABI motion graphics
7. Back through the vestibule and the door on the left into the **Law & History** classroom (desks, whiteboard, TV, framed prints)
8. Dissolve to the **Foreign Languages** classroom
9. Final cinematic wide: crane up and pull back from the glowing facade, then the title card

Shots 2–7 are a single continuous camera take.

## Rendering pipeline

* **Blender 5.2.4 LTS** (`bpy` module) with **Cycles path tracing** (physically based materials, global illumination,
  real refraction and reflection on glass, Nishita-type multiple-scattering sky and sun, area lights)
* OpenImageDenoise (albedo + normal), AgX view transform (Medium High Contrast)
* Path-traced natively at 1920×1080 on every second frame of the 24 fps timeline (CPU only), then
  motion-compensated interpolation to 24 fps with ffmpeg `minterpolate`. The fast camera moves (timeline frames 700–970)
  were also rendered on the even frames, so they play at native 24 fps with no interpolation. Cross-dissolves, H.264 encode

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
