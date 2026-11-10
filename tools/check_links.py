"""サイト内のリンク切れチェック。

全HTML/CSSの src / href / data-lb / poster / url(...) を調べ、相対パスの参照先ファイルが
実在するか確認します。ページを直したあと、公開する前に実行してください。

    python tools/check_links.py
"""
import pathlib, re, sys, urllib.parse
sys.stdout.reconfigure(encoding="utf-8")

ROOT = pathlib.Path(__file__).resolve().parents[1]
SKIP = {".git", "tools", "studio", "movie", "20261020", "drafts"}
ATTR = re.compile(r'(?:src|href|data-lb|poster)="([^"]+)"')
CSSURL = re.compile(r'url\(\s*["\']?([^"\')]+)["\']?\s*\)')

missing = []
for page in ROOT.rglob("*"):
    if page.suffix not in {".html", ".css"} or SKIP & set(page.relative_to(ROOT).parts):
        continue
    text = page.read_text(encoding="utf-8", errors="replace")
    for ref in ATTR.findall(text) + CSSURL.findall(text):
        if re.match(r"^(https?:|mailto:|tel:|data:|#|%23|javascript:)", ref) or any(c in ref for c in "{}+'"):
            continue
        path = urllib.parse.unquote(ref.split("#")[0].split("?")[0])
        if not path:
            continue
        target = (page.parent / path).resolve()
        if path.endswith("/"):
            target = target / "index.html"
        if not target.exists():
            missing.append(f"{page.relative_to(ROOT)} -> {ref}")

if missing:
    print("リンク切れ:", len(missing))
    print("\n".join(sorted(set(missing))[:200]))
    sys.exit(1)
print("OK: リンク切れはありません")
