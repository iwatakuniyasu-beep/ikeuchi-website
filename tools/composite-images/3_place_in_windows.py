"""手順3：作品ごとに違うショーウィンドウ（百貨店・ブランド店）を描き、切り抜いた作品を飾って保存します。

  入力: cutouts/<slug>.png（手順1）、data/cutouts.csv の height_m
  出力: rental_office-aile/assets/window/<slug>.jpg（作品ページ・作品リスト・ショーウィンドウのページに表示）

ウィンドウは写真を使わず、ここで一から描いています（通りから見た外観・ガラス・ウィンドウの中の箱を光線で描く方式）。
設定は下の SPECS にあり、作品ごとに1行です。主な項目:
  win=(左端, 右端, 奥行き, 高さ) … ウィンドウの中の寸法(m)。zg=ガラスまでの距離、sill=歩道からウィンドウの床までの高さ
  back / side / floor … 背景・側面・床の素材、facade … 建物の外観（limestone, blackmetal, whitetile, brick など）
  spots … スポットライトの横位置(m)、night … 夜の見え方、particles … 花びら・落ち葉・雪・紙吹雪など
  plinth … 作品をのせる台の高さ(m)、x … 作品の横位置(m)

    python tools/composite-images/3_place_in_windows.py            # 全作品
    python tools/composite-images/3_place_in_windows.py shishu     # 一部だけ
"""

import csv, sys, importlib
import numpy as np
import common as om

R2 = importlib.import_module("2_place_in_rooms")      # 素材（壁・床）の描き方を共用
n, C, hsh = R2.n, R2.C, R2.hsh
W, H, F = om.W, om.H, om.F
OUT = om.ROOT / "rental_office-aile" / "assets" / "window"
yy, xx = np.mgrid[0:H, 0:W].astype(np.float64)

# ---------------------------------------------------------------- backdrops (u, v in metres on the surface)
def drape(col, pitch=.32, depth=.38):
    """heavy curtain with vertical folds"""
    def f(u, v):
        ph = u / pitch * 2 * np.pi + 3 * n(u, v * .1, 1.2)
        k = 1 - depth + depth * (.5 + .5 * np.sin(ph)) ** .7
        return C(col, k * (.97 + .05 * n(u, v, .5)))
    return f

def gradient(top, bottom, h=3.0):
    def f(u, v):
        t = np.clip(v / h, 0, 1)[:, None]
        return (np.array(bottom, float) * (1 - t) + np.array(top, float) * t) * (.98 + .03 * n(u, v, 2))[:, None]
    return f

def disc(base, col, cx, cy, r, ring=None):
    """a large circle (sun, moon, ring) set into the backdrop"""
    def f(u, v):
        c = base(u, v)
        d = np.hypot(u - cx, v - cy)
        m = (d < r) & (d > r - ring) if ring else d < r
        c[m] = C(col, .96 + .06 * n(u[m], v[m], .6))
        return c
    return f

def dots(base, col, s=.3, r=.05):
    def f(u, v):
        c = base(u, v)
        row = np.floor(v / s); off = (row % 2) * s / 2
        m = np.hypot(((u + off) % s) - s / 2, (v % s) - s / 2) < r
        c[m] = col
        return c
    return f

def arch(base, col, cx, w, h):
    """a tall arch-shaped panel (doorway silhouette) on the backdrop"""
    def f(u, v):
        c = base(u, v)
        m = (np.abs(u - cx) < w / 2) & ((v < h - w / 2) | (np.hypot(u - cx, v - (h - w / 2)) < w / 2))
        c[m] = C(col, .96 + .05 * n(u[m], v[m], 1))
        return c
    return f

def f_lacquer(col, refl=.42): return (lambda u, v: C(col, .97 + .04 * n(u, v, 2))), refl
def f_sand(col=(222, 206, 176), refl=0):
    return (lambda u, v: C(col, .9 + .14 * n(u * 6, v * 6, .3))), refl

# ---------------------------------------------------------------- facades (u = x, v = height above the window floor)
def stone_facade(col=(214, 206, 190), course=.6, joint=1.2):
    def f(u, v):
        c = C(col, .92 + .1 * n(u, v, 1.5))
        m = ((v % course) < .01) | (((u + (np.floor(v / course) % 2) * joint / 2) % joint) < .01)
        c[m] *= .82
        return c
    return f

FACADES = {
    "limestone":  dict(face=stone_facade(), frame=(176, 146, 86), band=(30, 30, 32)),
    "blackmetal": dict(face=R2.panel((40, 40, 42), 1.0, None, (24, 24, 26)), frame=(186, 156, 96), band=(186, 156, 96)),
    "whitetile":  dict(face=R2.tiles((238, 238, 234), .3, (210, 210, 206)), frame=(150, 152, 156), band=(60, 62, 66)),
    "brick":      dict(face=R2.brick((136, 76, 56)), frame=(36, 58, 48), band=(36, 58, 48)),
    "greenmetal": dict(face=R2.panel((44, 70, 58), 1.2, None, (30, 48, 40)), frame=(186, 156, 96), band=(186, 156, 96)),
    "concrete":   dict(face=R2.concrete((196, 194, 188)), frame=(40, 40, 42), band=(40, 40, 42)),
    "navy":       dict(face=R2.panel((34, 42, 64), 1.0, None, (22, 28, 44)), frame=(196, 196, 200), band=(196, 196, 200)),
}
PAVE = lambda u, v: R2.tiles((150, 148, 144), .45, (118, 116, 112))(u, v)

# ---------------------------------------------------------------- render
def render(sp, rng):
    L, R, D, Hc = sp["win"]
    zg, cam, sill, hor = sp.get("zg", 4.5), sp.get("cam", 1.0), sp.get("sill", .55), sp.get("hor", 450)
    om.HOR, om.CAM = hor, cam
    night = sp.get("night", False)
    u = (xx - 800) / F; v = -(yy - hor) / F
    Xg, Yg = u * zg, cam + v * zg
    inside = (Xg > -L) & (Xg < R) & (Yg > 0) & (Yg < Hc)
    img = np.zeros((H, W, 3))
    INF = 1e9
    t_floor = np.where(v < 0, cam / np.maximum(-v, 1e-9), INF)
    t_ceil = np.where(v > 0, (Hc - cam) / np.maximum(v, 1e-9), INF)
    t_left = np.where(u < 0, L / np.maximum(-u, 1e-9), INF)
    t_right = np.where(u > 0, R / np.maximum(u, 1e-9), INF)
    t_back = np.full_like(u, zg + D)
    T = np.stack([t_floor, t_ceil, t_left, t_right, t_back]); idx = T.argmin(0); t = T.min(0)
    X, Y, Z = u * t, cam + v * t, t
    side = sp.get("side", sp["back"])
    mats = [sp["floor"][0], sp.get("ceiling", lambda a, b: C((26, 26, 28), .9 + .1 * n(a, b, 1))), side, side, sp["back"]]
    coords = [(X, Z - zg), (X, Z - zg), (Z - zg, Y), (Z - zg, Y), (X + L, Y)]
    for k in range(5):
        m = inside & (idx == k)
        if m.any():
            a, b = coords[k]
            img[m] = mats[k](a[m], b[m]) * (.95, .7, .78, .78, 1.0)[k]
    # lighting: dim ambient + spot pools on the backdrop and floor, darker under the valance
    amb = sp.get("amb", .62 if night else .82)
    lit = np.full((H, W), amb)
    for sx in sp.get("spots", [0.0]):
        r = sp.get("spot_r", .85)
        on_back = (idx == 4) * np.exp(-(((X - sx) / r) ** 2 + ((Y - 1.3) / (1.4 * r)) ** 2))
        on_floor = (idx == 0) * np.exp(-(((X - sx) / (1.1 * r)) ** 2 + ((Z - zg - D * .55) / (.9 * r)) ** 2))
        lit += sp.get("spot", .55 if night else .32) * (on_back + on_floor)
    lit *= 1 - .35 * np.clip((Y - (Hc - .5)) / .5, 0, 1) * (idx == 4)
    img *= lit[..., None] * np.array(sp.get("light", (1.0, .97, .9) if night else (1, 1, .98)))
    # floor reflection inside the window
    refl = sp["floor"][1]
    if refl > 0:
        fl = inside & (idx == 0)
        yb = hor - F * (0 - cam) / (zg + D)                       # where floor meets the back
        ym = (2 * yb - yy).astype(int).clip(0, H - 1)
        mir = om.blur(img, 4)[ym, xx.astype(int)]
        k = refl * np.clip(1 - (yy - yb) / 300, 0, 1)
        img[fl] = img[fl] * (1 - k[fl, None]) + mir[fl] * k[fl, None]
    # track lights along the top of the window
    for sx in np.linspace(-L + .4, R - .4, max(2, int((L + R) / .9))):
        px, py = 800 + F * sx / (zg + .25), hor - F * (Hc - .06 - cam) / (zg + .25)
        g = np.exp(-(((xx - px) / 9) ** 2 + ((yy - py) / 5) ** 2))
        img += (g * inside)[..., None] * np.array([255, 240, 200]) * .9

    # ---- outside the glass: facade and pavement
    fz = FACADES[sp.get("facade", "limestone")]
    out = ~inside
    face = out & (Yg > -sill)
    pave = out & ~face
    img[face] = fz["face"](Xg[face], Yg[face])
    fw = sp.get("frame_w", .1)
    frame = face & (Xg > -L - fw) & (Xg < R + fw) & (Yg > -fw) & (Yg < Hc + fw)
    img[frame] = C(fz["frame"], .9 + .2 * n(Xg[frame], Yg[frame], .3))
    ledge = face & (Yg > -fw - .1) & (Yg <= -fw) & (Xg > -L - .4) & (Xg < R + .4)
    img[ledge] = img[ledge] * .78
    b0, b1 = Hc + .28, Hc + .6
    band = face & (Yg > b0) & (Yg < b1) & (Xg > -L - .5) & (Xg < R + .5)
    img[band] = C(fz["band"], .92 + .12 * n(Xg[band], Yg[band], .5))
    for (x0, x1) in sp.get("neighbors", []):                     # other windows of the same store, seen at an angle
        m = face & (Xg > x0) & (Xg < x1) & (Yg > 0) & (Yg < Hc)
        img[m] = (np.array([46, 44, 42]) + 60 * np.clip((Yg[m] / Hc), 0, 1)[:, None]) * (1.2 if night else 1)
        fr = face & (Xg > x0 - fw) & (Xg < x1 + fw) & (Yg > -fw) & (Yg < Hc + fw) & ~m
        img[fr & ~frame] = fz["frame"]
    tp = (sill + cam) / np.maximum(-v, 1e-9)
    img[pave] = PAVE((u * tp)[pave], tp[pave])
    img[pave] *= np.clip(.95 - (yy[pave] - 800) / 2000, .7, 1)[:, None]
    if night:
        img[out] *= .36
        # light spilling out of the window onto facade and pavement
        cy = hor - F * (Hc / 2 - cam) / zg
        spill = np.exp(-(((xx - 800 - F * (R - L) / 2 / zg) / (F * (L + R) / zg * .6)) ** 2 + ((yy - cy) / 420) ** 2))
        img[out] += (spill[out] * 55)[:, None] * np.array([1, .9, .7])
        img[pave] += (np.exp(-((xx[pave] - 800) / 700) ** 2) * 22)[:, None] * np.array([1, .9, .7])
    return img, inside

def boxes(img, inside, sp, items):
    """plinths and props inside the window: axis-aligned boxes (x0,x1,y0,y1,z0,z1,top,front,side)"""
    cam, hor = sp.get("cam", 1.0), sp.get("hor", 450)
    u = (xx - 800) / F; v = -(yy - hor) / F
    for (x0, x1, y0, y1, z0, z1, top, front, sd) in items:
        with np.errstate(divide="ignore", invalid="ignore"):
            tx0, tx1 = np.sort(np.stack([x0 / u, x1 / u]), 0)
            ty0, ty1 = np.sort(np.stack([(y0 - cam) / v, (y1 - cam) / v]), 0)
            tn = np.maximum(np.maximum(tx0, ty0), z0); tf = np.minimum(np.minimum(tx1, ty1), z1)
        hit = (tn <= tf) & (tn > 0) & inside
        face = np.where(np.isclose(tn, z0), 0, np.where(np.isclose(tn, ty0) | np.isclose(tn, ty1), 1, 2))
        bxp = 800 + F * ((x0 + x1) / 2) / z1; byp = hor + F * cam / z1
        img *= (1 - .35 * inside * np.exp(-(((xx - bxp) / (F * (x1 - x0) / z0 * .7)) ** 2 + ((yy - byp) / 9) ** 2)))[..., None]
        for fi, colr, sh in ((0, front, 1.0), (1, top, 1.1), (2, sd, .75)):
            mm = hit & (face == fi)
            if mm.any():
                img[mm] = C(colr)[None].repeat(mm.sum(), 0) * sh * (.97 + .05 * n(xx[mm] / 300, yy[mm] / 300, .5))[:, None]

def particles(img, inside, sp, rng, zsplit, front):
    """petals / leaves / snow / confetti / hanging ornaments floating in the window"""
    L, R, D, Hc = sp["win"]; zg, cam, hor = sp.get("zg", 4.5), sp.get("cam", 1.0), sp.get("hor", 450)
    for kind, count, cols in sp.get("particles", []):
        for i in range(count):
            x, y, z = rng.uniform(-L + .1, R - .1), rng.uniform(.15, Hc - .15), rng.uniform(zg + .15, zg + D - .15)
            if kind == "hang": y = rng.uniform(Hc * .45, Hc - .3)
            col = np.array(cols[rng.integers(len(cols))], float) * rng.uniform(.85, 1.1)
            ang = rng.uniform(0, np.pi)
            if (z < zsplit) != front: continue
            px, py = 800 + F * x / z, hor - F * (y - cam) / z
            size = {"petal": (.035, .022), "leaf": (.07, .032), "snow": (.022, .022), "confetti": (.03, .012), "hang": (.065, .065)}[kind]
            a, b = size[0] * F / z, size[1] * F / z
            if kind == "hang":                                  # string from the ceiling
                top = hor - F * (Hc - cam) / z
                m = (np.abs(xx - px) < .7) & (yy > top) & (yy < py) & inside
                img[m] = img[m] * .5 + 120
            r0 = int(a + 3)
            ys, xs = slice(max(int(py) - r0, 0), min(int(py) + r0, H)), slice(max(int(px) - r0, 0), min(int(px) + r0, W))
            dx, dy = xx[ys, xs] - px, yy[ys, xs] - py
            if kind in ("snow", "hang"):
                d = np.hypot(dx, dy) / a
            else:
                d = np.sqrt(((dx * np.cos(ang) + dy * np.sin(ang)) / a) ** 2 + ((-dx * np.sin(ang) + dy * np.cos(ang)) / b) ** 2)
                if kind == "confetti":
                    d = np.maximum(np.abs(dx * np.cos(ang) + dy * np.sin(ang)) / a, np.abs(-dx * np.sin(ang) + dy * np.cos(ang)) / b)
            al = np.clip((1 - d) * 3, 0, 1) * inside[ys, xs] * (.85 if kind == "snow" else 1)
            c = col[None, None]
            if kind == "hang":                                   # shiny ball: highlight
                c = col[None, None] * (1.15 - .5 * np.clip((dx + dy) / (2 * a) + .4, 0, 1))[..., None] \
                    + 120 * np.exp(-(((dx + a * .35) ** 2 + (dy + a * .35) ** 2) / (a * .2) ** 2))[..., None]
            img[ys, xs] = img[ys, xs] * (1 - al[..., None]) + c * al[..., None]

def glass(img, inside, sp, rng):
    """reflections on the shop glass: the street behind the viewer, a soft sheen"""
    night = sp.get("night", False)
    sky = np.clip(1 - yy / 700, 0, 1)
    cols = om.blur(om.resize(rng.random((1, 24)), 1, W)[0][None, :].repeat(H, 0), 2)
    bld = (yy > 120 + 260 * cols) * (.5 + .5 * cols)
    ref = (np.array([200, 210, 220]) * sky[..., None] * .8 + np.array([120, 118, 116]) * bld[..., None] * .6)
    k = (.07 if night else .15) * inside
    sheen = np.exp(-(((xx * .55 + yy) - sp.get("sheen", 900)) / 70) ** 2) * .12 * inside
    if night:
        ref = ref * .3
        for _ in range(9):                                   # street-light bokeh
            bx, by, br = rng.uniform(0, W), rng.uniform(40, 520), rng.uniform(14, 34)
            ref += (np.exp(-((xx - bx) ** 2 + (yy - by) ** 2) / br ** 2) * 200)[..., None] * np.array([1, .85, .55])
        k = k + .25 * inside * np.clip(ref.mean(-1) / 255, 0, 1)
    img[:] = img * (1 - k[..., None]) + ref * k[..., None] + 255 * sheen[..., None]

def window_image(slug, sp, height_m, seed):
    rng = np.random.default_rng(seed)
    img, inside = render(sp, rng)
    L, R, D, Hc = sp["win"]; zg, cam = sp.get("zg", 4.5), sp.get("cam", 1.0)
    zpos = zg + D * sp.get("depth", .55)
    x = sp.get("x", 0.0)
    ph = sp.get("plinth", 0)
    items = list(sp.get("props", []))
    if ph:
        pw = sp.get("plinth_w", .9); pc = sp.get("plinth_col", (240, 238, 234))
        items.append((x - pw / 2, x + pw / 2, 0, ph, zpos - pw / 2, zpos + pw / 2, pc, tuple(c * .92 for c in pc), tuple(c * .8 for c in pc)))
    boxes(img, inside, sp, items)
    particles(img, inside, sp, rng, zpos, front=False)
    before = img.copy()
    rgb, a = R2.load_rgba(om.CUTOUTS / f"{slug}.png")
    om.CAM = cam - ph                                        # stand on the plinth
    zs = zpos - (sp.get("plinth_w", .9) * .3 if ph else 0)        # on a plinth: stand a little toward the front edge
    comp = om.place(img, rgb, a, height_m, zs, 800 + F * x / zs, reflect=not ph)
    om.CAM = cam
    comp[~inside] = before[~inside]                          # the facade hides anything outside the opening
    particles(comp, inside, sp, rng, zpos, front=True)
    glass(comp, inside, sp, rng)
    return comp

# ---------------------------------------------------------------- 18 windows (department stores and brand boutiques)
PINK, GOLD, SNOW = [(248, 196, 206), (240, 170, 186), (252, 222, 228)], [(226, 186, 96), (240, 214, 140), (200, 200, 204)], [(255, 255, 255)]
LEAVES = [(196, 90, 40), (222, 150, 52), (160, 62, 40), (200, 120, 50)]
SMALL = dict(win=(1.2, 1.2, 1.5, 2.0), zg=3.4, hor=440, cam=1.0, plinth=.6, plinth_w=.7)          # boutique window, piece on a plinth
TALL = dict(zg=6.0, hor=470, cam=1.0)

SPECS = {
  # spring
  "souga":   dict(win=(2.0, 2.0, 2.0, 2.3), facade="limestone", back=drape((246, 214, 218)), floor=f_lacquer((250, 246, 244)), spots=[0],
                  particles=[("petal", 90, PINK)], neighbors=[(-3.6, -2.4), (2.4, 3.6)]),
  "fukko":   dict(TALL, win=(2.4, 2.4, 2.2, 3.0), facade="concrete", back=disc(R2.concrete((214, 212, 204)), (236, 230, 214), 2.4, 1.7, 1.2), side=R2.concrete((214, 212, 204)),
                  floor=f_sand((216, 206, 186)), spots=[0], neighbors=[(-4.6, -3.0)]),
  "oka":     dict(TALL, win=(2.4, 2.4, 2.2, 3.0), facade="greenmetal", back=R2.moss(), side=R2.plaster((232, 230, 222)), floor=R2.f_wood((150, 112, 78)),
                  spots=[-.3], particles=[("leaf", 50, [(86, 140, 70), (120, 168, 90), (70, 112, 60)])]),
  "mudai1":  dict(win=(2.0, 2.0, 2.0, 2.3), facade="whitetile", back=R2.stripe_wall((206, 40, 46), (246, 244, 240), .35), floor=f_lacquer((196, 36, 40), .35),
                  spots=[0], props=[(1.0, 1.5, 0, .5, 5.0, 5.5, (246, 244, 240), (236, 234, 230), (210, 208, 204)), (-1.6, -1.1, 0, .3, 5.2, 5.7, (246, 244, 240), (236, 234, 230), (210, 208, 204))]),
  # summer
  "tou":     dict(win=(2.0, 2.0, 2.0, 2.3), facade="whitetile", back=disc(gradient((150, 196, 226), (226, 236, 240), 2.3), (250, 236, 200), 2.9, 1.5, .55), side=R2.plaster((226, 236, 240)),
                  floor=f_sand(), spots=[.2], neighbors=[(2.5, 3.7)]),
  "yusho":   dict(TALL, win=(2.6, 2.6, 2.4, 3.3), facade="navy", back=gradient((24, 40, 86), (60, 96, 150), 3.3), side=R2.plaster((40, 52, 86)),
                  floor=f_lacquer((30, 34, 48), .5), spots=[0], spot=.7, night=True, particles=[("confetti", 70, [(220, 60, 50), (240, 200, 60), (60, 120, 210), (250, 250, 250)])]),
  "irodori": dict(win=(2.0, 2.0, 2.0, 2.3), depth=.7, facade="whitetile", back=dots(R2.plaster((250, 214, 84)), (255, 246, 224), .32, .06), side=R2.plaster((250, 214, 84)), floor=R2.f_terrazzo((236, 232, 222)),
                  spots=[0]),
  # autumn
  "mudai2":  dict(SMALL, facade="brick", back=drape((176, 84, 44)), floor=R2.f_wood((120, 82, 52)), spots=[0], particles=[("leaf", 45, LEAVES)], plinth_col=(60, 46, 38)),
  "wasuremono": dict(SMALL, facade="greenmetal", back=R2.wainscot((56, 70, 64), (40, 50, 46), .7), floor=R2.f_herring((100, 70, 48)), spots=[0], night=True,
                  particles=[("leaf", 30, LEAVES)], plinth_col=(214, 196, 160)),
  "mudai5":  dict(win=(2.0, 2.0, 2.0, 2.3), facade="limestone", back=R2.plaster((242, 234, 220)), side=R2.slats((172, 124, 82), .09, .02), floor=R2.f_herring((140, 98, 64)), spots=[0],
                  props=[(-1.7, -1.0, 0, .9, 5.3, 5.8, (110, 72, 44), (96, 62, 38), (80, 52, 32))], light=(1.04, 1, .92)),
  "tamago":  dict(win=(2.0, 2.0, 2.0, 2.3), facade="blackmetal", back=disc(R2.panel((28, 28, 30), 1.0, None, (20, 20, 22)), (196, 160, 90), 2.0, 1.25, 1.0, ring=.06), side=R2.panel((28, 28, 30), 1.0, None, (20, 20, 22)),
                  floor=f_lacquer((22, 22, 24), .5), spots=[0], night=True, spot=.75, neighbors=[(-3.7, -2.5)]),
  # winter / holiday
  "shishu":  dict(SMALL, facade="limestone", back=drape((150, 22, 34)), floor=f_lacquer((120, 18, 28), .4), spots=[0], night=True, spot=.75,
                  particles=[("confetti", 50, GOLD), ("hang", 9, [(216, 176, 90), (196, 30, 40)])], plinth_col=(238, 226, 200)),
  "utage":   dict(TALL, win=(2.4, 2.4, 2.2, 3.0), facade="limestone", back=arch(gradient((236, 224, 196), (250, 244, 232), 3.0), (214, 74, 52), 2.4, 1.7, 2.6), side=R2.plaster((246, 240, 226)),
                  floor=f_lacquer((246, 242, 234), .3), spots=[0], particles=[("confetti", 60, GOLD)], neighbors=[(-4.7, -3.0), (3.0, 4.7)]),
  "mamoru":  dict(win=(2.0, 2.0, 2.0, 2.3), facade="navy", back=gradient((22, 30, 58), (70, 84, 120), 2.3), floor=f_lacquer((236, 238, 242), .25), spots=[0], night=True,
                  particles=[("snow", 140, SNOW)]),
  "mudai3":  dict(SMALL, facade="whitetile", back=gradient((206, 220, 232), (240, 244, 248), 2.0), floor=f_lacquer((244, 246, 248), .5), spots=[0],
                  particles=[("snow", 60, SNOW), ("hang", 6, [(200, 204, 210), (230, 232, 236)])], plinth=.35, plinth_w=1.2, plinth_col=(178, 184, 194)),
  "mudai4":  dict(win=(2.0, 2.0, 2.0, 2.3), facade="blackmetal", back=drape((24, 24, 28), .26, .45), side=R2.plaster((30, 30, 34)), floor=R2.f_check((236, 234, 230), (40, 40, 44), .5),
                  spots=[0], night=True, spot=.85, spot_r=.7),
  # all season
  "tsunagu": dict(TALL, win=(2.6, 2.6, 2.2, 3.0), facade="limestone", back=R2.slats((244, 244, 242), .1, .03, (206, 206, 204)), floor=R2.f_stone((212, 210, 206), 1.0),
                  spots=[-.8, .8], neighbors=[(-4.9, -3.2), (3.2, 4.9)]),
  "mudai6":  dict(SMALL, facade="brick", back=R2.brick((150, 90, 66)), floor=R2.f_wood((120, 84, 56)), spots=[0], night=True, light=(1.08, .98, .84), plinth_col=(40, 40, 42)),
  # added later (kept at the end so the windows above keep their random seeds)
  "moyuru":  dict(win=(2.0, 2.0, 2.0, 2.4), facade="limestone", back=gradient((40, 18, 14), (170, 70, 30), 2.4), side=R2.plaster((60, 30, 22)),
                  floor=f_lacquer((24, 20, 20), .5), spots=[0], night=True, spot=.8,
                  particles=[("confetti", 40, [(255, 150, 60), (240, 90, 40), (255, 200, 120)])]),
}

if __name__ == "__main__":
    rows = {r["slug"]: r for r in csv.DictReader(open(om.ROOT / "data" / "cutouts.csv", encoding="utf-8-sig"))}
    only = sys.argv[1].split(",") if len(sys.argv) > 1 else list(SPECS)
    OUT.mkdir(parents=True, exist_ok=True)
    for i, slug in enumerate(SPECS):
        if slug not in only: continue
        img = window_image(slug, SPECS[slug], float(rows[slug]["height_m"]), seed=100 + i)
        om.save(img, OUT / f"{slug}.jpg")
        print("done", slug)
