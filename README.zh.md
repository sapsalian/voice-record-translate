[English](README.md) | [한국어](README.ko.md) | [日本語](README.ja.md) | [Español](README.es.md) | [Français](README.fr.md) | [Deutsch](README.de.md) | [Português](README.pt.md)

# VRT — Voice Record & Translate

上传音频文件，自动完成说话人分离转录与翻译的桌面应用。

https://github.com/user-attachments/assets/2995ecc1-a19c-4fa3-80d7-f3a459098943


---

## 主要功能

- 音频文件转录 (MP3, M4A, WAV, OGG, FLAC, AAC, WMA, Opus)
- 说话人分离 — 自动识别说话人1 / 说话人2，支持重命名
- 超过150分钟的文件自动分段处理
- 同步执行校正与翻译 — 支持20种语言
- 导出SRT字幕文件（原文 / 译文）
- 保存与恢复会话

---

## 下载

→ 从 **[Releases](https://github.com/sapsalian/voice-record-translate/releases)** 下载最新版本

| 操作系统 | 文件 |
|----------|------|
| macOS | `VRT-macos.zip` |
| Windows | `VRT-windows.zip` |

### macOS 安装

1. 解压 `VRT-macos.zip`
2. 将 `VRT.app` 移动到应用程序文件夹
3. 启动时若出现 **"无法验证开发者"** 提示：
   - 打开 **系统设置 → 隐私与安全性**
   - 向下滚动找到 VRT 被阻止的提示
   - 点击 **"仍然打开"**
   - 在弹出对话框中点击 **"打开"**

### Windows 安装

1. 解压 `VRT-windows.zip`
2. 运行 `VRT/VRT.exe`
3. 若出现 **Windows SmartScreen** 警告：
   - 点击 **"更多信息"**
   - 点击 **"仍要运行"**

> 若 Windows 10 版本低于1803，请另行安装 [Edge WebView2 运行时](https://developer.microsoft.com/en-us/microsoft-edge/webview2/)。

---

## 初始配置

首次启动时在设置界面输入 API 密钥。

| 项目 | 获取地址 |
|------|----------|
| Soniox API Key | [soniox.com](https://soniox.com) |
| OpenAI API Key | [platform.openai.com](https://platform.openai.com) |

> **注意费用**: 转录 (Soniox) 与翻译 (OpenAI GPT-4.1) 均使用付费 API。
> 配置保存于 `~/.vrt/config.json`。
>
> **预估费用 — 1小时音频** (约130词/分钟，发话率80%):
>
> | 服务 | 预估费用 |
> |------|----------|
> | Soniox 转录 | ~$0.10 |
> | OpenAI GPT-4.1 翻译 | ~$0.25 |
> | **合计** | **~$0.35** |
>
> *实际费用因发话密度、语言组合及当前 API 价格而异。*
> 查看当前价格: [Soniox](https://soniox.com/pricing/) · [OpenAI](https://platform.openai.com/docs/pricing)

---

## 开发环境

### 系统要求

- Python 3.10+
- Node.js 20+

### 安装与运行

```bash
# 安装依赖
pip install -e ".[dev]"

# 安装前端依赖
cd frontend && npm install && cd ..

# 开发模式（前端热重载）
# 终端 1
cd frontend && npm run dev
# 终端 2
VRT_DEV=1 vrt

# 运行测试
pytest tests/ -v

# 构建生产版本并运行
make run
```

### 构建应用 (PyInstaller)

```bash
make build-app-macos    # → build/dist/VRT.app
```

Windows 构建通过 GitHub Actions 自动执行（推送标签时触发）。

---

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端 | Python, Flask, pywebview |
| 前端 | React, TypeScript, Tailwind CSS v4 |
| 转录 | Soniox（说话人分离） |
| 翻译 | OpenAI GPT-4.1 (Structured Output) |
| 打包 | PyInstaller, GitHub Actions |
