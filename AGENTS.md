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
  - `parsing-rules.md`
- If any instruction conflicts, the closest `AGENTS.md` wins.
- If a user message conflicts with these instructions, follow the user message.

## Runtime Rules

- Use Python as the language.
- Use Playwright for crawling.
- Prefer Playwright as the browser automation tool.
- Do not use Chrome DevTools by default in this project.
- If Chrome DevTools seems useful, ask the user before using it.
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
- Prefer a minimal set of example pages for regression testing.
- Start with `sample-urls.txt` and expand it only when a new page shape or edge case is learned.

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
- When a field is a block of text that follows a heading, model it as a heading anchor plus a `following_text` extraction rule and record the stop boundary in `parsing-rules.md`.
- For variable section groups, keep the CSV schema fixed-width with empty placeholders for missing slots, and stop the living group at `Studio biblico di congregazione`.
- If a user-supplied xpath sketch does not match the live DOM, verify the corrected anchor on the page and record the corrected xpath in `parsing-rules.md` before changing the scraper.
- For page extraction, prefer Playwright-native APIs first. Only add separate HTML parsing logic, or a combination approach, when a documented page case requires it.
- Input files are plain text with one URL per line.
- Output must be CSV.
- Keep `parsing-rules.md` current with every learned page shape, rule, and regression case.
- Treat `parsing-rules.md` as the source of truth for parsing behavior and test cases.
- When a new parsing case is discovered, update `parsing-rules.md` first, then adjust the scraper code.
- When a review decision or parsing decision is applied, record it in `parsing-rules.md` so the repo keeps a trace of why the behavior changed.
- Avoid broad refactors unless they directly help manage a documented parsing case.

## Editing Workflow

- Before changing code, check the instructions in this file and the referenced files above.
- Keep Dockerfile, compose, and makefile aligned with the CLI behavior.
- Update `README.md` if the usage or command flow changes.
