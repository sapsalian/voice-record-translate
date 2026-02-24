from pathlib import Path

from PyQt6.QtCore import QThread, pyqtSignal

from .config import Config
from .srt import write_srt
from .transcribe import transcribe
from .translate import translate


class ProcessingWorker(QThread):
    progress = pyqtSignal(str, int)   # (step_description, percent 0-100)
    finished = pyqtSignal(str, str)   # (original_srt_path, translated_srt_path)
    error = pyqtSignal(str)

    def __init__(self, file_path: str, config: Config) -> None:
        super().__init__()
        self.file_path = file_path
        self.config = config

    def run(self) -> None:
        try:
            self.progress.emit("전사 중...", 0)
            segments = transcribe(
                self.file_path,
                api_key=self.config.api_key,
                language=self.config.source_lang or None,
            )
            if not segments:
                self.error.emit("전사 결과가 없습니다.")
                return

            self.progress.emit("번역 중...", 50)
            translated = translate(
                segments,
                source_lang=self.config.source_lang,
                target_lang=self.config.target_lang,
                api_key=self.config.api_key,
            )

            self.progress.emit("SRT 파일 생성 중...", 90)
            base = Path(self.file_path).with_suffix("")
            original_path = str(base) + f".{self.config.source_lang}.srt"
            translated_path = str(base) + f".{self.config.target_lang}.srt"

            write_srt(
                [(s.start, s.end, s.original) for s in translated],
                original_path,
            )
            write_srt(
                [(s.start, s.end, s.translated) for s in translated],
                translated_path,
            )

            self.progress.emit("완료", 100)
            self.finished.emit(original_path, translated_path)

        except Exception as e:
            self.error.emit(str(e))
