.PHONY: dev seed build-css

dev:
	python -m app.main

seed:
	python infra/seed.py

build-css:
	npx tailwindcss -i app/static/css/tailwind.css -o app/static/css/out.css --watch
