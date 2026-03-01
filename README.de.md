[English](README.md) | [한국어](README.ko.md) | [日本語](README.ja.md) | [中文](README.zh.md) | [Español](README.es.md) | [Français](README.fr.md) | [Português](README.pt.md)

# VRT — Voice Record & Translate

Lade eine Audiodatei hoch → Transkription mit Sprechertrennung → Übersetzung — alles in einer Desktop-App.

---

## Funktionen

- Audiotranskription (MP3, M4A, WAV, OGG, FLAC, AAC, WMA, Opus)
- Sprecherdiarisierung — automatische Erkennung von Sprecher 1 / Sprecher 2, Umbenennung möglich
- Automatische Segmentverarbeitung für Dateien über 150 Minuten
- Korrektur + Übersetzung in einem Schritt — 20 Sprachen unterstützt
- Export von SRT-Untertiteln (Original / Übersetzung)
- Sitzung speichern und fortsetzen

---

## Download

→ Lade die neueste Version von **[Releases](https://github.com/sapsalian/voice-record-translate/releases)** herunter

| Betriebssystem | Datei |
|----------------|-------|
| macOS | `VRT-macos.zip` |
| Windows | `VRT-windows.zip` |

### macOS-Installation

1. `VRT-macos.zip` entpacken
2. `VRT.app` in den Ordner „Programme" verschieben
3. Beim ersten Start: Falls „Entwickler kann nicht überprüft werden" erscheint → **Rechtsklick auf VRT.app → Öffnen**

### Windows-Installation

1. `VRT-windows.zip` entpacken
2. `VRT/VRT.exe` ausführen

> Bei Windows 10 Version 1803 oder älter: [Edge WebView2 Runtime](https://developer.microsoft.com/en-us/microsoft-edge/webview2/) separat installieren.

---

## Konfiguration

Gib deine API-Schlüssel beim ersten Start im Einstellungsbildschirm ein.

| Element | Anbieter |
|---------|----------|
| Soniox API Key | [soniox.com](https://soniox.com) |
| OpenAI API Key | [platform.openai.com](https://platform.openai.com) |

> **Kostenhinweis**: Sowohl Transkription (Soniox) als auch Übersetzung (OpenAI GPT-4.1) nutzen kostenpflichtige APIs.
> Einstellungen werden in `~/.vrt/config.json` gespeichert.

---

## Entwicklung

### Voraussetzungen

- Python 3.10+
- Node.js 20+

### Installation und Ausführung

```bash
# Abhängigkeiten installieren
pip install -e ".[dev]"

# Frontend-Abhängigkeiten installieren
cd frontend && npm install && cd ..

# Entwicklungsmodus (Frontend-Hot-Reload)
# Terminal 1
cd frontend && npm run dev
# Terminal 2
VRT_DEV=1 vrt

# Tests ausführen
pytest tests/ -v

# Produktions-Build und Ausführung
make run
```

### App bauen (PyInstaller)

```bash
make build-app-macos    # → build/dist/VRT.app
```

Windows-Builds werden automatisch über GitHub Actions ausgeführt (bei Tag-Push).

---

## Tech-Stack

| Bereich | Technologie |
|---------|-------------|
| Backend | Python, Flask, pywebview |
| Frontend | React, TypeScript, Tailwind CSS v4 |
| Transkription | Soniox (Sprecherdiarisierung) |
| Übersetzung | OpenAI GPT-4.1 (Structured Output) |
| Paketierung | PyInstaller, GitHub Actions |
