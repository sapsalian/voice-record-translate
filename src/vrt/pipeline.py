import math
import threading
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict
from pathlib import Path

from .config import Config
from .session import load_session, save_session
from .srt import write_srt
from .transcribe import Segment, transcribe
from .translate import CHUNK_SIZE, CorrectedSegment, _ChunkCtx, translate

_executor = ThreadPoolExecutor(max_workers=4)


class ProcessingWorker:
    def __init__(
        self,
        session_id: str,
        file_path: str,
        config: Config,
        reset: bool = False,
    ) -> None:
        self.session_id = session_id
        self.file_path = file_path
        self.config = config
        self.reset = reset
        self._cancel_event = threading.Event()

    def cancel(self) -> None:
        self._cancel_event.set()

    def submit(self) -> None:
        _executor.submit(self._run)

    def _run(self) -> None:
        session = load_session(self.session_id)
        if session is None:
            return
        try:
            # ── 전사 ──────────────────────────────────────────────────
            if session.cp_segments is not None and not self.reset:
                segments = [
                    Segment(**{k: v for k, v in s.items() if k in Segment.__dataclass_fields__})
                    for s in session.cp_segments
                ]
            else:
                session.progress_message = "전사 중..."
                session.progress = 0
                save_session(session)

                def _on_transcribe_progress(done: int, total: int) -> None:
                    if self._cancel_event.is_set():
                        return
                    session.progress = int(done / total * 40)
                    session.progress_message = f"전사 중... ({done}/{total}청크)"
                    save_session(session)

                segments = transcribe(
                    self.file_path,
                    api_key=self.config.soniox_api_key,
                    progress_callback=_on_transcribe_progress,
                )

                if self._cancel_event.is_set():
                    session.status = "failed"
                    session.error_message = "취소됨"
                    save_session(session)
                    return

                if not segments:
                    session.status = "failed"
                    session.error_message = "전사 결과가 없습니다."
                    save_session(session)
                    return

                session.cp_segments = [asdict(s) for s in segments]
                save_session(session)

            # ── 번역 ──────────────────────────────────────────────────
            total_chunks = math.ceil(len(segments) / CHUNK_SIZE)
            start_chunk = (session.cp_last_chunk_done + 1) if not self.reset else 0

            initial_ctx: _ChunkCtx | None = None
            initial_corrected: list[CorrectedSegment] | None = None
            if start_chunk > 0 and session.cp_corrected_segments:
                initial_corrected = [
                    CorrectedSegment(**s) for s in session.cp_corrected_segments
                ]
                if session.cp_ctx_summary:
                    initial_ctx = _ChunkCtx(
                        summary=session.cp_ctx_summary,
                        recent_pairs=[tuple(p) for p in session.cp_ctx_recent_pairs],  # type: ignore[arg-type]
                    )

            session.progress = 50 + int(start_chunk / total_chunks * 40) if total_chunks else 90
            session.progress_message = f"번역 중... ({start_chunk}/{total_chunks}청크)"
            save_session(session)

            def _on_chunk_done(
                chunk_idx: int, all_corrected: list[CorrectedSegment], ctx: _ChunkCtx
            ) -> None:
                session.cp_last_chunk_done = chunk_idx
                session.cp_corrected_segments = [s.model_dump() for s in all_corrected]
                session.cp_ctx_summary = ctx.summary
                session.cp_ctx_recent_pairs = [list(p) for p in ctx.recent_pairs]
                session.progress = 50 + int((chunk_idx + 1) / total_chunks * 40)
                session.progress_message = f"번역 중... ({chunk_idx + 1}/{total_chunks}청크)"
                save_session(session)

            translated = translate(
                segments,
                target_lang=self.config.target_lang,
                api_key=self.config.openai_api_key,
                start_chunk=start_chunk,
                initial_ctx=initial_ctx,
                initial_corrected=initial_corrected,
                on_chunk_done=_on_chunk_done,
            )

            if self._cancel_event.is_set():
                session.status = "failed"
                session.error_message = "취소됨"
                save_session(session)
                return

            # ── SRT 생성 ──────────────────────────────────────────────
            session.progress = 90
            session.progress_message = "SRT 파일 생성 중..."
            save_session(session)

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
                {
                    "start": s.start,
                    "end": s.end,
                    "speaker": s.speaker,
                    "original": s.original,
                    "translated": s.translated,
                }
                for s in translated
            ]
            session.duration = translated[-1].end if translated else None
            session.status = "completed"
            session.cp_segments = None
            session.cp_corrected_segments = []
            session.cp_last_chunk_done = -1
            session.cp_ctx_summary = ""
            session.cp_ctx_recent_pairs = []
            session.progress = 100
            session.progress_message = "완료"
            save_session(session)

        except Exception as e:
            session.status = "failed"
            session.error_message = str(e)
            save_session(session)


def start_processing(
    session_id: str,
    file_path: str,
    config: Config,
    reset: bool = False,
) -> ProcessingWorker:
    worker = ProcessingWorker(session_id, file_path, config, reset)
    worker.submit()
    return worker
