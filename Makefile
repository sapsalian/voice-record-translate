.PHONY: build-frontend run

build-frontend:
	cd frontend && npm run build && cp -r dist/* ../src/vrt/static/

run: build-frontend
	vrt
