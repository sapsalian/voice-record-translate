import os
import threading
import webbrowser

from .server import app, find_free_port


def main() -> None:
    port = int(os.environ.get("VRT_PORT", 0)) or find_free_port()
    web_mode = bool(os.environ.get("VRT_WEB"))

    threading.Thread(
        target=lambda: app.run(host="0.0.0.0", port=port, use_reloader=False),
        daemon=True,
    ).start()

    if web_mode:
        print(f"VRT running at http://0.0.0.0:{port}")
        threading.Event().wait()
        return

    import webview

    class API:
        def open_url(self, url: str) -> None:
            webbrowser.open(url)

        def open_file_dialog(self) -> list[str] | None:
            result = webview.windows[0].create_file_dialog(
                webview.FileDialog.OPEN,
                allow_multiple=True,
                file_types=("Audio Files (*.mp3;*.m4a;*.wav;*.ogg;*.flac;*.aac;*.wma;*.opus)",),
            )
            return list(result) if result else None

    if os.environ.get("VRT_DEV"):
        url = f"http://localhost:5173?port={port}"
    else:
        url = f"http://localhost:{port}"

    webview.create_window("VRT", url, js_api=API(), width=900, height=700)
    webview.start()


if __name__ == "__main__":
    main()
