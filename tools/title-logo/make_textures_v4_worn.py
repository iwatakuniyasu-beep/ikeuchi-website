"""Matte, worn finishes taken from Ikeuchi's real pieces: galvanised sheet, rust, and chipped paint over steel."""
import numpy as np, subprocess, pathlib

try:
    import imageio_ffmpeg
    FF = imageio_ffmpeg.get_ffmpeg_exe()
except ImportError:
    FF = "ffmpeg"
OUT = pathlib.Path(__file__).parent / "textures"
W, H = 700, 280
rng = np.random.default_rng(23)

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

def save(img, name):
    img = np.clip(img, 0, 255).astype(np.uint8)
    subprocess.run([FF, "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-i", "-",
                    "-q:v", "3", str(OUT / name)], input=img.tobytes(), check=True)
    print("saved", name)

def rust():
    t = .6 * fbm(6, 3) + .4 * fbm(5, 14)
    return palette(t, [(0, (62, 30, 18)), (.35, (110, 50, 24)), (.6, (150, 74, 34)), (.85, (182, 104, 52)), (1, (204, 134, 76))])

def galv():
    # galvanised zinc: flat crystal patches ("spangle") in greys, plus white-rust bloom
    n = fbm(5, 6)
    spangle = np.floor(n * 7) / 7 * .6 + fbm(4, 20) * .4
    img = palette(spangle, [(0, (118, 124, 128)), (.4, (150, 156, 160)), (.7, (176, 182, 186)), (1, (204, 208, 210))])
    bloom = np.clip((fbm(4, 5) - .7) * 3, 0, 1)
    return img * (1 - bloom[..., None] * .3) + bloom[..., None] * np.array([214, 214, 206]) * .3

def worn_paint(rgb, chip=.66):
    """matte paint brushed on by hand, chipped and streaked to show rust / bare steel underneath"""
    tone = fbm(5, 3)
    base = np.array(rgb, float) * (.88 + .2 * tone)[..., None]
    brush = upsample(rng.random((H, 12)), H, W)          # long brush streaks
    base *= (.95 + .1 * brush)[..., None]
    n = fbm(6, 4)
    chipped = n > chip
    edge = (n > chip - .04) & ~chipped
    under = rust() * .9
    out = np.where(chipped[..., None], under, base)
    out[edge] *= .8
    grime = fbm(4, 2)
    return out * (.9 + .12 * grime)[..., None] * (.95 + .08 * rng.random((H, W)))[..., None]

save(galv(), "tex4-galv.jpg")
save(rust() * (.92 + .16 * rng.random((H, W)))[..., None], "tex4-rust.jpg")
save(worn_paint((232, 168, 176)), "tex4-pink.jpg")
save(worn_paint((226, 182, 48)), "tex4-yellow.jpg")
save(worn_paint((182, 52, 36), .7), "tex4-red.jpg")
save(worn_paint((234, 230, 220), .8), "tex4-white.jpg")
save(worn_paint((96, 112, 70), .7), "tex4-green.jpg")
