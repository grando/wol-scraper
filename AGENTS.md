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
- Host install: `make host-install`
- Shell launcher: `wol-scraper`
- Run scraper: `make run INPUT=sample-urls.txt OUTPUT=output.csv FORMAT=csv`
- Run scraper to stdout: `make run INPUT=sample-urls.txt FORMAT=csv`
- Run a direct URL: `make run URL=https://wol.jw.org/it/wol/d/r6/lp-i/202026161 FORMAT=csv`
- Run a deep direct URL crawl: `make run URL=https://wol.jw.org/it/wol/d/r6/lp-i/202026161 DEEP=3 FORMAT=csv`
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
- The CLI can also accept one or more direct URLs when `--urls` is omitted.
- Output defaults to CSV and can also be JSON when the CLI `--format json` option is used.
- If `--output` is omitted, the result is written to stdout.
- Progress messages and errors should go to stderr so stdout can stay pipe-friendly.
- `--show-browser` is an optional flag that opens Playwright in headed mode when a display is available.
- `make host-install` prepares the local `.venv` for running the scraper outside Docker and creates a `~/.local/bin/wol-scraper` symlink when that directory exists.
- The `wol-scraper` shell launcher is a local convenience script that can be symlinked into `~/.local/bin`.
- If the CLI is invoked with no arguments, it should print a short welcome page with the main options and common examples.
- Pages missing `section_1`, `section_2`, or `section_3` should be skipped, and the CLI should report how many URLs were skipped.
- `--deep` is only valid for a single direct URL, accepts values from 1 to 50, and follows `next_week_page` links.
- Deep mode should keep the parsed URL chain in output and mark each page with a validity flag.
- Keep `parsing-rules.md` current with every learned page shape, rule, and regression case.
- Treat `parsing-rules.md` as the source of truth for parsing behavior and test cases.
- When a new parsing case is discovered, update `parsing-rules.md` first, then adjust the scraper code.
- When a review decision or parsing decision is applied, record it in `parsing-rules.md` so the repo keeps a trace of why the behavior changed.
- Avoid broad refactors unless they directly help manage a documented parsing case.

## Editing Workflow

- Before changing code, check the instructions in this file and the referenced files above.
- Keep Dockerfile, compose, and makefile aligned with the CLI behavior.
- Update `README.md` if the usage or command flow changes.
