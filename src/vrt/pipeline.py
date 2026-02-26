import math
import os
from dataclasses import asdict
from pathlib import Path

from PyQt6.QtCore import QThread, pyqtSignal

from .config import Config
from .session import create_session, save_session
from .srt import write_srt
from .transcribe import transcribe
from .translate import CHUNK_SIZE, CorrectedSegment, _ChunkCtx, translate


class ProcessingWorker(QThread):
    progress = pyqtSignal(str, int)   # (step_description, percent 0-100)
    finished = pyqtSignal(str, str)   # (original_srt_path, translated_srt_path)
    error = pyqtSignal(str)

    def __init__(self, file_path: str, config: Config, reset: bool = False) -> None:
        super().__init__()
        self.file_path = file_path
        self.config = config
        self.reset = reset

    def run(self) -> None:
        session = create_session(
            title=os.path.basename(self.file_path),
            audio_src=self.file_path,
            target_lang=self.config.target_lang,
        )
        try:
            # ── 전사 ──────────────────────────────────────────────────
            self.progress.emit("전사 중...", 0)
            segments = transcribe(
                self.file_path,
                api_key=self.config.soniox_api_key,
            )
            if not segments:
                self.error.emit("전사 결과가 없습니다.")
                return
            session.cp_segments = [asdict(s) for s in segments]
            save_session(session)

            # ── 번역 ──────────────────────────────────────────────────
            total_chunks = math.ceil(len(segments) / CHUNK_SIZE)
            self.progress.emit(f"번역 중... (1/{total_chunks}청크)", 50)

            def _on_progress(done: int, total: int) -> None:
                pct = 50 + int((done / total) * 40)
                self.progress.emit(f"번역 중... ({done}/{total}청크)", pct)

            def _on_chunk_done(chunk_idx: int, all_corrected: list[CorrectedSegment], ctx: _ChunkCtx) -> None:
                session.cp_last_chunk_done = chunk_idx
                session.cp_corrected_segments = [s.model_dump() for s in all_corrected]
                session.cp_ctx_summary = ctx.summary
                session.cp_ctx_recent_pairs = [list(p) for p in ctx.recent_pairs]
                save_session(session)

            translated = translate(
                segments,
                target_lang=self.config.target_lang,
                api_key=self.config.openai_api_key,
                progress_callback=_on_progress,
                on_chunk_done=_on_chunk_done,
            )

            # ── SRT 생성 ──────────────────────────────────────────────
            self.progress.emit("SRT 파일 생성 중...", 90)
            base = Path(self.file_path).with_suffix("")
            original_path = str(base) + ".original.srt"
            translated_path = str(base) + f".{self.config.target_lang}.srt"

            write_srt(
                [(s.start, s.end, s.original) for s in translated],
                original_path,
            )
            write_srt(
                [(s.start, s.end, s.translated) for s in translated],
                translated_path,
            )

            speaker_ids = sorted({s.speaker for s in translated if s.speaker})
            session.speaker_names = {sid: f"화자 {i + 1}" for i, sid in enumerate(speaker_ids)}
            session.segments = [
                {"start": s.start, "end": s.end, "speaker": s.speaker,
                 "original": s.original, "translated": s.translated}
                for s in translated
            ]
            session.duration = translated[-1].end if translated else None
            session.status = "completed"
            session.cp_segments = None
            session.cp_corrected_segments = []
            session.cp_last_chunk_done = -1
            session.cp_ctx_summary = ""
            session.cp_ctx_recent_pairs = []
            save_session(session)

            self.progress.emit("완료", 100)
            self.finished.emit(original_path, translated_path)

        except Exception as e:
            session.status = "failed"
            session.error_message = str(e)
            save_session(session)
            self.error.emit(str(e))
