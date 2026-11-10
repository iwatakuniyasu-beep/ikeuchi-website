"""Generate seamless-ish iron textures for the title drafts (rust, mill scale, brushed steel, heat-tinted steel)."""
import numpy as np, subprocess, pathlib

try:
    import imageio_ffmpeg
    FF = imageio_ffmpeg.get_ffmpeg_exe()
except ImportError:
    FF = "ffmpeg"
OUT = pathlib.Path(__file__).parent / "textures"
W, H = 1400, 560
rng = np.random.default_rng(7)

def upsample(a, h, w):
    """bilinear resize of a 2-D array"""
    ys = np.linspace(0, a.shape[0] - 1, h); xs = np.linspace(0, a.shape[1] - 1, w)
    y0 = np.floor(ys).astype(int); x0 = np.floor(xs).astype(int)
    y1 = np.minimum(y0 + 1, a.shape[0] - 1); x1 = np.minimum(x0 + 1, a.shape[1] - 1)
    wy = (ys - y0)[:, None]; wx = (xs - x0)[None, :]
    a00 = a[y0][:, x0]; a01 = a[y0][:, x1]; a10 = a[y1][:, x0]; a11 = a[y1][:, x1]
    return (a00 * (1 - wx) + a01 * wx) * (1 - wy) + (a10 * (1 - wx) + a11 * wx) * wy

def fbm(octaves=6, base=4, persistence=.55, sx=1.0, sy=1.0):
    total = np.zeros((H, W)); amp = 1.0; norm = 0
    for o in range(octaves):
        f = base * 2 ** o
        g = rng.random((max(2, int(f * sy)) + 1, max(2, int(f * 2.5 * sx)) + 1))
        total += upsample(g, H, W) * amp; norm += amp; amp *= persistence
    t = total / norm
    return (t - t.min()) / (t.max() - t.min())

def palette(t, stops):
    """map 0..1 to colours via stops [(pos, (r,g,b)), ...]"""
    pos = np.array([s[0] for s in stops]); cols = np.array([s[1] for s in stops], float)
    out = np.zeros(t.shape + (3,))
    for c in range(3):
        out[..., c] = np.interp(t, pos, cols[:, c])
    return out

def shade(img, height, strength=.9):
    """fake lighting from top-left using the gradient of a height map"""
    gy, gx = np.gradient(height)
    light = -(gx + gy) * strength * 40
    return img * (1 + light[..., None])

def save(img, name):
    img = np.clip(img, 0, 255).astype(np.uint8)
    subprocess.run([FF, "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-i", "-",
                    "-q:v", "3", str(OUT / name)], input=img.tobytes(), check=True)
    print("saved", name)

# 1) rust (corten): layered oxide, darker pits and flaking
n1 = fbm(7, 3); n2 = fbm(6, 10); n3 = fbm(4, 40)
t = .55 * n1 + .3 * n2 + .15 * n3
rust = palette(t, [(0, (48, 22, 12)), (.3, (102, 44, 18)), (.5, (150, 66, 24)), (.68, (190, 96, 40)), (.82, (214, 128, 62)), (1, (232, 168, 98))])
pits = (fbm(5, 18) > .72).astype(float) * .45
rust *= (1 - pits[..., None])
flake = (n2 > .7) & (n1 < .45)
rust[flake] = rust[flake] * .55 + np.array([60, 40, 34]) * .45
rust = shade(rust, t * .8 + n3 * .2, 1.1)
rust *= (.9 + .2 * rng.random((H, W)))[..., None]
save(rust, "tex2-rust.jpg")

# 2) mill scale (黒皮): blue-black scale with mottled patches and bluish sheen
m1 = fbm(6, 4); m2 = fbm(5, 16); grain = rng.random((H, W))
ms = palette(.65 * m1 + .35 * m2, [(0, (22, 22, 24)), (.45, (38, 39, 42)), (.62, (52, 54, 58)), (.8, (72, 74, 78)), (1, (98, 100, 104))])
sheen = np.clip((m1 - .62) * 3, 0, 1)
ms += sheen[..., None] * np.array([4, 8, 16])
ms = shade(ms, m2, .45)
ms *= (.92 + .16 * grain)[..., None]
save(ms, "tex2-millscale.jpg")

# 3) brushed steel: fine horizontal streaks
rows = rng.random((H, 1)); streak = np.repeat(rows, W, axis=1)
fine = upsample(rng.random((H, 40)), H, W)
b = .5 + .35 * (streak - .5) + .25 * (fine - .5) + .15 * (fbm(4, 2) - .5)
steel = palette(np.clip(b, 0, 1), [(0, (92, 98, 106)), (.5, (160, 166, 172)), (.8, (200, 205, 210)), (1, (232, 235, 238))])
save(steel, "tex2-brushed.jpg")

# 4) heat tint (焼け色): steel with temper colours flowing across, plus fine scale
# temper colours run in bands across the bar: left = hottest (blue), right = coolest (straw)
x = np.linspace(0, 1, W)[None, :].repeat(H, 0)
wob = fbm(3, 1, persistence=.5) * .35
h = np.clip(x * .85 + wob - .1, 0, 1)
temper = palette(h, [(0, (150, 175, 205)), (.18, (70, 96, 170)), (.36, (110, 62, 140)), (.52, (150, 80, 70)), (.7, (196, 140, 72)), (.86, (220, 196, 128)), (1, (205, 208, 210))])
temper *= (.94 + .12 * fbm(4, 30))[..., None]
streak = np.repeat(rng.random((H, 1)), W, axis=1)
temper *= (.95 + .1 * streak)[..., None]
save(temper, "tex2-heat.jpg")

# 5) forged dark iron (for wire / bar): dark with hammer marks
f1 = fbm(6, 6); f2 = fbm(4, 24)
forged = palette(.6 * f1 + .4 * f2, [(0, (30, 28, 27)), (.5, (60, 55, 52)), (.75, (96, 84, 74)), (1, (150, 120, 96))])
forged = shade(forged, f1, 1.0)
save(forged, "tex2-forged.jpg")
