"""手順4：イベント会場（周年・式典・採用イベント）とショールームを描き、切り抜いた作品を置いて保存します。

  入力: cutouts/<slug>.png（手順1）、data/office-images.csv の height_m
  出力: rental_office-aile/assets/scene/<場面>-<slug>.jpg（USE 02 イベント・USE 03 ショールームのページに表示）

部屋の描き方は 2_place_in_rooms.py と同じです（写真は使わず、一から描く）。設定は下の SCENES に1場面1行。
  slug … 置く作品、room … (左の壁, 右の壁, 奥行き, 天井高) m、boxes … ステージ・テーブル・カウンターなどの箱、x … 作品の横位置(px)

    python tools/office-images/4_place_in_scenes.py                 # 全場面
    python tools/office-images/4_place_in_scenes.py event-yusho     # 一部だけ
"""
import csv, sys, importlib
import numpy as np
import common as om

R2 = importlib.import_module("2_place_in_rooms")
C, n = R2.C, R2.n
OUT = om.ROOT / "rental_office-aile" / "assets" / "scene"

def banner(col, stripe=None, w=.25):
    """a plain banner / sign panel (no lettering)"""
    def f(u, v):
        c = C(col, .97 + .04 * n(u, v, 1))
        if stripe is not None:
            c[(v % (2 * w)) < .03] = stripe
        return c
    return f

def fabric(col):
    return lambda u, v: C(col, .86 + .14 * (.5 + .5 * np.sin(u * 22 + 3 * n(u, v * .1, 1))))

WHITE, LINEN, WOOD, DARK = (248, 248, 246), (236, 230, 220), (150, 108, 70), (40, 40, 44)
def table(x0, x1, z0, z1, h=.74, top=WHITE): return (x0, x1, 0, h, z0, z1, top, top, tuple(c * .9 for c in top))

SCENES = {
  # ---- events: anniversaries, ceremonies, recruiting
  "event-yusho": dict(slug="yusho", room=(7, 7, 14, 6.0), hor=470, cam=1.6, back=fabric((40, 52, 96)), left=R2.plaster((222, 214, 200)),
      right=R2.plaster((222, 214, 200)), ceiling=R2.c_plaster((236, 230, 220)), floor=R2.f_carpet((120, 40, 46)), x=800,
      back_parts=[(4.6, 9.4, 3.4, 4.4, banner((246, 240, 226), (200, 168, 96)))],
      boxes=[(-6.5, 6.5, 0, .5, 12.0, 14.0, (60, 46, 40), (70, 54, 46), (50, 40, 34)),
             table(-5.6, -3.8, 7.5, 8.6), table(3.8, 5.6, 7.5, 8.6), table(-6.4, -4.6, 10.0, 11.0), table(4.6, 6.4, 10.0, 11.0)],
      pendants=[(-3, 6), (3, 6), (0, 9)], light=(1.04, .98, .9)),
  "event-utage": dict(slug="utage", room=(5, 5, 11, 4.0), hor=440, back=R2.wainscot((244, 236, 222), (170, 130, 90)), left=R2.wainscot((244, 236, 222), (170, 130, 90)),
      right=R2.wainscot((244, 236, 222), (170, 130, 90)), ceiling=R2.c_plaster((248, 244, 236)), floor=R2.f_herring((150, 104, 66)), x=620,
      boxes=[table(1.2, 3.6, 5.0, 5.9), table(-4.6, -2.6, 8.0, 8.9), table(1.6, 3.8, 8.6, 9.5)], pendants=[(-1.5, 5.5), (2.0, 6.5)],
      plants=[(2.4, 5.2, .7)], light=(1.06, 1, .9)),
  "event-tsunagu": dict(slug="tsunagu", room=(5.5, 5.5, 12, 4.2), hor=430, back=R2.panel((236, 238, 240), 1.6), left=R2.plaster((240, 240, 238)),
      right=R2.window((200, 214, 228)), ceiling=R2.c_lines(), floor=R2.f_carpet((84, 88, 96)), x=760,
      back_parts=[(2.0, 9.0, 1.2, 3.2, banner((30, 60, 120), (255, 255, 255), .5))],
      boxes=[(1.8, 4.6, 0, .9, 6.0, 6.7, WHITE, (30, 60, 120), (24, 50, 100)), (-4.8, -2.6, 0, .9, 7.5, 8.2, WHITE, (30, 60, 120), (24, 50, 100))]),
  "event-irodori": dict(slug="irodori", room=(4.5, 4.5, 9, 3.4), hor=440, back=R2.stripe_wall((246, 214, 90), (250, 246, 236), .5), left=R2.plaster((250, 246, 236)),
      right=R2.plaster((250, 246, 236)), ceiling=R2.c_plaster(), floor=R2.f_wood((196, 160, 118)), x=800,
      boxes=[table(-4.0, -2.4, 5.0, 5.8), table(2.4, 4.0, 5.0, 5.8), table(-1.2, 1.2, 7.4, 8.0, .9, (240, 120, 60))], plants=[(-3.6, 6.5, 1.0), (3.6, 6.5, 1.0)]),
  "event-mamoru": dict(slug="mamoru", room=(4, 4, 12, 3.6), hor=440, back=R2.plaster((236, 232, 224)), left=R2.slats((186, 146, 100)), right=R2.slats((186, 146, 100)),
      ceiling=R2.c_wood(), floor=R2.f_stone((200, 196, 188)), x=800,
      back_parts=[(3.2, 4.8, .9, 2.6, banner((20, 20, 22)))], boxes=[(-.9, .9, 0, .75, 10.6, 11.3, DARK, DARK, (30, 30, 34))], plants=[(-3.2, 9, 1.2), (3.2, 9, 1.2)]),
  "event-fukko": dict(slug="fukko", room=(6, 6, 13, 6.5), hor=440, back=R2.concrete(), left=R2.concrete(), right=R2.window((190, 206, 220), (120, 140, 120), 2.0),
      ceiling=R2.c_dark(), floor=R2.f_concrete(), x=700,
      boxes=[(1.6, 5.4, 0, .45, 6.0, 7.2, (70, 70, 74), (60, 60, 64), (50, 50, 54)), table(-5.4, -3.4, 8.0, 9.0, .74, LINEN)], pendants=[(-2.5, 5.5), (2.5, 7)]),
  # ---- showrooms: cars, furniture, kitchens, materials, lighting, company museums
  "showroom-mudai4": dict(slug="mudai4", room=(7, 7, 13, 5.0), hor=440, back=R2.window((206, 220, 232), (130, 150, 130), 3.0), left=R2.panel((236, 236, 238), 2.0),
      right=R2.panel((236, 236, 238), 2.0), ceiling=R2.c_lines((248, 248, 248)), floor=R2.f_big((60, 62, 66), 1.5, 3.0, refl=.45), x=1040,
      boxes=[(-5.4, -1.2, 0, .7, 6.4, 8.4, (190, 30, 40), (170, 24, 34), (140, 20, 28)), (-4.8, -2.0, .7, 1.25, 6.9, 8.0, (60, 70, 80), (30, 34, 40), (24, 28, 32))]),
  "showroom-tamago": dict(slug="tamago", room=(4.5, 4.5, 9, 3.0), hor=430, back=R2.woodpanel((176, 136, 96), 1.2), left=R2.plaster((238, 232, 222)),
      right=R2.plaster((238, 232, 222)), ceiling=R2.c_plaster((244, 240, 232)), floor=R2.f_wood((176, 140, 100)), x=1000,
      boxes=[(-3.8, -.8, 0, .42, 5.2, 6.1, (196, 186, 170), (186, 176, 160), (160, 150, 136)), (-3.8, -.8, .42, .85, 5.9, 6.1, (196, 186, 170), (186, 176, 160), (160, 150, 136)),
             (-3.6, -1.0, 0, .01, 4.6, 6.6, (150, 60, 50), (150, 60, 50), (150, 60, 50))], pendants=[(-2.2, 5.6)], plants=[(3.6, 6.5, 1.1)]),
  "showroom-mudai6": dict(slug="mudai6", room=(4.5, 4.5, 9, 3.0), hor=430, back=R2.tiles((70, 76, 84), .3, (200, 200, 198)), left=R2.plaster((244, 242, 238)),
      right=R2.plaster((244, 242, 238)), ceiling=R2.c_plaster(), floor=R2.f_big((214, 210, 204)), x=560,
      boxes=[(.6, 3.8, 0, .9, 5.6, 6.5, (246, 246, 244), (236, 236, 234), (214, 214, 212)), (.6, 4.4, 0, 2.2, 8.6, 9.0, (230, 226, 218), (230, 226, 218), (200, 196, 190))],
      pendants=[(1.6, 5.4), (2.8, 5.4)]),
  "showroom-oka": dict(slug="oka", room=(5, 5, 10, 3.4), hor=430, back=R2.concrete((214, 210, 202)), left=R2.concrete((214, 210, 202)), right=R2.concrete((214, 210, 202)),
      ceiling=R2.c_dark(), floor=R2.f_concrete((170, 166, 160)), x=800,
      back_parts=[(.5, 2.3, .6, 2.4, R2.tiles((180, 120, 90), .15)), (2.6, 4.4, .6, 2.4, R2.tiles((230, 228, 222), .3)), (5.6, 7.4, .6, 2.4, R2.brick((150, 90, 66))),
                  (7.7, 9.5, .6, 2.4, R2.woodpanel((170, 130, 90), .3))]),
  "showroom-minomushi": dict(slug="minomushi", room=(4, 4, 8, 3.2), hor=440, back=R2.plaster((44, 44, 48)), left=R2.plaster((52, 52, 56)), right=R2.plaster((52, 52, 56)),
      ceiling=R2.c_dark(), floor=R2.f_big((70, 70, 74), refl=.35), x=800, wash=40, plinth=.9,
      boxes=[(-.6, .6, 0, .9, 3.3, 3.9, (230, 228, 224), (220, 218, 214), (196, 194, 190))],
      pendants=[(-2.6, 5), (-1.4, 6), (1.4, 6), (2.6, 5), (0, 7)]),
  "showroom-souga": dict(slug="souga", room=(6, 6, 12, 5.5), hor=430, back=R2.panel((206, 200, 190), 2.4), left=R2.panel((190, 196, 202), 2.4), right=R2.window((200, 214, 226)),
      ceiling=R2.c_lines(), floor=R2.f_stone((206, 204, 198), 1.2), x=820, plinth=.12,
      boxes=[(-5.0, -2.6, 0, 1.0, 6.0, 6.8, WHITE, (230, 230, 228), (210, 210, 208)), (2.8, 5.0, 0, 1.0, 8.0, 8.8, WHITE, (230, 230, 228), (210, 210, 208)),
             (-1.0, 1.0, 0, .12, 3.0, 4.2, (200, 196, 190), (190, 186, 180), (170, 166, 160))]),
}

if __name__ == "__main__":
    rows = {r["slug"]: r for r in csv.DictReader(open(om.ROOT / "data" / "office-images.csv", encoding="utf-8-sig"))}
    only = sys.argv[1].split(",") if len(sys.argv) > 1 else list(SCENES)
    OUT.mkdir(parents=True, exist_ok=True)
    for key in only:
        sp = SCENES[key]
        bg = R2.render(sp)
        if "pendants" in sp: R2.pendants(bg, sp["pendants"], Hc=sp["room"][3])
        if "plants" in sp: R2.plants(bg, sp["plants"])
        rgb, a = R2.load_rgba(om.CUTOUTS / f'{sp["slug"]}.png')
        cam = om.CAM; om.CAM = cam - sp.get("plinth", 0)                 # stand on a plinth / platform if there is one
        comp = om.place(bg, rgb, a, float(rows[sp["slug"]]["height_m"]), 3.6, sp.get("x", 800), reflect=not sp.get("plinth"))
        om.CAM = cam
        om.save(comp, OUT / f"{key}.jpg")
        print("done", key)
