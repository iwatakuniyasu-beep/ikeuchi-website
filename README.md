# 鉄の作家・池内卓也（IKEUCHI）ホームページ提案

有限会社アイエル物産（高知県香南市）の、鉄の彫刻作品を紹介・レンタル・販売するためのホームページ案をまとめたフォルダです。

- 公開URL（提案一覧）：https://ikeuchi-website.pages.dev/
- 本命の案：**パブリックアートレンタル アイエル**（`rental_office-aile/`）
- GitHub：iwatakuniyasu-beep/ikeuchi-website（非公開）。ここへ push すると Cloudflare Pages が自動で公開します。

---

## フォルダ構成

```
Ikeuchi/
├─ README.md                ← この説明書
├─ index.html               ← 提案一覧のトップページ（各案へのリンク）
├─ _redirects               ← 旧URL（/website5/ など）→ 新URL への自動転送（Cloudflare Pages 用）
│
├─ rental_office-aile/      ★本命：パブリックアートレンタル アイエル（オフィス・企業向け）
│   ├─ index.html           　案A・案Bを選ぶページ
│   ├─ 01-entrance/         　案A（紺×オレンジ）
│   ├─ 02-workplace/        　案B（グリーン×イエロー）
│   ├─ entrance/            　USE 01 本社エントランスの詳しいページ ※自動生成（直接編集しない）
│   │   ├─ index.html       　　作品リスト
│   │   ├─ artist.html      　　作家ページ
│   │   ├─ <作品ID>.html    　　作品ごとのページ（例 tamago.html ＝「卵」）
│   │   └─ work.css         　　works/ 共通のデザイン
│   ├─ title/               　タイトルロゴ（鉄の四季デザイン）の部品 ※自動生成
│   └─ assets/              　この案だけで使う画像・動画
│       ├─ office/          　　「オフィスに置いたら」の合成画像 ※自動生成
│       ├─ video/           　　作家の15秒ループ動画 ※自動生成（いまは仮の映像）
│       ├─ photo/           　　この案で使う写真すべて（wix_＝公式サイトの写真、2026-10_＝10月20日撮影、名前なし＝背景を整えたもの）
│       ├─ poster/          　　映像のポスター画像
│       ├─ new-works.css    　　「新着の作品」欄のデザイン
│       └─ js/lightbox.js   　　写真や動画を拡大表示する部品
│
├─ rental_hotel-2designs/        レンタル提案：ホテル・旅館向け（2案）
├─ rental_modelroom-2designs/    レンタル提案：モデルルーム・住宅展示場向け（2案）
├─ rental_bridal-event-2designs/ レンタル提案：ブライダル・イベント向け（2案）
├─ rental_shop-2designs/         レンタル提案：商業施設・ショップ向け（2案）
├─ sales_luxury-5designs/        販売提案：高級マンション・会員制ラウンジ向け（最初の5案）
├─ sales_lounge-2designs/        販売提案：高級ラウンジ向け（2案）
├─ sales_pop-3designs/           販売提案：若い人向けのポップなデザイン（3案）
│
├─ shared-media/            写真・動画の元置き場（ほかの提案が使う。rental_office-aile は assets/ にコピーを持つ）
│   ├─ wix-photos/          　公式サイト（Wix）から取り込んだ作品写真
│   ├─ 2026-10_photos/      　2026年10月20日に撮影した作品・設置写真
│   ├─ 2026-10_videos/      　同じ日の動画（ループ用）
│   └─ 2026-10_new-works.css　「新着の作品」欄のデザイン
│
├─ data/                    ★作品の情報（Excel で開けます）。ここを直してプログラムを実行するとページに反映
│   ├─ works.csv            　作品一覧（作品名・制作年・受賞・設置場所・テーマ・写真・映像・紹介文）
│   ├─ seasons.csv          　トップの「四季の作品」に流す写真（春夏秋冬の順）
│   ├─ career.csv           　作家の経歴
│   └─ office-images.csv    　「オフィスに置いたら」の合成画像の設定（使う写真・作品の高さ など）
│
├─ tools/                   ページや画像を作るプログラム（Python）
│   ├─ requirements.txt     　必要なライブラリ
│   ├─ check_links.py       　リンク切れチェック（公開前に実行）
│   ├─ aile-site/build_pages.py 　data/ を読んで rental_office-aile のページを作る
│   ├─ title-logo/          　タイトルロゴを作る（make_title_logo.py、テクスチャ、これまでの案）
│   ├─ office-images/       　「オフィスに置いたら」「ショーウィンドウに飾ったら」の画像を作る（1_cutout.py → 2_place_in_rooms.py ／ 3_place_in_windows.py ／ 4_place_in_scenes.py）
│   │   ├─ cutouts/         　　作品を切り抜いた透過PNG
│   │   └─ models/          　　背景除去AI（GitHubには入れない。README.txt 参照）
│   └─ artist-video/        　作家の15秒ループ動画を作る
│
│  ── ここから下は GitHub に入れない（このパソコンにだけある）──
├─ movie/                   元の動画（作品映像・大きいため）
├─ 20261020/                撮影データの元ファイル（HEIC・MOV）
├─ studio/                  AI動画の自動生成の仕組み（別管理）
└─ db_接続情報.txt          秘密の情報（絶対にアップロードしない）
```

フォルダ名のつけ方：`rental_`＝レンタルの提案、`sales_`＝販売の提案、後ろが「業種-案の数」です。

---

## よくある作業

準備（最初の1回）：Python 3 を入れて、`pip install -r tools/requirements.txt`

以下のコマンドはすべて `Ikeuchi` フォルダで実行します。

### 作品を追加する・情報を直す
1. `data/works.csv` を Excel などで開き、1行追加（または修正）して保存（文字コードは UTF-8 のまま）
   - `slug` … 作品ID（半角英数字。ページのファイル名になる。例 `tamago` → `works/tamago.html`）
   - `photos` … 写真のパス。複数あるときは ` | ` で区切る（1枚目が代表写真）
   - `theme` … 作品リストの絞り込み：`nature`（植物・自然）/ `form`（卵・かたち）/ `human`（人・顔）/ `color`（色・モニュメント）
   - `film_url` … YouTube のURL（縦長ショート動画なら `film_vertical` に `yes`）
2. 写真は `rental_office-aile/assets/photo/` に置き、`photos` には `rental_office-aile/assets/photo/ファイル名` と書く
3. `python tools/aile-site/build_pages.py` を実行 → 作品ページ・作品リスト・作家ページ・トップが更新される

### 四季の作品・経歴を変える
`data/seasons.csv` または `data/career.csv` を直して、`python tools/aile-site/build_pages.py`

### トップのその他の文章を変える
- 案A・案Bの上部（タイトル〜リクエストオーダー）の文章とデザイン：`tools/aile-site/build_pages.py` の中（`DESIGNS`、`ORDER_STEPS` など）
- 上部より下（来訪者の動線・レンタルの理由・導入の流れ・お問い合わせなど）：`rental_office-aile/01-entrance/index.html` などを直接編集してOK
  ※ `<!-- AILE-TOP:START -->` 〜 `<!-- AILE-TOP:END -->`（タイトル〜作品と受賞歴）と `<!-- AILE-ORDER:START -->` 〜 `<!-- AILE-ORDER:END -->`（リクエストオーダー）の間はプログラムが上書きするので直接編集しない。2つの間（案Aの「買うより、借りる。」）は直接編集してOK

### 「オフィスに置いたら」の画像を作る・作り直す
```
python tools/office-images/1_cutout.py tamago          # 写真から作品を切り抜く（背景除去AIが必要）
python tools/office-images/2_place_in_rooms.py tamago  # 部屋を描いて作品を置く
python tools/aile-site/build_pages.py                  # 作品ページに反映
```
部屋の雰囲気は `2_place_in_rooms.py` の `SPECS`（作品ごとに1行）で変えます。部屋は写真を使わずプログラムで描いています。

### タイトルロゴを直す
`python tools/title-logo/make_title_logo.py` → `python tools/aile-site/build_pages.py`
（`tools/title-logo/preview_final.html` をブラウザで開くと確認できます）

### 作家の動画を差し替える
いまの動画は仮です（工房での作業の実写が無いため、作品映像と写真で編集）。
実写が届いたら `tools/artist-video/make_artist_loop.py` の `CLIPS` を差し替えて実行します。

---

## 公開の手順
```
python tools/check_links.py        # リンク切れが無いか確認
git add -A
git commit -m "変更内容"
git push                           # 1〜2分で https://ikeuchi-website.pages.dev/ に反映
```

## 注意
- `db_接続情報.txt` などの秘密ファイルはアップロードしない（`.gitignore` で除外済み）
- サイトは誰でも見られる状態です（Cloudflare Access による閲覧制限は未設定）
- Cloudflare Pages は 1ファイル25MBまで。大きい動画は YouTube に置いてリンクする
- 「オフィスに置いたら」は合成の参考イメージです（ページにもそう表記しています）
