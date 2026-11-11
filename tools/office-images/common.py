"""オフィスのイメージ画像づくりの共通部品（読み書き・縮小・ぼかし・切り抜き・合成）。

1_cutout.py と 2_place_in_rooms.py から読み込んで使います。単体では実行しません。
"""
import subprocess, pathlib, re
import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]                                   # Ikeuchi フォルダ
MODEL = HERE / "models" / "u2net.onnx"                   # 背景除去AI（GitHubには入れない。README参照）
CUTOUTS = HERE / "cutouts"                               # 切り抜いた作品（透過PNG）
OUT = ROOT / "rental_office-aile" / "assets" / "office"  # サイトに載せる完成画像
W, H = 1600, 1000
rng = np.random.default_rng(3)

def _ffmpeg():
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        return "ffmpeg"
FF = _ffmpeg()

# ---------------------------------------------------------------- io
def probe(path):
    r = subprocess.run([FF, "-i", str(path)], capture_output=True, text=True).stderr
    m = re.search(r"Video:.*?(\d{2,5})x(\d{2,5})", r)
    return int(m.group(1)), int(m.group(2))

def load(path, max_side=1100):
    w, h = probe(path)
    s = min(1, max_side / max(w, h))
    w2, h2 = int(w * s) // 2 * 2, int(h * s) // 2 * 2
    raw = subprocess.run([FF, "-v", "error", "-i", str(path), "-vf", f"scale={w2}:{h2}", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(h2, w2, 3).astype(np.float32)

def save(img, path, fmt="rgb24", q=3):
    img = np.clip(img, 0, 255).astype(np.uint8)
    h, w = img.shape[:2]
    args = ["-q:v", str(q)] if str(path).endswith(".jpg") else []
    subprocess.run([FF, "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", fmt, "-s", f"{w}x{h}", "-i", "-"] + args + [str(path)],
                   input=img.tobytes(), check=True)

def resize(a, h, w):
    """bilinear resize for HxW or HxWxC float arrays"""
    ys = np.linspace(0, a.shape[0] - 1, h); xs = np.linspace(0, a.shape[1] - 1, w)
    y0 = np.floor(ys).astype(int); x0 = np.floor(xs).astype(int)
    y1 = np.minimum(y0 + 1, a.shape[0] - 1); x1 = np.minimum(x0 + 1, a.shape[1] - 1)
    wy = (ys - y0)[:, None]; wx = (xs - x0)[None, :]
    if a.ndim == 3: wy, wx = wy[..., None], wx[..., None]
    return (a[y0][:, x0] * (1 - wx) + a[y0][:, x1] * wx) * (1 - wy) + (a[y1][:, x0] * (1 - wx) + a[y1][:, x1] * wx) * wy

def blur(a, r):
    """separable box blur (3 passes ≈ gaussian)"""
    r = max(1, int(r))
    for _ in range(3):
        for ax in (0, 1):
            c = np.cumsum(np.pad(a, [(r + 1, r) if i == ax else (0, 0) for i in range(a.ndim)], mode="edge"), axis=ax)
            hi = np.take(c, np.arange(2 * r + 1, c.shape[ax]), axis=ax); lo = np.take(c, np.arange(0, c.shape[ax] - 2 * r - 1), axis=ax)
            a = (hi - lo) / (2 * r + 1)
    return a

# ---------------------------------------------------------------- cut-out (u2net, runs locally)
_sess = None
def cutout(img, thr=.25, gapfix=False):
    x = resize(img, 320, 320) / 255.0
    x = (x - [0.485, 0.456, 0.406]) / [0.229, 0.224, 0.225]
    x = x.transpose(2, 0, 1)[None].astype(np.float32)
    global _sess
    if _sess is None:
        import onnxruntime as ort
        _sess = ort.InferenceSession(str(MODEL), providers=["CPUExecutionProvider"])
    m = _sess.run(None, {_sess.get_inputs()[0].name: x})[0][0, 0]
    m = (m - m.min()) / (m.max() - m.min() + 1e-6)
    m = resize(m, img.shape[0], img.shape[1])
    a = np.clip((m - thr) / .5, 0, 1)
    # u2net fills the gaps between thin wires with background: drop pixels whose colour matches
    # the surrounding background closely (sampled from where the mask is clearly empty)
    bgpix = img[a < .05] if gapfix else []
    if len(bgpix) > 200:
        samples = bgpix[rng.choice(len(bgpix), 96, replace=False)]
        flat = img.reshape(-1, 3)
        d = np.full(len(flat), 1e9, np.float32)
        for s in samples:
            d = np.minimum(d, ((flat - s) ** 2).sum(1))
        d = np.sqrt(d).reshape(a.shape)
        keep = np.clip((d - 10) / 22, 0, 1)
        a = a * keep
        core = blur((m > .9).astype(np.float32), 6) > .97          # deep inside large solid areas: never remove
        a = np.where(core, np.clip((m - thr) / .5, 0, 1), a)
    return a

# ---------------------------------------------------------------- camera (2_place_in_rooms.py sets these per room)
HOR, F, CAM = 430, 1000.0, 1.5          # horizon y, focal length (px), camera height (m)
WALL_Y = 640                             # where floor meets back wall

# ---------------------------------------------------------------- composite
def place(bg, obj, alpha, height_m, zpos, xpos, reflect=True):
    out = bg.copy()
    ys, xs = np.where(alpha > .5)
    y0, y1, x0, x1 = ys.min(), ys.max(), xs.min(), xs.max()
    obj, alpha = obj[y0:y1 + 1, x0:x1 + 1], alpha[y0:y1 + 1, x0:x1 + 1]
    hpx = int(height_m * F / zpos)
    wpx = max(2, int(obj.shape[1] * hpx / obj.shape[0]))
    if wpx > W * .62:                                   # very wide pieces: limit width
        wpx = int(W * .62); hpx = int(obj.shape[0] * wpx / obj.shape[1])
    obj, alpha = resize(obj, hpx, wpx), resize(alpha, hpx, wpx)
    base_y = int(HOR + CAM * F / zpos)
    left = int(xpos - wpx / 2); top = base_y - hpx
    # soft contact shadow + wider ambient shadow
    yy, xx = np.mgrid[0:H, 0:W]
    sh = np.exp(-(((xx - xpos) / (wpx * .48)) ** 2 + ((yy - base_y) / (wpx * .06 + 6)) ** 2) * 1.6)
    sh2 = np.exp(-(((xx - xpos - wpx * .15) / (wpx * .75)) ** 2 + ((yy - base_y - 4) / (wpx * .12 + 10)) ** 2))
    out *= (1 - .5 * sh - .2 * sh2)[..., None]
    # reflection on the polished floor
    ref_a = alpha[::-1] * np.linspace(.3, 0, hpx)[:, None] ** 1.2
    ref = blur(obj[::-1], 2)
    def paste(layer, a, t):
        ty0, ty1 = max(t, 0), min(t + layer.shape[0], H)
        tx0, tx1 = max(left, 0), min(left + layer.shape[1], W)
        if ty1 <= ty0 or tx1 <= tx0: return
        L = layer[ty0 - t:ty1 - t, tx0 - left:tx1 - left]; A = a[ty0 - t:ty1 - t, tx0 - left:tx1 - left][..., None]
        out[ty0:ty1, tx0:tx1] = out[ty0:ty1, tx0:tx1] * (1 - A) + L * A
    if reflect: paste(ref * .85, ref_a, base_y)
    # light the piece like the room (slightly warm, matched brightness)
    lum = (obj * alpha[..., None]).sum((0, 1)) / max(alpha.sum(), 1)
    obj = obj * (150 / max(lum.mean(), 1)) ** .35 * np.array([1.02, 1.0, .96])
    paste(obj, np.clip(alpha * 1.1, 0, 1), top)
    return out

