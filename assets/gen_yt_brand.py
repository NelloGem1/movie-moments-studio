"""Generate YouTube channel logo (800x800) + banner (2560x1440) for 'Movie Moments'."""
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

OUT = os.path.expanduser(r"~\Downloads")
F_BOLD = r"C:\Windows\Fonts\segoeuib.ttf"
F_REG = r"C:\Windows\Fonts\segoeui.ttf"

TEAL = np.array([14, 62, 84])
NAVY = np.array([8, 14, 26])
GOLD = np.array([245, 185, 66])
ORANGE = np.array([214, 110, 40])
WHITE = np.array([245, 247, 250])


def gradient(w, h, c_tl, c_br, c_glow=None, glow_xy=(0.5, 0.45), glow_r=0.55, glow_amt=0.35):
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


def grain(img, amount=4):
    a = np.asarray(img).astype(np.int16)
    n = np.random.default_rng(7).integers(-amount, amount + 1, a.shape)
    return Image.fromarray(np.clip(a + n, 0, 255).astype(np.uint8), "RGB")


def font(path, size):
    return ImageFont.truetype(path, size)


# ---------------- LOGO (800x800) ----------------
S = 800
img = gradient(S, S, TEAL, NAVY, c_glow=ORANGE, glow_xy=(0.5, 0.35), glow_r=0.5, glow_amt=0.30)
dr = ImageDraw.Draw(img)
cx = cy = S / 2

# film-frame corners (subtle)
for sx, sy in [(-1, -1), (1, -1), (-1, 1), (1, 1)]:
    ex, ey = cx + sx * 300, cy + sy * 300
    dr.rounded_rectangle([min(cx, ex) - 8, min(cy, ey) - 8,
                          max(cx, ex) + 8, max(cy, ey) + 8],
                         radius=14, outline=tuple(GOLD), width=6)

# play button
pr = 170
dr.ellipse([cx - pr, cy - pr, cx + pr, cy + pr], outline=tuple(WHITE), width=8)
dr.polygon([(cx - 55, cy - 95), (cx - 55, cy + 95), (cx + 110, cy)], fill=tuple(WHITE))

img = grain(img, 4)
img.save(os.path.join(OUT, "movie_moments_logo.png"))
print("logo:", os.path.join(OUT, "movie_moments_logo.png"))

# ---------------- BANNER (2560x1440) ----------------
W, H = 2560, 1440
img = gradient(W, H, TEAL, NAVY, c_glow=ORANGE, glow_xy=(0.5, 0.4), glow_r=0.7, glow_amt=0.35)
dr = ImageDraw.Draw(img)

# center everything inside safe area (~1546x423 centered)
scx = W / 2
safe_top, safe_bot = H / 2 - 211, H / 2 + 211

# film-strip ticks along bottom of safe area
tick_y = safe_bot - 30
for i in range(-8, 9):
    x = scx + i * 95
    dr.rectangle([x, tick_y, x + 45, tick_y + 12], fill=tuple(WHITE) + (110,))

# title — two lines to fit "Movie Moments Edits"
f_title = font(F_BOLD, 120)
line1, line2 = "MOVIE MOMENTS", "EDITS"
bb1 = dr.textbbox((0, 0), line1, font=f_title)
bb2 = dr.textbbox((0, 0), line2, font=f_title)
for i, (ln, bb) in enumerate([(line1, bb1), (line2, bb2)]):
    lw = bb[2] - bb[0]
    dr.text((scx - lw / 2 - bb[0], H / 2 - 190 + i * 135 - bb[1]),
            ln, font=f_title, fill=tuple(WHITE))

# subtitle
sub = "C I N E M A T I C   S C E N E S   &   S E A S O N A L   E D I T S"
f_sub = font(F_REG, 52)
sbb = dr.textbbox((0, 0), sub, font=f_sub)
dr.text((scx - (sbb[2] - sbb[0]) / 2 - sbb[0], H / 2 + 120 - sbb[1]),
        sub, font=f_sub, fill=tuple(GOLD))

# gold underline
ul_w = 700
dr.rounded_rectangle([scx - ul_w / 2, H / 2 + 215, scx + ul_w / 2, H / 2 + 225],
                     radius=5, fill=tuple(GOLD))

# side play buttons (outside safe area is ok, keep subtle)
for px in [W * 0.12, W * 0.88]:
    pr2 = 90
    py = H / 2
    dr.ellipse([px - pr2, py - pr2, px + pr2, py + pr2],
               outline=tuple(WHITE) + (60,), width=5)
    dr.polygon([(px - 25, py - 42), (px - 25, py + 42), (px + 50, py)],
               fill=tuple(WHITE) + (110,))

img = img.filter(ImageFilter.GaussianBlur(0.3))
img = grain(img, 4)
img.save(os.path.join(OUT, "movie_moments_banner.png"))
print("banner:", os.path.join(OUT, "movie_moments_banner.png"))
