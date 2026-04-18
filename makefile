COMPOSE ?= docker compose
INPUT ?= sample-urls.txt
OUTPUT ?= output.csv

.PHONY: build start stop up down shell run test clean

build:
	$(COMPOSE) build

start up:
	$(COMPOSE) up -d

stop down:
	$(COMPOSE) down

shell:
	$(COMPOSE) exec scraper /bin/sh

run:
	$(COMPOSE) run --rm scraper python scraper.py --urls $(INPUT) --output $(OUTPUT)

test:
	$(COMPOSE) run --rm scraper python scraper.py --urls sample-urls.txt --output test-output.csv

clean:
	rm -f output.csv test-output.csv
