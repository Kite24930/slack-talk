# slack-talk

Slackメッセージのリアルタイム音声読み上げと、ウェイクワードによるハンズフリー音声送信を実現する macOS ネイティブアプリケーション。

MacBook Pro M4 MAX (128GB) 単体で完結し、外部クラウドサービスは一切使用しません（Slack Socket Mode 接続のみ）。

## 主な機能

### 読み上げフロー
- Slack チャンネルのメッセージをリアルタイムに音声読み上げ
- チャンネル別の読み上げ ON/OFF 設定
- メンション・URL・絵文字・コードブロックの自動前処理
- FIFO キューによる順序制御（有効期限付きスキップ機能）

### 音声送信フロー
- ウェイクワード（例: "OK Slack"）でハンズフリー起動
- 音声認識 → チャンネル名・メッセージの自動解析
- 送信前の音声確認（「はい」で送信 /「キャンセル」で中止）

## アーキテクチャ

2プロセス構成: Python バックエンド + Tauri デスクトップ UI

```
┌─────────────────────────┐     WebSocket      ┌─────────────────────┐
│   Python バックエンド     │ ◄──────────────► │   Tauri + React      │
│                         │                    │   デスクトップUI      │
│ - Slack Socket Mode     │                    │                     │
│ - TADA TTS (MPS加速)    │   ── メッセージ ──►  │ - チャット画面表示    │
│ - Whisper STT (MPS加速) │   ◄─ 操作指示 ──   │ - チャンネル切替      │
│ - Porcupine Wake Word   │                    │ - 設定変更           │
│ - asyncio イベントループ │                    │ - アクティブch管理    │
│ - SQLite                │                    │                     │
└─────────────────────────┘                    └─────────────────────┘
```

## 技術スタック

| レイヤー | 技術 | 備考 |
|---|---|---|
| アプリ基盤 | Python 3.11 + asyncio | 非同期で全処理を統括 |
| パッケージ管理 | Poetry | 依存・ビルド・スクリプト一元管理 |
| Slack 連携 | slack-sdk (Socket Mode) | 双方向リアルタイム通信 |
| TTS | TADA 3B-ML (HumeAI OSS) | MPS 加速、bf16 約9GB |
| STT | Whisper large (OpenAI OSS) | MPS 加速 |
| ウェイクワード | Porcupine (Picovoice) | ローカル動作・低遅延 |
| 音声入出力 | sounddevice | macOS Core Audio 経由 |
| 設定 DB | SQLite | sqlite3 標準ライブラリ |
| デスクトップ UI | Tauri v2 + React + TypeScript | 軽量デスクトップアプリ |
| バックエンド通信 | WebSocket | リアルタイム双方向通信 |

## ディレクトリ構成

```
slack-talk/
├── pyproject.toml
├── slack_talk/                   # Python バックエンド
│   ├── main.py                   # エントリポイント
│   ├── app.py                    # Application クラス
│   ├── core/
│   │   ├── config.py             # SQLite 設定DB管理
│   │   ├── queue.py              # FIFO キューマネージャ
│   │   └── models.py             # データクラス定義
│   ├── slack/
│   │   └── client.py             # Socket Mode 接続・イベント受信
│   ├── tts/
│   │   └── engine.py             # TADA TTS エンジン
│   └── stt/
│       ├── wakeword.py           # Porcupine ウェイクワード検出
│       ├── whisper.py            # Whisper STT
│       ├── intent.py             # Intent Parser（正規表現）
│       └── audio.py              # マイク入力・スピーカー出力
├── ui/                           # Tauri + React フロントエンド
│   ├── src/                      # React ソース
│   ├── src-tauri/                # Tauri (Rust) ソース
│   └── package.json
├── tests/
└── docs/
```

## 必要環境

- macOS (Apple Silicon)
- Python 3.11+
- Node.js 18+ (UI ビルド用)
- Rust (Tauri ビルド用)
- 十分なメモリ (TADA 3B モデル bf16 で約9GB使用)

## Slack App の設定

1. [Slack API](https://api.slack.com/apps) で新しいアプリを作成
2. **Socket Mode** を有効化し、App-Level Token (`xapp-`) を取得
3. **Bot Token Scopes** を設定:
   - `channels:history` — チャンネルメッセージの読み取り
   - `channels:read` — チャンネル情報の取得
   - `chat:write` — メッセージの送信
   - `users:read` — ユーザー情報の取得（メンション変換用）
4. **Event Subscriptions** でイベントを購読:
   - `message.channels`
5. ワークスペースにアプリをインストールし、Bot Token (`xoxb-`) を取得

## セットアップ

```bash
# バックエンド
poetry install

# フロントエンド
cd ui
npm install

# 環境変数（MPS未対応オペレーションのCPUフォールバック）
export PYTORCH_ENABLE_MPS_FALLBACK=1
```

## 起動

```bash
# 開発時: バックエンドとフロントエンドを別々に起動
poetry run python -m slack_talk      # Python バックエンド
cd ui && npm run tauri dev           # Tauri + React UI

# 配布時: Tauri がPythonプロセスをサイドカーとして自動起動
cd ui && npm run tauri build
```

## ドキュメント

- [システム概要仕様書](docs/slack_tts_system_overview_v1.docx)
- [詳細設計書](docs/plans/2026-03-23-slack-talk-detail-design.md)
- [実装計画書](docs/plans/2026-03-23-slack-talk-implementation.md)

## ライセンス

TBD
