from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QVBoxLayout,
)

from ..config import Config, save_config
from ..translate import LANGUAGES


class SettingsDialog(QDialog):
    def __init__(self, config: Config, parent=None) -> None:
        super().__init__(parent)
        self.config = config
        self.setWindowTitle("설정")
        self.setMinimumWidth(360)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)

        form = QFormLayout()

        self._openai_key_input = QLineEdit(self.config.openai_api_key)
        self._openai_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self._openai_key_input.setPlaceholderText("sk-...")
        form.addRow("OpenAI API Key (번역용):", self._openai_key_input)

        self._soniox_key_input = QLineEdit(self.config.soniox_api_key)
        self._soniox_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self._soniox_key_input.setPlaceholderText("soniox-...")
        form.addRow("Soniox API Key (전사용):", self._soniox_key_input)

        lang_codes = list(LANGUAGES.keys())
        lang_names = list(LANGUAGES.values())

        self._source_combo = QComboBox()
        self._source_combo.addItems(lang_names)
        self._source_combo.setCurrentIndex(
            lang_codes.index(self.config.source_lang)
            if self.config.source_lang in lang_codes else 0
        )
        form.addRow("원본 언어:", self._source_combo)

        self._target_combo = QComboBox()
        self._target_combo.addItems(lang_names)
        self._target_combo.setCurrentIndex(
            lang_codes.index(self.config.target_lang)
            if self.config.target_lang in lang_codes else 1
        )
        form.addRow("번역 언어:", self._target_combo)

        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _save(self) -> None:
        lang_codes = list(LANGUAGES.keys())
        self.config.openai_api_key = self._openai_key_input.text().strip()
        self.config.soniox_api_key = self._soniox_key_input.text().strip()
        self.config.source_lang = lang_codes[self._source_combo.currentIndex()]
        self.config.target_lang = lang_codes[self._target_combo.currentIndex()]
        save_config(self.config)
        self.accept()
