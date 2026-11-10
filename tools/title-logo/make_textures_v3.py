"""Extra iron finishes for the 5-3 seasonal motifs: rose/gold heat tint, blued steel, polished steel, dark rust."""
import numpy as np, subprocess, pathlib

try:
    import imageio_ffmpeg
    FF = imageio_ffmpeg.get_ffmpeg_exe()
except ImportError:
    FF = "ffmpeg"
OUT = pathlib.Path(__file__).parent / "textures"
W, H = 700, 280
rng = np.random.default_rng(11)

def upsample(a, h, w):
    ys = np.linspace(0, a.shape[0] - 1, h); xs = np.linspace(0, a.shape[1] - 1, w)
    y0 = np.floor(ys).astype(int); x0 = np.floor(xs).astype(int)
    y1 = np.minimum(y0 + 1, a.shape[0] - 1); x1 = np.minimum(x0 + 1, a.shape[1] - 1)
    wy = (ys - y0)[:, None]; wx = (xs - x0)[None, :]
    a00 = a[y0][:, x0]; a01 = a[y0][:, x1]; a10 = a[y1][:, x0]; a11 = a[y1][:, x1]
    return (a00 * (1 - wx) + a01 * wx) * (1 - wy) + (a10 * (1 - wx) + a11 * wx) * wy

def fbm(octaves=6, base=4, persistence=.55):
    total = np.zeros((H, W)); amp = 1.0; norm = 0
    for o in range(octaves):
        fq = base * 2 ** o
        total += upsample(rng.random((int(fq) + 2, int(fq * 2.5) + 2)), H, W) * amp; norm += amp; amp *= persistence
    t = total / norm
    return (t - t.min()) / (t.max() - t.min())

def palette(t, stops):
    pos = np.array([s[0] for s in stops]); cols = np.array([s[1] for s in stops], float)
    return np.stack([np.interp(t, pos, cols[:, c]) for c in range(3)], -1)

def shade(img, height, strength=.9):
    gy, gx = np.gradient(height)
    return img * (1 + (-(gx + gy) * strength * 40)[..., None])

def hammer(img, n=260, r=(6, 14), k=.25):
    """shallow hammer dents: each dent darkens its rim and brightens its centre"""
    yy, xx = np.mgrid[0:H, 0:W]
    h = np.zeros((H, W))
    for _ in range(n):
        cx, cy, rr = rng.uniform(0, W), rng.uniform(0, H), rng.uniform(*r)
        d = np.hypot(xx - cx, yy - cy) / rr
        h -= np.clip(1 - d ** 2, 0, 1) * .5
    return shade(img, h, k)

def save(img, name):
    img = np.clip(img, 0, 255).astype(np.uint8)
    subprocess.run([FF, "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-i", "-",
                    "-q:v", "3", str(OUT / name)], input=img.tobytes(), check=True)
    print("saved", name)

grain = lambda: (.93 + .14 * rng.random((H, W)))[..., None]

# 桜: steel heat-tinted to bronze / rose-violet (焼き色)
n = fbm(5, 2)
rose = palette(n, [(0, (118, 96, 104)), (.35, (160, 126, 130)), (.6, (196, 158, 156)), (.8, (216, 188, 182)), (1, (172, 162, 178))])
save(hammer(rose * grain(), 120, k=.1), "tex3-rose.jpg")

# 向日葵: straw / gold temper colour
n = fbm(5, 2)
gold = palette(n, [(0, (150, 104, 40)), (.35, (196, 146, 62)), (.6, (222, 184, 96)), (.85, (236, 208, 136)), (1, (210, 196, 160))])
save(hammer(gold * grain(), 160, k=.14), "tex3-gold.jpg")

# 夏の葉: blued steel (青焼き)
n = fbm(5, 3)
blue = palette(n, [(0, (30, 44, 80)), (.4, (52, 74, 120)), (.7, (78, 104, 150)), (1, (120, 110, 150))])
save(hammer(blue * grain(), 100, k=.1), "tex3-blued.jpg")

# 冬: polished steel, bright brushed streaks
streak = np.repeat(rng.random((H, 1)), W, 1); fine = upsample(rng.random((H, 30)), H, W)
pol = palette(np.clip(.6 + .3 * (streak - .5) + .2 * (fine - .5), 0, 1), [(0, (130, 138, 148)), (.5, (196, 202, 210)), (1, (246, 248, 250))])
save(pol, "tex3-polished.jpg")

# 紅葉: rust with red-orange oxide (weathering steel at its reddest)
n1 = fbm(6, 3); n2 = fbm(5, 12)
t = .6 * n1 + .4 * n2
red = palette(t, [(0, (70, 24, 12)), (.3, (128, 40, 18)), (.55, (170, 62, 24)), (.75, (200, 92, 36)), (1, (226, 140, 72))])
red *= (1 - (fbm(4, 16) > .74)[..., None] * .4)
save(shade(red, t, .9) * grain(), "tex3-redrust.jpg")
