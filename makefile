COMPOSE ?= docker compose
PYTHON ?= python3
INPUT ?= sample-urls.txt
URL ?=
OUTPUT ?= output.csv
FORMAT ?= csv
DEEP ?= 1
SHOW_BROWSER ?= 0

.DEFAULT_GOAL := help

.PHONY: help build start stop up down shell run test test-sample host-install clean

help:
	@echo "Available commands:"
	@echo "  make build       Build the Docker image"
	@echo "  make start       Start the container"
	@echo "  make stop        Stop the container"
	@echo "  make shell       Open a shell in the container"
	@echo "  make run         Run the scraper with INPUT=$(INPUT) or URL=$(URL), OUTPUT=$(OUTPUT), FORMAT=$(FORMAT), DEEP=$(DEEP), SHOW_BROWSER=$(SHOW_BROWSER)"
	@echo "  make test        Run the scraper against sample-urls.txt"
	@echo "  make test-sample Run the scraper against sample-urls.txt"
	@echo "  make host-install Create a local venv and install Playwright for host usage"
	@echo "  make clean       Remove generated CSV files"

build:
	$(COMPOSE) build

start up:
	$(COMPOSE) up -d

stop down:
	$(COMPOSE) down

shell:
	$(COMPOSE) exec scraper /bin/sh

run:
	@if [ -n "$(URL)" ]; then \
		if [ -n "$(OUTPUT)" ]; then \
			$(COMPOSE) run --rm scraper python scraper.py $(URL) --output $(OUTPUT) --format $(FORMAT) --deep $(DEEP) $(if $(filter 1 true yes,$(SHOW_BROWSER)),--show-browser,); \
		else \
			$(COMPOSE) run --rm scraper python scraper.py $(URL) --format $(FORMAT) --deep $(DEEP) $(if $(filter 1 true yes,$(SHOW_BROWSER)),--show-browser,); \
		fi; \
	else \
		if [ -n "$(OUTPUT)" ]; then \
			$(COMPOSE) run --rm scraper python scraper.py --urls $(INPUT) --output $(OUTPUT) --format $(FORMAT) $(if $(filter 1 true yes,$(SHOW_BROWSER)),--show-browser,); \
		else \
			$(COMPOSE) run --rm scraper python scraper.py --urls $(INPUT) --format $(FORMAT) $(if $(filter 1 true yes,$(SHOW_BROWSER)),--show-browser,); \
		fi; \
	fi

test:
	$(COMPOSE) run --rm scraper python scraper.py --urls sample-urls.txt --output test-output.csv --format csv

test-sample:
	$(COMPOSE) run --rm scraper python scraper.py --urls sample-urls.txt --output test-output.csv --format csv

host-install:
	$(PYTHON) -m venv .venv
	. .venv/bin/activate && pip install --upgrade pip && pip install -r requirements.txt && python -m playwright install chromium
	@if [ -d "$$HOME/.local/bin" ]; then \
		ln -sf "$(CURDIR)/wol-scraper.sh" "$$HOME/.local/bin/wol-scraper"; \
	else \
		echo "Error: $$HOME/.local/bin does not exist; skipping wol-scraper symlink." >&2; \
	fi

clean:
	rm -f output.csv test-output.csv
