# 鉄の作家・池内卓也（IKEUCHI）ホームページ提案

有限会社アイエル物産（高知県香南市）の、鉄の彫刻作品を紹介・レンタル・販売するためのホームページ案をまとめたフォルダです。

- 公開URL（提案一覧）：https://ikeuchi-website.pages.dev/
- 本命の案：**パブリックアートレンタル アイエル**（`rental_office-aile/`）
- GitHub：iwatakuniyasu-beep/ikeuchi-website（非公開）。ここへ push すると Cloudflare Pages が自動で公開します。

---

## まず知っておくこと（3つだけ）

1. **文章・作品の情報は `data/` の表（CSV）を直す** → `python tools/aile-site/build_pages.py` を実行するとページに反映されます。
2. **★自動生成 と書いたフォルダ・ファイルは直接直さない**（プログラムを実行するたびに上書きされます）。直したいときは、下の「どこを直せば何が変わるか」の場所を直します。
3. **公開は `git push`**（下の「公開の手順」）。

---

## フォルダ構成

```
Ikeuchi/
├─ README.md                    ← この説明書
├─ index.html                   ← 提案一覧のトップページ（各案へのリンク）
├─ _redirects                   ← 古いURL → 新しいURL への自動転送（Cloudflare Pages 用）
│
├─ rental_office-aile/          ★本命：パブリックアートレンタル アイエル
│   ├─ index.html               　案A・案Bを選ぶページ（手で編集）
│   ├─ 01-entrance/             　案A のトップ（紺×オレンジ）　※上部と下部は自動生成、間は手で編集（下の説明）
│   ├─ 02-workplace/            　案B のトップ（グリーン×イエロー）　※同上
│   ├─ use01-entrance/          　USE 01 本社エントランスの詳しいページ　★自動生成
│   ├─ use02-event/             　USE 02 周年・式典・採用イベントの詳しいページ　★自動生成
│   ├─ use03-showroom/          　USE 03 ショールームの詳しいページ　★自動生成
│   ├─ use04-showwindow/        　USE 04 百貨店・ブランド店のショーウィンドウのページ　★自動生成
│   ├─ works/                   　作品ページ・作品リスト（index.html）・作家ページ（artist.html）　★自動生成
│   ├─ title/                   　タイトルロゴ（鉄の四季デザイン）の部品　★自動生成
│   └─ assets/                  　この案で使う画像・動画・部品
│       ├─ photo/               　　写真すべて（頭の文字＝出どころ：il_＝公式サイト il-teitetsu.com、wix_＝旧公式サイト、2026-10_＝10月20日撮影、なし＝背景を整えたもの）
│       ├─ office/              　　「オフィスに置いたら」の合成画像　★自動生成
│       ├─ window/              　　「ショーウィンドウに飾ったら」の合成画像　★自動生成
│       ├─ scene/               　　イベント会場・ショールームの合成画像　★自動生成
│       ├─ video/               　　動画（artist-loop.mp4 は作家の15秒動画・いまは仮）
│       ├─ poster/              　　映像のポスター画像
│       ├─ css/                 　　new-works.css（新着の作品の欄）、use-pages.css（USE 01〜04 共通・★自動生成）
│       └─ js/                  　　lightbox.js（写真の拡大表示）、back.js（戻ると元の場所へ・★自動生成）
│
├─ rental_hotel-2designs/        レンタル提案：ホテル・旅館向け（2案）
├─ rental_modelroom-2designs/    レンタル提案：モデルルーム・住宅展示場向け（2案）
├─ rental_bridal-event-2designs/ レンタル提案：ブライダル・イベント向け（2案）
├─ rental_shop-2designs/         レンタル提案：商業施設・ショップ向け（2案）
├─ sales_luxury-5designs/        販売提案：高級マンション・会員制ラウンジ向け（最初の5案）
├─ sales_lounge-2designs/        販売提案：高級ラウンジ向け（2案）
├─ sales_pop-3designs/           販売提案：若い人向けのポップなデザイン（3案）
├─ shared-media/                 上の7つの提案が使う写真・動画（rental_office-aile は使っていない）
│
├─ data/                        ★ここを直す：作品・作家の情報（Excel で開けます。保存は UTF-8 のまま）
│   ├─ works.csv                　作品一覧（作品名・制作年・受賞・設置場所・テーマ・写真・映像・紹介文）
│   ├─ seasons.csv              　トップの「四季の作品」に流す写真（春夏秋冬の順）
│   ├─ career.csv               　作家の経歴（〜2009年。top=yes の行は案A・Bにも表示）
│   ├─ awards.csv               　作家ページ「主な受賞・出品」（年・受賞/出品/展示・内容・作品ID）
│   └─ cutouts.csv              　合成画像のための作品の切り抜き設定（使う写真・作品の高さ など）
│
├─ tools/                       ページや画像を作るプログラム（Python）
│   ├─ requirements.txt         　必要なライブラリ
│   ├─ check_links.py           　リンク切れチェック（公開前に実行）
│   ├─ aile-site/build_pages.py 　data/ を読んで rental_office-aile のページを全部作る
│   ├─ composite-images/        　合成画像を作る
│   │   ├─ 1_cutout.py          　　① 写真から作品を切り抜く → cutouts/
│   │   ├─ 2_place_in_rooms.py  　　② オフィスのエントランスに置く → assets/office/
│   │   ├─ 3_place_in_windows.py　　③ ショーウィンドウに飾る → assets/window/
│   │   ├─ 4_place_in_scenes.py 　　④ イベント会場・ショールームに置く → assets/scene/
│   │   ├─ common.py            　　①〜④の共通部品
│   │   ├─ cutouts/             　　切り抜いた作品（透過PNG）
│   │   └─ models/              　　背景除去AI（GitHubには入れない。README.txt 参照）
│   ├─ title-logo/              　タイトルロゴを作る（make_title_logo.py。draft_* はこれまでの案）
│   └─ artist-video/            　作家の15秒動画を作る
│
│  ── ここから下は GitHub に入れない（このパソコンにだけある）──
├─ movie/                       元の動画（作品映像・大きいため）
├─ 20261020/                    撮影データの元ファイル（HEIC・MOV）
├─ studio/                      AI動画の自動生成の仕組み（別管理）
└─ db_接続情報.txt              秘密の情報（絶対にアップロードしない）
```

フォルダ名のつけ方：`rental_`＝レンタルの提案、`sales_`＝販売の提案、後ろが「業種-案の数」。`use01〜04` は案Aの「USE 01〜04」のカードから開くページです。

---

## どこを直せば何が変わるか

| 直したいもの | 直す場所 | そのあと |
|---|---|---|
| 作品の追加・作品名・制作年・受賞・写真・紹介文 | `data/works.csv` | build_pages.py |
| 四季の作品（トップで流れる写真） | `data/seasons.csv` | build_pages.py |
| 作家の経歴 | `data/career.csv` | build_pages.py |
| 作家ページの「主な受賞・出品」 | `data/awards.csv` | build_pages.py |
| 作家ページの紹介文・肩書き | `tools/aile-site/build_pages.py` の `ARTIST_PAGE` | build_pages.py |
| 案A・Bの上部（紹介文・リクエストオーダー） | `tools/aile-site/build_pages.py` の `DESIGNS`・`ORDER_STEPS` | build_pages.py |
| 案A・Bの真ん中（買うより借りる・来訪者の動線・新着・お問い合わせ など） | `rental_office-aile/01-entrance/index.html`・`02-workplace/index.html` を直接 | なし |
| USE 01〜03 のページの文章 | `tools/aile-site/build_pages.py` の `USE_PAGES` | build_pages.py |
| USE 04 ショーウィンドウのページ | `tools/aile-site/build_pages.py` の `SW_PAGE`・`SW_SEASONS` | build_pages.py |
| 合成画像の部屋・ウィンドウ・会場の雰囲気 | `tools/composite-images/2〜4_*.py` の `SPECS`／`SCENES` | その番号のプログラム → build_pages.py |
| タイトルロゴ | `tools/title-logo/make_title_logo.py` | 実行 → build_pages.py |

※ 案A・Bのページは、`<!-- AILE-TOP:START -->`〜`<!-- AILE-TOP:END -->`（タイトル〜作品と受賞歴）と `<!-- AILE-ORDER:START -->`〜`<!-- AILE-ORDER:END -->`（リクエストオーダー）の間だけプログラムが上書きします。それ以外は手で直してかまいません。

---

## よくある作業

準備（最初の1回）：Python 3 を入れて、`pip install -r tools/requirements.txt`。以下のコマンドはすべて `Ikeuchi` フォルダで実行します。

### 作品を追加する
1. 写真を `rental_office-aile/assets/photo/` に入れる
2. `data/works.csv` に1行追加
   - `slug` … 作品ID（半角英数字。ページのファイル名になる。例 `tamago` → `works/tamago.html`）
   - `photos` … `rental_office-aile/assets/photo/ファイル名`。複数あるときは ` | ` で区切る（1枚目が代表写真）
   - `theme` … 作品リストの絞り込み：`nature`（植物・自然）/ `form`（卵・かたち）/ `human`（人・顔）/ `color`（色・モニュメント）
   - `film_url` … YouTube のURL（縦長ショート動画なら `film_vertical` に `yes`）
3. 受賞・出品があれば `data/awards.csv` にも1行（`slug` に作品ID）
4. `python tools/aile-site/build_pages.py`

### 合成画像（オフィス・ショーウィンドウ・会場）を作る
```
python tools/composite-images/1_cutout.py tamago             # ① 切り抜き（data/cutouts.csv に1行足してから。背景除去AIが必要）
python tools/composite-images/2_place_in_rooms.py tamago     # ② オフィス（SPECS に1行足してから）
python tools/composite-images/3_place_in_windows.py tamago   # ③ ショーウィンドウ（SPECS に1行足してから）
python tools/aile-site/build_pages.py                       # ページに反映
```
部屋・ウィンドウは写真を使わずプログラムで描いています。背景がごちゃごちゃした写真や真上から撮った写真は、きれいに切り抜けません（無地の背景で横から撮った写真が向いています）。

### 作家の動画を差し替える
いまの動画は仮です。工房での作業の実写が届いたら `tools/artist-video/make_artist_loop.py` の `CLIPS` を差し替えて実行します。

---

## 公開の手順
```
python tools/check_links.py        # リンク切れが無いか確認
git add -A
git commit -m "変更内容"
git push                           # 1〜2分で https://ikeuchi-website.pages.dev/ に反映
```
フォルダ名やファイル名を変えたときは、古いURLが開けるように `_redirects` に1行足します。

## 注意
- `db_接続情報.txt` などの秘密ファイルはアップロードしない（`.gitignore` で除外済み）
- サイトは誰でも見られる状態です（Cloudflare Access による閲覧制限は未設定）
- Cloudflare Pages は 1ファイル25MBまで。大きい動画は YouTube に置いてリンクする
- 合成画像は参考イメージです（ページにもそう表記しています）
