"""作家ページ・作家欄の15秒ループ動画（rental_office-aile/assets/video/artist-loop.mp4）を作ります。

※ いまの動画は「仮」です。工房での作業風景の実写が無かったため、movie/ フォルダの作品映像（CG）と
  作品写真のズームを、約0.94秒×16カットでつないでいます。
  実写の作業動画が届いたら、下の CLIPS を差し替えて実行してください（("v", ファイル, 開始秒) が動画、
  ("p", 写真, "in"/"out") が写真のズーム）。カット数を変えたら CUT も合わせて変えます。

movie/ は大きいのでGitHubに入っていません（このパソコンの Ikeuchi/movie フォルダにあります）。

    python tools/artist-video/make_artist_loop.py
"""
import subprocess, pathlib, tempfile

try:
    import imageio_ffmpeg
    FF = imageio_ffmpeg.get_ffmpeg_exe()
except ImportError:
    FF = "ffmpeg"
ROOT = pathlib.Path(__file__).resolve().parents[2]   # Ikeuchi フォルダ
MOV, NEW, WIX = ROOT / "movie", ROOT / "shared-media" / "2026-10_photos", ROOT / "shared-media" / "wix-photos"
OUT = ROOT / "rental_office-aile" / "assets" / "video"
W, H, FPS = 1280, 720, 30
CUT = 15 / 16                                   # 16 cuts → exactly 15 s
FR = round(CUT * FPS)                           # frames per cut

# (kind, source, start-seconds or zoom-direction)
CLIPS = [
    ("v", MOV / "地面炎30Sec_2.mp4", 9.0),
    ("p", NEW / "garden-leaf-1.jpg", "in"),
    ("v", MOV / "炎.mp4", 17.0),
    ("p", NEW / "wings-1.jpg", "out"),
    ("v", MOV / "地面炎30Sec_2.mp4", 21.5),
    ("p", NEW / "sphere-1.jpg", "in"),
    ("v", MOV / "Video1.mp4", 24.5),
    ("p", WIX / "mudai2.jpg", "out"),
    ("v", MOV / "まもるべきもの.mp4", 13.0),
    ("p", NEW / "yusho-1.jpg", "in"),
    ("v", MOV / "問うVer3.mp4", 36.0),
    ("p", NEW / "color-1.jpg", "out"),
    ("v", MOV / "植物.mp4", 14.0),
    ("p", NEW / "hill-plant-1.jpg", "in"),
    ("v", MOV / "白卵_0119.mp4", 12.0),
    ("v", MOV / "地面炎30Sec_2.mp4", 15.0),
]

GRADE = "eq=contrast=1.08:saturation=1.05"
tmp = pathlib.Path(tempfile.mkdtemp())
parts = []
for i, (kind, src, arg) in enumerate(CLIPS):
    out = tmp / f"c{i:02d}.mp4"
    if kind == "v":
        # slight push-in on every video cut keeps the rhythm lively
        vf = (f"scale={int(W*1.12)}:{int(H*1.12)}:force_original_aspect_ratio=increase,"
              f"crop={W}:{H}:(iw-{W})/2:(ih-{H})/2,fps={FPS},{GRADE}")
        cmd = [FF, "-v", "error", "-y", "-ss", str(arg), "-i", str(src), "-frames:v", str(FR), "-vf", vf]
    else:
        z = f"1.15+0.10*on/{FR}" if arg == "in" else f"1.25-0.10*on/{FR}"
        vf = (f"scale={W*3}:{H*3}:force_original_aspect_ratio=increase,crop={W*3}:{H*3},"
              f"zoompan=z='{z}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={FR}:s={W}x{H}:fps={FPS},{GRADE}")
        cmd = [FF, "-v", "error", "-y", "-loop", "1", "-i", str(src), "-frames:v", str(FR), "-vf", vf]
    subprocess.run(cmd + ["-an", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "veryfast", "-crf", "18", str(out)], check=True)
    parts.append(out)

lst = tmp / "list.txt"
lst.write_text("".join(f"file '{p.as_posix()}'\n" for p in parts), encoding="utf-8")
OUT.mkdir(parents=True, exist_ok=True)
mp4 = OUT / "artist-loop.mp4"
subprocess.run([FF, "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-an",
                "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "slow", "-crf", "28",
                "-movflags", "+faststart", str(mp4)], check=True)
subprocess.run([FF, "-v", "error", "-y", "-ss", "0.3", "-i", str(mp4), "-frames:v", "1", "-q:v", "3",
                str(OUT / "artist-loop-poster.jpg")], check=True)
print(mp4, mp4.stat().st_size // 1024, "KB")
