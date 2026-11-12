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
NEW = "../assets/photo/2026-10_"
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
CAREER = [(r["year"].strip(), r["text"].strip()) for r in read_csv("career.csv")]            # 作家ページ：全部
CAREER_TOP = [(r["year"].strip(), r["text"].strip()) for r in read_csv("career.csv") if (r.get("top") or "").strip().lower() in ("yes", "y", "1", "はい")]   # 案A・B：top=yes の行だけ（動画と高さをそろえる）

def space2():
    career = "".join(f'<li><span class="y">{y or "─"}</span><span>{e(t)}</span></li>' for y, t in CAREER_TOP)
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
          <p>鉄芸家・エクステリアプランナー。生家の鉄工所で磨いた溶接の技術で、門扉やガーデンの鉄製品から彫刻までを手がける。高知県展 特選、新象展 大阪府知事賞ほか受賞。高知の工房で、一点ずつ手で仕上げています。</p>
          <a class="ai-making" href="../works/artist.html" aria-label="作家ページへ"><video src="../assets/video/artist-loop.mp4" poster="../assets/video/artist-loop-poster.jpg" autoplay muted loop playsinline preload="metadata"></video><span>IKEUCHI ／ IRON WORKS</span></a>
        </div>
        <ul class="ai-career">{career}</ul>
      </div>
      <div class="ai-works">
        <h3>作品と受賞歴<a class="ai-list" href="../works/index.html">作品リストを見る →</a></h3>
        <p class="ai-legend"><span class="ai-k ai-k-a">受賞</span>受賞タイトル　<span class="ai-k ai-k-p">設置</span>設置場所　<span class="ai-k ai-k-s">出品</span>出品した展覧会</p>
        <div class="ai-wgrid">{"".join(cards)}</div>
        <p class="ai-tnote">※ 作成年度が「確認中」の作品は調べています。写真の一部は公式サイト（il-teitetsu.com・iwatakuniyasu.wixsite.com/ikeuchi）掲載のものです。</p>
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
        <p>レンタル作品のほかに、設置する場所のために新しい作品を企画・制作する「リクエストオーダー」も承ります。会社やブランドの想い、場所の歴史をうかがい、その空間にしかない一点をつくります。</p>
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
        <ul><li>本社エントランスのシンボル</li><li>百貨店・ブランド店のシーズンのショーウィンドウ</li><li>創業・周年の記念モニュメント</li><li>会社のロゴや理念をモチーフにしたオブジェ</li><li>吹き抜け・中庭・公開空地のアート</li><li>門扉・フェンスなどのロートアイアン</li></ul>
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
// 作品ページ・USEのページなどから戻ってきたとき、飛ぶ前に見ていた場所に戻す
(function(){
  var key = 'aile-scroll:' + location.pathname;
  function save(){ try { sessionStorage.setItem(key, String(Math.round(scrollY))); } catch(e){} }
  addEventListener('pagehide', save);
  document.addEventListener('click', function(ev){ if (ev.target.closest && ev.target.closest('a[href]')) save(); }, true);
  var back = false, y = null;
  try {
    var u = new URL(document.referrer);
    back = u.origin === location.origin && /\\/rental_office-aile\\/(works|entrance|event|showroom|showwindow)\\//.test(u.pathname);
    y = sessionStorage.getItem(key);
  } catch(e){}
  if (!back || y === null) return;
  if ('scrollRestoration' in history) history.scrollRestoration = 'manual';
  var stop = false;
  ['wheel', 'touchstart', 'keydown'].forEach(function(t){ addEventListener(t, function(){ stop = true; }, {once:true, passive:true}); });
  function go(){ if (!stop) window.scrollTo({top:+y, behavior:'instant'}); }
  go(); addEventListener('load', go); setTimeout(go, 400); setTimeout(go, 1200);
})();
</script>"""

# 作品ページ・USEのページの「戻る」：案A／案Bから来たときは、ブラウザの「戻る」と同じ動き（見ていた場所に戻る）
BACK_JS = """// 「パブリックアートレンタル アイエル」のロゴと「戻る」ボタン：来たページ（案A／案B）の、見ていた場所に戻す
(function () {
  var from = null, direct = false;
  try {
    var u = new URL(document.referrer);
    if (u.origin === location.origin) {
      var m = u.pathname.match(/\\/(01-entrance|02-workplace)\\//);
      if (m) { from = m[1]; direct = true; }
    }
  } catch (e) {}
  try { if (from) sessionStorage.setItem('aile-from', from); else from = sessionStorage.getItem('aile-from'); } catch (e) {}
  document.querySelectorAll('[data-back], .wk-logo, .sw-logo').forEach(function (a) {
    if (from) a.href = a.href.replace(/01-entrance|02-workplace/, from);
    a.addEventListener('click', function (ev) {
      if (direct && history.length > 1) { ev.preventDefault(); history.back(); }
    });
  });
})();
"""

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
    sub="鉄の作家・池内卓也の作品を、オフィスや百貨店・ブランド店のショーウィンドウにレンタルでお届け。季節ごとに入れ替えて、毎日の景色に新しい出会いを。",
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
    sub="鉄の作家・池内卓也の作品を、オフィスやショーウィンドウにレンタル。季節のボタンを押すと、流れる作品が切り替わります。",
    hero_re=r'<section class="wrap hero">.*?</section>',
    logo_re=(r'<span class="logo">IKEUCHI<span>鉄</span></span>', '<span class="logo">パブリックアートレンタル <span>アイエル</span></span>'),
    nav_re=('<nav><a href="#new">新着の作品</a>', '<nav><a href="#aile-top">四季の作品</a><a href="#aile-career">作家と作品</a><a href="#new">新着の作品</a>'),
    title=("<title>IKEUCHI Workplace</title>", "<title>パブリックアートレンタル アイエル｜オフィス向け 案B</title>"),
  ),
}

# the iron title is generated by tools/title-logo/make_title_logo.py
TITLE_SVG = (W5 / "title" / "aile-title.svg.html").read_text(encoding="utf-8").strip()

ORDER_START, ORDER_END = "<!-- AILE-ORDER:START -->", "<!-- AILE-ORDER:END -->"

def top_block(d):
    """2つに分けて作る：①タイトル〜作品と受賞歴（AILE-TOP）、②リクエストオーダー（AILE-ORDER）。
    2つの間はページ側で自由に置ける（案Aは「買うより、借りる。」をここに置いている）。"""
    return f"""{START}
<section class="ai-top" data-season="spring">
  <div class="ai-head">
    <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Kiwi+Maru:wght@500&display=swap">
    <h1 class="ai-brand iron"><span class="ai-vh">パブリックアートレンタル アイエル</span><span class="ai-ttl">{TITLE_SVG}</span></h1>
    <p class="ai-sub">{e(d["sub"])}</p>
  </div>
  {space1(d["rows"])}
  {space2()}
</section>
{END}""", f"""{ORDER_START}
<section class="ai-top ai-top-order">
  {order()}
</section>
<nav class="ai-tabbar" aria-label="スマホ用メニュー">
  <a href="#aile-top"><svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="5" width="18" height="14" rx="3"/><path d="M3 15l5-5 4 4 3-3 6 6"/></svg>作品</a>
  <a href="#aile-career"><svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="8" r="4"/><path d="M4 21c1.5-4 4.5-6 8-6s6.5 2 8 6"/></svg>作家</a>
  <a href="#aile-order"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 20l4-1 11-11-3-3L5 16z"/><path d="M14 6l3 3"/></svg>オーダー</a>
  <a href="#contact" class="hot"><svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="5" width="18" height="14" rx="3"/><path d="M3 7l9 6 9-6"/></svg>相談</a>
</nav>
{SCRIPT}
{ORDER_END}"""

for name, d in DESIGNS.items():
    f = W5 / name / "index.html"
    src = f.read_text(encoding="utf-8")
    top, orderblock = top_block(d)
    block = top + "\n" + orderblock
    if ORDER_START in src:
        src = re.sub(re.escape(START) + ".*?" + re.escape(END), lambda m: top, src, flags=re.S)
        src = re.sub(re.escape(ORDER_START) + ".*?" + re.escape(ORDER_END), lambda m: orderblock, src, flags=re.S)
    if START in src:
        if ORDER_START not in src:   # older pages: one block → split into two
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
<footer class="wk-foot">パブリックアートレンタル アイエル ／ 作品の写真の一部は公式サイト（il-teitetsu.com・iwatakuniyasu.wixsite.com/ikeuchi）掲載のものです。</footer>
<script src="../assets/js/lightbox.js"></script>
<script>
  // go back to the design the visitor came from (A or B); fall back to design A
  var ref = document.referrer, back = document.querySelectorAll('[data-back], .wk-logo');
  if (/\\/02-workplace\\//.test(ref)) back.forEach(function(a){{ a.href = a.href.replace('01-entrance', '02-workplace'); }});
</script>
<script src="../assets/js/back.js"></script>
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
.wk-window figcaption b{background:#1E2230; color:#F2D48A;}
.wk-window figcaption a{display:inline-block; margin-left:8px; font-weight:700; color:#FF5A1F;}
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
    body = urllib.parse.quote(f"パブリックアートレンタル アイエル 御中\n\n作品「{w['title']}」のレンタルについて相談したいです。\n\n【会社名・店舗名】\n【設置したい場所（オフィス／ショーウィンドウ など）】\n【希望の時期・期間】\n【ご連絡先】\n")
    office = ""
    if (W5 / "assets" / "office" / f'{w["slug"]}.jpg').exists():
        o = f'../assets/office/{w["slug"]}.jpg'
        office = (f'<figure class="wk-office"><div class="wk-office-img" data-lb="{o}" data-lb-cap="{e(w["title"])}（オフィスに置いたイメージ）">'
                  f'<img src="{o}" alt="{e(w["title"])}をオフィスのエントランスに置いたイメージ" loading="lazy"></div>'
                  '<figcaption><b>オフィスに置いたら</b>エントランス・受付に設置したイメージです（写真を合成した参考イメージ）</figcaption></figure>')
    if (W5 / "assets" / "window" / f'{w["slug"]}.jpg').exists():
        o = f'../assets/window/{w["slug"]}.jpg'
        office += (f'<figure class="wk-office wk-window"><div class="wk-office-img" data-lb="{o}" data-lb-cap="{e(w["title"])}（ショーウィンドウに飾ったイメージ）">'
                   f'<img src="{o}" alt="{e(w["title"])}を百貨店・ブランド店のショーウィンドウに飾ったイメージ" loading="lazy"></div>'
                   '<figcaption><b>ショーウィンドウに飾ったら</b>百貨店・ブランド店のウィンドウに展示したイメージです（合成した参考イメージ）'
                   '<a href="../showwindow/index.html">ショーウィンドウでのレンタル →</a></figcaption></figure>')
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
.ar-aw{display:flex; flex-wrap:wrap; align-items:baseline; gap:4px 14px;}
.ar-work{font-size:14px; font-weight:700; color:#FF5A1F; text-decoration:none; white-space:nowrap;}
.ar-work i{font-style:normal; display:inline-block; margin-left:2px; transition:transform .2s;}
.ar-work:hover{text-decoration:underline;}
.ar-work:hover i{transform:translateX(3px);}
.ar-work.off{color:#8a7d70; font-weight:500;}
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
  <p class="ar-yomi">いけうち たくや ／ 鉄芸家・エクステリアプランナー・一級土木施工管理技士（高知）</p>
  <div class="ar-film"><video src="../assets/video/artist-loop.mp4" poster="../assets/video/artist-loop-poster.jpg" autoplay muted loop playsinline preload="auto" aria-label="池内卓也の作品の映像"></video><span class="ar-tag">IKEUCHI ／ IRON WORKS</span></div>
</section>
<p class="ar-lead">1961年、高知県香南市赤岡町生まれ。高知工業高校を卒業後、生家の鉄工所で溶接の腕を磨き、高知県の溶接コンクールで2度入賞。1995年に有限会社アイエル物産を設立し、ロートアイアンの門扉やフェンス、国内外の植物園のガーデンアイテムを手がけてきました。芸術的な感性を高めるため、2009年から高知県展 先端美術（立体）の部に出品。2014年の特選「覚醒する自我」は、造形美・技術ともに優れ、野外彫刻としても完成された作品と高く評価されました。同じ年に全国公募展「新象展」で佳作賞とホルベイン工業賞をW受賞し、2017年に展賞、2018年に大阪府知事賞。いまも造形作家として、高知の工房で一点ずつ鉄の作品をつくっています。</p>
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
<footer class="wk-foot">パブリックアートレンタル アイエル ／ 作品の写真の一部は公式サイト（il-teitetsu.com・iwatakuniyasu.wixsite.com/ikeuchi）掲載のものです。</footer>
<script src="../assets/js/lightbox.js"></script>
<script>
  // go back to the design the visitor came from (A or B); fall back to design A
  var ref = document.referrer, back = document.querySelectorAll('[data-back], .wk-logo');
  if (/\\/02-workplace\\//.test(ref)) back.forEach(function(a){{ a.href = a.href.replace('01-entrance', '02-workplace'); }});
</script>
<script src="../assets/js/back.js"></script>
</body>
</html>
"""

def artist_page():
    career = "".join(f'<li><span class="y">{y or "─"}</span><span>{e(t)}</span></li>' for y, t in CAREER)
    def award_work(w):   # 作品ページがあればリンク、無ければ（写真準備中）文字だけ
        if w["photos"]:
            return f'<a class="ar-work" href="{w["slug"]}.html">作品「{e(w["title"])}」<i>→</i></a>'
        return f'<span class="ar-work off">作品「{e(w["title"])}」</span>'
    awards = "".join(f'<li><span class="y">{w["year"]}</span><span class="ar-aw"><span>{e(w["award"])}</span>{award_work(w)}</span></li>'
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
.ct-toggle2{margin-left:12px;}
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
  <p>レンタル・ご購入をご相談いただける作品の一覧です。写真にカーソルを合わせると（スマホは「詳しく見る」から）、オフィスに置いたイメージをご覧いただけます。作品ページでは、百貨店・ブランド店の<a href="../showwindow/index.html">ショーウィンドウ</a>に飾ったイメージもご覧いただけます。</p>
</section>
<div class="ct-tools"><div class="ct-tools-in" role="group" aria-label="テーマで絞り込む">
  {chips}
  <label class="ct-toggle"><input type="checkbox" id="ct-office"> オフィスのイメージあり</label>
  <label class="ct-toggle ct-toggle2"><input type="checkbox" id="ct-window"> ショーウィンドウのイメージあり</label>
</div></div>
<p class="ct-count" id="ct-count" aria-live="polite"></p>
<div class="ct-grid" id="ct-grid">{cards}</div>
<p class="ct-foot-note">※ サイズ・レンタル料金・制作期間は、作品と設置場所に合わせてお見積もりします。「オフィスに置いたイメージ」「ショーウィンドウに飾ったイメージ」は写真を合成した参考イメージです。</p>
<div class="wk-sticky"><a class="wk-sticky-main" href="mailto:ilbussan@coral.ocn.ne.jp?subject={subj}&amp;body={body}">作品について相談する</a><a class="wk-sticky-tel" href="tel:0887540711" aria-label="電話する">電話</a></div>
<footer class="wk-foot">パブリックアートレンタル アイエル ／ 有限会社アイエル物産　TEL 0887-54-0711 ／ 作品の写真の一部は公式サイト（il-teitetsu.com・iwatakuniyasu.wixsite.com/ikeuchi）掲載のものです。</footer>
<script>
  // theme chips + "has office image" toggle
  (function(){{
    var chips = document.querySelectorAll('.ct-chip'), cards = document.querySelectorAll('.ct-card'),
        office = document.getElementById('ct-office'), win = document.getElementById('ct-window'), count = document.getElementById('ct-count'), theme = 'all';
    function apply(){{
      var n = 0;
      cards.forEach(function(c){{
        var show = (theme === 'all' || c.dataset.theme === theme) && (!office.checked || c.dataset.office === '1') && (!win.checked || c.dataset.window === '1');
        c.hidden = !show; if (show) n++;
      }});
      count.textContent = n + ' 点の作品';
    }}
    chips.forEach(function(b){{ b.addEventListener('click', function(){{
      theme = b.dataset.theme; chips.forEach(function(x){{ x.setAttribute('aria-pressed', x === b ? 'true' : 'false'); }}); apply();
    }}); }});
    office.addEventListener('change', apply); win.addEventListener('change', apply); apply();
  }})();
  // go back to the design the visitor came from (A or B); fall back to design A
  var ref = document.referrer, back = document.querySelectorAll('[data-back], .wk-logo');
  if (/\\/02-workplace\\//.test(ref)) back.forEach(function(a){{ a.href = a.href.replace('01-entrance', '02-workplace'); }});
</script>
<script src="../assets/js/back.js"></script>
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
        has_win = (W5 / "assets" / "window" / f"{slug}.jpg").exists()
        cards.append(f'<article class="ct-card" data-theme="{t}" data-office="{1 if has_off else 0}" data-window="{1 if has_win else 0}">{media}<div class="ct-body">'
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

# ---------------------------------------------------------------- show windows (showwindow/index.html)
# 百貨店・ブランド店のオーナー向けページ。画像は tools/office-images/3_place_in_windows.py が作る assets/window/<slug>.jpg
# 季節ごとの並びと説明文はここで直します。
SW_SEASONS = [
  ("spring", "春", "桜・新生活・母の日", [
    ("souga", "桜の花びらが舞う、百貨店の春のウィンドウ。"),
    ("fukko", "光の円と砂の床。旗艦店の新作発表に。"),
    ("oka", "苔の壁と木の床。ボタニカルなコレクションに。"),
    ("mudai1", "赤と白のストライプ。コスメ・雑貨の春のキャンペーンに。")]),
  ("summer", "夏", "光と海・お中元", [
    ("tou", "夏空と太陽、砂の床。リゾートコレクションに。"),
    ("yusho", "夜の群青に舞い上がる色の羽。大型ウィンドウのシンボルに。"),
    ("irodori", "黄色の水玉と、色をまとった鉄。夏のポップなウィンドウに。")]),
  ("autumn", "秋", "実り・錆色・秋冬の立ち上がり", [
    ("mudai2", "錆色のカーテンと落ち葉。秋冬コレクションの立ち上がりに。"),
    ("wasuremono", "深緑の壁と落ち葉。レザー・クラフトの店に。"),
    ("mudai5", "木の格子と生成りの壁。家具・インテリアの店に。"),
    ("tamago", "黒と金の輪。時計・ジュエリーの夜のウィンドウに。")]),
  ("winter", "冬", "ホリデー・新春・バレンタイン", [
    ("shishu", "深紅のカーテンと金の飾り。ホリデーシーズンに。"),
    ("utage", "朱の門と金の紙吹雪。新春・初売りに。"),
    ("mamoru", "夜に降る雪。冬のギフトシーズンに。"),
    ("mudai3", "白と銀の雪景色。冬のコレクションに。"),
    ("mudai4", "黒のベルベットと市松の床。ハイジュエリーに。")]),
  ("all", "通年", "ブランドの顔として", [
    ("tsunagu", "白い格子と石の床。百貨店の連続したウィンドウに。"),
    ("mudai6", "レンガの壁と木の床。路面のセレクトショップに。")]),
]

SW_CSS = """*{box-sizing:border-box;}
html{overflow-x:clip; scroll-behavior:smooth;}
body{margin:0; background:#14161B; color:#EFE9DF; font-family:'Zen Maru Gothic', sans-serif; font-weight:500; line-height:1.9; overflow-x:clip;}
img{display:block; max-width:100%;}
a{color:inherit;}
h1,h2,h3{font-family:'Shippori Mincho B1', serif; font-weight:700; letter-spacing:.02em;}
.sw-bar{position:sticky; top:0; z-index:30; display:flex; align-items:center; gap:18px; padding:12px 24px; background:rgba(20,22,27,.9); backdrop-filter:blur(8px); border-bottom:1px solid #2A2D35;}
.sw-logo{font-weight:900; text-decoration:none; white-space:nowrap;}
.sw-logo span{color:#FF5A1F;}
.sw-bar nav{display:flex; gap:18px; margin-left:auto; font-size:14px;}
.sw-bar nav a{text-decoration:none; color:#C9C2B6; white-space:nowrap;}
.sw-bar nav a:hover{color:#fff;}
.sw-cta{white-space:nowrap; text-decoration:none; font-weight:900; font-size:14px; background:#C9A45C; color:#14161B; padding:8px 16px; border-radius:30px;}
.sw-hero{position:relative; min-height:min(88vh,820px); display:flex; align-items:flex-end; overflow:hidden;}
.sw-hero > img{position:absolute; inset:0; width:100%; height:100%; object-fit:cover; object-position:50% 40%;}
.sw-hero::after{content:""; position:absolute; inset:0; background:linear-gradient(180deg, rgba(20,22,27,.15) 0%, rgba(20,22,27,.35) 45%, #14161B 98%);}
.sw-hero-in{position:relative; z-index:1; max-width:1180px; width:100%; margin:0 auto; padding:0 24px 56px;}
.sw-kick{margin:0; font-size:12px; letter-spacing:.3em; color:#C9A45C; font-weight:700;}
.sw-hero h1{font-size:clamp(34px,5.4vw,68px); line-height:1.35; margin:10px 0 14px;}
.sw-hero h1 .nb{display:inline-block;}
.sw-hero p.lead{max-width:40em; margin:0; color:#DAD3C8; font-size:clamp(15px,1.4vw,17px);}
.sw-hero-btns{display:flex; flex-wrap:wrap; gap:12px; margin-top:24px;}
.sw-btn{display:inline-block; text-decoration:none; font-weight:900; padding:13px 24px; border-radius:40px; background:#FF5A1F; color:#fff;}
.sw-btn.ghost{background:transparent; border:1px solid #C9A45C; color:#F2D48A;}
.sw-wrap{max-width:1180px; margin:0 auto; padding:84px 24px;}
.sw-eyebrow{display:block; font-size:12px; letter-spacing:.3em; color:#C9A45C; font-weight:700;}
.sw-wrap h2{font-size:clamp(26px,3.4vw,42px); line-height:1.45; margin:8px 0 14px;}
.sw-lead{color:#BDB5A8; max-width:46em; margin:0;}
.sw-points{display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:18px; margin-top:36px;}
.sw-point{background:#1C1F26; border:1px solid #2A2D35; border-radius:20px; padding:22px;}
.sw-point b{font-family:'Shippori Mincho B1', serif; font-size:28px; color:#C9A45C;}
.sw-point h3{font-size:19px; margin:6px 0 8px; line-height:1.5;}
.sw-point p{margin:0; font-size:14px; color:#BDB5A8;}
.sw-trend{margin-top:26px; padding:16px 20px; border-left:3px solid #C9A45C; background:#1A1C22; color:#BDB5A8; font-size:14px;}
.sw-seasons{display:flex; flex-wrap:wrap; gap:8px; margin:30px 0 22px;}
.sw-seasons button{font-family:inherit; font-weight:700; font-size:15px; cursor:pointer; border:1px solid #3A3E48; background:transparent; color:#DAD3C8; padding:9px 18px; border-radius:30px;}
.sw-seasons button small{font-weight:500; font-size:12px; margin-left:6px; opacity:.75;}
.sw-seasons button[aria-pressed="true"]{background:#C9A45C; border-color:#C9A45C; color:#14161B;}
.sw-grid{display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:22px;}
.sw-grid[hidden]{display:none;}
.sw-card{margin:0; background:#1C1F26; border:1px solid #2A2D35; border-radius:22px; overflow:hidden;}
.sw-img{aspect-ratio:16/10; cursor:zoom-in; overflow:hidden;}
.sw-img img{width:100%; height:100%; object-fit:cover; transition:transform .6s;}
.sw-card:hover .sw-img img{transform:scale(1.03);}
.sw-card figcaption{padding:14px 18px 18px; display:flex; flex-direction:column; gap:4px;}
.sw-card figcaption b{font-size:18px; font-family:'Shippori Mincho B1', serif;}
.sw-card figcaption span{font-size:14px; color:#BDB5A8;}
.sw-card figcaption a{align-self:flex-start; margin-top:6px; font-size:13px; font-weight:700; color:#F2D48A; text-decoration:none;}
.sw-note{font-size:13px; color:#8F887C; margin-top:16px;}
.sw-pair{display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:18px; margin-top:32px;}
.sw-pair div{border-top:1px solid #3A3E48; padding-top:14px;}
.sw-pair h3{font-size:18px; margin:0 0 6px;}
.sw-pair p{margin:0; color:#BDB5A8; font-size:14.5px;}
.sw-pair em{font-style:normal; color:#F2D48A;}
.sw-band{background:#EFE9DF; color:#1E2230;}
.sw-band .sw-lead, .sw-band p{color:#4a4e5c;}
.sw-band .sw-eyebrow{color:#9A7A3A;}
.sw-specs{display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:16px; margin-top:32px;}
.sw-spec{background:#fff; border-radius:18px; padding:20px; border:1px solid #E2D9CB;}
.sw-spec h3{font-size:17px; margin:0 0 6px;}
.sw-spec p{margin:0; font-size:14px;}
.sw-steps{list-style:none; margin:36px 0 0; padding:0; display:grid; grid-template-columns:repeat(6,minmax(0,1fr)); gap:14px;}
.sw-steps li{background:#1C1F26; border:1px solid #2A2D35; border-radius:18px; padding:18px 16px;}
.sw-steps b{font-family:'Shippori Mincho B1', serif; color:#C9A45C; font-size:22px;}
.sw-steps h3{font-size:16px; margin:4px 0 6px; line-height:1.5;}
.sw-steps p{margin:0; font-size:13px; color:#BDB5A8;}
.sw-order{display:grid; grid-template-columns:1.1fr .9fr; gap:36px; align-items:center;}
.sw-order ul{margin:16px 0 0; padding-left:1.2em; color:#DAD3C8;}
.sw-order img{border-radius:22px; cursor:zoom-in;}
.sw-faq{margin-top:28px; border-top:1px solid #2A2D35;}
.sw-faq details{border-bottom:1px solid #2A2D35; padding:14px 0;}
.sw-faq summary{cursor:pointer; font-weight:700; list-style:none;}
.sw-faq summary::before{content:"Q. "; color:#C9A45C;}
.sw-faq details p{margin:8px 0 0; color:#BDB5A8; font-size:14.5px;}
.sw-contact{background:#0E0F13; border-top:1px solid #2A2D35;}
.sw-contact .sw-wrap{display:grid; grid-template-columns:1.1fr .9fr; gap:36px; align-items:center;}
.sw-contact dl{margin:0; display:grid; grid-template-columns:auto 1fr; gap:6px 18px; font-size:14px; color:#BDB5A8;}
.sw-contact dt{color:#C9A45C; font-weight:700; letter-spacing:.1em;}
.sw-contact dd{margin:0;}
.sw-foot{text-align:center; font-size:12px; color:#8F887C; padding:24px 16px 40px; background:#0E0F13;}
.sw-foot a{color:#C9C2B6;}
.sw-sticky{display:none;}
@media (max-width:1100px){ .sw-bar nav{display:none;} .sw-bar .sw-cta{margin-left:auto;} .sw-steps{grid-template-columns:repeat(3,minmax(0,1fr));} .sw-points{grid-template-columns:repeat(2,minmax(0,1fr));} }
@media (max-width:760px){
  .sw-bar{padding:10px 16px;} .sw-logo{font-size:14px;}
  .sw-wrap{padding:60px 16px;} .sw-hero-in{padding:0 16px 40px;}
  .sw-hero{min-height:78vh;}
  .sw-grid, .sw-pair, .sw-specs, .sw-order, .sw-contact .sw-wrap, .sw-points{grid-template-columns:minmax(0,1fr);}
  .sw-steps{grid-template-columns:repeat(2,minmax(0,1fr));}
  .sw-sticky{display:flex; gap:8px; position:fixed; left:10px; right:10px; bottom:calc(10px + env(safe-area-inset-bottom)); z-index:90; background:#C9A45C; padding:8px; border-radius:20px; box-shadow:0 10px 30px rgba(0,0,0,.4);}
  .sw-sticky a{text-decoration:none; font-weight:900; border-radius:14px; padding:12px; text-align:center;}
  .sw-sticky-main{flex:1; background:#14161B; color:#fff;}
  .sw-sticky-tel{background:#fff; color:#14161B; min-width:72px;}
  body{padding-bottom:90px;}
}
"""

SW_PAGE = """<!doctype html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="robots" content="noindex, nofollow">
<title>ショーウィンドウのアート｜パブリックアートレンタル アイエル</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Shippori+Mincho+B1:wght@700&family=Zen+Maru+Gothic:wght@500;700;900&display=swap">
<link rel="stylesheet" href="../assets/use-pages.css">
</head>
<body>
<header class="sw-bar">
  <a class="sw-logo" href="../01-entrance/index.html">パブリックアートレンタル <span>アイエル</span></a>
  <nav><a href="#why">なぜ鉄の彫刻か</a><a href="#seasons">季節のウィンドウ</a><a href="#styling">商品との組み合わせ</a><a href="#install">設置について</a><a href="#flow">ご依頼の流れ</a><a href="#order">オーダー制作</a></nav>
  <a class="sw-cta" href="#contact">相談する</a>
</header>

<section class="sw-hero">
  <img src="../assets/window/tamago.jpg" alt="鉄の彫刻「卵」をジュエリー店の夜のショーウィンドウに飾ったイメージ">
  <div class="sw-hero-in">
    <p class="sw-kick">SHOW WINDOW ART RENTAL</p>
    <h1><span class="nb">通りを歩く人の</span><span class="nb">足を、</span><br>止める鉄。</h1>
    <p class="lead">百貨店・ブランド店のショーウィンドウに、鉄の作家・池内卓也の彫刻を。シーズンの展示に合わせてレンタルし、会期が終われば次の作品へ。ブランドのためのオーダー制作も承ります。</p>
    <div class="sw-hero-btns"><a class="sw-btn" href="#contact">ウィンドウの展示を相談する</a><a class="sw-btn ghost" href="#seasons">季節のウィンドウを見る</a></div>
  </div>
</section>

<section class="sw-wrap" id="why">
  <span class="sw-eyebrow">WHY IRON SCULPTURE</span>
  <h2>ウィンドウに、<br>手でつくられた一点を。</h2>
  <p class="sw-lead">ショーウィンドウは、店に入る前のお客様に、ブランドの世界観を伝える舞台です。量産の什器ではなく、作家が手で溶接した鉄の彫刻を置くことで、通りの景色の中で目を引くウィンドウになります。</p>
  <div class="sw-points">
    <div class="sw-point"><b>01</b><h3>一点ものの物語が、<br>ブランドの物語になる</h3><p>高知の工房で、溶接職人として三十余年の作家が一点ずつ仕上げた作品です。「誰が、どうつくったか」を語れるウィンドウになります。</p></div>
    <div class="sw-point"><b>02</b><h3>素材の対比が、<br>商品を引き立てる</h3><p>鉄の錆や黒皮の質感は、シルク・レザー・ガラス・宝石の輝きと好対照。商品の素材感が際立ちます。</p></div>
    <div class="sw-point"><b>03</b><h3>光と影で、<br>夜のウィンドウが変わる</h3><p>透かしや編んだ鉄は、スポットライトを当てると背景に影の模様を落とします。閉店後も通りを照らす舞台に。</p></div>
    <div class="sw-point"><b>04</b><h3>レンタルだから、<br>季節ごとに入れ替え</h3><p>会期に合わせて借り、終われば返却や次の作品へ。購入しなくても、シーズンごとに新しいウィンドウをつくれます。</p></div>
  </div>
  <p class="sw-trend">国内外の百貨店やブランドでは、アーティストと組んだショーウィンドウが季節の風物詩になっています。作家の作品をウィンドウに迎えることは、通りを歩く人に「この店は何かが違う」と感じてもらうための、確かな方法です。</p>
</section>

<section class="sw-wrap" id="seasons" style="padding-top:0">
  <span class="sw-eyebrow">SEASONAL WINDOWS</span>
  <h2>季節のウィンドウ ── 飾ったイメージ</h2>
  <p class="sw-lead">すべての作品を、さまざまなウィンドウに飾ったイメージをつくりました。季節を選ぶと切り替わります。画像を押すと大きく表示します。</p>
  <div class="sw-seasons" role="group" aria-label="季節を選ぶ">{buttons}</div>
  {grids}
  <p class="sw-note">※ ウィンドウの画像は、作品の写真をもとに合成した参考イメージです（実在の店舗ではありません）。作品の大きさ・ウィンドウの寸法により、実際の見え方は変わります。</p>
</section>

<section class="sw-wrap" id="styling" style="padding-top:0">
  <span class="sw-eyebrow">STYLING WITH YOUR PRODUCTS</span>
  <h2>商品と、鉄の組み合わせ。</h2>
  <p class="sw-lead">作品は主役にも、商品を引き立てる背景にもなります。ディスプレイ担当の方やディスプレイ会社と一緒に、置き方を考えます。</p>
  <div class="sw-pair">
    <div><h3>ジュエリー・時計 × <em>編んだ鉄、透かしの鉄</em></h3><p>細い鉄の帯を編んだ球や、レースのように透かした羽。小さな輝きを、粗い鉄の質感がいっそう引き立てます。</p></div>
    <div><h3>バッグ・レザー × <em>錆の色</em></h3><p>革の艶と、錆びた鉄の深い茶色。秋冬のコレクションに、温かみと重みを加えます。</p></div>
    <div><h3>コスメ・香水 × <em>色をまとった鉄</em></h3><p>赤・黄・青に塗られた鉄の作品は、パッケージの色と響き合い、キャンペーンの色を通りに伝えます。</p></div>
    <div><h3>ファッション × <em>大きなモニュメント</em></h3><p>人の背丈を超える作品は、マネキンと並べても負けない存在感。ウィンドウ全体を一つの風景にします。</p></div>
  </div>
</section>

<section class="sw-band" id="install">
  <div class="sw-wrap">
    <span class="sw-eyebrow">INSTALLATION</span>
    <h2>ウィンドウの条件に合わせて、<br>作家が設置します。</h2>
    <p class="sw-lead">鉄の作品は重さがあるため、ウィンドウの寸法と床の強さを確かめてから作品を選びます。搬入・設置・撤去は、有限会社アイエル物産と作家が担当します。</p>
    <div class="sw-specs">
      <div class="sw-spec"><h3>寸法と重さ</h3><p>ウィンドウの幅・奥行き・高さ、床の耐荷重、搬入口の大きさをうかがい、無理なく置ける作品をご提案します。</p></div>
      <div class="sw-spec"><h3>営業時間外に搬入</h3><p>閉店後や定休日など、営業のじゃまにならない時間に搬入・設置・撤去をします。</p></div>
      <div class="sw-spec"><h3>転倒の防止</h3><p>台座や固定の方法を、ウィンドウの床や壁に合わせて考えます。お客様の通行がある場所でも安心して置けるようにします。</p></div>
      <div class="sw-spec"><h3>照明の相談</h3><p>スポットライトの位置で、作品の影や表情が大きく変わります。照明を含めた見え方をご提案します。</p></div>
      <div class="sw-spec"><h3>会期・期間</h3><p>季節の展示、キャンペーン期間、周年イベントなど、会期に合わせてご相談ください。</p></div>
      <div class="sw-spec"><h3>料金</h3><p>作品・期間・搬入の条件をうかがってお見積りします。</p></div>
    </div>
  </div>
</section>

<section class="sw-wrap" id="flow">
  <span class="sw-eyebrow">HOW IT WORKS</span>
  <h2>ご依頼の流れ</h2>
  <ol class="sw-steps">
    <li><b>01</b><h3>ご相談</h3><p>店舗名、ウィンドウの写真と寸法、展示のテーマ、会期をお知らせください。</p></li>
    <li><b>02</b><h3>作品のご提案</h3><p>季節・テーマ・商品に合う作品と、置き方をご提案します。</p></li>
    <li><b>03</b><h3>イメージで確認</h3><p>このページの画像のように、ウィンドウに飾った姿を事前にお見せします。</p></li>
    <li><b>04</b><h3>搬入・設置</h3><p>営業時間外に搬入し、照明を見ながら設置します。</p></li>
    <li><b>05</b><h3>会期中</h3><p>位置の調整やお手入れのご相談に応じます。</p></li>
    <li><b>06</b><h3>撤去・次の季節へ</h3><p>会期が終われば撤去。次のシーズンの作品へ入れ替えもできます。</p></li>
  </ol>
</section>

<section class="sw-wrap" id="order" style="padding-top:0">
  <div class="sw-order">
    <div>
      <span class="sw-eyebrow">REQUEST ORDER</span>
      <h2>ブランドのための、<br>一点をつくる。</h2>
      <p class="sw-lead">レンタル作品のほかに、ブランドやシーズンのテーマに合わせて新しい作品を企画・制作する「リクエストオーダー」も承ります。完成前に、ウィンドウに置いた姿をCGで確かめてから制作に入ります。</p>
      <ul><li>ブランドのロゴやモチーフを鉄で表現したオブジェ</li><li>シーズンのテーマに合わせた新作</li><li>並んだ複数のウィンドウをつなぐ連作</li><li>周年・新店オープンの記念作品</li></ul>
      <div class="sw-hero-btns"><a class="sw-btn ghost" href="../01-entrance/index.html#aile-order">リクエストオーダーについて詳しく →</a></div>
    </div>
    <img src="../assets/window/utage.jpg" alt="作品「宴の色」を新春のショーウィンドウに飾ったイメージ" data-lb="../assets/window/utage.jpg" data-lb-cap="宴の色（新春のウィンドウに飾ったイメージ）" loading="lazy">
  </div>
  <div class="sw-faq">
    <details><summary>小さなウィンドウでも置けますか？</summary><p>作品の大きさはさまざまです。台座にのせる小ぶりな作品もあります。ウィンドウの寸法をお知らせください。</p></details>
    <details><summary>作品に商品を掛けたり、のせたりできますか？</summary><p>作品の形や強さによってはできます。どのように見せたいか、事前にご相談ください。</p></details>
    <details><summary>店内やエントランスにも置けますか？</summary><p>はい。店内・エントランス・オフィスへのレンタルも承ります。<a href="../01-entrance/index.html">オフィス・エントランス向けのご案内</a>もご覧ください。</p></details>
    <details><summary>気に入った作品を購入することはできますか？</summary><p>作品によってはご購入のご相談もできます。</p></details>
  </div>
</section>

<section class="sw-contact" id="contact">
  <div class="sw-wrap">
    <div>
      <span class="sw-eyebrow">CONTACT</span>
      <h2>次のシーズンのウィンドウに、<br>鉄の一点を。</h2>
      <p class="sw-lead">ウィンドウの写真と寸法、会期を添えて、お気軽にご相談ください。</p>
      <div class="sw-hero-btns"><a class="sw-btn" href="mailto:ilbussan@coral.ocn.ne.jp?subject={subj}&amp;body={body}">メールで相談する</a><a class="sw-btn ghost" href="tel:0887540711">0887-54-0711</a></div>
    </div>
    <dl><dt>STUDIO</dt><dd>有限会社アイエル物産</dd><dt>ADDRESS</dt><dd>高知県香南市野市町土居1073-2</dd><dt>FAX</dt><dd>0887-54-0712</dd><dt>MAIL</dt><dd>ilbussan@coral.ocn.ne.jp</dd></dl>
  </div>
</section>
{uses}
<footer class="sw-foot">パブリックアートレンタル アイエル ／ <a href="../01-entrance/index.html">オフィス・エントランス向け</a> ／ <a href="../works/index.html">作品リスト</a> ／ <a href="../works/artist.html">作家 池内卓也</a></footer>
<div class="sw-sticky"><a class="sw-sticky-main" href="mailto:ilbussan@coral.ocn.ne.jp?subject={subj}&amp;body={body}">ウィンドウの展示を相談する</a><a class="sw-sticky-tel" href="tel:0887540711" aria-label="電話する">電話</a></div>
<script src="../assets/js/lightbox.js"></script>
<script>
(function(){{
  var buttons = document.querySelectorAll('.sw-seasons button'), grids = document.querySelectorAll('.sw-grid');
  function show(key){{
    grids.forEach(function(g){{ g.hidden = g.dataset.season !== key; }});
    buttons.forEach(function(b){{ b.setAttribute('aria-pressed', b.dataset.season === key); }});
  }}
  buttons.forEach(function(b){{ b.addEventListener('click', function(){{ show(b.dataset.season); }}); }});
  var m = new Date().getMonth() + 1;
  show(m >= 3 && m <= 5 ? 'spring' : m >= 6 && m <= 8 ? 'summer' : m >= 9 && m <= 11 ? 'autumn' : 'winter');
}})();
</script>
<script src="../assets/js/back.js"></script>
</body>
</html>
"""

# ---------------------------------------------------------------- USE 01〜04 の詳しいページ（共通の部品）
# 案Aの「USE 01〜04」のカードから飛ぶページ。デザインは use-pages.css を共用します。
USES = [  # (フォルダ, 番号, 名前, カード用の画像)
  ("entrance", "USE 01", "本社エントランス", "../assets/office/tsunagu.jpg"),
  ("event", "USE 02", "周年・式典・採用イベント", "../assets/scene/event-yusho.jpg"),
  ("showroom", "USE 03", "ショールーム", "../assets/scene/showroom-mudai4.jpg"),
  ("showwindow", "USE 04", "店舗のショーウィンドウ", "../assets/window/tamago.jpg"),
]

USE_CSS = """
/* other uses (USE 01-04) */
.sw-uses{border-top:1px solid #2A2D35;}
.sw-usegrid{display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:16px; margin-top:24px;}
.sw-use{display:block; text-decoration:none; background:#1C1F26; border:1px solid #2A2D35; border-radius:18px; overflow:hidden; transition:transform .25s, border-color .25s;}
.sw-use:hover{transform:translateY(-3px); border-color:#C9A45C;}
.sw-use img{width:100%; aspect-ratio:16/10; object-fit:cover;}
.sw-use span{display:block; padding:12px 16px 14px;}
.sw-use small{display:block; font-size:12px; font-weight:700; letter-spacing:.14em; color:#C9A45C;}
.sw-use b{font-size:16px;}
.sw-use.now{border-color:#C9A45C; pointer-events:none;}
.sw-use.now small::after{content:"（このページ）"; letter-spacing:0; color:#8F887C; font-weight:500;}
.sw-gallery{display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:20px; margin-top:30px;}
@media (max-width:1100px){ .sw-gallery{grid-template-columns:repeat(2,minmax(0,1fr));} }
@media (max-width:760px){ .sw-usegrid{grid-template-columns:repeat(2,minmax(0,1fr)); gap:10px;} .sw-use b{font-size:14px;} .sw-gallery{grid-template-columns:minmax(0,1fr);} }
"""

def uses_nav(current):
    cards = "".join(f'<a class="sw-use{" now" if f == current else ""}" href="../{f}/index.html"><img src="{img}" alt="" loading="lazy"><span><small>{no}</small><b>{e(name)}</b></span></a>'
                    for f, no, name, img in USES)
    return f'<section class="sw-uses"><div class="sw-wrap"><span class="sw-eyebrow">OTHER USES</span><h2>ほかの使い方</h2><div class="sw-usegrid">{cards}</div></div></section>'

def showwindow_page():
    buttons, grids = [], []
    for key, jp, mood, items in SW_SEASONS:
        buttons.append(f'<button type="button" data-season="{key}" aria-pressed="false">{jp}<small>{e(mood)}</small></button>')
        cards = []
        for slug, desc in items:
            if not (W5 / "assets" / "window" / f"{slug}.jpg").exists():
                continue
            w = BY[slug]; src = f"../assets/window/{slug}.jpg"
            cards.append(f'<figure class="sw-card"><div class="sw-img" data-lb="{src}" data-lb-cap="{e(w["title"])}（{jp}のウィンドウに飾ったイメージ）" data-lb-group="sw-{key}">'
                         f'<img src="{src}" alt="作品「{e(w["title"])}」をショーウィンドウに飾ったイメージ" loading="lazy"></div>'
                         f'<figcaption><b>{e(w["title"])}</b><span>{e(desc)}</span><a href="../works/{slug}.html">作品ページへ →</a></figcaption></figure>')
        grids.append(f'<div class="sw-grid" data-season="{key}"{"" if key == "spring" else " hidden"}>{"".join(cards)}</div>')
    subj = urllib.parse.quote("ショーウィンドウでの作品レンタルの相談")
    body = urllib.parse.quote("パブリックアートレンタル アイエル 御中\n\nショーウィンドウでの作品の展示について相談したいです。\n\n【店舗名】\n【ウィンドウの場所・寸法（幅・奥行き・高さ）】\n【展示のテーマ・季節】\n【会期（希望の期間）】\n【気になる作品】\n【ご連絡先】\n")
    return SW_PAGE.format(buttons="".join(buttons), grids="".join(grids), subj=subj, body=body, uses=uses_nav("showwindow"))

sw = W5 / "showwindow"; sw.mkdir(exist_ok=True)
(W5 / "assets" / "use-pages.css").write_text(SW_CSS + USE_CSS, encoding="utf-8", newline="\n")
(sw / "showwindow.css").unlink(missing_ok=True)
(sw / "index.html").write_text(showwindow_page(), encoding="utf-8", newline="\n")
print("show windows ->", sw / "index.html")

# ---------------------------------------------------------------- USE 01〜03 のページ（entrance/ event/ showroom/）
# 文章と画像は下の USE_PAGES で直します。画像：
#   assets/office/<slug>.jpg … 2_place_in_rooms.py（エントランス）
#   assets/scene/<場面>.jpg  … 4_place_in_scenes.py（イベント会場・ショールーム）
USE_PAGE = """<!doctype html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="robots" content="noindex, nofollow">
<title>{title}｜パブリックアートレンタル アイエル</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Shippori+Mincho+B1:wght@700&family=Zen+Maru+Gothic:wght@500;700;900&display=swap">
<link rel="stylesheet" href="../assets/use-pages.css">
</head>
<body>
<header class="sw-bar">
  <a class="sw-logo" href="../01-entrance/index.html">パブリックアートレンタル <span>アイエル</span></a>
  <nav><a href="#why">{nav_why}</a><a href="#gallery">{nav_gallery}</a><a href="#ideas">{nav_ideas}</a><a href="#install">設置について</a><a href="#flow">ご依頼の流れ</a><a href="#order">オーダー制作</a></nav>
  <a class="sw-cta" href="#contact">相談する</a>
</header>

<section class="sw-hero">
  <img src="{hero_img}" alt="{hero_alt}">
  <div class="sw-hero-in">
    <p class="sw-kick">{kick}</p>
    <h1>{h1}</h1>
    <p class="lead">{lead}</p>
    <div class="sw-hero-btns"><a class="sw-btn" href="#contact">{cta}</a><a class="sw-btn ghost" href="#gallery">{nav_gallery}を見る</a></div>
  </div>
</section>

<section class="sw-wrap" id="why">
  <span class="sw-eyebrow">WHY IRON SCULPTURE</span>
  <h2>{why_h2}</h2>
  <p class="sw-lead">{why_lead}</p>
  <div class="sw-points">{points}</div>
</section>

<section class="sw-wrap" id="gallery" style="padding-top:0">
  <span class="sw-eyebrow">IMAGES</span>
  <h2>{gallery_h2}</h2>
  <p class="sw-lead">{gallery_lead}</p>
  <div class="sw-gallery">{cards}</div>
  <p class="sw-note">※ 画像は、作品の写真をもとに合成した参考イメージです（実在の会場・施設ではありません）。{gallery_note}</p>
</section>

<section class="sw-wrap" id="ideas" style="padding-top:0">
  <span class="sw-eyebrow">IDEAS</span>
  <h2>{ideas_h2}</h2>
  <p class="sw-lead">{ideas_lead}</p>
  <div class="sw-pair">{ideas}</div>
</section>

<section class="sw-band" id="install">
  <div class="sw-wrap">
    <span class="sw-eyebrow">INSTALLATION</span>
    <h2>{install_h2}</h2>
    <p class="sw-lead">{install_lead}</p>
    <div class="sw-specs">{specs}</div>
  </div>
</section>

<section class="sw-wrap" id="flow">
  <span class="sw-eyebrow">HOW IT WORKS</span>
  <h2>ご依頼の流れ</h2>
  <ol class="sw-steps">{steps}</ol>
</section>

<section class="sw-wrap" id="order" style="padding-top:0">
  <div class="sw-order">
    <div>
      <span class="sw-eyebrow">REQUEST ORDER</span>
      <h2>{order_h2}</h2>
      <p class="sw-lead">{order_lead}</p>
      <ul>{order_list}</ul>
      <div class="sw-hero-btns"><a class="sw-btn ghost" href="../01-entrance/index.html#aile-order">リクエストオーダーについて詳しく →</a></div>
    </div>
    <img src="{order_img}" alt="{order_alt}" data-lb="{order_img}" data-lb-cap="{order_alt}" loading="lazy">
  </div>
  <div class="sw-faq">{faq}</div>
</section>

<section class="sw-contact" id="contact">
  <div class="sw-wrap">
    <div>
      <span class="sw-eyebrow">CONTACT</span>
      <h2>{contact_h2}</h2>
      <p class="sw-lead">{contact_lead}</p>
      <div class="sw-hero-btns"><a class="sw-btn" href="mailto:ilbussan@coral.ocn.ne.jp?subject={subj}&amp;body={body}">メールで相談する</a><a class="sw-btn ghost" href="tel:0887540711">0887-54-0711</a></div>
    </div>
    <dl><dt>STUDIO</dt><dd>有限会社アイエル物産</dd><dt>ADDRESS</dt><dd>高知県香南市野市町土居1073-2</dd><dt>FAX</dt><dd>0887-54-0712</dd><dt>MAIL</dt><dd>ilbussan@coral.ocn.ne.jp</dd></dl>
  </div>
</section>
{uses}
<footer class="sw-foot">パブリックアートレンタル アイエル ／ <a href="../01-entrance/index.html">トップ（案A）</a> ／ <a href="../02-workplace/index.html">トップ（案B）</a> ／ <a href="../works/index.html">作品リスト</a> ／ <a href="../works/artist.html">作家 池内卓也</a></footer>
<div class="sw-sticky"><a class="sw-sticky-main" href="mailto:ilbussan@coral.ocn.ne.jp?subject={subj}&amp;body={body}">{cta}</a><a class="sw-sticky-tel" href="tel:0887540711" aria-label="電話する">電話</a></div>
<script src="../assets/js/lightbox.js"></script>
<script src="../assets/js/back.js"></script>
</body>
</html>
"""

# 共通の流れ（ページごとに上書きできる）
def steps6(items):
    return "".join(f"<li><b>{i:02d}</b><h3>{t}</h3><p>{d}</p></li>" for i, (t, d) in enumerate(items, 1))

USE_PAGES = {
  "entrance": dict(
    title="本社エントランスのアート", nav_why="なぜ鉄の彫刻か", nav_gallery="エントランスのイメージ", nav_ideas="置く場所",
    hero_img="../assets/office/tsunagu.jpg", hero_alt="作品「つなぐ」を明るいロビーに置いたイメージ",
    kick="USE 01 ── ENTRANCE", h1='<span class="nb">会社の顔に、</span><br>鉄の一点を。',
    lead="来訪者が最初に目にするエントランスや受付に、鉄の作家・池内卓也の彫刻を。ブランドを体現する一点を来訪者の動線上に置き、季節や節目に合わせて入れ替えられます。",
    cta="エントランスの作品を相談する",
    why_h2="エントランスは、<br>会社の第一印象をつくる場所。",
    why_lead="エレベーターの扉が開いた瞬間、受付で名乗るまでの数十秒。来訪者はその間に「どんな会社か」を感じとっています。手でつくられた一点の作品は、言葉より先に会社の姿勢を伝えます。",
    points=[("第一印象をつくる", "大きな作品ひとつで、空間の印象が決まります。「この会社は、何かが違う」と感じてもらう入口に。"),
            ("会話のきっかけに", "「この作品は？」から商談の雑談が始まります。作家や作品の背景を、会社の想いとあわせて語れます。"),
            ("社員が毎日通る場所", "来訪者だけでなく、毎日出社する社員の目にも入ります。働く場所への誇りや愛着につながります。"),
            ("季節・節目に入れ替え", "レンタルなので、季節や周年、移転・改装に合わせて作品を見直せます。")],
    gallery_h2="エントランスに置いたイメージ",
    gallery_lead="作品ごとに違うエントランスを描き、作品を置いてみました。画像を押すと大きく表示します。",
    gallery_note='すべての作品の設置イメージは<a href="../works/index.html" style="color:#F2D48A">作品リスト</a>の各作品ページでご覧いただけます。',
    cards=[("office/yusho", "湧昇の夢", "6mの吹き抜けと大きな窓のロビーに。来訪者を迎えるシンボルとして。", "yusho"),
           ("office/tsunagu", "つなぐ", "白い格子と両側の窓。明るく開放的なロビーの中央に。", "tsunagu"),
           ("office/mamoru", "守るべきもの", "木のルーバーに挟まれた細長いアプローチの先に。", "mamoru"),
           ("office/utage", "宴の色", "白い壁と窓、テラゾーの床。受付カウンターの横に。", "utage"),
           ("office/mudai3", "無題3", "ミントのタイル壁と受付カウンター。やわらかな雰囲気のフロアに。", "mudai3"),
           ("office/mudai1", "無題1", "赤と白のストライプの壁。ブランドカラーのある受付に。", "mudai1"),
           ("office/shishu", "死守", "黒いパネルと金のライン。重厚なエグゼクティブフロアに。", "shishu"),
           ("office/mudai6", "無題6", "レンガの壁と木の床、吊り照明。クリエイティブなオフィスに。", "mudai6"),
           ("office/wasuremono", "君の忘れもの", "深緑の腰壁と寄木の床。落ち着いた応接スペースに。", "wasuremono")],
    ideas_h2="エントランスの、ここに置く。", ideas_lead="来訪者の動線に沿って、置く場所ごとに合う作品を考えます。",
    ideas=[("エレベーターホール × <em>大きな作品</em>", "扉が開いた瞬間に目に入る場所。存在感のある作品ひとつで、会社の世界観が伝わります。"),
           ("受付カウンターの横 × <em>使えるアート</em>", "コートや傘を掛けられるツリーハンガーなど、おもてなしと話題を兼ねた作品も。"),
           ("吹き抜け・ロビーの中央 × <em>モニュメント</em>", "高い天井を生かした背の高い作品や、見上げる作品で、空間に軸をつくります。"),
           ("屋外のアプローチ・公開空地 × <em>屋外に強い鉄</em>", "美術館の入口や神社の参道、海岸など、屋外への設置実績があります。")],
    install_h2="オフィスの条件に合わせて、<br>作家が設置します。",
    install_lead="鉄の作品は重さがあるため、置き場所の広さと床の強さを確かめてから作品を選びます。搬入・設置・撤去は、有限会社アイエル物産と作家が担当します。",
    specs=[("寸法と重さ", "置き場所の広さ・天井の高さ・床の耐荷重・搬入経路（エレベーターの大きさなど）をうかがいます。"),
           ("動線をさまたげない", "来訪者や社員の通り道、避難経路をふさがない位置と向きをご提案します。"),
           ("業務時間外に搬入", "始業前や休日など、業務のじゃまにならない時間に搬入・設置します。"),
           ("照明との相性", "ダウンライトやスポットライトの当たり方で、作品の表情が変わります。照明も含めて見え方を考えます。"),
           ("期間", "季節ごと、1年ごとなど、ご希望に合わせてご相談ください。"),
           ("料金", "作品・期間・搬入の条件をうかがってお見積りします。")],
    steps=[("ご相談", "エントランスの写真と置きたい場所、期間のご希望をお知らせください。"), ("現地の確認", "広さ・天井の高さ・光の入り方・動線を確かめます。"),
           ("作品のご提案", "空間と会社のイメージに合う作品と置き方をご提案します。"), ("イメージで確認", "このページの画像のように、置いた姿を事前にお見せします。"),
           ("搬入・設置", "業務時間外に搬入し、照明を見ながら設置します。"), ("入れ替え・返却", "期間が終われば返却、または次の作品へ入れ替えます。")],
    order_h2="会社のための、<br>一点をつくる。",
    order_lead="レンタル作品のほかに、会社の想いや場所の歴史をうかがい、エントランスのための新しい作品を企画・制作します。完成前に、置いた姿をCGで確かめてから制作に入ります。",
    order_list=["本社エントランスのシンボル", "会社のロゴや理念をモチーフにしたオブジェ", "吹き抜け・中庭・公開空地のアート", "門扉・フェンスなどのロートアイアン"],
    order_img="../assets/photo/2026-10_yusho-1.jpg", order_alt="湧昇の夢（中土佐町立美術館の入口に設置したモニュメント）",
    faq=[("賃貸のオフィスでも置けますか？", "建物の決まりをうかがい、床や壁を傷つけない置き方を一緒に考えます。"),
         ("屋外にも置けますか？", "はい。美術館の入口、神社の参道、海岸、ワイナリーの庭など、屋外への設置実績があります。"),
         ("気に入った作品を購入できますか？", "作品によってはご購入のご相談もできます。"),
         ("移転やレイアウト変更のときは？", "取り外しと、新しい場所への再設置もご相談いただけます。")],
    contact_h2="御社の受付に、<br>まず一点。", contact_lead="受付やエントランスの写真を添えて、お気軽にご相談ください。",
    subj="エントランスへの作品レンタルの相談",
    body="パブリックアートレンタル アイエル 御中\n\nエントランス・受付への作品のレンタルについて相談したいです。\n\n【会社名】\n【置きたい場所（エレベーターホール・受付 など）】\n【広さ・天井の高さ】\n【希望の時期・期間】\n【気になる作品】\n【ご連絡先】\n"),

  "event": dict(
    title="周年・式典・採用イベントのアート", nav_why="なぜ鉄の彫刻か", nav_gallery="会場のイメージ", nav_ideas="イベントの例",
    hero_img="../assets/scene/event-yusho.jpg", hero_alt="作品「湧昇の夢」を周年記念式典の会場に置いたイメージ",
    kick="USE 02 ── EVENTS", h1='<span class="nb">特別な日の会場に、</span><br>記憶に残る一点を。',
    lead="周年記念式典、表彰式、記念パーティ、採用説明会。会社にとって大切な一日の空間を、鉄の彫刻で演出します。必要な期間だけ借りられるので、イベントにも気軽に取り入れられます。",
    cta="イベントでの展示を相談する",
    why_h2="一日のために、<br>本物の作品を。",
    why_lead="イベントの装飾は、終われば片づけられてしまうものがほとんどです。作家が手でつくった鉄の作品は、会場に本物の重みを与え、写真や記憶の中に長く残ります。",
    points=[("期間を決めて借りられる", "1日だけの式典から、数週間の展示会まで。イベントの日程に合わせてレンタルできます。"),
            ("写真に残る", "記念撮影の背景やフォトスポットに。参加者が撮った写真が、イベントの記憶を広げます。"),
            ("会社の歩みを語る", "「つなぐ」「守るべきもの」「湧昇の夢」。作品の名前やテーマを、周年のメッセージと重ねられます。"),
            ("搬入から撤去まで", "会場の決まりに合わせて、搬入・設置・撤去を作家と当社が担当します。")],
    gallery_h2="イベント会場に置いたイメージ",
    gallery_lead="式典・パーティ・説明会など、場面ごとに会場を描いて作品を置いてみました。画像を押すと大きく表示します。",
    gallery_note="",
    cards=[("scene/event-yusho", "湧昇の夢", "周年記念式典。ステージの正面に、会社の未来を象徴するモニュメントとして。", "yusho"),
           ("scene/event-mamoru", "守るべきもの", "表彰式・式典。壇上へ向かうアプローチに。", "mamoru"),
           ("scene/event-utage", "宴の色", "記念パーティ・懇親会。木の床とテーブルの華やかな会場に。", "utage"),
           ("scene/event-tsunagu", "つなぐ", "採用説明会・会社説明会。ブースの間で、会社の想いを伝える一点に。", "tsunagu"),
           ("scene/event-irodori", "彩りの鉄", "社内イベント・ファミリーデー。明るい会場のフォトスポットに。", "irodori"),
           ("scene/event-fukko", "復興芽図", "竣工式・開所式。新しい建物の空間に、芽吹きの作品を。", "fukko")],
    ideas_h2="こんなイベントに。", ideas_lead="会社の節目や、人が集まる日の空間演出に。",
    ideas=[("周年記念式典 × <em>モニュメント</em>", "会社の歩みと未来を、作品のテーマに重ねて。式典のあとに本社へ移して飾ることもできます。"),
           ("表彰式・式典 × <em>静かな存在感</em>", "壇上の脇やアプローチに置き、式典の格を高めます。"),
           ("採用イベント・会社説明会 × <em>話題になる一点</em>", "ブースに作品があるだけで、学生や来場者の足が止まり、会社を語るきっかけになります。"),
           ("竣工・開所・新店オープン × <em>記念作品のオーダー</em>", "新しい建物のための作品を制作し、式典でお披露目することもできます。")],
    install_h2="会場の決まりに合わせて、<br>作家が設置します。",
    install_lead="ホテルの宴会場、展示会場、自社のホールなど、会場ごとに搬入の時間や方法が決まっています。会場の担当者と調整しながら進めます。",
    specs=[("会場の確認", "会場の図面や写真、搬入口・エレベーターの大きさ、床の強さをうかがいます。"),
           ("短い期間でも", "1日だけのイベントでもご相談ください。前日搬入・当日撤去などにも合わせます。"),
           ("搬入の時間", "会場が指定する時間に合わせて、搬入・設置・撤去をします。"),
           ("人が多い場所の安全", "参加者がぶつからない位置や、転倒しない置き方を考えます。"),
           ("照明・撮影", "ステージの照明やフォトスポットとしての見え方も含めてご提案します。"),
           ("料金", "作品・期間・会場の条件をうかがってお見積りします。")],
    steps=[("ご相談", "イベントの内容・日程・会場をお知らせください。"), ("会場の確認", "図面や写真、搬入の条件を確かめます。"),
           ("作品のご提案", "イベントのテーマと会場に合う作品と置き方をご提案します。"), ("イメージで確認", "会場に置いた姿を事前にお見せします。"),
           ("搬入・設置", "会場の指定時間に搬入し、照明を見ながら設置します。"), ("撤去", "イベントが終われば撤去します。本社への移設もご相談ください。")],
    order_h2="記念の日のための、<br>一点をつくる。",
    order_lead="周年や竣工など、会社の節目に合わせて新しい作品を企画・制作する「リクエストオーダー」も承ります。式典でお披露目し、そのまま会社のシンボルとして残せます。",
    order_list=["創業・周年の記念モニュメント", "竣工・開所の記念作品", "表彰のトロフィーやオブジェ", "社名やロゴをモチーフにした作品"],
    order_img="../assets/photo/2026-10_fukko-1.jpg", order_alt="復興芽図（屋外の展示会で展示した作品）",
    faq=[("1日だけでも借りられますか？", "はい、ご相談ください。会場の搬入・撤去の時間に合わせます。"),
         ("ホテルや展示会場でも大丈夫ですか？", "会場の決まりに合わせて、担当者と調整しながら進めます。"),
         ("イベントのあと、そのまま会社に置けますか？", "はい。イベント後に本社などへ移して、レンタルを続けることもできます。"),
         ("作品の前で記念撮影をしてもいいですか？", "はい。フォトスポットとして使っていただけるよう、置き方をご提案します。")],
    contact_h2="次の記念日に、<br>鉄の一点を。", contact_lead="イベントの内容と日程、会場を添えて、お気軽にご相談ください。",
    subj="イベントでの作品レンタルの相談",
    body="パブリックアートレンタル アイエル 御中\n\nイベントでの作品のレンタルについて相談したいです。\n\n【会社名】\n【イベントの内容（周年・式典・採用イベント など）】\n【日程】\n【会場】\n【気になる作品】\n【ご連絡先】\n"),

  "showroom": dict(
    title="ショールームのアート", nav_why="なぜ鉄の彫刻か", nav_gallery="ショールームのイメージ", nav_ideas="業種ごとの例",
    hero_img="../assets/scene/showroom-mudai4.jpg", hero_alt="作品「無題4」を大きなショールームに置いたイメージ",
    kick="USE 03 ── SHOWROOM", h1='<span class="nb">製品の世界観を、</span><br>鉄でつくる。',
    lead="自動車、家具、住宅設備、建材、照明。製品を見ていただくショールームに、鉄の作家・池内卓也の彫刻を。自社製品とあわせて、ブランドの世界観をつくる背景になります。",
    cta="ショールームの作品を相談する",
    why_h2="製品を、<br>もっと良く見せる背景に。",
    why_lead="ショールームは、製品の性能だけでなく「この会社の製品がある暮らし」を感じてもらう場所です。手仕事の鉄の作品は、工業製品の精密さや素材の良さを引き立て、空間に物語を加えます。",
    points=[("製品が引き立つ", "粗い鉄の質感と、製品のなめらかな仕上げ。対比で製品の素材感が際立ちます。"),
            ("空間に物語を", "「高知の工房で、溶接職人が一点ずつ」。作品の背景が、ブランドの姿勢を語ります。"),
            ("来場者の話題に", "作品の前で足が止まり、写真に撮られ、ショールームの記憶に残ります。"),
            ("展示替えに合わせて", "新製品の発表や季節の展示替えに合わせて、作品も入れ替えられます。")],
    gallery_h2="ショールームに置いたイメージ",
    gallery_lead="業種ごとにショールームを描き、作品を置いてみました。画像を押すと大きく表示します。",
    gallery_note="",
    cards=[("scene/showroom-mudai4", "無題4", "自動車・製品の大きなショールーム。光る床の展示ステージの横に。", "mudai4"),
           ("scene/showroom-tamago", "卵", "家具・インテリア。ソファとラグのある展示の横に。", "tamago"),
           ("scene/showroom-mudai6", "無題6", "キッチン・住宅設備。タイルの壁とカウンターの前に。", "mudai6"),
           ("scene/showroom-oka", "丘の上の植物", "建材・タイル。素材見本の壁の前で、鉄という素材の力を。", "oka"),
           ("scene/showroom-wasuremono", "君の忘れもの", "照明器具。たくさんの照明の下、台座の上で光と影を見せる。", "wasuremono"),
           ("scene/showroom-souga", "想芽", "企業ミュージアム・ギャラリー。展示台の並ぶ空間に。", "souga")],
    ideas_h2="業種ごとの、組み合わせ。", ideas_lead="製品の素材や色に合わせて、作品を選びます。",
    ideas=[("自動車・バイク × <em>色をまとった鉄</em>", "ボディカラーと響き合う、赤・青・黄の鉄の作品。展示ステージの横に置いて、空間に動きを。"),
           ("家具・インテリア × <em>錆の色、木と鉄</em>", "木や布のやわらかさと、錆びた鉄の深い色。暮らしの場面に置ける作品を。"),
           ("住宅設備・建材 × <em>素材としての鉄</em>", "タイルや石、木の見本と並べて、鉄という素材の表情を見せます。"),
           ("照明・ガラス × <em>透かしの鉄</em>", "透かしや編んだ鉄に光を当てると、壁や床に影の模様が生まれます。")],
    install_h2="ショールームの条件に合わせて、<br>作家が設置します。",
    install_lead="展示のレイアウトや来場者の動線をうかがい、製品の見え方をじゃましない置き方をご提案します。搬入・設置・撤去は、有限会社アイエル物産と作家が担当します。",
    specs=[("寸法と重さ", "置き場所の広さ・床の耐荷重・搬入経路をうかがい、無理なく置ける作品を選びます。"),
           ("製品を主役に", "製品の前をふさがず、目線を製品へ導く位置と高さを考えます。"),
           ("営業時間外に搬入", "閉館後や休館日に搬入・設置・撤去をします。"),
           ("照明の相談", "スポットライトの位置で、作品と製品の両方がきれいに見えるようにします。"),
           ("展示替えに合わせて", "新製品の発表や季節の展示替えの時期に合わせてご相談ください。"),
           ("料金", "作品・期間・搬入の条件をうかがってお見積りします。")],
    steps=[("ご相談", "ショールームの写真とレイアウト、展示の時期をお知らせください。"), ("現地の確認", "広さ・照明・来場者の動線を確かめます。"),
           ("作品のご提案", "製品とブランドに合う作品と置き方をご提案します。"), ("イメージで確認", "ショールームに置いた姿を事前にお見せします。"),
           ("搬入・設置", "営業時間外に搬入し、照明を見ながら設置します。"), ("入れ替え・返却", "展示替えに合わせて、次の作品への入れ替えや返却を。")],
    order_h2="ブランドのための、<br>一点をつくる。",
    order_lead="製品やブランドのテーマに合わせて、新しい作品を企画・制作する「リクエストオーダー」も承ります。自社製品の素材やかたちをモチーフにすることもできます。",
    order_list=["ブランドのロゴやモチーフを鉄で表現したオブジェ", "新製品の発表に合わせた新作", "自社製品の素材を組み合わせた作品", "企業ミュージアムの展示作品"],
    order_img="../assets/photo/2026-10_wings-1.jpg", order_alt="君の忘れもの（ギャラリーでの展示）",
    faq=[("製品と一緒に作品を置いても、製品の邪魔になりませんか？", "製品を主役にするため、置く位置・高さ・照明を一緒に考えます。"),
         ("作品に製品をのせたり、組み合わせたりできますか？", "作品の形や強さによってはできます。事前にご相談ください。"),
         ("展示替えのたびに作品を替えられますか？", "はい。レンタルなので、展示替えに合わせて入れ替えができます。"),
         ("気に入った作品を購入できますか？", "作品によってはご購入のご相談もできます。")],
    contact_h2="ショールームに、<br>鉄の一点を。", contact_lead="ショールームの写真とレイアウト、展示の時期を添えて、お気軽にご相談ください。",
    subj="ショールームへの作品レンタルの相談",
    body="パブリックアートレンタル アイエル 御中\n\nショールームへの作品のレンタルについて相談したいです。\n\n【会社名】\n【ショールームの場所・広さ】\n【扱っている製品】\n【希望の時期・期間】\n【気になる作品】\n【ご連絡先】\n"),
}

def use_page(folder, c):
    cards = []
    for img, title, desc, slug in c["cards"]:
        src = f"../assets/{img}.jpg"
        if not (W5 / "assets" / f"{img}.jpg").exists():
            continue
        cards.append(f'<figure class="sw-card"><div class="sw-img" data-lb="{src}" data-lb-cap="{e(title)}（{e(desc)}）" data-lb-group="use-{folder}">'
                     f'<img src="{src}" alt="作品「{e(title)}」を置いたイメージ" loading="lazy"></div>'
                     f'<figcaption><b>{e(title)}</b><span>{e(desc)}</span><a href="../works/{slug}.html">作品ページへ →</a></figcaption></figure>')
    return USE_PAGE.format(
        title=e(c["title"]), nav_why=c["nav_why"], nav_gallery=c["nav_gallery"], nav_ideas=c["nav_ideas"],
        hero_img=c["hero_img"], hero_alt=e(c["hero_alt"]), kick=c["kick"], h1=c["h1"], lead=e(c["lead"]), cta=e(c["cta"]),
        why_h2=c["why_h2"], why_lead=e(c["why_lead"]),
        points="".join(f'<div class="sw-point"><b>{i:02d}</b><h3>{e(t)}</h3><p>{e(d)}</p></div>' for i, (t, d) in enumerate(c["points"], 1)),
        gallery_h2=c["gallery_h2"], gallery_lead=e(c["gallery_lead"]), gallery_note=c["gallery_note"], cards="".join(cards),
        ideas_h2=c["ideas_h2"], ideas_lead=e(c["ideas_lead"]), ideas="".join(f"<div><h3>{t}</h3><p>{e(d)}</p></div>" for t, d in c["ideas"]),
        install_h2=c["install_h2"], install_lead=e(c["install_lead"]),
        specs="".join(f'<div class="sw-spec"><h3>{e(t)}</h3><p>{e(d)}</p></div>' for t, d in c["specs"]),
        steps=steps6(c["steps"]), order_h2=c["order_h2"], order_lead=e(c["order_lead"]),
        order_list="".join(f"<li>{e(x)}</li>" for x in c["order_list"]), order_img=c["order_img"], order_alt=e(c["order_alt"]),
        faq="".join(f"<details><summary>{e(q)}</summary><p>{e(a)}</p></details>" for q, a in c["faq"]),
        contact_h2=c["contact_h2"], contact_lead=e(c["contact_lead"]),
        subj=urllib.parse.quote(c["subj"]), body=urllib.parse.quote(c["body"]), uses=uses_nav(folder))

for folder, c in USE_PAGES.items():
    d = W5 / folder; d.mkdir(exist_ok=True)
    (d / "index.html").write_text(use_page(folder, c), encoding="utf-8", newline="\n")
    print("use page ->", d / "index.html")

(W5 / "assets" / "js" / "back.js").write_text(BACK_JS, encoding="utf-8", newline="\n")
print("back.js ->", W5 / "assets" / "js" / "back.js")
