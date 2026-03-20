[English](README.md) | [한국어](README.ko.md) | [中文](README.zh.md) | [Español](README.es.md) | [Français](README.fr.md) | [Deutsch](README.de.md) | [Português](README.pt.md)

# VRT — Voice Record & Translate

音声ファイルをアップロードするだけで、話者分離付き文字起こし＋翻訳まで自動処理するデスクトップアプリ。

https://github.com/user-attachments/assets/2542f517-85cc-47de-b15a-1d8a623a66fe


---

## 主な機能

- 音声ファイルの文字起こし (MP3, M4A, WAV, OGG, FLAC, AAC, WMA, Opus)
- 話者分離 — 話者1 / 話者2 の自動識別＋名前変更に対応
- 150分超のファイルも自動分割処理
- 校正＋翻訳を同時実行 — 20言語対応
- SRT字幕ファイルのエクスポート (原文 / 翻訳文)
- セッションの保存と再開

---

## ダウンロード

→ **[Releases](https://github.com/sapsalian/voice-record-translate/releases)** から最新版をダウンロード

| OS | ファイル |
|----|----------|
| macOS | `VRT-macos.zip` |
| Windows | `VRT-windows.zip` |

### macOS インストール

1. `VRT-macos.zip` を解凍
2. `VRT.app` をアプリケーションフォルダへ移動
3. 起動時に **「開発元を確認できません」** と表示されたら:
   - **システム設定 → プライバシーとセキュリティ** を開く
   - 下部に表示された VRT のブロックメッセージを確認
   - **「このまま開く」** をクリック
   - ダイアログで **「開く」** をクリック

### Windows インストール

1. `VRT-windows.zip` を解凍
2. `VRT/VRT.exe` を実行
3. **Windows SmartScreen** の警告が表示されたら:
   - **「詳細情報」** をクリック
   - **「実行」** をクリック

> Windows 10 バージョン 1803 未満の場合は [Edge WebView2 ランタイム](https://developer.microsoft.com/en-us/microsoft-edge/webview2/) を別途インストールしてください。

---

## 初期設定

初回起動時に設定画面で API キーを入力してください。

| 項目 | 取得先 |
|------|--------|
| Soniox API Key | [soniox.com](https://soniox.com) |
| OpenAI API Key | [platform.openai.com](https://platform.openai.com) |

> **課金に注意**: 文字起こし (Soniox) と翻訳 (OpenAI GPT-4.1) はいずれも有料 API です。
> 設定は `~/.vrt/config.json` に保存されます。
>
> **料金の目安 — 1時間の音声ファイル** (約130語/分、発話率80%を想定):
>
> | サービス | 目安料金 |
> |----------|----------|
> | Soniox 文字起こし | ~$0.10 |
> | OpenAI GPT-4.1 翻訳 | ~$0.25 |
> | **合計** | **~$0.35** |
>
> *実際の料金は発話密度、言語ペア、現在の API 料金によって異なります。*
> 現在の料金を確認: [Soniox](https://soniox.com/pricing/) · [OpenAI](https://platform.openai.com/docs/pricing)

---

## 開発環境

### 動作要件

- Python 3.10+
- Node.js 20+

### インストールと実行

```bash
# 依存関係のインストール
pip install -e ".[dev]"

# フロントエンド依存関係のインストール
cd frontend && npm install && cd ..

# 開発モード（フロントエンドのホットリロード）
# ターミナル 1
cd frontend && npm run dev
# ターミナル 2
VRT_DEV=1 vrt

# テスト
pytest tests/ -v

# プロダクションビルド後に実行
make run
```

### アプリのビルド (PyInstaller)

```bash
make build-app-macos    # → build/dist/VRT.app
```

Windows ビルドは GitHub Actions で自動実行されます（タグ push 時）。

---

## 技術スタック

| 分野 | 技術 |
|------|------|
| バックエンド | Python, Flask, pywebview |
| フロントエンド | React, TypeScript, Tailwind CSS v4 |
| 文字起こし | Soniox (話者分離) |
| 翻訳 | OpenAI GPT-4.1 (Structured Output) |
| パッケージング | PyInstaller, GitHub Actions |
