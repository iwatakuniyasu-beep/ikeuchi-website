# Higgsfield × Claude 動画生成セットアップ

Claude から Higgsfield（Kling / Veo / Sora / Seedance などの動画生成モデル）を呼び出して動画を作るための手順です。

## ⚠️ 先に知っておくこと：料金

- **Higgsfield 公式ヘルプでは、MCP 連携には「有料サブスクリプションが必要」** と書かれています。
- 無料プランはクレジットがほぼ 0（生成 1 回程度）で、MCP 経由の生成は事実上できません。
- 最安は Starter プラン（年払いで月 $19 前後 / 270 クレジット）。料金は変わるので契約前に https://higgsfield.ai/pricing で確認してください。
- 生成のたびにクレジットを消費します（動画は画像より多く消費）。

## 方法 A：Claude アプリ / claude.ai（いちばん簡単）

1. Claude の **設定 → コネクタ**（Customize → Connectors）を開く
2. **カスタムコネクタを追加** を選ぶ
3. URL に `https://mcp.higgsfield.ai/mcp` を貼り付けて追加
4. **Connect** を押すと Higgsfield のログイン画面が開くので、ログインして許可
5. チャットで「Kling で、桜並木を歩く女性の 5 秒の縦動画を作って」のように頼む

認証エラーが出たら、トークン切れのことが多いので、コネクタを一度切断して再接続してください。

## 方法 B：Claude Code（自分の PC のターミナル）

このリポジトリには `.mcp.json` を入れてあるので、リポジトリ直下で `claude` を起動すると Higgsfield MCP が候補に出ます。

```bash
cd ikeuchi-website
claude
# 起動後に /mcp → higgsfield を選んで「Authenticate」→ ブラウザでログイン
```

手動で追加する場合：

```bash
claude mcp add --transport http higgsfield https://mcp.higgsfield.ai/mcp
```

### 公式推奨：Higgsfield CLI を使う方法

Higgsfield 公式は Claude Code では MCP より CLI を推奨しています。

```bash
npm install -g @higgsfield/cli
higgsfield auth login
```

ログイン後、Claude Code に「higgsfield CLI で動画を作って」と頼めば CLI を使って生成します。

## 注意：クラウド版 Claude Code では使えません

claude.ai/code（クラウドのコンテナ）からは、ネットワーク制限で `mcp.higgsfield.ai` に接続できず、ブラウザでのログインもできません。
**方法 A（Claude アプリのコネクタ）か、自分の PC の Claude Code を使ってください。**

## 作った動画をサイトに載せるとき

- 生成した mp4 はダウンロードして `website/` などに置くか、YouTube にアップしてリンクを貼る（今の作品映像と同じ方式）
- 商用利用の可否はプランによって異なります。無料プランは商用不可です。

## 完全無料でやりたい場合の代替案

Higgsfield 自体は無料ではほぼ使えないので、お金をかけたくない場合は以下を検討してください（無料枠の内容は変わります）。

- 各動画生成サービスの無料枠（Kling、Hailuo、Pika など）を Web 画面から直接使う
- Google の Veo を Gemini アプリの無料/トライアル枠で試す
