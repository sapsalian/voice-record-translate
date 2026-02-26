.PHONY: build-frontend

build-frontend:
	cd frontend && npm run build && cp -r dist/* ../src/vrt/static/
