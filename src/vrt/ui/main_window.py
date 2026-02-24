from pathlib import Path

from PyQt6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ..checkpoint import load_checkpoint
from ..config import Config
from ..pipeline import ProcessingWorker
from .settings_dialog import SettingsDialog


class MainWindow(QMainWindow):
    def __init__(self, config: Config) -> None:
        super().__init__()
        self.config = config
        self.worker: ProcessingWorker | None = None
        self.selected_file: str = ""

        self.setWindowTitle("Voice Record Translate")
        self.setFixedSize(500, 320)
        self._build_ui()

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        # Top bar: title + settings button
        top = QHBoxLayout()
        top.addStretch()
        settings_btn = QPushButton("⚙ 설정")
        settings_btn.setFixedWidth(80)
        settings_btn.clicked.connect(self._open_settings)
        top.addWidget(settings_btn)
        layout.addLayout(top)

        # File selection
        file_row = QHBoxLayout()
        self._select_btn = QPushButton("📁 파일 선택")
        self._select_btn.clicked.connect(self._select_file)
        file_row.addWidget(self._select_btn)
        self._file_label = QLabel("선택된 파일 없음")
        self._file_label.setWordWrap(True)
        file_row.addWidget(self._file_label, stretch=1)
        layout.addLayout(file_row)

        # Start button
        self._start_btn = QPushButton("▶ 변환 시작")
        self._start_btn.setFixedHeight(40)
        self._start_btn.clicked.connect(self._start)
        layout.addWidget(self._start_btn)

        # Progress bar
        self._progress = QProgressBar()
        self._progress.setRange(0, 100)
        self._progress.setValue(0)
        layout.addWidget(self._progress)

        # Status label
        self._status_label = QLabel("준비")
        self._status_label.setWordWrap(True)
        layout.addWidget(self._status_label)

        layout.addStretch()

    def _open_settings(self) -> None:
        dlg = SettingsDialog(self.config, parent=self)
        dlg.exec()

    def _select_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "녹음 파일 선택",
            "",
            "Audio Files (*.m4a *.mp3 *.wav *.mp4);;All Files (*)",
        )
        if path:
            self.selected_file = path
            self._file_label.setText(Path(path).name)
            cp = load_checkpoint(path)
            if cp and cp.source_lang == self.config.source_lang and cp.target_lang == self.config.target_lang:
                self._status_label.setText("이전 작업이 감지되었습니다. 이어서 진행합니다.")
            else:
                self._status_label.setText("준비")

    def _start(self, reset: bool = False) -> None:
        if not self.selected_file:
            QMessageBox.warning(self, "오류", "파일을 먼저 선택해주세요.")
            return
        if not self.config.api_key:
            QMessageBox.warning(self, "오류", "설정에서 OpenAI API Key를 입력해주세요.")
            return

        self._set_controls_enabled(False)
        self._progress.setValue(0)

        self.worker = ProcessingWorker(self.selected_file, self.config, reset=reset)
        self.worker.progress.connect(self._on_progress)
        self.worker.finished.connect(self._on_finished)
        self.worker.error.connect(self._on_error)
        self.worker.start()

    def _on_progress(self, message: str, percent: int) -> None:
        self._status_label.setText(message)
        self._progress.setValue(percent)

    def _on_finished(self, original_path: str, translated_path: str) -> None:
        self._set_controls_enabled(True)
        self._status_label.setText("완료!")
        QMessageBox.information(
            self,
            "완료",
            f"SRT 파일이 생성되었습니다.\n\n원본: {original_path}\n번역: {translated_path}",
        )

    def _on_error(self, message: str) -> None:
        self._set_controls_enabled(True)
        self._status_label.setText("오류 발생")

        dlg = QMessageBox(self)
        dlg.setIcon(QMessageBox.Icon.Critical)
        dlg.setWindowTitle("오류")
        dlg.setText(message)
        retry_btn = dlg.addButton("재시도", QMessageBox.ButtonRole.AcceptRole)
        reset_btn = dlg.addButton("처음부터", QMessageBox.ButtonRole.DestructiveRole)
        dlg.addButton("닫기", QMessageBox.ButtonRole.RejectRole)
        dlg.exec()

        clicked = dlg.clickedButton()
        if clicked == retry_btn:
            self._start(reset=False)
        elif clicked == reset_btn:
            self._start(reset=True)

    def _set_controls_enabled(self, enabled: bool) -> None:
        self._select_btn.setEnabled(enabled)
        self._start_btn.setEnabled(enabled)
