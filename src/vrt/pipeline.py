from dataclasses import asdict
from pathlib import Path

from PyQt6.QtCore import QThread, pyqtSignal

from .checkpoint import Checkpoint, delete_checkpoint, load_checkpoint, save_checkpoint
from .config import Config
from .srt import write_srt
from .transcribe import Segment, transcribe
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
        try:
            # 체크포인트 로드 (reset=True면 삭제 후 무시)
            if self.reset:
                delete_checkpoint(self.file_path)
            cp = load_checkpoint(self.file_path)
            if cp and (cp.source_lang != self.config.source_lang or cp.target_lang != self.config.target_lang):
                cp = None  # lang 불일치 체크포인트는 무시

            # ── 전사 ──────────────────────────────────────────────────
            if cp and cp.segments is not None:
                self.progress.emit("이전 전사 결과 불러오는 중...", 40)
                valid = Segment.__dataclass_fields__.keys()
                segments = [Segment(**{k: v for k, v in s.items() if k in valid}) for s in cp.segments]
            else:
                self.progress.emit("전사 중...", 0)
                segments = transcribe(
                    self.file_path,
                    api_key=self.config.soniox_api_key,
                    language=self.config.source_lang or None,
                )
                if not segments:
                    self.error.emit("전사 결과가 없습니다.")
                    return
                cp = Checkpoint(
                    file_path=self.file_path,
                    source_lang=self.config.source_lang,
                    target_lang=self.config.target_lang,
                    segments=[asdict(s) for s in segments],
                )
                save_checkpoint(cp)

            # ── 번역 ──────────────────────────────────────────────────
            import math
            total_chunks = math.ceil(len(segments) / CHUNK_SIZE)

            start_chunk = 0
            initial_ctx: _ChunkCtx | None = None
            initial_corrected: list[CorrectedSegment] | None = None

            if cp and cp.last_chunk_done >= 0:
                start_chunk = cp.last_chunk_done + 1
                initial_corrected = [CorrectedSegment(**s) for s in cp.corrected_segments]
                if cp.ctx_summary:
                    initial_ctx = _ChunkCtx(
                        summary=cp.ctx_summary,
                        recent_pairs=[tuple(p) for p in cp.ctx_recent_pairs],  # type: ignore[arg-type]
                    )

            self.progress.emit(f"번역 중... ({start_chunk + 1}/{total_chunks}청크)", 50)

            def _on_progress(done: int, total: int) -> None:
                pct = 50 + int((done / total) * 40)
                self.progress.emit(f"번역 중... ({done}/{total}청크)", pct)

            def _on_chunk_done(chunk_idx: int, all_corrected: list[CorrectedSegment], ctx: _ChunkCtx) -> None:
                assert cp is not None
                cp.last_chunk_done = chunk_idx
                cp.corrected_segments = [s.model_dump() for s in all_corrected]
                cp.ctx_summary = ctx.summary
                cp.ctx_recent_pairs = [list(p) for p in ctx.recent_pairs]
                save_checkpoint(cp)

            translated = translate(
                segments,
                source_lang=self.config.source_lang,
                target_lang=self.config.target_lang,
                api_key=self.config.openai_api_key,
                progress_callback=_on_progress,
                start_chunk=start_chunk,
                initial_ctx=initial_ctx,
                initial_corrected=initial_corrected,
                on_chunk_done=_on_chunk_done,
            )

            # ── SRT 생성 ──────────────────────────────────────────────
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

            delete_checkpoint(self.file_path)
            self.progress.emit("완료", 100)
            self.finished.emit(original_path, translated_path)

        except Exception as e:
            self.error.emit(str(e))
