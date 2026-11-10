"""パブリックアートレンタル アイエル（rental_office-aile）のページを作るプログラム。

data/ フォルダの表（CSV）を読み込んで、次のページを作り直します。
  - 案A・案B（01-entrance / 02-workplace）の上部（タイトル・四季の作品・作家・作品と受賞歴・リクエストオーダー）
    ※ <!-- AILE-TOP:START --> 〜 <!-- AILE-TOP:END --> の間だけを書き換えます。その下の部分は手で直してOKです。
  - 作品ページ（works/<slug>.html）、作家ページ（works/artist.html）、作品リスト（works/index.html）、works/work.css

使い方（Ikeuchi フォルダで）:
    python tools/aile-site/build_pages.py

作品を追加・修正するときは data/works.csv を直してから実行します（README.md 参照）。
works/ の HTML は毎回上書きされるので、直接は編集しないでください。
"""
import csv, pathlib, re, html, urllib.parse

ROOT = pathlib.Path(__file__).resolve().parents[2]      # Ikeuchi フォルダ
DATA = ROOT / "data"
SITE = "rental_office-aile"
W5 = ROOT / SITE
START, END = "<!-- AILE-TOP:START -->", "<!-- AILE-TOP:END -->"

# image roots, relative to a page one level below the site folder (<design>/ or works/)
NEW = "../../shared-media/2026-10_photos/"
OWN = "../assets/photo/"
POST = "../assets/poster/"

def e(s): return html.escape(s, quote=True)

def rel(p):
    """data/*.csv のパス（Ikeuchi フォルダからの相対）を、ページからの相対パスに変える"""
    p = p.strip()
    return "../" + p[len(SITE) + 1:] if p.startswith(SITE + "/") else "../../" + p

def read_csv(name):
    with open(DATA / name, encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))

# ---------------------------------------------------------------- works (data/works.csv)
# award: 受賞名 / place: 設置場所 / shown: 出品先 (used when there is neither award nor place)
WORKS = []
for r in read_csv("works.csv"):
    w = dict(slug=r["slug"].strip(), title=r["title"].strip(), year=r["year"].strip(), theme=r["theme"].strip() or "nature",
             photos=[rel(p) for p in r["photos"].split("|") if p.strip()])
    for k in ("award", "place", "shown", "text"):
        if r[k].strip():
            w[k] = r[k].strip()
    if r["film_url"].strip():
        w["film"] = (r["film_url"].strip(), r["film_vertical"].strip().lower() in ("yes", "y", "1", "はい"))
    WORKS.append(w)
BY = {w["slug"]: w for w in WORKS}

def note(w):
    """受賞タイトル、無ければ設置場所、どちらも無ければ出品先"""
    if w.get("award"): return ("受賞", w["award"])
    if w.get("place"): return ("設置", w["place"])
    return ("出品", w["shown"])

# ---------------------------------------------------------------- seasons (space ①, data/seasons.csv)
SEASONS = []
for r in read_csv("seasons.csv"):
    if not SEASONS or SEASONS[-1][0] != r["season_key"]:
        SEASONS.append((r["season_key"], r["season"], r["mood"], []))
    SEASONS[-1][3].append((r["slug"], rel(r["photo"])))

def tile(slug, img):
    w = BY[slug]; k, v = note(w)
    return (f'<a class="ai-tile" href="../works/{slug}.html"><img src="{img}" alt="{e(w["title"])}" loading="lazy">'
            f'<span class="ai-cap"><b>{e(w["title"])}</b><small>{e(v)}</small></span></a>')

def space1(rows):
    tracks = []
    for key, jp, mood, items in SEASONS:
        tiles = "".join(tile(s, i) for s, i in items)
        if rows == 1:
            inner = f'<div class="ai-row"><div class="ai-track">{tiles}{tiles}</div></div>'
        else:  # two rows moving in opposite directions
            a, b = items[:3] + items[3:], items[2:] + items[:2]
            ta, tb = "".join(tile(s, i) for s, i in a), "".join(tile(s, i) for s, i in b)
            inner = (f'<div class="ai-row"><div class="ai-track">{ta}{ta}</div></div>'
                     f'<div class="ai-row rev"><div class="ai-track">{tb}{tb}</div></div>')
        tracks.append(f'<div class="ai-season" data-season="{key}" data-mood="{e(mood)}"{"" if key == "spring" else " hidden"}>{inner}</div>')
    buttons = "".join(f'<button type="button" data-season="{k}" aria-pressed="{"true" if k == "spring" else "false"}">{jp}<small>{e(m)}</small></button>'
                      for k, jp, m, _ in SEASONS)
    return f'<div class="ai-space1" id="aile-top" aria-label="作品の画像（自動でスクロールします）">{"".join(tracks)}</div><div class="ai-seasons" role="group" aria-label="季節を選ぶ">{buttons}</div>'

# ---------------------------------------------------------------- career (space ②, data/career.csv)
CAREER = [(r["year"].strip(), r["text"].strip()) for r in read_csv("career.csv")]

def space2():
    career = "".join(f'<li><span class="y">{y or "─"}</span><span>{e(t)}</span></li>' for y, t in CAREER)
    cards = []
    for w in WORKS:
        k, v = note(w)
        kind = {"受賞": "a", "設置": "p", "出品": "s"}[k]
        if w["photos"]:
            thumb = f'<a class="ai-wthumb" href="../works/{w["slug"]}.html"><img src="{w["photos"][0]}" alt="{e(w["title"])}" loading="lazy"></a>'
            btn = f'<a class="ai-btn" href="../works/{w["slug"]}.html">作品ページ →</a>'
        else:
            thumb = '<span class="ai-wthumb ai-noimg">鉄</span>'
            btn = '<span class="ai-btn off">写真準備中</span>'
        cards.append(f'<article class="ai-wcard">{thumb}<div class="ai-winfo"><span class="ai-wy">{w["year"] or "年度確認中"}</span>'
                     f'<h4>{e(w["title"])}</h4><p><span class="ai-k ai-k-{kind}">{k}</span>{e(v)}</p>{btn}</div></article>')
    return f"""<div class="ai-space2" id="aile-career">
      <div class="ai-profile">
        <div class="ai-prof-text">
          <h2><a class="ai-name" href="../works/artist.html">作家　<span>池内卓也</span><em>作家ページへ →</em></a></h2>
          <p>溶接職人として鉄と向き合ってきた三十余年の技術で、彫刻をつくる作家。高知の工房で、一点ずつ手で仕上げています。</p>
          <a class="ai-making" href="../works/artist.html" aria-label="作家ページへ"><video src="../assets/video/artist-loop.mp4" poster="../assets/video/artist-loop-poster.jpg" autoplay muted loop playsinline preload="metadata"></video><span>IKEUCHI ／ IRON WORKS</span></a>
        </div>
        <ul class="ai-career">{career}</ul>
      </div>
      <div class="ai-works">
        <h3>作品と受賞歴<a class="ai-list" href="../works/index.html">作品リストを見る →</a></h3>
        <p class="ai-legend"><span class="ai-k ai-k-a">受賞</span>受賞タイトル　<span class="ai-k ai-k-p">設置</span>設置場所　<span class="ai-k ai-k-s">出品</span>出品した展覧会</p>
        <div class="ai-wgrid">{"".join(cards)}</div>
        <p class="ai-tnote">※ 作成年度が「確認中」の作品は調べています。写真の一部は公式サイト（iwatakuniyasu.wixsite.com/ikeuchi）掲載のものです。</p>
      </div>
    </div>"""


ORDER_STEPS = [
  ("ご相談・ヒアリング", "設置したい場所、目的（エントランスの顔、周年記念、来客へのおもてなし など）、時期、ご予算をうかがいます。"),
  ("現地の確認", "空間の広さ・天井の高さ・光の入り方・人の動線・見る人の目線の高さを確かめます。"),
  ("企画・デザインのご提案", "スケッチと、CG映像で「その場所に置いたらどう見えるか」をつくり、形・大きさ・色を一緒に決めます。"),
  ("制作", "高知の工房で、池内卓也が一点ずつ手で溶接して仕上げます。"),
  ("搬入・設置", "建物や営業の都合に合わせて日程を調整し、照明との相性も見ながら設置します。"),
  ("メンテナンス・移設", "設置後のお手入れや、改装・移転のときの取り外しと再設置もご相談いただけます。"),
]

def order():
    steps = "".join(f'<li><b>{i:02d}</b><h4>{e(t)}</h4><p>{e(d)}</p></li>' for i, (t, d) in enumerate(ORDER_STEPS, 1))
    subj = urllib.parse.quote("リクエストオーダーのご相談")
    body = urllib.parse.quote("パブリックアートレンタル アイエル 御中\n\nリクエストオーダー（オーダー制作）について相談したいです。\n\n【会社名】\n【設置したい場所】\n【目的・イメージ】\n【希望の時期】\n【ご予算の目安】\n【ご連絡先】\n")
    return f"""<div class="ai-order" id="aile-order">
      <div class="ai-order-head">
        <p class="ai-order-kick">REQUEST ORDER</p>
        <h2>リクエストオーダー<small>あなたの場所のための、一点を。</small></h2>
        <p>レンタル作品のほかに、設置する場所のために新しい作品を企画・制作する「リクエストオーダー」も承ります。会社の想いや場所の歴史をうかがい、その空間にしかない一点をつくります。</p>
      </div>
      <div class="ai-order-points">
        <div><h4>企画から設置まで一貫</h4><p>ご相談・デザイン・制作・設置まで、有限会社アイエル物産と作家が直接担当します。</p></div>
        <div><h4>完成前にCGで確認</h4><p>設置後の姿を先に映像で見てから制作に入るので、「イメージと違った」を防げます。</p></div>
        <div><h4>屋外にも置ける鉄</h4><p>美術館の入口、神社の参道、海岸、ワイナリーの庭など、屋外への設置実績があります。</p></div>
      </div>
      <div class="ai-order-cases">
        <figure><img src="{NEW}yusho-1.jpg" alt="湧昇の夢" loading="lazy"><figcaption>モニュメント<small>湧昇の夢（中土佐町立美術館）</small></figcaption></figure>
        <figure><div class="ai-pair"><img src="{POST}protect.jpg" alt="CGでの提案" loading="lazy"><img src="{OWN}protect-clean.jpg" alt="設置した実物" loading="lazy"></div><figcaption>CGで提案 → 実物に<small>守るべきもの（神社の参道）</small></figcaption></figure>
        <figure><img src="{NEW}gate-1.jpg" alt="ロートアイアンの門扉" loading="lazy"><figcaption>暮らしの鉄<small>ロートアイアンの門扉（施工例）</small></figcaption></figure>
      </div>
      <h3 class="ai-order-sub">ご依頼から設置までの流れ</h3>
      <ol class="ai-steps">{steps}</ol>
      <div class="ai-order-ideas">
        <h4>たとえば、こんなご依頼に</h4>
        <ul><li>本社エントランスのシンボル</li><li>創業・周年の記念モニュメント</li><li>会社のロゴや理念をモチーフにしたオブジェ</li><li>吹き抜け・中庭・公開空地のアート</li><li>門扉・フェンスなどのロートアイアン</li></ul>
      </div>
      <div class="ai-order-fee">
        <div><b>料金</b><span>打ち合わせのうえでお見積りします</span></div>
        <div><b>制作期間</b><span>打ち合わせのうえでご案内します</span></div>
        <p>作品の大きさ・設置場所・ご希望の時期をうかがってから決めます。まずはお気軽にご相談ください。</p>
      </div>
      <div class="ai-order-cta">
        <a class="ai-btn big" href="mailto:ilbussan@coral.ocn.ne.jp?subject={subj}&amp;body={body}">リクエストオーダーを相談する</a>
        <span>有限会社アイエル物産　TEL 0887-54-0711</span>
      </div>
    </div>"""

SCRIPT = """<script>
(function(){
  var root = document.querySelector('.ai-top');
  var seasons = root.querySelectorAll('.ai-season'), buttons = root.querySelectorAll('.ai-seasons button');
  function show(key){
    seasons.forEach(function(s){
      s.hidden = s.dataset.season !== key;
      // tiles slide into view by animation, which lazy loading does not notice: load the visible season up front
      if (!s.hidden) s.querySelectorAll('img').forEach(function(i){ i.loading = 'eager'; });
    });
    buttons.forEach(function(b){ b.setAttribute('aria-pressed', b.dataset.season === key); });
    root.dataset.season = key;
  }
  buttons.forEach(function(b){ b.addEventListener('click', function(){ show(b.dataset.season); }); });
  var m = new Date().getMonth() + 1;
  show(m >= 3 && m <= 5 ? 'spring' : m >= 6 && m <= 8 ? 'summer' : m >= 9 && m <= 11 ? 'autumn' : 'winter');
})();
</script>"""

# shared mechanics for space ① (each design adds its own look below)
BASE_CSS = """
  .ai-top{background:var(--ai-bg); color:var(--ai-fg); transition:background .6s; padding:0 !important;}
  .ai-top[data-season="spring"]{--ai-s:var(--ai-spring);} .ai-top[data-season="summer"]{--ai-s:var(--ai-summer);}
  .ai-top[data-season="autumn"]{--ai-s:var(--ai-autumn);} .ai-top[data-season="winter"]{--ai-s:var(--ai-winter);}
  .ai-head{max-width:1240px; margin:0 auto; padding:56px 28px 26px;}
  .ai-brand{font-family:var(--ai-font); font-weight:700; font-size:clamp(24px,7.4vw,64px); line-height:1.3; margin:0; letter-spacing:.02em;}
  .ai-brand .l1{display:inline-block;}
  .ai-brand .nm{display:inline-block; color:var(--ai-s, var(--ai-acc)); transition:color .6s;}
  /* iron title (案5-3): hand-cut seasonal motifs on a bent rod, on its own cream panel */
  .ai-brand.iron{font-size:0; line-height:0;}
  /* transparent and full-bleed: the iron wire runs to both screen edges; narrow screens crop the sides */
  .ai-top{overflow-x:clip;}
  .ai-ttl{display:block; width:100vw; margin-left:calc(50% - 50vw);}
  .ai-ttl svg.ttl{display:block; width:100%; height:max(150px, 12.5vw); overflow:hidden;}
  .ai-vh{position:absolute; width:1px; height:1px; overflow:hidden; clip:rect(0 0 0 0); white-space:nowrap;}
  .ai-sub{margin:12px 0 0; color:var(--ai-dim); font-size:15.5px;}
  @media (min-width:1180px){ .ai-sub{white-space:nowrap;} }  /* one line on wide screens */
  .ai-space1{overflow:hidden; padding:10px 0;}
  .ai-row{overflow:hidden;}
  .ai-track{display:flex; gap:var(--ai-gap,18px); width:max-content; animation:ai-scroll var(--ai-speed,46s) linear infinite;}
  .ai-row.rev .ai-track{animation-direction:reverse;}
  .ai-space1:hover .ai-track{animation-play-state:paused;}
  @keyframes ai-scroll{to{transform:translateX(calc(-50% - var(--ai-gap,18px) / 2));}}
  .ai-season[hidden]{display:none;}
  .ai-season{animation:ai-fade .6s ease;}
  @keyframes ai-fade{from{opacity:0;}}
  .ai-tile{position:relative; flex:none; display:block; overflow:hidden; color:#fff; text-decoration:none;}
  .ai-tile img{width:100%; height:100%; object-fit:cover; display:block; transition:transform .6s;}
  .ai-tile:hover img{transform:scale(1.05);}
  .ai-cap{position:absolute; left:0; right:0; bottom:0; padding:28px 14px 12px; background:linear-gradient(transparent, rgba(0,0,0,.65)); display:flex; flex-direction:column;}
  .ai-cap b{font-family:var(--ai-font); font-size:17px; font-weight:700;}
  .ai-cap small{font-size:12px; opacity:.9;}
  .ai-seasons{display:flex; justify-content:center; gap:12px; padding:22px 16px 10px; flex-wrap:wrap;}
  .ai-seasons button{cursor:pointer; font-family:var(--ai-font); font-size:24px; font-weight:700; line-height:1.2; display:flex; flex-direction:column; align-items:center; gap:2px; min-width:92px; padding:12px 18px; border:2px solid var(--ai-line); background:var(--ai-card); color:var(--ai-fg); transition:all .25s;}
  .ai-seasons button small{font-family:inherit; font-size:11.5px; font-weight:500; color:var(--ai-dim);}
  .ai-seasons button[aria-pressed="true"]{background:var(--ai-s, var(--ai-acc)); border-color:var(--ai-s, var(--ai-acc)); color:#fff;}
  .ai-seasons button[aria-pressed="true"] small{color:rgba(255,255,255,.9);}
  .ai-seasons button[data-season="spring"]{--ai-s:var(--ai-spring);} .ai-seasons button[data-season="summer"]{--ai-s:var(--ai-summer);}
  .ai-seasons button[data-season="autumn"]{--ai-s:var(--ai-autumn);} .ai-seasons button[data-season="winter"]{--ai-s:var(--ai-winter);}
  .ai-space2{max-width:1240px; margin:0 auto; padding:56px 28px 90px; display:grid; grid-template-columns:.8fr 1.2fr; gap:44px; align-items:start;}
  .ai-space2 > *{min-width:0;}
  .ai-profile h2{font-family:var(--ai-font); font-weight:700; font-size:clamp(24px,2.8vw,32px); margin:0 0 10px;}
  .ai-profile p{color:var(--ai-dim); margin:0 0 18px; font-size:15px;}
  .ai-career{list-style:none; margin:0; padding:0; border-top:2px solid var(--ai-fg); display:flex; flex-direction:column;}
  .ai-career li{flex:1; align-content:center; display:grid; grid-template-columns:62px 1fr; gap:10px; padding:10px 0; border-bottom:1px solid var(--ai-line); font-size:14px; line-height:1.6;}
  .ai-career .y{font-weight:700; color:var(--ai-acc);}
  .ai-works h3{font-family:var(--ai-font); font-weight:700; font-size:22px; margin:0 0 6px;}
  .ai-legend{font-size:12.5px; color:var(--ai-dim); margin:0 0 12px; display:flex; gap:6px; align-items:center; flex-wrap:wrap;}
  .ai-k{display:inline-block; font-size:11px; font-weight:700; padding:1px 7px; margin-right:6px; border-radius:4px; color:#fff; vertical-align:1px;}
  .ai-k-a{background:var(--ai-acc);} .ai-k-p{background:#2E7D5B;} .ai-k-s{background:#7A7F8C;}
  .ai-table-wrap{border:1px solid var(--ai-line); background:var(--ai-card);}
  .ai-table{width:100%; border-collapse:collapse; font-size:14px;}
  .ai-table th{white-space:nowrap; font-size:12.5px; text-align:left; padding:10px 12px; color:var(--ai-dim); border-bottom:2px solid var(--ai-line); font-weight:700;}
  .ai-table td{padding:8px 12px; border-bottom:1px solid var(--ai-line); vertical-align:middle;}
  .ai-table tr:last-child td{border-bottom:0;}
  .ai-y{font-weight:700; white-space:nowrap; width:64px;}
  .ai-t{display:flex; align-items:center; gap:10px; min-width:0;}
  .ai-t img,.ai-noimg{width:46px; height:46px; object-fit:cover; flex:none; border-radius:6px;}
  .ai-noimg{display:grid; place-items:center; background:var(--ai-line); color:var(--ai-dim); font-size:13px;}
  .ai-t b{font-family:var(--ai-font); font-size:16px;}
  .ai-b{text-align:right; white-space:nowrap;}
  .ai-btn{display:inline-block; font-size:12.5px; font-weight:700; padding:7px 12px; border-radius:30px; background:var(--ai-fg); color:var(--ai-bg); text-decoration:none; transition:background .2s;}
  .ai-btn:hover{background:var(--ai-acc);}
  .ai-btn.off{background:var(--ai-line); color:var(--ai-dim);}
  .ai-list{display:inline-block; vertical-align:middle; margin-left:14px; font-size:14px; font-weight:700; text-decoration:none; background:var(--ai-acc); color:#fff; padding:8px 16px; border-radius:30px; white-space:nowrap; box-shadow:0 4px 14px color-mix(in srgb, var(--ai-acc) 40%, transparent); transition:transform .2s;}
  .ai-list:hover{transform:translateX(4px);}
  .ai-name{text-decoration:none; color:inherit; display:inline-flex; flex-wrap:wrap; align-items:center; gap:4px 12px;}
  .ai-name span{background:linear-gradient(transparent 62%, color-mix(in srgb, var(--ai-acc) 45%, transparent) 62%); padding:0 2px;}
  .ai-name em{font-style:normal; font-size:14px; font-weight:700; letter-spacing:.02em; background:var(--ai-acc); color:#fff; padding:7px 14px; border-radius:30px; white-space:nowrap; transition:transform .2s, box-shadow .2s; box-shadow:0 4px 14px color-mix(in srgb, var(--ai-acc) 40%, transparent);}
  .ai-name:hover em{transform:translateX(4px);}
  .ai-name:hover span{color:var(--ai-acc);}
  .ai-making{position:relative; display:block; margin-top:18px; border-radius:18px; overflow:hidden; background:#000; aspect-ratio:16/9;}
  .ai-making video{display:block; width:100%; height:100%; object-fit:cover;}
  .ai-making span{position:absolute; left:12px; bottom:10px; color:#fff; font-size:11px; font-weight:700; letter-spacing:.12em; background:rgba(0,0,0,.45); padding:4px 10px; border-radius:20px;}
  .ai-tnote{font-size:12px; color:var(--ai-dim); margin:10px 0 0;}
  @media (max-width:900px){ .ai-space2{grid-template-columns:minmax(0,1fr); padding:40px 16px 70px;} .ai-head{padding:40px 16px 20px;} }
  @media (max-width:620px){
    .ai-table thead{display:none;}
    .ai-table, .ai-table tbody, .ai-table tr, .ai-table td{display:block;}
    .ai-table tr{display:grid; grid-template-columns:auto 1fr; gap:4px 12px; padding:12px; border-bottom:1px solid var(--ai-line);}
    .ai-table td{padding:0; border:0;}
    .ai-y{grid-column:1; grid-row:1 / span 2; align-self:start; padding-top:4px !important;}
    .ai-t{grid-column:2;} .ai-n{grid-column:2; font-size:13px;} .ai-b{grid-column:2; text-align:left;}
    .ai-seasons button{min-width:70px; font-size:20px; padding:10px 12px;}
  }
  @media (prefers-reduced-motion:reduce){ .ai-track{animation:none;} .ai-row{overflow-x:auto;} }

  /* space ②: artist first, then works as a 3-column card grid (2 on tablets, 1 on phones) */
  .ai-space2{display:block !important;}
  /* career rows spread out so the list ends level with the bottom of the making video */
  .ai-profile{display:grid; grid-template-columns:.9fr 1.1fr; gap:36px; align-items:stretch; margin-bottom:46px;}
  .ai-wgrid{display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:14px;}
  @media (max-width:1060px){ .ai-wgrid{grid-template-columns:repeat(2,minmax(0,1fr));} }
  .ai-wcard{display:grid; grid-template-columns:104px 1fr; gap:14px; align-items:center; background:var(--ai-card); border:1px solid var(--ai-line); border-radius:var(--ai-radius,16px); padding:12px;}
  .ai-wthumb{display:block; width:104px; height:104px; border-radius:calc(var(--ai-radius,16px) - 4px); overflow:hidden; background:var(--ai-line);}
  .ai-wthumb img{width:100%; height:100%; object-fit:cover; transition:transform .5s;}
  .ai-wcard:hover .ai-wthumb img{transform:scale(1.06);}
  .ai-wthumb.ai-noimg{display:grid; place-items:center; color:var(--ai-dim); font-size:18px;}
  .ai-winfo{min-width:0; display:flex; flex-direction:column; align-items:flex-start; gap:4px;}
  .ai-wy{font-size:12.5px; font-weight:700; color:var(--ai-acc);}
  .ai-winfo h4{margin:0; font-family:var(--ai-font); font-size:19px; line-height:1.35;}
  .ai-winfo p{margin:0; font-size:13.5px; color:var(--ai-dim); line-height:1.6;}
  .ai-winfo .ai-btn{margin-top:6px;}
  @media (max-width:900px){ .ai-profile{grid-template-columns:minmax(0,1fr); gap:16px;} }
  @media (max-width:700px){ .ai-wgrid{grid-template-columns:minmax(0,1fr);} .ai-wcard{grid-template-columns:96px 1fr;} .ai-wthumb{width:96px; height:96px;} }

  /* request order */
  .ai-order{max-width:1240px; margin:0 auto; padding:30px 28px 100px;}
  .ai-order-head{background:var(--ai-fg); color:var(--ai-bg); border-radius:var(--ai-radius,16px); padding:clamp(24px,4vw,48px);}
  .ai-order-kick{margin:0 0 6px; font-size:12.5px; font-weight:700; letter-spacing:.2em; color:var(--ai-acc2, #FFB27A);}
  .ai-order-head h2{font-family:var(--ai-font); font-weight:700; font-size:clamp(28px,4vw,46px); line-height:1.3; margin:0 0 12px;}
  .ai-order-head h2 small{display:block; font-size:.48em; font-weight:500; opacity:.85; margin-top:6px;}
  .ai-order-head p{margin:0; max-width:46em; opacity:.9; font-size:15.5px;}
  .ai-order-points{display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:14px; margin-top:16px;}
  .ai-order-points div{background:var(--ai-card); border:1px solid var(--ai-line); border-radius:var(--ai-radius,16px); padding:20px;}
  .ai-order-points h4{margin:0 0 6px; font-family:var(--ai-font); font-size:18px;}
  .ai-order-points p{margin:0; font-size:14px; color:var(--ai-dim);}
  .ai-order-cases{display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:14px; margin-top:16px;}
  .ai-order-cases figure{margin:0; background:var(--ai-card); border:1px solid var(--ai-line); border-radius:var(--ai-radius,16px); overflow:hidden;}
  .ai-order-cases img{width:100%; aspect-ratio:4/3; object-fit:cover;}
  .ai-pair{display:grid; grid-template-columns:1fr 1fr; gap:2px;}
  .ai-pair img{aspect-ratio:2/3;}
  .ai-order-cases figcaption{padding:12px 16px 14px; font-weight:700; font-family:var(--ai-font);}
  .ai-order-cases figcaption small{display:block; font-family:inherit; font-weight:500; font-size:12.5px; color:var(--ai-dim);}
  .ai-order-sub{font-family:var(--ai-font); font-size:22px; margin:44px 0 14px;}
  .ai-steps{list-style:none; margin:0; padding:0; display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:14px;}
  .ai-steps li{background:var(--ai-card); border:1px solid var(--ai-line); border-radius:var(--ai-radius,16px); padding:20px; position:relative;}
  .ai-steps b{display:inline-grid; place-items:center; width:40px; height:40px; border-radius:50%; background:var(--ai-acc); color:#fff; font-size:15px;}
  .ai-steps h4{margin:10px 0 4px; font-family:var(--ai-font); font-size:18px;}
  .ai-steps p{margin:0; font-size:14px; color:var(--ai-dim);}
  .ai-order-ideas{margin-top:28px; background:var(--ai-card); border:2px dashed var(--ai-line); border-radius:var(--ai-radius,16px); padding:20px 24px;}
  .ai-order-ideas h4{margin:0 0 8px; font-family:var(--ai-font); font-size:17px;}
  .ai-order-ideas ul{margin:0; padding:0; list-style:none; display:flex; flex-wrap:wrap; gap:8px;}
  .ai-order-ideas li{background:var(--ai-bg); border-radius:30px; padding:5px 14px; font-size:14px;}
  .ai-order-fee{margin-top:16px; display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:12px;}
  .ai-order-fee div{background:var(--ai-card); border:1px solid var(--ai-line); border-radius:var(--ai-radius,16px); padding:16px 20px; display:flex; flex-direction:column; gap:2px;}
  .ai-order-fee b{font-family:var(--ai-font); font-size:13px; color:var(--ai-acc);}
  .ai-order-fee span{font-family:var(--ai-font); font-size:18px; font-weight:700;}
  .ai-order-fee p{grid-column:1 / -1; margin:0; font-size:13.5px; color:var(--ai-dim);}
  @media (max-width:560px){ .ai-order-fee{grid-template-columns:minmax(0,1fr);} }
  .ai-order-cta{display:flex; align-items:center; gap:18px; flex-wrap:wrap; margin-top:26px;}
  .ai-btn.big{font-size:16px; padding:15px 28px;}
  .ai-order-cta span{font-size:13.5px; color:var(--ai-dim);}
  @media (max-width:900px){ .ai-order{padding:20px 16px 70px;} .ai-order-points,.ai-order-cases{grid-template-columns:minmax(0,1fr);} .ai-steps{grid-template-columns:repeat(2,minmax(0,1fr));} }
  @media (max-width:560px){ .ai-steps{grid-template-columns:minmax(0,1fr);} }

  /* phone version */
  .ai-tabbar{display:none;}
  @media (max-width:760px){
    .ai-tabbar{display:grid; grid-template-columns:repeat(4,1fr); position:fixed; left:10px; right:10px; bottom:calc(10px + env(safe-area-inset-bottom)); z-index:90;
      background:var(--ai-fg); border-radius:20px; padding:6px; box-shadow:0 10px 30px rgba(0,0,0,.25);}
    .ai-tabbar a{display:flex; flex-direction:column; align-items:center; gap:2px; padding:6px 2px; border-radius:14px; color:var(--ai-bg); text-decoration:none; font-size:11px; font-weight:700;}
    .ai-tabbar a.hot{background:var(--ai-acc); color:#fff;}
    .ai-tabbar svg{width:22px; height:22px; fill:none; stroke:currentColor; stroke-width:1.8; stroke-linecap:round; stroke-linejoin:round;}
    body{padding-bottom:92px;}
    .ai-seasons{display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:8px; padding:16px 12px 6px;}
    .ai-seasons button{min-width:0; padding:8px 2px; font-size:20px; flex-direction:column !important; gap:0 !important; align-items:center !important;}
    .ai-seasons button small{font-size:10px;}
    .ai-sub{font-size:14.5px;}
    .ai-tile{width:62vw !important;}
    .ai-order-cta{flex-direction:column; align-items:stretch; text-align:center;}
    .ai-btn.big{display:block; text-align:center;}
  }
"""

DESIGNS = {
  "01-entrance": dict(
    rows=1,
    fonts='<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Kiwi+Maru:wght@400;500&display=swap">',
    vars="--ai-bg:#FFF8F1; --ai-card:#FFFFFF; --ai-fg:#0F1B33; --ai-dim:#5E6677; --ai-line:#E9DED3; --ai-acc:#FF5A1F; --ai-font:'Kiwi Maru', serif; --ai-spring:#E86F8E; --ai-summer:#1E8FB8; --ai-autumn:#D2691E; --ai-winter:#4B6C9E; --ai-gap:18px; --ai-speed:48s;",
    css="""
  .ai-tile{width:clamp(220px,26vw,340px); aspect-ratio:3/4; border-radius:22px;}
  .ai-seasons button{border-radius:20px;}
  h1,h2,h3{font-family:'Kiwi Maru', serif !important; font-weight:500 !important;}
  .bar .logo, .bar nav a{white-space:nowrap;}
  @media (max-width:1440px){ .bar nav{display:none;} .bar{justify-content:space-between;} }
  .bar .btn{white-space:nowrap; flex:none;}
  @media (max-width:360px){ .bar .logo{font-size:12px !important;} .bar .btn{display:none;} }
  @media (max-width:560px){ .bar{padding:10px 14px; gap:10px;} .bar .logo{font-size:14px !important;} .bar .btn{padding:8px 12px; font-size:12px; white-space:nowrap; flex:none;} }
  .ai-top{--ai-radius:22px; --ai-acc2:#FFB27A;}
""",
    sub="鉄の作家・池内卓也の作品を、オフィスのエントランスや受付にレンタルでお届けします。季節ごとに作品を入れ替えて、毎日の景色に新しい出会いを。",
    hero_re=r'<header class="hero">.*?</header>',
    logo_re=(r'<span class="logo">IKEUCHI<span>\.</span> for OFFICE</span>', '<span class="logo" style="font-family:\'Kiwi Maru\',serif; font-weight:500">パブリックアートレンタル <span>アイエル</span></span>'),
    nav_re=('<nav><a href="#new">新着の作品</a>', '<nav><a href="#aile-top">四季の作品</a><a href="#aile-career">作家と作品</a><a href="#new">新着の作品</a>'),
    title=("<title>IKEUCHI for Offices</title>", "<title>パブリックアートレンタル アイエル｜オフィス向け 案A</title>"),
  ),
  "02-workplace": dict(
    rows=2,
    fonts="",
    vars="--ai-bg:#F1F4EE; --ai-card:#FFFFFF; --ai-fg:#1D2B24; --ai-dim:#5F6E66; --ai-line:#DCE3DA; --ai-acc:#1F4D3A; --ai-font:'Zen Maru Gothic', sans-serif; --ai-spring:#F07C9A; --ai-summer:#2BA4C8; --ai-autumn:#E08A3C; --ai-winter:#6A7FB5; --ai-gap:14px; --ai-speed:40s;",
    css="""
  .ai-top{background-image:radial-gradient(circle at 12% 18%, rgba(255,255,255,.7) 0 120px, transparent 121px), radial-gradient(circle at 88% 70%, rgba(242,193,78,.25) 0 160px, transparent 161px);}
  .ai-brand{font-weight:900;}
  .ai-space1{display:flex; flex-direction:column; gap:14px;}
  .ai-season{display:flex; flex-direction:column; gap:14px;}
  .ai-tile{width:clamp(180px,20vw,260px); aspect-ratio:1/1; border-radius:28px; border:6px solid #fff; box-shadow:0 10px 24px rgba(29,43,36,.12);}
  .ai-row:nth-child(1) .ai-tile:nth-child(odd){transform:rotate(-1.5deg);} .ai-row:nth-child(1) .ai-tile:nth-child(even){transform:rotate(1.5deg);}
  .ai-seasons button{border-radius:999px; flex-direction:row; gap:8px; align-items:baseline;}
  .ai-table-wrap{border-radius:22px; overflow:hidden;}
  .nav .logo, .nav nav a{white-space:nowrap;}
  @media (max-width:1440px){ .nav nav{display:none;} .nav{justify-content:space-between;} .nav .btn{margin-left:auto;} }
  .nav .btn{white-space:nowrap; flex:none;}
  .nav nav{flex-wrap:nowrap; min-width:0;}
  @media (max-width:360px){ .nav .logo{font-size:12px !important;} }
  @media (max-width:560px){ .nav{padding:8px 8px 8px 14px; gap:8px;} .nav .logo{font-size:14px;} .nav .btn{padding:8px 12px !important; font-size:12px !important; white-space:nowrap; flex:none;} }
  .ai-top{--ai-radius:26px; --ai-acc2:#F2C14E;}
""",
    sub="鉄の作家・池内卓也の作品を、オフィスにレンタル。季節のボタンを押すと、流れる作品が切り替わります。",
    hero_re=r'<section class="wrap hero">.*?</section>',
    logo_re=(r'<span class="logo">IKEUCHI<span>鉄</span></span>', '<span class="logo">パブリックアートレンタル <span>アイエル</span></span>'),
    nav_re=('<nav><a href="#new">新着の作品</a>', '<nav><a href="#aile-top">四季の作品</a><a href="#aile-career">作家と作品</a><a href="#new">新着の作品</a>'),
    title=("<title>IKEUCHI Workplace</title>", "<title>パブリックアートレンタル アイエル｜オフィス向け 案B</title>"),
  ),
}

# the iron title is generated by tools/title-logo/make_title_logo.py
TITLE_SVG = (W5 / "title" / "aile-title.svg.html").read_text(encoding="utf-8").strip()

def top_block(d):
    return f"""{START}
<section class="ai-top" data-season="spring">
  <div class="ai-head">
    <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Kiwi+Maru:wght@500&display=swap">
    <h1 class="ai-brand iron"><span class="ai-vh">パブリックアートレンタル アイエル</span><span class="ai-ttl">{TITLE_SVG}</span></h1>
    <p class="ai-sub">{e(d["sub"])}</p>
  </div>
  {space1(d["rows"])}
  {space2()}
  {order()}
</section>
<nav class="ai-tabbar" aria-label="スマホ用メニュー">
  <a href="#aile-top"><svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="5" width="18" height="14" rx="3"/><path d="M3 15l5-5 4 4 3-3 6 6"/></svg>作品</a>
  <a href="#aile-career"><svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="8" r="4"/><path d="M4 21c1.5-4 4.5-6 8-6s6.5 2 8 6"/></svg>作家</a>
  <a href="#aile-order"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 20l4-1 11-11-3-3L5 16z"/><path d="M14 6l3 3"/></svg>オーダー</a>
  <a href="#contact" class="hot"><svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="5" width="18" height="14" rx="3"/><path d="M3 7l9 6 9-6"/></svg>相談</a>
</nav>
{SCRIPT}
{END}"""

for name, d in DESIGNS.items():
    f = W5 / name / "index.html"
    src = f.read_text(encoding="utf-8")
    block = top_block(d)
    if START in src:
        src = re.sub(re.escape(START) + ".*?" + re.escape(END), lambda m: block, src, flags=re.S)
        fresh = f'<style id="ai-style">\n  .ai-top, .ai-tabbar{{{d["vars"]}}}\n{BASE_CSS}{d["css"]}</style>'
        src = re.sub(r'<style id="ai-style">.*?</style>', lambda m: fresh, src, count=1, flags=re.S)
    else:
        src = re.sub(d["hero_re"], lambda m: block, src, count=1, flags=re.S)
        style = f'{d["fonts"]}\n<style id="ai-style">\n  .ai-top, .ai-tabbar{{{d["vars"]}}}\n{BASE_CSS}{d["css"]}</style>\n</head>'
        src = src.replace("</head>", style, 1)
        src = re.sub(d["logo_re"][0], d["logo_re"][1], src, count=1)
        src = src.replace(d["nav_re"][0], d["nav_re"][1], 1)
        src = src.replace(*d["title"])
    f.write_text(src, encoding="utf-8", newline="\n")
    print(name, "top updated", "(rows=%d)" % d["rows"])

# ---------------------------------------------------------------- one page per work
PAGE = """<!doctype html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="robots" content="noindex, nofollow">
<title>{title}｜パブリックアートレンタル アイエル</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Zen+Maru+Gothic:wght@500;700;900&display=swap">
<link rel="stylesheet" href="work.css">
</head>
<body>
<header class="wk-bar"><a class="wk-logo" href="../01-entrance/index.html#aile-career">パブリックアートレンタル <span>アイエル</span></a><a class="wk-back" href="../01-entrance/index.html#aile-career" data-back>← 作品一覧へ戻る</a></header>
<main class="wk-main">
  <section class="wk-gallery">
    {main}
    {thumbs}
    {office}
  </section>
  <section class="wk-info">
    <p class="wk-kick"><a href="artist.html">作家　池内卓也 →</a></p>
    <h1>{title}</h1>
    <dl class="wk-facts">{facts}</dl>
    {text}
    {film}
    <div class="wk-cta">
      <a class="wk-btn" href="mailto:ilbussan@coral.ocn.ne.jp?subject={subj}&amp;body={body}">この作品のレンタルを相談する</a>
      <p>有限会社アイエル物産　TEL 0887-54-0711</p>
    </div>
  </section>
</main>
<nav class="wk-pager">{prev}<a href="index.html">作品リスト</a>{next}</nav>
<div class="wk-sticky"><a class="wk-sticky-main" href="mailto:ilbussan@coral.ocn.ne.jp?subject={subj}&amp;body={body}">この作品を相談する</a><a class="wk-sticky-tel" href="tel:0887540711" aria-label="電話する">電話</a></div>
<footer class="wk-foot">パブリックアートレンタル アイエル ／ 作品の写真の一部は公式サイト（iwatakuniyasu.wixsite.com/ikeuchi）掲載のものです。</footer>
<script src="../assets/js/lightbox.js"></script>
<script>
  // go back to the design the visitor came from (A or B); fall back to design A
  var ref = document.referrer, back = document.querySelectorAll('[data-back], .wk-logo');
  if (/\\/02-workplace\\//.test(ref)) back.forEach(function(a){{ a.href = a.href.replace('01-entrance', '02-workplace'); }});
</script>
</body>
</html>
"""

WORK_CSS = """*{box-sizing:border-box;}
html{overflow-x:clip;}
body{margin:0; background:#FFF8F1; color:#1E2230; font-family:'Zen Maru Gothic', sans-serif; font-weight:500; line-height:1.85; overflow-x:clip;}
img{display:block; max-width:100%;}
a{color:inherit;}
.wk-bar{display:flex; justify-content:space-between; align-items:center; gap:12px; padding:14px 24px; background:#fff; border-bottom:1px solid #EEE3D8; position:sticky; top:0; z-index:20;}
.wk-logo{font-weight:900; text-decoration:none; font-size:16px;}
.wk-logo span{color:#FF5A1F;}
.wk-back{font-size:13.5px; font-weight:700; text-decoration:none; background:#1E2230; color:#fff; padding:7px 14px; border-radius:30px; white-space:nowrap;}
.wk-main{max-width:1180px; margin:0 auto; padding:40px 24px 60px; display:grid; grid-template-columns:1.15fr .85fr; gap:44px; align-items:start;}
.wk-main > *{min-width:0;}
.wk-big{border-radius:26px; overflow:hidden; background:#000; aspect-ratio:4/3; cursor:zoom-in;}
.wk-big img{width:100%; height:100%; object-fit:cover;}
.wk-noimg{border-radius:26px; aspect-ratio:4/3; display:grid; place-items:center; background:#F1E6DA; color:#8a7d70; font-size:15px;}
.wk-thumbs{display:flex; gap:10px; margin-top:12px; overflow-x:auto;}
.wk-thumbs button{flex:none; width:96px; height:96px; padding:0; border:0; border-radius:16px; overflow:hidden; cursor:zoom-in; background:#000;}
.wk-thumbs img{width:100%; height:100%; object-fit:cover;}
.wk-office{margin:26px 0 0;}
.wk-office-img{border-radius:22px; overflow:hidden; aspect-ratio:16/10; background:#ddd; cursor:zoom-in;}
.wk-office-img img{width:100%; height:100%; object-fit:cover;}
.wk-office figcaption{margin-top:8px; font-size:13px; color:#8a7d70;}
.wk-office figcaption b{display:inline-block; margin-right:10px; color:#1E2230; background:#FFE6D8; padding:2px 10px; border-radius:20px;}
.wk-kick{margin:0; font-size:13px; font-weight:700; color:#FF5A1F;}
.wk-info h1{font-size:clamp(32px,4.4vw,52px); line-height:1.3; margin:6px 0 18px; font-weight:900;}
.wk-facts{margin:0 0 20px; display:grid; grid-template-columns:auto 1fr; gap:8px 16px; font-size:15px; border-top:2px solid #1E2230; padding-top:14px;}
.wk-facts dt{font-weight:700; color:#8a7d70;}
.wk-facts dd{margin:0;}
.wk-text{margin:0 0 18px; color:#4a4e5c;}
.wk-film{display:inline-flex; align-items:center; gap:8px; border:0; cursor:pointer; font-family:inherit; font-weight:700; font-size:15px; padding:12px 20px; border-radius:30px; background:#FFE6D8; color:#1E2230; margin-bottom:22px;}
.wk-cta{background:#fff; border:1px solid #EEE3D8; border-radius:22px; padding:20px;}
.wk-btn{display:block; text-align:center; text-decoration:none; background:#FF5A1F; color:#fff; font-weight:900; padding:15px; border-radius:40px;}
.wk-cta p{margin:10px 0 0; text-align:center; font-size:13px; color:#8a7d70;}
.wk-pager{max-width:1180px; margin:0 auto; padding:0 24px 40px; display:flex; justify-content:space-between; gap:12px;}
.wk-pager a{text-decoration:none; font-weight:700; font-size:14px; background:#fff; border:1px solid #EEE3D8; padding:10px 16px; border-radius:30px;}
.wk-foot{text-align:center; font-size:12px; color:#8a7d70; padding:0 16px 40px;}
@media (max-width:860px){ .wk-main{grid-template-columns:minmax(0,1fr); padding:24px 16px 40px; gap:24px;} .wk-bar{padding:12px 16px;} .wk-logo{font-size:14px;} }
.wk-sticky{display:none;}
@media (max-width:760px){
  .wk-sticky{display:flex; gap:8px; position:fixed; left:10px; right:10px; bottom:calc(10px + env(safe-area-inset-bottom)); z-index:90; background:#1E2230; padding:8px; border-radius:20px; box-shadow:0 10px 30px rgba(0,0,0,.25);}
  .wk-sticky a{text-decoration:none; font-weight:900; border-radius:14px; padding:12px; text-align:center;}
  .wk-sticky-main{flex:1; background:#FF5A1F; color:#fff;}
  .wk-sticky-tel{background:#fff; color:#1E2230; min-width:72px;}
  body{padding-bottom:90px;}
  .wk-back{font-size:12px; padding:6px 12px;}
  .wk-thumbs button{width:80px; height:80px;}
  .wk-pager a{font-size:13px;}
}
"""

out = W5 / "works"; out.mkdir(exist_ok=True)
paged = [w for w in WORKS if w["photos"]]
for i, w in enumerate(WORKS):
    if not w["photos"]:
        continue
    g = "wk-" + w["slug"]
    main = f'<div class="wk-big" data-lb="{w["photos"][0]}" data-lb-cap="{e(w["title"])}" data-lb-group="{g}"><img src="{w["photos"][0]}" alt="{e(w["title"])}"></div>'
    thumbs = ""
    if len(w["photos"]) > 1:
        thumbs = '<div class="wk-thumbs">' + "".join(
            f'<button type="button" data-lb="{p}" data-lb-cap="{e(w["title"])}" data-lb-group="{g}" aria-label="写真を拡大"><img src="{p}" alt="" loading="lazy"></button>' for p in w["photos"]) + "</div>"
    facts = [("作成年度", (w["year"] + "年") if w["year"] else "確認中")]
    if w.get("award"): facts.append(("受賞", w["award"]))
    if w.get("place"): facts.append(("設置場所", w["place"]))
    if w.get("shown") and not w.get("award"): facts.append(("出品", w["shown"]))
    facts_html = "".join(f"<dt>{k}</dt><dd>{e(v)}</dd>" for k, v in facts)
    text = f'<p class="wk-text">{e(w["text"])}</p>' if w.get("text") else ""
    film = ""
    if w.get("film"):
        url, portrait = w["film"]
        film = f'<button class="wk-film" type="button" data-lb="{url}" data-lb-type="youtube"{" data-lb-aspect=\"9/16\"" if portrait else ""} data-lb-cap="{e(w["title"])}">▶ 映像を見る（YouTube）</button>'
    k = paged.index(w)
    prev = f'<a href="{paged[k-1]["slug"]}.html">← {e(paged[k-1]["title"])}</a>' if k > 0 else "<span></span>"
    nxt = f'<a href="{paged[k+1]["slug"]}.html">{e(paged[k+1]["title"])} →</a>' if k < len(paged) - 1 else "<span></span>"
    subj = urllib.parse.quote(f"作品「{w['title']}」のレンタルについて")
    body = urllib.parse.quote(f"パブリックアートレンタル アイエル 御中\n\n作品「{w['title']}」のレンタルについて相談したいです。\n\n【会社名】\n【設置したい場所】\n【希望の時期・期間】\n【ご連絡先】\n")
    office = ""
    if (W5 / "assets" / "office" / f'{w["slug"]}.jpg').exists():
        o = f'../assets/office/{w["slug"]}.jpg'
        office = (f'<figure class="wk-office"><div class="wk-office-img" data-lb="{o}" data-lb-cap="{e(w["title"])}（オフィスに置いたイメージ）">'
                  f'<img src="{o}" alt="{e(w["title"])}をオフィスのエントランスに置いたイメージ" loading="lazy"></div>'
                  '<figcaption><b>オフィスに置いたら</b>エントランス・受付に設置したイメージです（写真を合成した参考イメージ）</figcaption></figure>')
    (out / f'{w["slug"]}.html').write_text(PAGE.format(title=e(w["title"]), main=main, thumbs=thumbs, office=office, facts=facts_html, text=text,
                                                       film=film, subj=subj, body=body, prev=prev, next=nxt), encoding="utf-8", newline="\n")
print("work pages:", len(paged), "->", out)

# ---------------------------------------------------------------- artist page (works/artist.html)
ARTIST_CSS = """
/* artist page */
.wk-kick a{text-decoration:none;}
.ar-hero{max-width:1180px; margin:0 auto; padding:40px 24px 10px;}
.ar-hero h1{font-size:clamp(40px,6vw,76px); line-height:1.15; margin:4px 0 4px; font-weight:900; letter-spacing:.04em;}
.ar-hero .ar-yomi{margin:0 0 22px; color:#8a7d70; font-weight:700; letter-spacing:.2em; font-size:14px;}
.ar-film{position:relative; border-radius:26px; overflow:hidden; background:#000; aspect-ratio:16/9;}
.ar-film video{display:block; width:100%; height:100%; object-fit:cover;}
.ar-film .ar-tag{position:absolute; left:16px; bottom:14px; color:#fff; font-size:12px; font-weight:700; letter-spacing:.12em; background:rgba(0,0,0,.45); padding:5px 12px; border-radius:20px;}
.ar-lead{max-width:1180px; margin:0 auto; padding:28px 24px 10px; font-size:clamp(17px,1.9vw,21px); line-height:2;}
.ar-sec{max-width:1180px; margin:0 auto; padding:44px 24px 10px;}
.ar-sec h2{font-size:clamp(22px,2.6vw,30px); font-weight:900; margin:0 0 18px; display:flex; align-items:center; gap:12px;}
.ar-sec h2::before{content:""; width:28px; height:4px; border-radius:4px; background:#FF5A1F;}
.ar-two{display:grid; grid-template-columns:1fr 1fr; gap:36px;}
.ar-two > *{min-width:0;}
.ar-line{list-style:none; margin:0; padding:0; border-top:2px solid #1E2230;}
.ar-line li{display:grid; grid-template-columns:5.5em 1fr; gap:14px; padding:12px 0; border-bottom:1px solid #EEE3D8; font-size:15px;}
.ar-line .y{font-weight:900; color:#FF5A1F;}
.ar-line small{color:#8a7d70;}
.ar-place{list-style:none; margin:0; padding:0; display:grid; grid-template-columns:repeat(auto-fill,minmax(300px,1fr)); gap:10px;}
.ar-place li a{display:flex; gap:14px; align-items:center; text-decoration:none; background:#fff; border:1px solid #EEE3D8; border-radius:18px; padding:10px; transition:border-color .2s;}
.ar-place li a:hover{border-color:#FF5A1F;}
.ar-place img{width:76px; height:76px; object-fit:cover; border-radius:12px; flex:none;}
.ar-place b{display:block; font-size:16px;}
.ar-place small{color:#8a7d70; font-size:13px;}
.ar-craft{display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:16px;}
.ar-craft div{background:#fff; border:1px solid #EEE3D8; border-radius:22px; padding:20px;}
.ar-craft b{display:block; font-size:30px; color:#FF5A1F; font-weight:900; line-height:1;}
.ar-craft h3{margin:10px 0 6px; font-size:17px;}
.ar-craft p{margin:0; font-size:14px; color:#4a4e5c;}
.ar-grid{display:grid; grid-template-columns:repeat(auto-fill,minmax(150px,1fr)); gap:12px;}
.ar-grid a{position:relative; display:block; aspect-ratio:1; border-radius:18px; overflow:hidden; background:#000; text-decoration:none;}
.ar-grid img{width:100%; height:100%; object-fit:cover; transition:transform .4s;}
.ar-grid a:hover img{transform:scale(1.06);}
.ar-grid span{position:absolute; left:0; right:0; bottom:0; padding:22px 10px 8px; color:#fff; font-weight:700; font-size:13px; background:linear-gradient(transparent,rgba(0,0,0,.7));}
.ar-more{margin-left:auto; font-size:14px; font-weight:700; text-decoration:none; background:#FF5A1F; color:#fff; padding:8px 16px; border-radius:30px; white-space:nowrap;}
.ar-films{display:flex; flex-wrap:wrap; gap:10px;}
.ar-films .wk-film{margin:0;}
.ar-studio{background:#1E2230; color:#fff; border-radius:26px; padding:28px; display:grid; grid-template-columns:1fr auto; gap:20px; align-items:center;}
.ar-studio h3{margin:0 0 6px; font-size:20px;}
.ar-studio p{margin:0; font-size:14px; line-height:1.9; color:#d9dbe3;}
.ar-studio a{color:#fff;}
.ar-studio .wk-btn{padding:15px 26px;}
@media (max-width:860px){
  .ar-hero, .ar-lead, .ar-sec{padding-left:16px; padding-right:16px;}
  .ar-two, .ar-studio, .ar-craft{grid-template-columns:minmax(0,1fr);}
  .ar-place{grid-template-columns:minmax(0,1fr);}
  .ar-film{border-radius:18px;}
}
"""

CRAFT = [
  ("01", "溶接の技術", "溶接職人として三十余年。高知県の溶接コンクールで2度入賞した技術が、作品の土台になっています。"),
  ("02", "鉄を切り、曲げ、編む", "鉄板の切り抜き、手で曲げた鉄の棒、細い鉄の帯を編んだ球体。鉄のさまざまな表情を一つの作品にまとめます。"),
  ("03", "置かれる場所まで考える", "美術館の入口、ワイナリーの庭、神社の参道、波打ちぎわ。光や風景との関係まで考えてつくります。"),
]

ARTIST_PAGE = """<!doctype html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="robots" content="noindex, nofollow">
<title>作家 池内卓也｜パブリックアートレンタル アイエル</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Zen+Maru+Gothic:wght@500;700;900&display=swap">
<link rel="stylesheet" href="work.css">
</head>
<body>
<header class="wk-bar"><a class="wk-logo" href="../01-entrance/index.html">パブリックアートレンタル <span>アイエル</span></a><a class="wk-back" href="../01-entrance/index.html#aile-career" data-back>← トップへ戻る</a></header>
<section class="ar-hero">
  <p class="wk-kick">IRON SCULPTOR</p>
  <h1>池内卓也</h1>
  <p class="ar-yomi">いけうち たくや ／ 鉄の彫刻家・高知</p>
  <div class="ar-film"><video src="../assets/video/artist-loop.mp4" poster="../assets/video/artist-loop-poster.jpg" autoplay muted loop playsinline preload="auto" aria-label="池内卓也の作品の映像"></video><span class="ar-tag">IKEUCHI ／ IRON WORKS</span></div>
</section>
<p class="ar-lead">高知県香南市生まれ。生家の鉄工所で溶接職人として鉄と向き合い、門扉やフェンス、植物園のガーデンアイテムをつくってきました。その三十余年の技術で、いまは鉄の彫刻をつくっています。錆びた鉄板の葉、手で曲げた鉄の棒、細い鉄の帯を編んだ卵。高知の工房で、一点ずつ手で仕上げています。</p>
<section class="ar-sec">
  <h2>鉄とものづくり</h2>
  <div class="ar-craft">{craft}</div>
</section>
<section class="ar-sec ar-two">
  <div><h2>経歴</h2><ul class="ar-line">{career}</ul></div>
  <div><h2>主な受賞</h2><ul class="ar-line">{awards}</ul></div>
</section>
<section class="ar-sec">
  <h2>作品が置かれている場所</h2>
  <ul class="ar-place">{places}</ul>
</section>
<section class="ar-sec">
  <h2>作品 <a class="ar-more" href="index.html">作品リストを見る →</a></h2>
  <div class="ar-grid">{grid}</div>
</section>
<section class="ar-sec">
  <h2>映像作品</h2>
  <div class="ar-films">{films}</div>
</section>
<section class="ar-sec" style="padding-bottom:50px">
  <div class="ar-studio">
    <div><h3>有限会社アイエル物産</h3><p>高知県香南市野市町土居1073-2<br>TEL <a href="tel:0887540711">0887-54-0711</a>　FAX 0887-54-0712<br><a href="mailto:ilbussan@coral.ocn.ne.jp">ilbussan@coral.ocn.ne.jp</a></p></div>
    <a class="wk-btn" href="mailto:ilbussan@coral.ocn.ne.jp?subject={subj}&amp;body={body}">作品について相談する</a>
  </div>
</section>
<div class="wk-sticky"><a class="wk-sticky-main" href="mailto:ilbussan@coral.ocn.ne.jp?subject={subj}&amp;body={body}">作品について相談する</a><a class="wk-sticky-tel" href="tel:0887540711" aria-label="電話する">電話</a></div>
<footer class="wk-foot">パブリックアートレンタル アイエル ／ 作品の写真の一部は公式サイト（iwatakuniyasu.wixsite.com/ikeuchi）掲載のものです。</footer>
<script src="../assets/js/lightbox.js"></script>
<script>
  // go back to the design the visitor came from (A or B); fall back to design A
  var ref = document.referrer, back = document.querySelectorAll('[data-back], .wk-logo');
  if (/\\/02-workplace\\//.test(ref)) back.forEach(function(a){{ a.href = a.href.replace('01-entrance', '02-workplace'); }});
</script>
</body>
</html>
"""

def artist_page():
    career = "".join(f'<li><span class="y">{y or "─"}</span><span>{e(t)}</span></li>' for y, t in CAREER)
    awards = "".join(f'<li><span class="y">{w["year"]}</span><span>{e(w["award"])}<br><small>作品「{e(w["title"])}」</small></span></li>'
                     for w in sorted((w for w in WORKS if w.get("award")), key=lambda w: w["year"]))
    places = "".join(f'<li><a href="{w["slug"]}.html"><img src="{w["photos"][0]}" alt="" loading="lazy"><span><b>{e(w["title"])}</b><small>{e(w["place"])}</small></span></a></li>'
                     for w in WORKS if w.get("place") and w["photos"])
    craft = "".join(f'<div><b>{n}</b><h3>{e(t)}</h3><p>{e(d)}</p></div>' for n, t, d in CRAFT)
    grid = "".join(f'<a href="{w["slug"]}.html"><img src="{w["photos"][0]}" alt="" loading="lazy"><span>{e(w["title"])}</span></a>' for w in WORKS if w["photos"])
    films = "".join(f'<button class="wk-film" type="button" data-lb="{w["film"][0]}" data-lb-type="youtube"'
                    + (' data-lb-aspect="9/16"' if w["film"][1] else "")
                    + f' data-lb-cap="{e(w["title"])}">▶ {e(w["title"])}</button>' for w in WORKS if w.get("film"))
    subj = urllib.parse.quote("作家・池内卓也の作品について")
    body = urllib.parse.quote("パブリックアートレンタル アイエル 御中\n\n作品のレンタル・制作について相談したいです。\n\n【会社名】\n【設置したい場所】\n【希望の時期・期間】\n【ご連絡先】\n")
    return ARTIST_PAGE.format(craft=craft, career=career, awards=awards, places=places, grid=grid, films=films, subj=subj, body=body)

(out / "artist.html").write_text(artist_page(), encoding="utf-8", newline="\n")
print("artist page ->", out / "artist.html")

# ---------------------------------------------------------------- work catalogue (works/index.html)
THEMES = [("nature", "植物・自然"), ("form", "卵・かたち"), ("human", "人・顔"), ("color", "色・モニュメント")]

CATALOG_CSS = """
/* work catalogue */
.ct-head{max-width:1180px; margin:0 auto; padding:40px 24px 8px;}
.ct-head h1{font-size:clamp(30px,4.4vw,50px); font-weight:900; margin:4px 0 8px;}
.ct-head p{margin:0; color:#4a4e5c;}
.ct-tools{position:sticky; top:57px; z-index:15; background:rgba(255,248,241,.94); backdrop-filter:blur(6px); border-bottom:1px solid #EEE3D8;}
.ct-tools-in{max-width:1180px; margin:0 auto; padding:12px 24px; display:flex; flex-wrap:wrap; gap:8px; align-items:center;}
.ct-chip{border:1px solid #E2D6C9; background:#fff; color:#1E2230; font-family:inherit; font-weight:700; font-size:14px; padding:8px 16px; border-radius:30px; cursor:pointer;}
.ct-chip[aria-pressed="true"]{background:#1E2230; color:#fff; border-color:#1E2230;}
.ct-chip small{font-weight:500; opacity:.7; margin-left:4px;}
.ct-toggle{margin-left:auto; display:flex; align-items:center; gap:8px; font-size:14px; font-weight:700; cursor:pointer;}
.ct-toggle input{width:18px; height:18px; accent-color:#FF5A1F;}
.ct-count{max-width:1180px; margin:0 auto; padding:16px 24px 0; font-size:13px; color:#8a7d70;}
.ct-grid{max-width:1180px; margin:0 auto; padding:12px 24px 60px; display:grid; grid-template-columns:repeat(auto-fill,minmax(250px,1fr)); gap:20px;}
.ct-card{background:#fff; border:1px solid #EEE3D8; border-radius:22px; overflow:hidden; display:flex; flex-direction:column; transition:box-shadow .25s, transform .25s;}
.ct-card:hover{box-shadow:0 14px 34px rgba(30,34,48,.12); transform:translateY(-3px);}
.ct-card[hidden]{display:none;}
.ct-img{position:relative; display:block; aspect-ratio:4/3; background:#F1E6DA; overflow:hidden;}
.ct-img img{position:absolute; inset:0; width:100%; height:100%; object-fit:cover; transition:opacity .45s, transform .6s;}
.ct-img .ct-alt{opacity:0;}
.ct-card:hover .ct-img .ct-alt{opacity:1;}
.ct-card:hover .ct-img img{transform:scale(1.04);}
.ct-img .ct-none{position:absolute; inset:0; display:grid; place-items:center; color:#8a7d70; font-size:14px;}
.ct-no{position:absolute; left:10px; top:10px; background:rgba(30,34,48,.82); color:#fff; font-size:11px; font-weight:700; letter-spacing:.08em; padding:4px 10px; border-radius:20px;}
.ct-off{position:absolute; right:10px; top:10px; background:#FF5A1F; color:#fff; font-size:11px; font-weight:700; padding:4px 10px; border-radius:20px;}
.ct-body{padding:14px 16px 16px; display:flex; flex-direction:column; gap:6px; flex:1;}
.ct-theme{font-size:12px; font-weight:700; color:#FF5A1F;}
.ct-body h2{margin:0; font-size:20px; font-weight:900; line-height:1.4;}
.ct-note{margin:0; font-size:13px; color:#4a4e5c;}
.ct-spec{margin:4px 0 0; display:grid; grid-template-columns:auto 1fr; gap:2px 12px; font-size:13px; border-top:1px dashed #E2D6C9; padding-top:8px;}
.ct-spec dt{color:#8a7d70; font-weight:700;}
.ct-spec dd{margin:0;}
.ct-btns{margin-top:auto; padding-top:10px; display:flex; gap:8px;}
.ct-btns a{flex:1; text-align:center; text-decoration:none; font-weight:900; font-size:14px; padding:10px; border-radius:30px;}
.ct-more{background:#1E2230; color:#fff;}
.ct-ask{background:#FFE6D8; color:#1E2230;}
.ct-btns .off{background:#EEE3D8; color:#8a7d70; pointer-events:none;}
.ct-foot-note{max-width:1180px; margin:0 auto; padding:0 24px 40px; font-size:13px; color:#8a7d70;}
@media (max-width:760px){
  .ct-head, .ct-count, .ct-grid, .ct-foot-note{padding-left:16px; padding-right:16px;}
  .ct-tools{top:53px;} .ct-tools-in{padding:10px 16px; flex-wrap:nowrap; overflow-x:auto;}
  .ct-chip{flex:none; font-size:13px; padding:7px 13px;}
  .ct-toggle{flex:none; margin-left:8px; font-size:13px; white-space:nowrap;}
  .ct-grid{grid-template-columns:repeat(2,minmax(0,1fr)); gap:12px;}
  .ct-body{padding:10px 12px 12px;} .ct-body h2{font-size:16px;} .ct-note{font-size:12px;}
  .ct-spec{font-size:12px; grid-template-columns:minmax(0,1fr);} .ct-spec dd{margin-bottom:4px;}
  .ct-btns{flex-direction:column; gap:6px;} .ct-btns a{font-size:13px; padding:8px;}
}
"""

CATALOG_PAGE = """<!doctype html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="robots" content="noindex, nofollow">
<title>作品リスト｜パブリックアートレンタル アイエル</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Zen+Maru+Gothic:wght@500;700;900&display=swap">
<link rel="stylesheet" href="work.css">
</head>
<body>
<header class="wk-bar"><a class="wk-logo" href="../01-entrance/index.html">パブリックアートレンタル <span>アイエル</span></a><a class="wk-back" href="../01-entrance/index.html#aile-career" data-back>← トップへ戻る</a></header>
<section class="ct-head">
  <p class="wk-kick"><a href="artist.html">作家　池内卓也 →</a></p>
  <h1>作品リスト</h1>
  <p>レンタル・ご購入をご相談いただける作品の一覧です。写真にカーソルを合わせると（スマホは「詳しく見る」から）、オフィスに置いたイメージをご覧いただけます。</p>
</section>
<div class="ct-tools"><div class="ct-tools-in" role="group" aria-label="テーマで絞り込む">
  {chips}
  <label class="ct-toggle"><input type="checkbox" id="ct-office"> オフィスのイメージあり</label>
</div></div>
<p class="ct-count" id="ct-count" aria-live="polite"></p>
<div class="ct-grid" id="ct-grid">{cards}</div>
<p class="ct-foot-note">※ サイズ・レンタル料金・制作期間は、作品と設置場所に合わせてお見積もりします。「オフィスに置いたイメージ」は写真を合成した参考イメージです。</p>
<div class="wk-sticky"><a class="wk-sticky-main" href="mailto:ilbussan@coral.ocn.ne.jp?subject={subj}&amp;body={body}">作品について相談する</a><a class="wk-sticky-tel" href="tel:0887540711" aria-label="電話する">電話</a></div>
<footer class="wk-foot">パブリックアートレンタル アイエル ／ 有限会社アイエル物産　TEL 0887-54-0711 ／ 作品の写真の一部は公式サイト（iwatakuniyasu.wixsite.com/ikeuchi）掲載のものです。</footer>
<script>
  // theme chips + "has office image" toggle
  (function(){{
    var chips = document.querySelectorAll('.ct-chip'), cards = document.querySelectorAll('.ct-card'),
        office = document.getElementById('ct-office'), count = document.getElementById('ct-count'), theme = 'all';
    function apply(){{
      var n = 0;
      cards.forEach(function(c){{
        var show = (theme === 'all' || c.dataset.theme === theme) && (!office.checked || c.dataset.office === '1');
        c.hidden = !show; if (show) n++;
      }});
      count.textContent = n + ' 点の作品';
    }}
    chips.forEach(function(b){{ b.addEventListener('click', function(){{
      theme = b.dataset.theme; chips.forEach(function(x){{ x.setAttribute('aria-pressed', x === b ? 'true' : 'false'); }}); apply();
    }}); }});
    office.addEventListener('change', apply); apply();
  }})();
  // go back to the design the visitor came from (A or B); fall back to design A
  var ref = document.referrer, back = document.querySelectorAll('[data-back], .wk-logo');
  if (/\\/02-workplace\\//.test(ref)) back.forEach(function(a){{ a.href = a.href.replace('01-entrance', '02-workplace'); }});
</script>
</body>
</html>
"""

def catalog_page():
    names = dict(THEMES)
    cards = []
    for i, w in enumerate(WORKS, 1):
        slug, t = w["slug"], w["theme"]
        has_off = (W5 / "assets" / "office" / f"{slug}.jpg").exists()
        if w["photos"]:
            img = f'<img src="{w["photos"][0]}" alt="{e(w["title"])}" loading="lazy">'
            if has_off:
                img += f'<img class="ct-alt" src="../assets/office/{slug}.jpg" alt="" loading="lazy">'
            media = f'<a class="ct-img" href="{slug}.html">{img}<span class="ct-no">No.{i:02d}</span>{"<span class=ct-off>オフィスのイメージ</span>" if has_off else ""}</a>'
            more = f'<a class="ct-more" href="{slug}.html">詳しく見る</a>'
        else:
            media = f'<span class="ct-img"><span class="ct-none">写真準備中</span><span class="ct-no">No.{i:02d}</span></span>'
            more = '<a class="ct-more off" aria-disabled="true">準備中</a>'
        k, v = note(w)
        subj = urllib.parse.quote(f"作品「{w['title']}」について")
        body = urllib.parse.quote(f"パブリックアートレンタル アイエル 御中\n\n作品「{w['title']}」（No.{i:02d}）について相談したいです。\n\n【レンタル／購入】\n【会社名】\n【設置したい場所】\n【希望の時期・期間】\n【ご連絡先】\n")
        cards.append(f'<article class="ct-card" data-theme="{t}" data-office="{1 if has_off else 0}">{media}<div class="ct-body">'
                     f'<span class="ct-theme">{names[t]}</span><h2>{e(w["title"])}</h2>'
                     f'<p class="ct-note">{k}：{e(v)}</p>'
                     f'<dl class="ct-spec"><dt>制作年</dt><dd>{(w["year"] + "年") if w["year"] else "確認中"}</dd><dt>素材</dt><dd>鉄など</dd>'
                     f'<dt>サイズ</dt><dd>ご相談</dd><dt>レンタル料</dt><dd>お見積もり</dd></dl>'
                     f'<div class="ct-btns">{more}<a class="ct-ask" href="mailto:ilbussan@coral.ocn.ne.jp?subject={subj}&amp;body={body}">相談する</a></div>'
                     f'</div></article>')
    total = len(WORKS)
    chips = f'<button type="button" class="ct-chip" data-theme="all" aria-pressed="true">すべて<small>{total}</small></button>' + "".join(
        f'<button type="button" class="ct-chip" data-theme="{k}" aria-pressed="false">{n}<small>{sum(1 for w in WORKS if w["theme"] == k)}</small></button>' for k, n in THEMES)
    subj = urllib.parse.quote("作品リストを見て相談したいです")
    body = urllib.parse.quote("パブリックアートレンタル アイエル 御中\n\n作品リストを見て相談したいです。\n\n【気になる作品】\n【会社名】\n【設置したい場所】\n【ご連絡先】\n")
    return CATALOG_PAGE.format(chips=chips, cards="".join(cards), subj=subj, body=body)

(out / "work.css").write_text(WORK_CSS + ARTIST_CSS + CATALOG_CSS, encoding="utf-8", newline="\n")
(out / "index.html").write_text(catalog_page(), encoding="utf-8", newline="\n")
print("catalogue ->", out / "index.html")
