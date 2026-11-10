"""手順1：作品写真から作品だけを切り抜いて、cutouts/<slug>.png（透過PNG）に保存します。

切り抜く写真・しきい値などは data/office-images.csv で指定します。
  photo     … 使う写真（Ikeuchi フォルダからのパス）
  height_m  … 作品の高さ（m）。部屋に置くときの大きさになります（手順2で使用）
  crop      … 写真の一部だけ使うとき "左 上 右 下"（0〜1の割合）。空欄なら全体
  threshold … 切り抜きの強さ。細い針金の作品は小さく（0.05〜0.15）
  gapfix    … yes にすると、針金のすき間に残った背景色を消す

    python tools/office-images/1_cutout.py            # 全作品
    python tools/office-images/1_cutout.py tou,tamago # 一部だけ
"""
import csv, sys
import numpy as np
import common as om

rows = list(csv.DictReader(open(om.ROOT / "data" / "office-images.csv", encoding="utf-8-sig")))
only = sys.argv[1].split(",") if len(sys.argv) > 1 else None
om.CUTOUTS.mkdir(exist_ok=True)
for r in rows:
    if only and r["slug"] not in only:
        continue
    img = om.load(om.ROOT / r["photo"])
    if r["crop"].strip():
        x0, y0, x1, y1 = map(float, r["crop"].split()); h, w = img.shape[:2]
        img = img[int(y0 * h):int(y1 * h), int(x0 * w):int(x1 * w)]
    a = om.cutout(img, float(r["threshold"] or .25), r["gapfix"].strip().lower() == "yes")
    om.save(np.dstack([img, a * 255]), om.CUTOUTS / f"{r['slug']}.png", "rgba")
    print("cut", r["slug"])
