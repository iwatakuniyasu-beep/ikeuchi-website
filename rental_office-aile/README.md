# パブリックアートレンタル アイエル（rental_office-aile）

鉄の作家・池内卓也の作品を、オフィス・イベント・ショールーム・ショーウィンドウにレンタルする提案サイトです。

```
rental_office-aile/
├─ index.html          案A・案Bを選ぶページ（手で編集）
├─ 01-entrance/        案A のトップ
├─ 02-workplace/       案B のトップ
├─ use01-entrance/     USE 01 本社エントランス        ★自動生成
├─ use02-event/        USE 02 周年・式典・採用イベント  ★自動生成
├─ use03-showroom/     USE 03 ショールーム            ★自動生成
├─ use04-showwindow/   USE 04 ショーウィンドウ        ★自動生成
├─ works/              作品ページ・作品リスト・作家ページ ★自動生成
├─ title/              タイトルロゴの部品              ★自動生成
└─ assets/             写真・合成画像・動画・CSS・JS
```

★自動生成 のものは `tools/aile-site/build_pages.py` が毎回作り直すので、直接は直しません。
文章や作品の情報を直す場所は、1つ上のフォルダの `README.md`「どこを直せば何が変わるか」を見てください。

案A・Bの `index.html` は、次の2か所だけプログラムが上書きします。それ以外（「買うより、借りる。」「来訪者の動線」「新着の作品」「お問い合わせ」など）は手で直してかまいません。
- `<!-- AILE-TOP:START -->` 〜 `<!-- AILE-TOP:END -->`：タイトル・四季の作品・作家・作品と受賞歴
- `<!-- AILE-ORDER:START -->` 〜 `<!-- AILE-ORDER:END -->`：リクエストオーダー
