[English](README.md) | [한국어](README.ko.md) | [日本語](README.ja.md) | [中文](README.zh.md) | [Français](README.fr.md) | [Deutsch](README.de.md) | [Português](README.pt.md)

# VRT — Voice Record & Translate

Sube un archivo de audio → transcripción con separación de hablantes → traducción — todo en una aplicación de escritorio.

https://github.com/user-attachments/assets/2995ecc1-a19c-4fa3-80d7-f3a459098943


---

## Características

- Transcripción de audio (MP3, M4A, WAV, OGG, FLAC, AAC, WMA, Opus)
- Diarización de hablantes — detección automática de Hablante 1 / Hablante 2, con soporte para renombrar
- Procesamiento automático por segmentos para archivos de más de 150 minutos
- Corrección + traducción en un solo paso — compatible con 20 idiomas
- Exportación de subtítulos SRT (original / traducido)
- Guardado y reanudación de sesiones

---

## Descarga

→ Descarga la última versión desde **[Releases](https://github.com/sapsalian/voice-record-translate/releases)**

| SO | Archivo |
|----|---------|
| macOS | `VRT-macos.zip` |
| Windows | `VRT-windows.zip` |

### Instalación en macOS

1. Descomprime `VRT-macos.zip`
2. Mueve `VRT.app` a la carpeta Aplicaciones
3. Si al iniciar aparece **"no se puede verificar el desarrollador"**:
   - Abre **Configuración del Sistema → Privacidad y Seguridad**
   - Desplázate hacia abajo hasta encontrar el mensaje de VRT bloqueado
   - Haz clic en **"Abrir de todas formas"**
   - Confirma haciendo clic en **"Abrir"**

### Instalación en Windows

1. Descomprime `VRT-windows.zip`
2. Ejecuta `VRT/VRT.exe`
3. Si aparece la advertencia de **Windows SmartScreen**:
   - Haz clic en **"Más información"**
   - Haz clic en **"Ejecutar de todas formas"**

> Si usas Windows 10 versión 1803 o anterior, instala el [Edge WebView2 Runtime](https://developer.microsoft.com/en-us/microsoft-edge/webview2/) por separado.

---

## Configuración

Ingresa tus claves API en la pantalla de configuración al iniciar por primera vez.

| Elemento | Proveedor |
|----------|-----------|
| Soniox API Key | [soniox.com](https://soniox.com) |
| OpenAI API Key | [platform.openai.com](https://platform.openai.com) |

> **Nota de facturación**: Tanto la transcripción (Soniox) como la traducción (OpenAI GPT-4.1) usan APIs de pago.
> La configuración se guarda en `~/.vrt/config.json`.
>
> **Costo estimado — 1 hora de audio** (aprox. 130 palabras/min, tasa de habla del 80%):
>
> | Servicio | Costo estimado |
> |----------|----------------|
> | Transcripción Soniox | ~$0.10 |
> | Traducción OpenAI GPT-4.1 | ~$0.25 |
> | **Total** | **~$0.35** |
>
> *Los costos reales varían según la densidad del habla, el par de idiomas y los precios actuales de la API.*
> Ver precios actuales: [Soniox](https://soniox.com/pricing/) · [OpenAI](https://platform.openai.com/docs/pricing)

---

## Desarrollo

### Requisitos

- Python 3.10+
- Node.js 20+

### Instalar y ejecutar

```bash
# Instalar dependencias
pip install -e ".[dev]"

# Instalar dependencias del frontend
cd frontend && npm install && cd ..

# Modo desarrollo (hot-reload del frontend)
# Terminal 1
cd frontend && npm run dev
# Terminal 2
VRT_DEV=1 vrt

# Ejecutar pruebas
pytest tests/ -v

# Compilar y ejecutar en producción
make run
```

### Compilar la aplicación (PyInstaller)

```bash
make build-app-macos    # → build/dist/VRT.app
```

Las compilaciones para Windows se ejecutan automáticamente mediante GitHub Actions (al hacer push de una etiqueta).

---

## Stack tecnológico

| Área | Tecnología |
|------|------------|
| Backend | Python, Flask, pywebview |
| Frontend | React, TypeScript, Tailwind CSS v4 |
| Transcripción | Soniox (diarización de hablantes) |
| Traducción | OpenAI GPT-4.1 (Structured Output) |
| Empaquetado | PyInstaller, GitHub Actions |
