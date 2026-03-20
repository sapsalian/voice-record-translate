[English](README.md) | [한국어](README.ko.md) | [日本語](README.ja.md) | [中文](README.zh.md) | [Español](README.es.md) | [Français](README.fr.md) | [Deutsch](README.de.md)

# VRT — Voice Record & Translate

Faça upload de um arquivo de áudio → transcrição com separação de falantes → tradução — tudo em um aplicativo de desktop.

https://github.com/user-attachments/assets/2542f517-85cc-47de-b15a-1d8a623a66fe


---

## Funcionalidades

- Transcrição de áudio (MP3, M4A, WAV, OGG, FLAC, AAC, WMA, Opus)
- Diarização de falantes — detecção automática de Falante 1 / Falante 2, com suporte a renomear
- Processamento automático em segmentos para arquivos com mais de 150 minutos
- Correção + tradução em uma única etapa — suporte a 20 idiomas
- Exportação de legendas SRT (original / traduzido)
- Salvar e retomar sessão

---

## Download

→ Baixe a versão mais recente em **[Releases](https://github.com/sapsalian/voice-record-translate/releases)**

| SO | Arquivo |
|----|---------|
| macOS | `VRT-macos.zip` |
| Windows | `VRT-windows.zip` |

### Instalação no macOS

1. Descompacte `VRT-macos.zip`
2. Mova `VRT.app` para a pasta Aplicativos
3. Se aparecer **"desenvolvedor não pode ser verificado"**:
   - Abra **Configurações do Sistema → Privacidade e Segurança**
   - Role para baixo até encontrar a mensagem de bloqueio do VRT
   - Clique em **"Abrir mesmo assim"**
   - Confirme clicando em **"Abrir"**

### Instalação no Windows

1. Descompacte `VRT-windows.zip`
2. Execute `VRT/VRT.exe`
3. Se o **Windows SmartScreen** exibir um aviso:
   - Clique em **"Mais informações"**
   - Clique em **"Executar mesmo assim"**

> Se estiver no Windows 10 versão 1803 ou anterior, instale o [Edge WebView2 Runtime](https://developer.microsoft.com/en-us/microsoft-edge/webview2/) separadamente.

---

## Configuração

Insira suas chaves de API na tela de configurações na primeira execução.

| Item | Provedor |
|------|----------|
| Soniox API Key | [soniox.com](https://soniox.com) |
| OpenAI API Key | [platform.openai.com](https://platform.openai.com) |

> **Atenção ao custo**: Tanto a transcrição (Soniox) quanto a tradução (OpenAI GPT-4.1) utilizam APIs pagas.
> As configurações são salvas em `~/.vrt/config.json`.
>
> **Custo estimado — 1 hora de áudio** (aprox. 130 palavras/min, taxa de fala de 80%):
>
> | Serviço | Custo estimado |
> |---------|----------------|
> | Transcrição Soniox | ~$0.10 |
> | Tradução OpenAI GPT-4.1 | ~$0.25 |
> | **Total** | **~$0.35** |
>
> *Os custos reais variam conforme a densidade de fala, o par de idiomas e os preços atuais da API.*
> Verificar preços atuais: [Soniox](https://soniox.com/pricing/) · [OpenAI](https://platform.openai.com/docs/pricing)

---

## Desenvolvimento

### Requisitos

- Python 3.10+
- Node.js 20+

### Instalação e execução

```bash
# Instalar dependências
pip install -e ".[dev]"

# Instalar dependências do frontend
cd frontend && npm install && cd ..

# Modo desenvolvimento (hot-reload do frontend)
# Terminal 1
cd frontend && npm run dev
# Terminal 2
VRT_DEV=1 vrt

# Executar testes
pytest tests/ -v

# Build de produção e execução
make run
```

### Build do aplicativo (PyInstaller)

```bash
make build-app-macos    # → build/dist/VRT.app
```

Os builds para Windows são executados automaticamente via GitHub Actions (ao fazer push de uma tag).

---

## Stack tecnológico

| Área | Tecnologia |
|------|------------|
| Backend | Python, Flask, pywebview |
| Frontend | React, TypeScript, Tailwind CSS v4 |
| Transcrição | Soniox (diarização de falantes) |
| Tradução | OpenAI GPT-4.1 (Structured Output) |
| Empacotamento | PyInstaller, GitHub Actions |
