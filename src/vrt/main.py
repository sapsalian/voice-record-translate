import os
import threading

import webview

from .server import app, find_free_port


def main() -> None:
    port = find_free_port()

    threading.Thread(
        target=lambda: app.run(port=port, use_reloader=False),
        daemon=True,
    ).start()

    class API:
        def open_file_dialog(self) -> str | None:
            result = webview.windows[0].create_file_dialog(webview.OPEN_DIALOG)
            return result[0] if result else None

    if os.environ.get("VRT_DEV"):
        url = f"http://localhost:5173?port={port}"
    else:
        url = f"http://localhost:{port}"

    webview.create_window("VRT", url, js_api=API(), width=900, height=700)
    webview.start()


if __name__ == "__main__":
    main()
