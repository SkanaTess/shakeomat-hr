from PIL import Image
import os

BASE = "C:/Users/korisnik/Desktop/Claude_Code_Projects/shakeomat-hr"

# Images: 768x1376 portrait. People visible in y:500-1100 range.
# Crops (left, top, right, bottom) in absolute pixels
crops = [
    # gym-viz-1: man left of machine, side profile face
    ("gym-viz-1.png", "face-luka.png",    10, 520, 270, 800),
    # gym-viz-4: man right of machine, front face
    ("gym-viz-4.png", "face-tomislav.png", 530, 490, 768, 760),
    # gym-viz-2: man at screen, face upper-right
    ("gym-viz-2.png", "face-marko.png",   450, 390, 720, 680),
]

for inp, out, l, t, r, b in crops:
    src = os.path.join(BASE, inp)
    dst = os.path.join(BASE, out)
    img = Image.open(src)
    cropped = img.crop((l, t, r, b))
    cw, ch = cropped.size
    side = min(cw, ch)
    cx, cy = cw//2, ch//2
    sq = cropped.crop((cx - side//2, cy - side//2, cx + side//2, cy + side//2))
    sq = sq.resize((240, 240), Image.LANCZOS)
    sq.save(dst, optimize=True)
    print(f"  {out} done")

print("Done.")
