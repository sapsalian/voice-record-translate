[English](README.md) | [한국어](README.ko.md) | [日本語](README.ja.md) | [中文](README.zh.md) | [Español](README.es.md) | [Deutsch](README.de.md) | [Português](README.pt.md)

# VRT — Voice Record & Translate

Importez un fichier audio → transcription avec identification des locuteurs → traduction — tout en une seule application de bureau.

https://github.com/user-attachments/assets/2995ecc1-a19c-4fa3-80d7-f3a459098943


---

## Fonctionnalités

- Transcription audio (MP3, M4A, WAV, OGG, FLAC, AAC, WMA, Opus)
- Diarisation des locuteurs — détection automatique du Locuteur 1 / Locuteur 2, renommage pris en charge
- Traitement automatique par segments pour les fichiers de plus de 150 minutes
- Correction + traduction en une seule étape — 20 langues prises en charge
- Export de sous-titres SRT (original / traduit)
- Sauvegarde et reprise de session

---

## Téléchargement

→ Téléchargez la dernière version depuis **[Releases](https://github.com/sapsalian/voice-record-translate/releases)**

| OS | Fichier |
|----|---------|
| macOS | `VRT-macos.zip` |
| Windows | `VRT-windows.zip` |

### Installation sur macOS

1. Décompressez `VRT-macos.zip`
2. Déplacez `VRT.app` dans le dossier Applications
3. Si au lancement apparaît **« le développeur ne peut pas être vérifié »** :
   - Ouvrez **Réglages système → Confidentialité et sécurité**
   - Faites défiler vers le bas pour trouver le message de blocage de VRT
   - Cliquez sur **« Ouvrir quand même »**
   - Confirmez en cliquant **« Ouvrir »**

### Installation sur Windows

1. Décompressez `VRT-windows.zip`
2. Lancez `VRT/VRT.exe`
3. Si **Windows SmartScreen** affiche un avertissement :
   - Cliquez sur **« Informations complémentaires »**
   - Cliquez sur **« Exécuter quand même »**

> Si vous utilisez Windows 10 version 1803 ou antérieure, installez séparément le [Edge WebView2 Runtime](https://developer.microsoft.com/en-us/microsoft-edge/webview2/).

---

## Configuration

Saisissez vos clés API dans l'écran des paramètres au premier lancement.

| Élément | Fournisseur |
|---------|-------------|
| Soniox API Key | [soniox.com](https://soniox.com) |
| OpenAI API Key | [platform.openai.com](https://platform.openai.com) |

> **Note de facturation** : La transcription (Soniox) et la traduction (OpenAI GPT-4.1) utilisent toutes deux des API payantes.
> Les paramètres sont enregistrés dans `~/.vrt/config.json`.
>
> **Coût estimé — 1 heure d'audio** (environ 130 mots/min, taux de parole de 80 %) :
>
> | Service | Coût estimé |
> |---------|-------------|
> | Transcription Soniox | ~$0.10 |
> | Traduction OpenAI GPT-4.1 | ~$0.25 |
> | **Total** | **~$0.35** |
>
> *Les coûts réels varient selon la densité de parole, la paire de langues et les tarifs actuels de l'API.*
> Consulter les tarifs actuels : [Soniox](https://soniox.com/pricing/) · [OpenAI](https://platform.openai.com/docs/pricing)

---

## Développement

### Prérequis

- Python 3.10+
- Node.js 20+

### Installation et exécution

```bash
# Installer les dépendances
pip install -e ".[dev]"

# Installer les dépendances du frontend
cd frontend && npm install && cd ..

# Mode développement (hot-reload du frontend)
# Terminal 1
cd frontend && npm run dev
# Terminal 2
VRT_DEV=1 vrt

# Lancer les tests
pytest tests/ -v

# Compiler et lancer en production
make run
```

### Compiler l'application (PyInstaller)

```bash
make build-app-macos    # → build/dist/VRT.app
```

Les compilations Windows s'exécutent automatiquement via GitHub Actions (lors d'un push de tag).

---

## Stack technique

| Domaine | Technologie |
|---------|-------------|
| Backend | Python, Flask, pywebview |
| Frontend | React, TypeScript, Tailwind CSS v4 |
| Transcription | Soniox (diarisation des locuteurs) |
| Traduction | OpenAI GPT-4.1 (Structured Output) |
| Packaging | PyInstaller, GitHub Actions |
