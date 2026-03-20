[한국어](README.ko.md) | [日本語](README.ja.md) | [中文](README.zh.md) | [Español](README.es.md) | [Français](README.fr.md) | [Deutsch](README.de.md) | [Português](README.pt.md)

# VRT — Voice Record & Translate

Upload an audio file → speaker-separated transcription → translated — all in one desktop app.

---

https://github.com/user-attachments/assets/2542f517-85cc-47de-b15a-1d8a623a66fe

![Main](docs/screenshots/main.png)
![Processing](docs/screenshots/processing.png)
![Viewer](docs/screenshots/viewer.png)

---

## Features

- Audio transcription (MP3, M4A, WAV, OGG, FLAC, AAC, WMA, Opus)
- Speaker diarization — auto-detect Speaker 1 / Speaker 2, rename supported
- Automatic chunked processing for files over 150 minutes
- Correction + translation in one step — supports 20 languages
- Export SRT subtitle files (original / translated)
- Session save & resume

---

## Download

→ Download the latest version from **[Releases](https://github.com/sapsalian/voice-record-translate/releases)**

| OS | File |
|----|------|
| macOS | `VRT-macos.zip` |
| Windows | `VRT-windows.zip` |

### macOS Installation

1. Unzip `VRT-macos.zip`
2. Move `VRT.app` to the Applications folder
3. Double-click to launch — if you see **"developer cannot be verified"**:
   - Open **System Settings → Privacy & Security**
   - Scroll down to find the blocked VRT message
   - Click **"Open Anyway"**
   - Confirm by clicking **"Open"** in the dialog

### Windows Installation

1. Unzip `VRT-windows.zip`
2. Run `VRT/VRT.exe`
3. If **Windows SmartScreen** blocks the app:
   - Click **"More info"**
   - Click **"Run anyway"**

> If you're on Windows 10 version 1803 or earlier, install [Edge WebView2 Runtime](https://developer.microsoft.com/en-us/microsoft-edge/webview2/) separately.

---

## Configuration

Enter your API keys in the settings screen on first launch.

| Item | Provider |
|------|----------|
| Soniox API Key | [soniox.com](https://soniox.com) |
| OpenAI API Key | [platform.openai.com](https://platform.openai.com) |

> **Billing note**: Both transcription (Soniox) and translation (OpenAI GPT-4.1) use paid APIs.
> Settings are saved to `~/.vrt/config.json`.
>
> **Estimated cost — 1 hour of audio** (assuming ~130 words/min, ~80% speech ratio):
>
> | Service | Estimated Cost |
> |---------|----------------|
> | Soniox transcription | ~$0.10 |
> | OpenAI GPT-4.1 translation | ~$0.25 |
> | **Total** | **~$0.35** |
>
> *Actual costs vary by speech density, language pair, and current API pricing.*
> Check current pricing: [Soniox](https://soniox.com/pricing/) · [OpenAI](https://platform.openai.com/docs/pricing)

---

## Development

### Requirements

- Python 3.10+
- Node.js 20+

### Install & Run

```bash
# Install dependencies
pip install -e ".[dev]"

# Install frontend dependencies
cd frontend && npm install && cd ..

# Development mode (frontend hot-reload)
# Terminal 1
cd frontend && npm run dev
# Terminal 2
VRT_DEV=1 vrt

# Run tests
pytest tests/ -v

# Build and run production
make run
```

### Build App (PyInstaller)

```bash
make build-app-macos    # → build/dist/VRT.app
```

Windows builds run automatically via GitHub Actions (on tag push).

---

## Tech Stack

| Area | Technology |
|------|------------|
| Backend | Python, Flask, pywebview |
| Frontend | React, TypeScript, Tailwind CSS v4 |
| Transcription | Soniox (speaker diarization) |
| Translation | OpenAI GPT-4.1 (Structured Output) |
| Packaging | PyInstaller, GitHub Actions |
