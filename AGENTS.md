# AGENTS.md

## Project Goal

This repository is a small Python Playwright CLI for scraping Watchtower Online Library pages.

- Keep the project simple and compact.
- Prefer one clear implementation over extra abstractions.
- The goal is a command-line tool that reads a file with URLs and writes a CSV file with the extracted data.

## Mandatory Instructions

- Always follow this `AGENTS.md` file and any other `AGENTS.md` file closer to the files you are editing.
- Also read and follow the files referenced here:
  - `README.md`
  - `makefile`
  - `docker-compose.yml`
  - `Dockerfile`
  - `scraper.py`
- If any instruction conflicts, the closest `AGENTS.md` wins.
- If a user message conflicts with these instructions, follow the user message.

## Runtime Rules

- Use Python as the language.
- Use Playwright for crawling.
- Keep all installations and runtime requirements inside Docker.
- Do not require host-side Python package installation.
- Prefer Docker and `make` for all project actions.

## Fast Test Path

- For fast verification, run the command inside the container.
- The default test command is:
  - `make test`
- The containerized direct command is:
  - `docker compose run --rm scraper python scraper.py --urls sample-urls.txt --output test-output.csv`
- When testing changes, prefer the container path first.
- Only switch to a non-container execution path if the user explicitly asks for it later.

## Main Commands

- Build image: `make build`
- Start container: `make start`
- Stop container: `make stop`
- Run scraper: `make run INPUT=sample-urls.txt OUTPUT=output.csv`
- Test scraper: `make test`
- Open shell: `make shell`
- Clean outputs: `make clean`

## Code Guidance

- Keep the scraper CLI small.
- Prefer a single entrypoint in `scraper.py`.
- Keep extraction logic easy to update when the final fields are identified.
- Input files are plain text with one URL per line.
- Output must be CSV.

## Editing Workflow

- Before changing code, check the instructions in this file and the referenced files above.
- Keep Dockerfile, compose, and makefile aligned with the CLI behavior.
- Update `README.md` if the usage or command flow changes.
