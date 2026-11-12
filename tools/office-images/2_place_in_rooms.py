"""手順2：作品ごとに違うオフィスのエントランスを描き、切り抜いた作品を置いて保存します。

  入力: cutouts/<slug>.png（手順1）、data/office-images.csv の height_m
  出力: rental_office-aile/assets/office/<slug>.jpg（作品ページ・作品リストに表示）

部屋は写真を使わず、ここで一から描いています（左右の壁・奥の壁・床・天井の箱を光線で描く方式）。
部屋の設定は下の SPECS にあり、作品ごとに1行です。主な項目:
  room=(左の壁までの距離, 右の壁までの距離, 奥行き, 天井高)  … 単位はm
  back / left / right / ceiling / floor … 壁・天井・床の素材（plaster, concrete, brick, marble, window など）
  boxes … カウンターやベンチ、pendants … 吊り照明、plants … 観葉植物、x … 作品を置く横位置(px)

    python tools/office-images/2_place_in_rooms.py            # 全作品
    python tools/office-images/2_place_in_rooms.py mudai4     # 一部だけ
"""

import csv, sys, subprocess
import numpy as np
import common as om

W, H, F = om.W, om.H, om.F
rng = np.random.default_rng(11)
_N = om.resize(rng.random((40, 40)), 512, 512) * .5 + om.resize(rng.random((160, 160)), 512, 512) * .3 + om.resize(rng.random((512, 512)), 512, 512) * .2
_N = (_N - _N.min()) / (_N.max() - _N.min())

def n(u, v, s):
    """tileable value noise sampled at world coords (metres), feature size s"""
    i = (v / s * 64) % 512; j = (u / s * 64) % 512
    i0 = i.astype(int); j0 = j.astype(int); fi = i - i0; fj = j - j0
    i1 = (i0 + 1) % 512; j1 = (j0 + 1) % 512
    return (_N[i0, j0] * (1 - fj) + _N[i0, j1] * fj) * (1 - fi) + (_N[i1, j0] * (1 - fj) + _N[i1, j1] * fj) * fi

def C(col, k=None):
    c = np.array(col, float)
    return c if k is None else c[None] * k[:, None]

def hsh(a):
    return (np.sin(a * 12.9898 + 4.1) * 43758.5453) % 1

# ---------------------------------------------------------------- materials: f(u, v) -> (N,3); u, v in metres
def plaster(col):            return lambda u, v: C(col, .95 + .07 * n(u, v, 3))
def concrete(col=(206, 202, 194)):
    def f(u, v):
        c = C(col, .88 + .16 * n(u, v, 1.5))
        seam = ((u % 1.8) < .012) | ((v % .9) < .012)
        hole = (np.hypot((u % .6) - .3, (v % .45) - .225) < .018)
        return c * np.where(seam | hole, .8, 1)[:, None]
    return f
def slats(col, pitch=.06, gap=.018, dark=(55, 42, 32)):
    def f(u, v):
        m = (u % pitch) < (pitch - gap)
        return np.where(m[:, None], C(col, .86 + .2 * n(u * .2, v, .4)), C(dark)[None])
    return f
def hslats(col, pitch=.08, gap=.02, dark=(55, 42, 32)):
    return lambda u, v: slats(col, pitch, gap, dark)(v, u)
def woodpanel(col, w=1.2):
    def f(u, v):
        grain = .85 + .2 * n(u * 6, v * .3, .5) + .06 * np.sin(u * 40 + n(u, v, .8) * 6)
        c = C(col, grain); c[(u % w) < .01] *= .6
        return c
    return f
def brick(col=(150, 82, 60), mortar=(196, 188, 176)):
    def f(u, v):
        row = np.floor(v / .075); off = (row % 2) * .11
        m = ((v % .075) < .011) | (((u + off) % .22) < .011)
        b = C(col, .78 + .3 * hsh(np.floor((u + off) / .22) * 7 + row) ** 1.5)
        return np.where(m[:, None], C(mortar)[None], b)
    return f
def marble(col=(234, 232, 228), vein=60):
    def f(u, v):
        t = n(u, v, 2.5); s = np.abs(np.sin(u * 1.3 + v * .7 + t * 7))
        return C(col, .97 + .03 * n(u, v, .5)) - (np.clip(1 - s * 10, 0, 1) * vein)[:, None]
    return f
def moss():
    def f(u, v):
        k = n(u * 4, v * 4, .5)
        return np.stack([56 + 48 * k, 98 + 70 * k, 48 + 36 * k], -1) * (.8 + .3 * n(u, v, 1))[:, None]
    return f
def tiles(col, s=.1, grout=(220, 218, 214)):
    def f(u, v):
        g = ((u % s) < .006) | ((v % s) < .006)
        return np.where(g[:, None], C(grout)[None], C(col, .9 + .15 * hsh(np.floor(u / s) * 3 + np.floor(v / s) * 17)))
    return f
def panel(col, w=1.0, h=None, seam=(28, 28, 30)):
    def f(u, v):
        m = (u % w) < .01
        if h: m |= (v % h) < .01
        return np.where(m[:, None], C(seam)[None], C(col, .9 + .12 * n(u, v, 2)))
    return f
def window(sky=(196, 214, 228), ground=(120, 140, 120), mull=1.5, frame=(50, 52, 56), city=True):
    def f(u, v):
        t = np.clip(v / 3.5, 0, 1)
        c = C(sky)[None] * (1 - .25 * t[:, None]) + 18
        if city:
            bh = 1.0 + 2.2 * hsh(np.floor(u / .9))
            b = v < bh
            c[b] = C((170, 178, 186), .85 + .2 * hsh(np.floor(u / .9) * 5))[b]
            c[v < .6] = C(ground, .8 + .3 * n(u[v < .6], v[v < .6], .4))
        m = ((u % mull) < .05) | (np.abs(v - 2.4) < .03)
        c[m] = frame
        return c * 1.05
    return f
def stripe_wall(c1, c2, w=.6):
    return lambda u, v: np.where(((u % (2 * w)) < w)[:, None], C(c1, .97 + .05 * n(u, v, 2)), C(c2, .97 + .05 * n(u, v, 2)))
def wainscot(top, low, rail=1.0):
    def f(u, v):
        c = np.where((v < rail)[:, None], C(low), C(top))
        c = c * (.96 + .05 * n(u, v, 3))[:, None]
        fr = (v < rail - .1) & (v > .12) & (((u % 1.1) < .03) | ((u % 1.1) > 1.07) | (np.abs(v - (rail - .1)) < .015) | (np.abs(v - .12) < .015))
        c[fr] *= .8; c[np.abs(v - rail) < .025] *= .75
        return c
    return f

# floors (u = x, v = z)
def f_stone(col, s=.9, refl=.24):  return (lambda u, v: np.where((((u % s) < .008) | ((v % s) < .008))[:, None], C(col) * .82, C(col, .94 + .1 * n(u, v, 2)))), refl
def f_big(col, sx=1.2, sz=2.4, refl=.32): return (lambda u, v: np.where((((u % sx) < .006) | ((v % sz) < .006))[:, None], C(col) * .85, C(col, .92 + .14 * n(u, v, 3)))), refl
def f_wood(col, w=.19, refl=.08):
    def f(u, v):
        p = np.floor(u / w); j = ((v + hsh(p) * 2.1) % 2.1) < .008
        c = C(col, (.84 + .22 * hsh(p * 3)) * (.94 + .1 * n(u * 4, v * .3, .5)))
        c[((u % w) < .006) | j] *= .75
        return c
    return f, refl
def f_herring(col, w=.09, L=.45, refl=.07):
    def f(u, v):
        a = (u + v) / np.sqrt(2); b = (v - u) / np.sqrt(2)
        cell = np.floor(a / L); off = (cell % 2) * L / 2
        k = np.floor((b + off) / w)
        c = C(col, (.82 + .24 * hsh(cell * 7 + k)) * (.95 + .08 * n(u * 5, v * 5, .5)))
        c[((a % L) < .008) | (((b + off) % w) < .006)] *= .7
        return c
    return f, refl
def f_check(c1, c2, s=.6, refl=.3):
    return (lambda u, v: np.where(((np.floor(u / s) + np.floor(v / s)) % 2 == 0)[:, None], C(c1, .97 + .05 * n(u, v, 1)), C(c2, .97 + .05 * n(u, v, 1)))), refl
def f_terrazzo(col, refl=.16):
    def f(u, v):
        c = C(col, .96 + .05 * n(u, v, 2))
        s = hsh(np.floor(u / .02) * 13 + np.floor(v / .02) * 71)
        c[s > .93] *= .55; c[(s > .89) & (s <= .93)] = (236, 230, 220)
        return c
    return f, refl
def f_carpet(col, refl=0):
    return (lambda u, v: C(col, (.92 + .1 * hsh(np.floor(u / .01) * 3 + np.floor(v / .01) * 7)) * np.where(((u % .5) < .01) | ((v % .5) < .01), .93, 1))), refl
def f_concrete(col=(150, 148, 144), refl=.2): return (lambda u, v: C(col, .86 + .2 * n(u, v, 2))), refl

# ceilings (u = x, v = z)
def c_plaster(col=(238, 236, 232)):
    def f(u, v):
        c = C(col, .97 + .03 * n(u, v, 3))
        dl = np.hypot((u % 1.8) - .9, (v % 1.8) - .9) < .07
        c[dl] = (255, 252, 240)
        return c
    return f
def c_wood(col=(176, 132, 90)):        return lambda u, v: slats(col, .1, .03, (40, 34, 30))(u, v)
def c_dark():
    def f(u, v):
        c = C((38, 38, 40), .9 + .2 * n(u, v, 2))
        duct = (np.abs((u % 3.0) - 1.5) < .18)
        c[duct] = C((92, 94, 98), .9 + .2 * n(u[duct], v[duct], .4))
        c[(u % 1.5) < .02] = (250, 248, 236)
        return c
    return f
def c_lines(col=(240, 240, 238)):
    def f(u, v):
        c = C(col, .97 + .03 * n(u, v, 3))
        c[(np.abs((v % 1.6) - .8) < .03)] = (255, 255, 250)
        return c
    return f

# ---------------------------------------------------------------- ray casting
def render(sp):
    om.HOR, om.CAM = sp.get("hor", 430), sp.get("cam", 1.5)
    L, R, D, Hc = sp["room"]                       # left wall x=-L, right wall x=R, back wall z=D, ceiling height
    cx = 800
    u = (om_x - cx) / F; v = -(om_y - om.HOR) / F
    INF = 1e9
    t_floor = np.where(v < 0, om.CAM / np.maximum(-v, 1e-9), INF)
    t_ceil = np.where(v > 0, (Hc - om.CAM) / np.maximum(v, 1e-9), INF)
    t_left = np.where(u < 0, L / np.maximum(-u, 1e-9), INF)
    t_right = np.where(u > 0, R / np.maximum(u, 1e-9), INF)
    t_back = np.full_like(u, D)
    T = np.stack([t_floor, t_ceil, t_left, t_right, t_back]); idx = T.argmin(0); t = T.min(0)
    X, Y, Z = u * t, om.CAM + v * t, t
    img = np.zeros((H, W, 3))
    shade = sp.get("shade", (.95, .9, .86, .86, 1.0))
    surf = [("floor", X, Z), ("ceiling", X, Z), ("left", Z, Y), ("right", Z, Y), ("back", X + L, Y)]
    for k, (name, a, b) in enumerate(surf):
        m = idx == k
        if not m.any(): continue
        if name == "floor": col = sp["floor"][0](a[m], b[m])
        elif name == "ceiling": col = sp["ceiling"](a[m], b[m])
        else:
            col = None
            for (z0, z1, y0, y1, fn) in sp.get(name + "_parts", []):     # windows / doors / signs on a wall
                pm = (a[m] >= z0) & (a[m] < z1) & (b[m] >= y0) & (b[m] < y1)
                if pm.any():
                    if col is None: col = sp[name](a[m], b[m])
                    col[pm] = fn(a[m][pm] - z0, b[m][pm] - y0)
            if col is None: col = sp[name](a[m], b[m])
        img[m] = col * shade[k]
    # wall wash under downlights (back + side walls), and light falling off toward the far end
    wall = idx >= 2
    pos = np.where(idx == 4, X + L, Z)
    wash = np.exp(-(((pos % sp.get("wash_pitch", 1.8)) - sp.get("wash_pitch", 1.8) / 2) / .45) ** 2) * np.exp(-(Hc - Y) / 1.1)
    img += (wash * wall)[..., None] * sp.get("wash", 26) * np.array(sp.get("light", (1, .97, .9)))
    img *= (1 - .025 * np.clip(t - 3, 0, 20))[..., None]
    # boxes (counters, benches, sofas, plinths): axis-aligned, nearest hit wins over the room
    for bx in sp.get("boxes", []):
        x0, x1, y0, y1, z0, z1, top, front, side = bx
        with np.errstate(divide="ignore", invalid="ignore"):
            tx0, tx1 = np.sort(np.stack([x0 / u, x1 / u]), 0)
            ty0, ty1 = np.sort(np.stack([(y0 - om.CAM) / v, (y1 - om.CAM) / v]), 0)
            tz0, tz1 = z0, z1
            tn = np.maximum(np.maximum(tx0, ty0), tz0); tf = np.minimum(np.minimum(tx1, ty1), tz1)
        hit = (tn <= tf) & (tn > 0) & (tn < t)
        if not hit.any(): continue
        hx, hy = u * tn, om.CAM + v * tn
        face = np.where(np.isclose(tn, tz0), 0, np.where(np.isclose(tn, ty0) | np.isclose(tn, ty1), 1, 2))
        for fi, colr, sh in ((0, front, 1.0), (1, top, 1.08), (2, side, .78)):
            mm = hit & (face == fi)
            if mm.any():
                c = colr(hx[mm], hy[mm]) if callable(colr) else C(colr)[None].repeat(mm.sum(), 0)
                img[mm] = c * sh
        t = np.where(hit, tn, t)
        # contact shadow on the floor around the box
        bxp = (cx + F * ((x0 + x1) / 2) / z0); byp = om.HOR + F * om.CAM / z0
        img *= (1 - .35 * np.exp(-(((om_x - bxp) / (F * (x1 - x0) / z0 * .6)) ** 2 + ((om_y - byp) / 10) ** 2)))[..., None]
    # floor reflection: mirror the walls into polished floors
    refl = sp["floor"][1]
    if refl > 0:
        fl = idx == 0
        ym = (2 * horizon_line(sp) - om_y).astype(int).clip(0, H - 1)
        mir = om.blur(img, 5)[ym, om_x.astype(int)]
        k = refl * np.clip(1 - (om_y - horizon_line(sp)) / 520, 0, 1)
        img[fl] = img[fl] * (1 - k[fl, None]) + mir[fl] * k[fl, None]
    # the floor/back-wall junction is where the piece's base sits; remember it for place()
    om.WALL_Y = int(horizon_line(sp))
    return img * np.array(sp.get("tint", (1, 1, 1)))

def horizon_line(sp):
    return om.HOR + F * om.CAM / sp["room"][2]

def proj(x, y, z):
    return 800 + F * x / z, om.HOR - F * (y - om.CAM) / z

om_y, om_x = np.mgrid[0:H, 0:W].astype(np.float64)

def load_rgba(path):
    w, h = om.probe(path)
    raw = subprocess.run([om.FF, "-v", "error", "-i", str(path), "-f", "rawvideo", "-pix_fmt", "rgba", "-"], capture_output=True, check=True).stdout
    a = np.frombuffer(raw, np.uint8).reshape(h, w, 4).astype(np.float32)
    return a[..., :3], a[..., 3] / 255

def plant(img, x, base, s=1.0, pot=(60, 60, 62)):
    pw, ph = 60 * s, 90 * s
    m = (np.abs(om_x - x) < pw / 2 - (om_y - (base - ph)) * .08) & (om_y > base - ph) & (om_y < base)
    img[m] = np.array(pot, float) * (1 - .25 * ((om_x[m] - x) / pw + .5))[:, None]
    for _ in range(int(26 * s)):
        a = om.rng.uniform(-2.5, -.6); L = om.rng.uniform(60, 150) * s
        cx, cy = x + np.cos(a) * L * .55, base - ph - 10 + np.sin(a) * L * .55
        d = (((om_x - cx) * np.cos(a) + (om_y - cy) * np.sin(a)) / (L * .5)) ** 2 + (((om_x - cx) * -np.sin(a) + (om_y - cy) * np.cos(a)) / (L * .12)) ** 2
        img[d < 1] = np.array([50, 96, 52]) * om.rng.uniform(.7, 1.3)
    img *= (1 - .3 * np.exp(-(((om_x - x) / pw) ** 2 + ((om_y - base) / 8) ** 2)))[..., None]


def pendants(img, pts, shade_col=(30, 30, 32), Hc=3.0):
    for (x, z) in pts:
        px, py = proj(x, 2.1, z); top = proj(x, Hc, z)[1]
        img[(np.abs(om_x - px) < 1.2) & (om_y > top) & (om_y < py)] = (60, 60, 60)
        r = 0.22 * F / z
        d = ((om_x - px) / r) ** 2 + ((om_y - py) / (r * .6)) ** 2
        img[(d < 1) & (om_y < py)] = shade_col
        img += np.exp(-(((om_x - px) / (r * 4)) ** 2 + ((om_y - py - r) / (r * 2.5)) ** 2))[..., None] * np.array([46, 38, 22])

def plants(img, pts):
    for (x, z, s) in pts:
        px, py = proj(x, 0, z)
        plant(img, px, py, s * 4.2 / z)

def wood(col): return woodpanel(col)

# ---------------------------------------------------------------- 18 rooms
GREY = (120, 120, 124)
SPECS = {
  "souga":     dict(room=(4.5, 4.0, 9, 3.0), hor=420, back=concrete(), left=concrete(), right=concrete(), ceiling=c_plaster(),
                    floor=f_big((196, 192, 186)), x=820, plants=[(-3.6, 6.5, 1.2), (3.2, 6.0, 1.0)]),
  "utage":     dict(room=(3.2, 6.5, 11, 3.2), hor=440, back=plaster((246, 244, 240)), left=plaster((240, 238, 234)), right=window(), ceiling=c_lines(),
                    floor=f_terrazzo((214, 210, 202)), x=640, boxes=[(-3.0, -0.9, 0, 1.05, 8.6, 9.4, (250, 250, 250), (236, 236, 234), (220, 220, 218))]),
  "mudai5":    dict(room=(5, 5, 8, 3.4), hor=430, back=wainscot((236, 228, 214), (120, 86, 60)), left=wainscot((236, 228, 214), (120, 86, 60)),
                    right=wainscot((236, 228, 214), (120, 86, 60)), ceiling=c_plaster((240, 234, 222)), floor=f_herring((150, 106, 70)), x=800, tint=(1.03, 1, .93),
                    pendants=[(-1.8, 5.2), (1.8, 5.2)]),
  "mamoru":    dict(room=(2.6, 2.6, 12, 2.9), hor=450, back=plaster((232, 228, 220)), left=slats((176, 136, 94)), right=slats((176, 136, 94)), ceiling=c_wood(),
                    floor=f_stone((190, 186, 180)), x=800),
  "shishu":    dict(room=(4, 4, 8, 3.0), hor=430, back=panel((36, 36, 40), 1.2), left=panel((44, 44, 48), 1.2), right=panel((44, 44, 48), 1.2), ceiling=c_dark(),
                    floor=f_big((52, 52, 56), refl=.38), x=800, wash=38, back_parts=[(3.0, 5.0, 1.9, 2.2, plaster((200, 170, 110)))]),
  "mudai6":    dict(room=(5.5, 3.0, 9, 3.6), hor=420, back=brick(), left=brick(), right=plaster((236, 232, 224)), ceiling=c_dark(), floor=f_wood((120, 84, 56)), x=760,
                    pendants=[(-2.5, 5.5), (0, 6), (2.0, 5.5)], plants=[(2.2, 5.0, 1.1)]),
  "mudai3":    dict(room=(3.5, 5, 10, 3.0), hor=440, back=tiles((210, 226, 216), .2), left=plaster((230, 238, 232)), right=window((206, 222, 234), (150, 170, 140), 2.0),
                    ceiling=c_lines(), floor=f_terrazzo((232, 228, 220)), x=900, boxes=[(-3.4, -1.4, 0, 1.0, 7.0, 7.8, (250, 250, 250), (200, 220, 208), (180, 200, 188))]),
  "mudai4":    dict(room=(4.2, 4.2, 10, 3.5), hor=430, back=marble(), left=marble((226, 224, 220)), right=marble((226, 224, 220)), ceiling=c_plaster(),
                    floor=f_check((230, 228, 224), (60, 60, 64), .8), x=800, back_parts=[(3.0, 5.4, 2.3, 2.6, plaster((180, 150, 96)))]),
  "mudai2":    dict(room=(3.0, 5.5, 9, 3.0), hor=430, back=moss(), left=plaster((240, 238, 232)), right=woodpanel((186, 150, 108)), ceiling=c_wood((196, 160, 118)),
                    floor=f_wood((178, 140, 100)), x=760),
  "tsunagu":   dict(room=(6, 6, 13, 4.5), hor=410, back=slats((244, 244, 242), .1, .03, (200, 200, 198)), left=window((200, 214, 226)), right=window((200, 214, 226)),
                    ceiling=c_lines(), floor=f_stone((212, 210, 206), 1.2), x=800),
  "mudai1":    dict(room=(3.8, 4.6, 8, 2.8), hor=440, back=stripe_wall((196, 52, 46), (244, 242, 238), 1.5), left=plaster((244, 242, 238)), right=plaster((244, 242, 238)),
                    ceiling=c_plaster(), floor=f_carpet((90, 90, 96)), x=700, boxes=[(1.4, 3.8, 0, 1.0, 6.2, 7.0, (250, 250, 250), (250, 250, 250), (226, 226, 226))]),
  "tou":       dict(room=(4.5, 3.5, 9, 3.2), hor=430, back=panel((64, 74, 92), 1.5), left=panel((70, 80, 98), 1.5), right=window((180, 196, 214), (110, 120, 110), 1.2),
                    ceiling=c_plaster(), floor=f_big((150, 152, 156)), x=760, back_parts=[(5.0, 7.0, 1.8, 2.2, plaster((220, 222, 226)))]),
  "yusho":     dict(room=(7, 7, 14, 6.0), hor=470, cam=1.6, back=window((176, 204, 224), (110, 140, 110), 2.4), left=concrete(), right=concrete(), ceiling=c_lines((246, 246, 246)),
                    floor=f_big((204, 200, 194), 1.5, 3.0), x=820),
  "tamago":    dict(room=(4.0, 4.0, 9, 3.0), hor=430, back=woodpanel((120, 84, 58), .9), left=concrete(), right=concrete(), ceiling=c_dark(), floor=f_stone((96, 96, 100), .6, .3), x=820,
                    plants=[(-3.2, 6.0, 1.0)]),
  "irodori":   dict(room=(4.5, 4.5, 8.5, 3.0), hor=430, back=plaster((250, 246, 236)), left=hslats((230, 196, 140)), right=plaster((250, 246, 236)), ceiling=c_plaster((248, 244, 236)),
                    floor=f_wood((196, 160, 118)), x=800, plants=[(-3.6, 6, 1.2), (3.6, 6, 1.3)], back_parts=[(3.4, 5.6, 2.0, 2.4, plaster((242, 196, 70)))]),
  "fukko":     dict(room=(3.0, 6.0, 10, 3.6), hor=430, back=concrete(), left=brick((176, 170, 160)), right=window((190, 206, 220)), ceiling=c_dark(), floor=f_concrete(), x=700,
                    boxes=[(1.0, 4.4, 0, .45, 6.6, 7.2, (60, 60, 64), (52, 52, 56), (44, 44, 48))]),
  "wasuremono": dict(room=(4, 4, 7, 3.0), hor=440, back=wainscot((56, 70, 64), (40, 50, 46)), left=wainscot((56, 70, 64), (40, 50, 46)), right=wainscot((56, 70, 64), (40, 50, 46)),
                    ceiling=c_wood((90, 66, 46)), floor=f_herring((100, 70, 48)), x=800, wash=34, tint=(1.05, 1, .9), pendants=[(0, 4.6)]),
  "oka":       dict(room=(4.5, 4.5, 10, 3.2), hor=430, back=plaster((236, 234, 228)), left=moss(), right=moss(), ceiling=c_plaster(), floor=f_stone((210, 206, 198)), x=800),
}

if __name__ == "__main__":
    rows = {r["slug"]: r for r in csv.DictReader(open(om.ROOT / "data" / "office-images.csv", encoding="utf-8-sig"))}
    only = sys.argv[1].split(",") if len(sys.argv) > 1 else list(SPECS)
    om.OUT.mkdir(parents=True, exist_ok=True)
    for slug in only:
        sp = SPECS[slug]
        bg = render(sp)
        if "pendants" in sp: pendants(bg, sp["pendants"], Hc=sp["room"][3])
        if "plants" in sp: plants(bg, sp["plants"])
        rgb, a = load_rgba(om.CUTOUTS / f"{slug}.png")
        comp = om.place(bg, rgb, a, float(rows[slug]["height_m"]), 3.6, sp.get("x", 800))
        om.save(comp, om.OUT / f"{slug}.jpg")
        print("done", slug)
