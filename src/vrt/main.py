import sys

from PyQt6.QtWidgets import QApplication

from .config import load_config
from .ui.main_window import MainWindow


def main() -> None:
    app = QApplication(sys.argv)
    config = load_config()
    window = MainWindow(config)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
