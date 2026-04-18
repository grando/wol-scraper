COMPOSE ?= docker compose
INPUT ?= sample-urls.txt
OUTPUT ?= output.csv
FORMAT ?= csv

.DEFAULT_GOAL := help

.PHONY: help build start stop up down shell run test test-sample clean

help:
	@echo "Available commands:"
	@echo "  make build       Build the Docker image"
	@echo "  make start       Start the container"
	@echo "  make stop        Stop the container"
	@echo "  make shell       Open a shell in the container"
	@echo "  make run         Run the scraper with INPUT=$(INPUT), OUTPUT=$(OUTPUT), FORMAT=$(FORMAT)"
	@echo "  make test        Run the scraper against sample-urls.txt"
	@echo "  make test-sample Run the scraper against sample-urls.txt"
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
	@if [ -n "$(OUTPUT)" ]; then \
		$(COMPOSE) run --rm scraper python scraper.py --urls $(INPUT) --output $(OUTPUT) --format $(FORMAT); \
	else \
		$(COMPOSE) run --rm scraper python scraper.py --urls $(INPUT) --format $(FORMAT); \
	fi

test:
	$(COMPOSE) run --rm scraper python scraper.py --urls sample-urls.txt --output test-output.csv --format csv

test-sample:
	$(COMPOSE) run --rm scraper python scraper.py --urls sample-urls.txt --output test-output.csv --format csv

clean:
	rm -f output.csv test-output.csv
