.PHONY: build-frontend run build-app-macos build-app-windows

build-frontend:
	cd frontend && npm run build && cp -r dist/* ../src/vrt/static/

run: build-frontend
	vrt

build-app-macos: build-frontend
	cd build && ../.venv/bin/pyinstaller vrt-macos.spec

build-app-windows: build-frontend
	cd build && ../.venv/Scripts/pyinstaller vrt-windows.spec
