# IKEUCHI 鉄彫刻 販売サイト（5案）

高級マンションのエントランス、会員制クラブ・ラウンジなどへの設置提案を目的とした、
鉄の彫刻家 IKEUCHI 氏の作品販売用ランディングページです。デザインの異なる5案を用意しました。

## フォルダ構成

```
website/
├── index.html              ← 5案を見比べるための一覧ページ（まずこれを開く）
├── 01-obsidian/index.html   ← 案1: OBSIDIAN（漆黒×真鍮、ギャラリー/建築系）
├── 02-ember/index.html      ← 案2: EMBER（炭×琥珀、鍛冶場の熱を感じる劇的な世界観）
├── 03-washi/index.html      ← 案3: WASHI（生成り×墨×朱、和の間・侘寂）
├── 04-atelier/index.html    ← 案4: ATELIER（雑誌的エディトリアル、ギャラリー作家として提示）
├── 05-noir-royale/index.html← 案5: NOIR ROYALE（濃紺×銀、デベロッパー/法人向けB2B提案書スタイル）
└── assets/
    ├── video/
    │   ├── hero/            ← 各ページの背景ループ動画（無音・テキストなし・軽量）
    │   └── films/           ← フル尺のブランド映像（CG→実写の証明カット入り、再生ボタン付き）
    ├── poster/              ← 動画のポスター（サムネイル）静止画
    ├── photo/               ← 作品写真（Gallery / Functional Iron セクションで使用）
    ├── gallery.css          ← 写真セクションとライトボックスの共通スタイル（5案共通）
    ├── gallery.js           ← 写真クリックで拡大表示するライトボックス（5案共通）
    └── img/                 ← その他画像（現状空。ロゴ等を追加する場合はここに）
```

## 写真セクション（Gallery）

全5案の「Collection」の直後に、次の2セクションを追加しています（ナビの「Gallery」から移動できます）。

| セクション | 作品 | 写真ファイル |
|---|---|---|
| Works in Iron (`#gallery`) | Flower & Stone（錆鉄の花と石） | rust-flower.jpg, rust-flower-detail.jpg |
| | Rebar Tree（鉄筋の木） | rebar-tree.jpg, rebar-tree-2.jpg, rebar-tree-sky.jpg |
| | Museum Monument（中土佐町立美術館） | museum-monument.jpg |
| Functional Iron (`#functional`) | Tree Hanger（木のハンガー） | tree-hanger-nursery.jpg, tree-hanger-office.jpg |
| | Leaf Bench（ベンチ） | leaf-bench.jpg, leaf-bench-2.jpg |
| | Garden Store（収納庫） | garden-shed.jpg |

- 作品名（英語）は仮のものです。正式な作品名があれば各HTML内の `<h3>` を書き換えてください。
- Functional Iron の写真には「Placement image（設置イメージ）」のラベルを付けています。
  実際の納品・設置写真であれば、該当箇所の `pf-badge` を `pf-badge real` に、文言を "Photographed" 等に変更してください。
- 写真を追加する場合は `assets/photo/` に置き、既存の `<article class="pf-work">` をコピーしてパスを書き換えます。

## 動画素材について

`C:\tmp\Ikeuchi\movie` 内の7本の元動画（1本あたり最大300MB超）から、Web用に軽量化した
バージョンをこの `assets` フォルダ内に自動生成しています。元動画は一切変更していません。

| 元動画 | 内容 | 使用箇所 |
|---|---|---|
| まもるべきもの.mp4 | CG(雪山+満月) → 実写(神社参道に設置された実物) | protect |
| 問うVer3.mp4 | CG(鏡面砂漠) → 実写(海岸に設置された実物) | question |
| 植物.mp4 | CG(雪の森) → 実写(竹林の庭園に設置された実物) | plant |
| 炎.mp4 | CG(教会堂内の炎のオブジェ) | fire（コンセプト/受注制作） |
| 白卵_0119.mp4 | CG(海辺の草原の白い卵) | white-egg（コンセプト/受注制作） |
| 地面炎30Sec_2.mp4 | CG(炎上する砂漠) | inquire-fire（コンセプト映像） |
| Video1.mp4 | CG(鏡面砂漠の器状オブジェ) | leaf-dream（コンセプト映像） |

「実写あり」の3作品＝すでに実在し設置実績のある作品、「コンセプトのみ」の3作品＝
CG映像で先に空間イメージを見せた上で受注制作するオーダーメイド作品、という2本立ての
ストーリーを全5サイトで共通して使っています。

## 更新のしかた

- **文章を直す**: 各 `xx-xxxx/index.html` を開き、該当箇所のテキストをそのまま書き換えるだけです。
  ビルドツールは使っていないので、保存してブラウザで開き直せばすぐ反映されます。
- **動画・写真を差し替える**: `assets/video/hero`・`assets/video/films`・`assets/poster` の中の
  同名ファイルを新しいものに置き換えてください（5サイトすべてに反映されます）。
  ファイル名を変える場合は、各HTML内の `<source src="...">` と `poster="..."` のパスも合わせて変更してください。
- **新しい動画を元素材から作り直したい場合**: `C:\tmp\Ikeuchi\movie` に動画を追加し、
  ffmpeg（`pip install imageio-ffmpeg` で取得可能）で 1280px幅・H.264に変換して
  `assets/video/hero` または `assets/video/films` に保存してください。
- **問い合わせ先**: 現状、有限会社アイエル物産の実際の連絡先（住所・電話・メール）を
  掲載しています。変更する場合は各HTML内の "Contact" セクションを検索してください。

## 見るときの注意

- ダブルクリックで直接 `index.html` を開いても閲覧できますが、一部ブラウザでは
  ローカルファイルの動画自動再生がブロックされることがあります。その場合はページ内の
  再生ボタンを押すか、フォルダを右クリックして「ターミナルで開く」→
  `python -m http.server 8000` を実行し `http://localhost:8000` で見てください。
