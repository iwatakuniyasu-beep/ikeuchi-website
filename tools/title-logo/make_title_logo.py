"""パブリックアートレンタル アイエルのタイトルロゴ（鉄の四季デザイン）を作るプログラム。

実行すると次の2つを書き出します。
  - preview_final.html … 確認用のページ（ブラウザで開く）
  - rental_office-aile/title/aile-title.svg.html とテクスチャ画像 … サイトに埋め込む部品
そのあと tools/aile-site/build_pages.py を実行すると、案A・案Bのページにロゴが入ります。

    python tools/title-logo/make_title_logo.py
    python tools/aile-site/build_pages.py

飾り（桜・向日葵・紅葉・雪）の位置や大きさは art() / extra_art() の数字で調整します。
形は乱数で作っていますが、rnd = random.Random(5) で固定しているので毎回同じ形になります。
"""
import math, pathlib, random, re

HERE = pathlib.Path(__file__).parent
head = HERE.joinpath("draft_v5_arrange.html").read_text(encoding="utf-8").split("<!-- reusable leaf")[0]
rnd = random.Random(5)

def f(v):
    return f"{v:.1f}".rstrip("0").rstrip(".")

def pol(cx, cy, r, deg):
    a = math.radians(deg - 90)  # 0deg = up
    return cx + r * math.cos(a), cy + r * math.sin(a)

def path(points, close=True):
    return "M" + " L".join(f"{f(x)} {f(y)}" for x, y in points) + (" Z" if close else "")

def wobble(amp):
    """smooth random radial wobble r(θ) multiplier, plus fine cut roughness"""
    terms = [(k, amp / k ** .8 * rnd.uniform(.5, 1), rnd.uniform(0, 6.3)) for k in range(2, 10)]
    return lambda deg: 1 + sum(a * math.sin(k * math.radians(deg) + p) for k, a, p in terms) + rnd.uniform(-.012, .012)

def polar_shape(rfun, step=2.0):
    w = wobble(.05)
    return [pol(0, 0, rfun(d) * w(d), d) for d in [i * step for i in range(int(360 / step))]]

def slit(r0, r1, ang, width, bend=0):
    """a teardrop-shaped slit cut along a radius (like the cut-outs in his leaves)"""
    pts = []
    n = 10
    for i in range(n + 1):                                    # one side, out
        t = i / n
        r = r0 + (r1 - r0) * t
        hw = width * math.sin(math.pi * t) ** .7 * (1.2 - .6 * t)
        a = ang + bend * math.sin(math.pi * t) + math.degrees(hw / max(r, 1))
        pts.append(pol(0, 0, r, a))
    for i in range(n, -1, -1):                                # other side, back
        t = i / n
        r = r0 + (r1 - r0) * t
        hw = width * math.sin(math.pi * t) ** .7 * (1.2 - .6 * t)
        a = ang + bend * math.sin(math.pi * t) - math.degrees(hw / max(r, 1))
        pts.append(pol(0, 0, r, a))
    return path(pts)

def spiral(r_max, turns, jitter=.06):
    """grinder swirl marks"""
    pts = []
    n = int(turns * 40)
    for i in range(n):
        t = i / n
        pts.append(pol(0, 0, r_max * t * (1 + rnd.uniform(-jitter, jitter)), t * turns * 360))
    return path(pts, close=False)

def ang_dist(a, b):
    return (a - b + 180) % 360 - 180

# ---------- shapes ----------
def sakura(R):
    base = rnd.uniform(0, 72)
    petals = [(base + i * 72 + rnd.uniform(-7, 7), R * rnd.uniform(.82, 1.1)) for i in range(5)]
    def r(d):
        a, L = min(petals, key=lambda p: abs(ang_dist(d, p[0])))
        u = ang_dist(d, a) / 36
        v = L * (.3 + .7 * math.sqrt(max(0, 1 - u * u)))
        return v - L * .22 * math.exp(-(u / .14) ** 2)        # the notch at the petal tip
    holes = [slit(L * .38, L * .74, a + rnd.uniform(-4, 4), L * .07, rnd.uniform(-6, 6)) for a, L in petals if rnd.random() < .8]
    return path(polar_shape(r)) + " " + " ".join(holes)

def sunflower_petals(R):
    n = 13
    petals = [(i * 360 / n + rnd.uniform(-5, 5), R * rnd.uniform(.72, 1.08)) for i in range(n)]
    def r(d):
        a, L = min(petals, key=lambda p: abs(ang_dist(d, p[0])))
        u = abs(ang_dist(d, a)) / (180 / n)
        return R * .4 + (L - R * .4) * max(0, 1 - u) ** .75
    return path(polar_shape(r, 1.5))

def sun_disc(R):
    disc = path(polar_shape(lambda d: R))
    holes = []
    for _ in range(16):
        rr, a = R * math.sqrt(rnd.uniform(.02, .7)), rnd.uniform(0, 360)
        x, y = pol(0, 0, rr, a)
        s = R * rnd.uniform(.07, .13)
        holes.append(path([(x + s * math.cos(k / 8 * 6.283) * rnd.uniform(.8, 1.2), y + s * math.sin(k / 8 * 6.283) * rnd.uniform(.8, 1.2)) for k in range(8)]))
    return disc + " " + " ".join(holes)

def leaf(L):
    """broad leaf pointing up from 0,0 with herringbone slits"""
    w = wobble(.04)
    left, right = [], []
    for i in range(41):
        t = i / 40
        hw = L * .36 * math.sin(math.pi * t ** .85) * (1 - .25 * t)
        tooth = L * .025 * (1 if i % 5 == 0 else 0)
        left.append((-(hw + tooth) * w(i * 9), -L * t))
        right.append(((hw + tooth) * w(i * 9 + 180), -L * t))
    outline = path(left + right[::-1])
    holes = []
    for k, t in enumerate([.22, .34, .46, .58, .7]):
        side = -1 if k % 2 else 1
        holes.append(f'<path d="{slit(4, L * .24 * (1 - t * .4), side * 55, L * .03, side * 8)}" transform="translate(0 {f(-L * t)})"/>')
    return outline, holes

LOBES = [(-120, .5), (-80, .78), (-40, .95), (0, 1.0), (40, .93), (80, .8), (120, .48)]

def momiji(R):
    lobes = [(a + rnd.uniform(-6, 6), L * rnd.uniform(.88, 1.08)) for a, L in LOBES]
    pts = []
    for i, (ang, L) in enumerate(lobes):
        L *= R
        prev = lobes[i - 1][0] if i else ang - 40
        pts.append(pol(0, 0, R * rnd.uniform(.14, .22), (prev + ang) / 2))
        for side in (-1, 1):
            ts = [.32, .5, .68, .84] if side < 0 else [.84, .68, .5, .32]
            if side > 0:
                pts.append(pol(0, 0, L, ang + rnd.uniform(-3, 3)))
            for t in ts:
                hw = L * .38 * t * (1 - t) * rnd.uniform(.8, 1.25) + (L * .05 if rnd.random() < .5 else 0)
                cx, cy = pol(0, 0, L * t, ang)
                a = math.radians(ang - 90 + 90 * side)
                pts.append((cx + hw * math.cos(a), cy + hw * math.sin(a)))
    holes = [slit(R * .25, L * R * .68, a, L * R * .045, rnd.uniform(-5, 5)) for a, L in lobes if rnd.random() < .85]
    return path(pts) + " " + " ".join(holes)

def snow(r):
    d = []
    for k in range(6):
        a = k * 60 + rnd.uniform(-7, 7)
        L = r * rnd.uniform(.82, 1.12)
        x, y = pol(0, 0, L, a)
        mx, my = pol(0, 0, L * .5, a + rnd.uniform(-8, 8))
        d.append(f"M0 0 Q{f(mx)} {f(my)} {f(x)} {f(y)}")
        for t in (.45, .72):
            if rnd.random() < .15:
                continue
            bx, by = pol(0, 0, L * t, a)
            for s in (-1, 1):
                bl = L * rnd.uniform(.16, .32) * (1.2 - t)
                ex, ey = pol(bx, by, bl, a + s * rnd.uniform(38, 60))
                d.append(f"M{f(bx)} {f(by)} L{f(ex)} {f(ey)}")
    return " ".join(d)

def coil(x0, y0, length, ang, r, turns):
    """hand-wound wire coil (his signature springs)"""
    pts = []
    n = int(turns * 30)
    ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    for i in range(n + 1):
        t = i / n
        u = length * t + r * math.cos(t * turns * 6.283) - r
        v = r * math.sin(t * turns * 6.283) * rnd.uniform(.9, 1.1)
        pts.append((x0 + u * ca - v * sa, y0 + u * sa + v * ca))
    return path(pts, close=False)

# ---------- defs ----------
def pat(pid, img):
    return f'    <pattern id="{pid}" patternUnits="userSpaceOnUse" width="350" height="140"><image href="textures/{img}" width="350" height="140"/></pattern>\n'

FILTERS = """    <!-- flat cut sheet: barely-rounded cut edge, matte, small cast shadow (roomy region so thin parts never clip) -->
    <filter id="fCut" x="-50%" y="-50%" width="200%" height="200%" color-interpolation-filters="sRGB">
      <feGaussianBlur in="SourceAlpha" stdDeviation="1" result="b"/>
      <feDiffuseLighting in="b" surfaceScale="1.6" diffuseConstant="1.05" lighting-color="#fff" result="dif"><feDistantLight azimuth="225" elevation="62"/></feDiffuseLighting>
      <feComposite in="SourceGraphic" in2="dif" operator="arithmetic" k1="1.08" k2="0" k3="0" k4="0" result="lit"/>
      <feComposite in="lit" in2="SourceAlpha" operator="in" result="face"/>
      <feGaussianBlur in="SourceAlpha" stdDeviation="2"/><feOffset dx="4" dy="6" result="sho"/>
      <feFlood flood-color="#3a2a1a" flood-opacity=".38"/><feComposite in2="sho" operator="in" result="shadow"/>
      <feMerge><feMergeNode in="shadow"/><feMergeNode in="face"/></feMerge>
    </filter>
    <!-- hand-bent rod: round but matte -->
    <filter id="fRod" x="-50%" y="-50%" width="200%" height="200%" color-interpolation-filters="sRGB">
      <feGaussianBlur in="SourceAlpha" stdDeviation="1.5" result="b"/>
      <feDiffuseLighting in="b" surfaceScale="3" diffuseConstant="1.1" lighting-color="#fff" result="dif"><feDistantLight azimuth="225" elevation="55"/></feDiffuseLighting>
      <feComposite in="SourceGraphic" in2="dif" operator="arithmetic" k1="1.12" k2="0" k3="0" k4="0" result="lit"/>
      <feComposite in="lit" in2="SourceAlpha" operator="in" result="face"/>
      <feGaussianBlur in="SourceAlpha" stdDeviation="1.6"/><feOffset dx="3" dy="5" result="sho"/>
      <feFlood flood-color="#3a2a1a" flood-opacity=".35"/><feComposite in2="sho" operator="in" result="shadow"/>
      <feMerge><feMergeNode in="shadow"/><feMergeNode in="face"/></feMerge>
    </filter>
"""

defs = ("".join(pat(p, i) for p, i in [("tGalv", "tex4-galv.jpg"), ("tRust4", "tex4-rust.jpg"), ("tPink", "tex4-pink.jpg"),
                                         ("tYellow", "tex4-yellow.jpg"), ("tRed4", "tex4-red.jpg"), ("tWhite", "tex4-white.jpg"),
                                         ("tGreen", "tex4-green.jpg"), ("tForged4", "tex2-forged.jpg")])
        + FILTERS + "  </defs>\n</svg>\n")

# wide, low banner: アイエル in the middle, spring/summer to its left, autumn/winter to its right
VW, VH = 2400, 300
OX = 500  # x offset of the original centre composition
WIRE = "M20 140 C 120 120, 200 200, 330 250 S 560 276, 700 266 S 900 250, 1070 250 S 1290 170, 1380 130"
SCRATCH = 'fill="none" stroke-linecap="round"'

def weld(x, y, r=4.5):
    return "".join(f'<circle cx="{f(x + rnd.uniform(-2, 2))}" cy="{f(y + rnd.uniform(-2, 2))}" r="{f(r * rnd.uniform(.6, 1))}" fill="url(#tForged4)"/>' for _ in range(3))

def g(x, y, rot, inner):
    return f'<g transform="translate({x} {y}) rotate({rot})">{inner}</g>'

rod = 'fill="none" stroke="url(#tForged4)" stroke-linecap="round" stroke-linejoin="round"'

def flower(x, y, R, rot):
    return g(x, y, rot,
             f'<path d="{sakura(R)}" fill="url(#tPink)" fill-rule="evenodd" filter="url(#fCut)"/>'
             f'<g filter="url(#fCut)"><path d="{path(polar_shape(lambda d: R * .3))}" fill="url(#tGalv)"/></g>'
             f'<path d="{spiral(R * .27, 3.2)}" {SCRATCH} stroke="#fff" stroke-opacity=".55" stroke-width="1"/>'
             f'<path d="{spiral(R * .25, 2.6)}" {SCRATCH} stroke="#3a3a3a" stroke-opacity=".35" stroke-width=".8"/>')

def maple(x, y, rot, R, tex):
    # leaf stalk: a short bent rod running from the leaf's centre down to the stem
    stalk = f'<path d="M0 0 Q{f(R * .06)} {f(R * .2)} {f(R * .02)} {f(R * .4)}" {rod} stroke-width="{f(max(2.5, R * .05))}" filter="url(#fRod)"/>'
    return g(x, y, rot, stalk + f'<path d="{momiji(R)}" fill="{tex}" fill-rule="evenodd" filter="url(#fCut)"/>')

def sunflower(x, y, R, rot=0):
    return g(x, y, rot, f'<path d="{sunflower_petals(R)}" fill="url(#tYellow)" filter="url(#fCut)"/>'
                        f'<path d="{sun_disc(R * .43)}" fill="url(#tRust4)" fill-rule="evenodd" filter="url(#fCut)"/>')

def leaf_at(x, y, rot, L, tex):
    o, h = leaf(L)
    return g(x, y, rot, f'<path d="{o}" fill="{tex}" filter="url(#fCut)"/><g fill="#efeae2">{"".join(h)}</g>')

def snow_at(x, y, rot, r, w):
    return g(x, y, rot, f'<path d="{snow(r)}" stroke-width="{w}"/>')

def art():
    out = []
    # hand-bent stems (slightly kinked), welded onto the wire
    stems = ["M92 142 C 102 160, 92 186, 100 214", "M164 169 C 176 146, 158 112, 166 82",
             "M241 207 C 256 180, 262 150, 276 122", "M241 207 C 236 214, 232 220, 228 226",
             "M1173 236 C 1168 206, 1150 180, 1143 146", "M1255 205 C 1270 216, 1264 234, 1273 248",
             "M1312 165 C 1306 130, 1298 110, 1292 74"]
    out.append(f'<g {rod} stroke-width="4" filter="url(#fRod)">' + "".join(f'<path d="{d}"/>' for d in stems) + "</g>")
    # the coils were removed at the client's request; still draw them from rnd so the other shapes keep their exact form
    for args in [(40, 322, 70, 100, 9, 5), (760, 342, 64, 75, 8, 4.5), (1150, 120, 48, 30, 7, 3.5)]:
        coil(*args)
    joints = [(92, 142), (164, 169), (241, 207), (241, 207), (1173, 236), (1255, 205), (1312, 165)]
    out.append('<g filter="url(#fRod)">' + "".join(weld(x, y) for x, y in joints) + "</g>")
    weld(40, 322); weld(760, 342)  # welds of the removed coils (keeps rnd in step)

    # 春: 桜 — 手塗りの淡いピンク、塗装の剥げから錆がのぞく
    out += [flower(100, 214, 40, 8), flower(166, 80, 34, -24)]
    flower(282, 432, 18, 40); sakura(14)  # removed small flower and falling petal (keeps rnd in step)
    # 夏: 向日葵 — 黄色塗装の鉄板 + 打ち抜き穴の錆びた中心 / 亜鉛メッキの葉
    lo, lh = leaf(70)
    lo2, lh2 = leaf(50)
    out += [g(228, 226, 205, f'<path d="{lo}" fill="url(#tGalv)" filter="url(#fCut)"/><g fill="#efeae2">{"".join(lh)}</g>'),
            g(262, 152, -105, f'<path d="{lo2}" fill="url(#tGreen)" filter="url(#fCut)"/><g fill="#efeae2">{"".join(lh2)}</g>'),
            g(278, 118, 0, f'<path d="{sunflower_petals(56)}" fill="url(#tYellow)" filter="url(#fCut)"/>'
                           f'<path d="{sun_disc(24)}" fill="url(#tRust4)" fill-rule="evenodd" filter="url(#fCut)"/>')]
    # 秋: 紅葉 — 錆びた鉄板 / 赤の手塗り、スリットの切り抜き
    out += [maple(1150, 118, 16, 70, "url(#tRust4)"), maple(1265, 256, -148, 44, "url(#tRed4)")]
    maple(812, 416, 196, 36, "url(#tRust4)")  # removed small falling leaf (keeps rnd in step)
    # 冬: 雪 — 白く塗った丸棒を手曲げ、錆が浮く
    out.append('<g fill="none" stroke="url(#tWhite)" stroke-linecap="round" filter="url(#fRod)">'
               + g(1292, 70, 0, f'<path d="{snow(28)}" stroke-width="4.5"/>')
               + g(1380, 130, 12, f'<path d="{snow(20)}" stroke-width="3.6"/>')
               + g(1362, 236, -8, f'<path d="{snow(14)}" stroke-width="3"/>') + "</g>")
    out.append('<g font-family="\'Zen Kaku Gothic New\', sans-serif" font-size="17" font-weight="700" fill="#8a7d70">'
               '<text x="30" y="268">春</text><text x="318" y="64">夏</text><text x="1072" y="70">秋</text><text x="1356" y="58">冬</text></g>')
    return "\n      ".join(out)

ART = art()

# the wire runs on to both screen edges, with more of each season along it
WIRE_L = "M-10 118 C 90 92, 190 176, 300 168 S 450 128, 520 140"
WIRE_R = "M1880 130 C 1960 100, 2040 176, 2150 168 S 2320 104, 2410 122"

def extra_art():
    out = []
    stems = ["M88 112 C 100 140, 84 170, 92 196", "M214 152 C 226 126, 206 96, 212 72", "M338 160 C 344 180, 334 200, 340 214",
             "M448 136 C 460 112, 444 94, 452 76", "M404 142 C 400 150, 398 156, 396 162",
             "M1958 120 C 1966 142, 1960 156, 1968 168", "M2068 160 C 2072 136, 2060 116, 2064 96",
             "M2186 160 C 2192 182, 2182 200, 2186 214", "M2292 124 C 2300 104, 2286 86, 2292 66"]
    out.append(f'<g {rod} stroke-width="4" filter="url(#fRod)">' + "".join(f'<path d="{d}"/>' for d in stems) + "</g>")
    out.append('<g filter="url(#fRod)">' + "".join(weld(x, y) for x, y in
               [(88, 112), (214, 152), (338, 160), (448, 136), (404, 142), (1958, 120), (2068, 160), (2186, 160), (2292, 124)]) + "</g>")
    # 春・夏 on the far left
    out += [flower(92, 200, 38, 20), flower(212, 66, 32, -10), flower(340, 218, 30, 30),
            leaf_at(396, 162, 196, 60, "url(#tGreen)"), sunflower(452, 70, 46)]
    # 秋・冬 on the far right
    out += [maple(1975, 190, -164, 56, "url(#tRed4)"), maple(2068, 70, 8, 50, "url(#tRust4)")]
    out.append('<g fill="none" stroke="url(#tWhite)" stroke-linecap="round" filter="url(#fRod)">'
               + snow_at(2186, 236, 0, 24, 4) + snow_at(2292, 54, 18, 30, 4.5) + snow_at(2380, 214, -10, 15, 3) + "</g>")
    return "\n      ".join(out)

EXTRA = extra_art()
SVG_MAIN = f"""<svg class="ttl" viewBox="0 0 {VW} {VH}" preserveAspectRatio="xMidYMid slice" role="img" aria-label="パブリックアートレンタル アイエル">
    <g fill="none" stroke="url(#pForged)" stroke-linejoin="round" stroke-linecap="round" filter="url(#fBar)" font-family="'Kiwi Maru', serif" font-weight="500">
      <text x="1200" y="58" text-anchor="middle" font-size="46" stroke-width="3.6" letter-spacing="4">パブリックアートレンタル</text>
      <text x="1207" y="232" text-anchor="middle" font-size="160" stroke-width="10" letter-spacing="14">アイエル</text>
    </g>
    <g transform="translate({OX} 0)">
    <path d="{WIRE}" fill="none" stroke="url(#pForged)" stroke-width="9" stroke-linecap="round" filter="url(#fRod)"/>
      {ART}
    </g>
    <path d="{WIRE_L} {WIRE_R}" fill="none" stroke="url(#pForged)" stroke-width="9" stroke-linecap="round" filter="url(#fRod)"/>
      {EXTRA}
  </svg>"""

body = f"""
<p class="label">5-3 改　四季がめぐる鉄<small>池内さんの作品のように、ラフに切った鉄板・スリットの切り抜き・手塗りの剥げた塗装・手曲げの棒とコイルで</small></p>
<header class="t v3">
  <p class="en">PUBLIC ART RENTAL — AIEL</p>
  {SVG_MAIN}
  <p class="sub">鉄の作家・池内卓也の作品を、オフィスにレンタル。</p>
</header>
"""

html = (head.replace("<title>アイエル タイトル案5 アレンジ</title>", "<title>アイエル タイトル案5-3 改</title>")
        + defs + body + "\n</body>\n</html>\n")
HERE.joinpath("preview_final.html").write_text(html, encoding="utf-8", newline="\n")

# fragment for the live site: hidden defs + the title svg; textures are copied to rental_office-aile/title/
SITE = HERE.parents[1] / "rental_office-aile" / "title"
SITE.mkdir(exist_ok=True)
frag = head[head.index('<svg width="0"'):] + defs + SVG_MAIN + "\n"
frag = frag.replace('href="textures/tex', 'href="../title/tex')
SITE.joinpath("aile-title.svg.html").write_text(frag, encoding="utf-8", newline="\n")
for t in sorted(set(re.findall(r'href="\.\./title/(tex[^"]+)"', frag))):
    (SITE / t).write_bytes((HERE / "textures" / t).read_bytes())
print("ok")
