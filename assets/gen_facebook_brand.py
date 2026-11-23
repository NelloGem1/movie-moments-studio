"""Generate Facebook Page profile photo + cover photo for 'Movie Edits'."""
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

OUT = os.path.expanduser(r"~\Downloads")
F_BOLD = r"C:\Windows\Fonts\segoeuib.ttf"
F_REG = r"C:\Windows\Fonts\segoeui.ttf"

TEAL = np.array([14, 62, 84])     # deep cinematic teal
NAVY = np.array([8, 14, 26])     # near-black blue
GOLD = np.array([245, 185, 66])   # warm gold accent
ORANGE = np.array([214, 110, 40]) # warm highlight
WHITE = np.array([245, 247, 250])


def gradient(w, h, c_tl, c_br, c_glow=None, glow_xy=(0.5, 0.45), glow_r=0.55, glow_amt=0.35):
    """Diagonal gradient + optional radial warm glow."""
    ys, xs = np.mgrid[0:h, 0:w].astype(np.float32)
    fx = xs / max(w - 1, 1); fy = ys / max(h - 1, 1)
    t = (fx * 0.6 + fy * 0.4)[..., None]
    img = c_tl * (1 - t) + c_br * t
    if c_glow is not None:
        gx = (fx - glow_xy[0]) * (w / h)
        gy = (fy - glow_xy[1])
        d = np.sqrt(gx * gx + gy * gy)
        mask = np.clip(1 - d / glow_r, 0, 1) ** 2 * glow_amt
        img = img * (1 - mask[..., None]) + c_glow * mask[..., None]
    return Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), "RGB")


def grain(img, amount=5):
    a = np.asarray(img).astype(np.int16)
    n = np.random.default_rng(7).integers(-amount, amount + 1, a.shape)
    return Image.fromarray(np.clip(a + n, 0, 255).astype(np.uint8), "RGB")


def font(path, size):
    return ImageFont.truetype(path, size)


def text_center(dr, cx, y, s, f, fill):
    bb = dr.textbbox((0, 0), s, font=f)
    dr.text((cx - (bb[2] - bb[0]) / 2 - bb[0], y - bb[1]), s, font=f, fill=fill)


# ---------------- PROFILE PHOTO (1080x1080, circle-safe center) ----------------
S = 1080
img = gradient(S, S, TEAL, NAVY, c_glow=ORANGE, glow_xy=(0.5, 0.35), glow_r=0.5, glow_amt=0.30)
img = img.filter(ImageFilter.GaussianBlur(0.4))
dr = ImageDraw.Draw(img)

# gold ring
cx = cy = S / 2
r_out, r_in = 400, 372
dr.ellipse([cx - r_out, cy - r_out, cx + r_out, cy + r_out], outline=tuple(GOLD), width=10)
dr.ellipse([cx - r_in, cy - r_in, cx + r_in, cy + r_in], outline=tuple(WHITE), width=4)

# play triangle
tri = [(cx - 130, cy - 210), (cx - 130, cy + 210), (cx + 230, cy)]
dr.polygon(tri, fill=tuple(WHITE))
# subtle gold underline bar
bw = 560
dr.rounded_rectangle([cx - bw / 2, cy + 330, cx + bw / 2, cy + 342], radius=6, fill=tuple(GOLD))

img = grain(img, 4)
img.save(os.path.join(OUT, "movie_edits_profile.png"))
print("profile:", os.path.join(OUT, "movie_edits_profile.png"))

# ---------------- COVER PHOTO (1640x624 retina) ----------------
W, H = 1640, 624
img = gradient(W, H, TEAL, NAVY, c_glow=ORANGE, glow_xy=(0.72, 0.4), glow_r=0.65, glow_amt=0.38)
dr = ImageDraw.Draw(img)

# left accent: vertical gold line + film-strip ticks
x0 = 150
dr.rectangle([x0 - 6, 170, x0 + 6, H - 170], fill=tuple(GOLD))
for i in range(7):
    y = 190 + i * 38
    dr.rectangle([x0 + 26, y, x0 + 66, y + 14], fill=tuple(WHITE) + (90,))

# title
f_title = font(F_BOLD, 130)
f_sub = font(F_REG, 44)
title = "MOVIE EDITS"
bb = dr.textbbox((0, 0), title, font=f_title)
tw = bb[2] - bb[0]
dr.text((x0 + 110, 190 - bb[1]), title, font=f_title, fill=tuple(WHITE))

# subtitle with letter spacing
sub = "O F F I C I A L   T R A I L E R   E D I T S"
f_sub2 = font(F_REG, 46)
sbb = dr.textbbox((0, 0), sub, font=f_sub2)
dr.text((x0 + 110, 360 - sbb[1]), sub, font=f_sub2, fill=tuple(GOLD))

# small play triangles row (film motif)
for i, tx in enumerate([x0 + 120, x0 + 200, x0 + 280]):
    dr.polygon([(tx, 480), (tx + 34, 480 + 24), (tx, 480 + 48)],
               fill=tuple(WHITE) + (120 - i * 30,))

# right side: big translucent play button
pr = 150
px, py = W - 330, H / 2
dr.ellipse([px - pr, py - pr, px + pr, py + pr], outline=tuple(WHITE) + (70,), width=6)
dr.polygon([(px - 40, py - 70), (px - 40, py + 70), (px + 90, py)],
           fill=tuple(WHITE) + (200,))

img = img.filter(ImageFilter.GaussianBlur(0.3))
img = grain(img, 4)
img.save(os.path.join(OUT, "movie_edits_cover.png"))
print("cover:", os.path.join(OUT, "movie_edits_cover.png"))
