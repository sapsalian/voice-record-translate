[English](README.md) | [日本語](README.ja.md) | [中文](README.zh.md) | [Español](README.es.md) | [Français](README.fr.md) | [Deutsch](README.de.md) | [Português](README.pt.md)

# VRT — Voice Record & Translate

음성 파일을 업로드하면 화자 분리 전사 + 번역까지 자동으로 처리해주는 데스크탑 앱.

---

https://github.com/user-attachments/assets/2542f517-85cc-47de-b15a-1d8a623a66fe


---

## 주요 기능

- 음성 파일 전사 (MP3, M4A, WAV, OGG, FLAC, AAC, WMA, Opus)
- 화자 분리 — 화자 1 / 화자 2 자동 구분 + 이름 변경 가능
- 150분 초과 파일도 자동 분할 처리
- 교정 + 번역 동시 수행 — 20개 언어 지원
- SRT 자막 파일 내보내기 (원문 / 번역문)
- 세션 저장 및 재개

---

## 다운로드

→ **[Releases](https://github.com/sapsalian/voice-record-translate/releases)** 에서 최신 버전 다운로드

| OS | 파일 |
|----|------|
| macOS | `VRT-macos.zip` |
| Windows | `VRT-windows.zip` |

### macOS 설치

1. `VRT-macos.zip` 압축 해제
2. `VRT.app`을 응용 프로그램 폴더로 이동
3. 실행 시 **"개발자를 확인할 수 없음"** 경고가 뜨면:
   - **시스템 설정 → 개인 정보 보호 및 보안** 열기
   - 하단의 VRT 차단 메시지 확인
   - **"그래도 열기"** 클릭
   - 팝업에서 **"열기"** 클릭

### Windows 설치

1. `VRT-windows.zip` 압축 해제
2. `VRT/VRT.exe` 실행
3. **Windows SmartScreen** 경고가 뜨면:
   - **"추가 정보"** 클릭
   - **"실행"** 클릭

> Windows 10 1803 미만이면 [Edge WebView2 런타임](https://developer.microsoft.com/en-us/microsoft-edge/webview2/) 별도 설치 필요.

---

## 초기 설정

첫 실행 시 설정 화면에서 API 키를 입력해주세요.

| 항목 | 발급처 |
|------|--------|
| Soniox API Key | [soniox.com](https://soniox.com) |
| OpenAI API Key | [platform.openai.com](https://platform.openai.com) |

> **과금 주의**: 전사(Soniox)와 번역(OpenAI GPT-4.1) 모두 유료 API입니다.
> 설정은 `~/.vrt/config.json`에 저장됩니다.
>
> **예상 비용 — 1시간 오디오 기준** (약 130단어/분, 발화율 80% 가정):
>
> | 서비스 | 예상 비용 |
> |--------|-----------|
> | Soniox 전사 | ~$0.10 |
> | OpenAI GPT-4.1 번역 | ~$0.25 |
> | **합계** | **~$0.35** |
>
> *실제 비용은 발화 밀도, 언어 조합, 현재 API 가격에 따라 달라질 수 있습니다.*
> 현재 가격 확인: [Soniox](https://soniox.com/pricing/) · [OpenAI](https://platform.openai.com/docs/pricing)

---

## 개발 환경

### 요구사항

- Python 3.10+
- Node.js 20+

### 설치 및 실행

```bash
# 의존성 설치
pip install -e ".[dev]"

# 프론트엔드 의존성 설치
cd frontend && npm install && cd ..

# 개발 모드 실행 (프론트엔드 핫리로드)
# 터미널 1
cd frontend && npm run dev
# 터미널 2
VRT_DEV=1 vrt

# 테스트
pytest tests/ -v

# 프로덕션 빌드 후 실행
make run
```

### 앱 빌드 (PyInstaller)

```bash
make build-app-macos    # → build/dist/VRT.app
```

Windows 빌드는 GitHub Actions에서 자동 실행됩니다 (태그 push 시).

---

## 기술 스택

| 영역 | 기술 |
|------|------|
| 백엔드 | Python, Flask, pywebview |
| 프론트엔드 | React, TypeScript, Tailwind CSS v4 |
| 전사 | Soniox (화자 분리) |
| 번역 | OpenAI GPT-4.1 (Structured Output) |
| 패키징 | PyInstaller, GitHub Actions |
