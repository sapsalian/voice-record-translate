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
        def open_file_dialog(self) -> list[str] | None:
            result = webview.windows[0].create_file_dialog(
                webview.FileDialog.OPEN,
                allow_multiple=True,
                file_types=("Audio Files (*.mp3;*.m4a;*.wav;*.ogg;*.flac;*.aac;*.wma;*.opus)",),
            )
            return list(result) if result else None

        def open_viewer(self, session_id: str) -> None:
            if os.environ.get("VRT_DEV"):
                viewer_url = f"http://localhost:5173/viewer/{session_id}?port={port}"
            else:
                viewer_url = f"http://localhost:{port}/viewer/{session_id}"
            webview.create_window("VRT Viewer", viewer_url, width=1100, height=750)

    if os.environ.get("VRT_DEV"):
        url = f"http://localhost:5173?port={port}"
    else:
        url = f"http://localhost:{port}"

    webview.create_window("VRT", url, js_api=API(), width=900, height=700)
    webview.start()


if __name__ == "__main__":
    main()
