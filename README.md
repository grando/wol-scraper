# WOL Scraper

Small Python + Playwright CLI for scraping Watchtower Online Library pages.

## Input And Output

- Input: a text file with one URL per line, or one or more direct URLs on the command line
- Output: a CSV file or a JSON list of page results
- If `--output` is omitted, the result is written to stdout
- `--deep` is only for a single direct URL, with values from 1 to 50
- In deep mode, the CLI follows `next_week_page` links and includes each parsed URL with its validity flag
- `--show-browser` opens Playwright in headed mode when the container has a display available

## Commands

```bash
make build
make start
make test
make run INPUT=sample-urls.txt OUTPUT=output.csv FORMAT=csv
make run INPUT=sample-urls.txt FORMAT=json
make run URL=https://wol.jw.org/it/wol/d/r6/lp-i/202026161 FORMAT=csv
make run URL=https://wol.jw.org/it/wol/d/r6/lp-i/202026161 DEEP=3 FORMAT=json
make run URL=https://wol.jw.org/it/wol/d/r6/lp-i/202026161 SHOW_BROWSER=1
make stop
```

## Notes

- Run everything in Docker.
- Use `make` for the main workflow.
- Extraction prefers Playwright-native rendered-page APIs first.
- Update `scraper.py` when the final fields are defined.
- Use `FORMAT=json` with `make run` when you want JSON output from the CLI.
- Omit `OUTPUT` to stream the result to stdout.
- Use `URL=...` with `make run` when you want to scrape a direct URL without a file.
- Use `DEEP=...` only with `URL=...`.
- Use `SHOW_BROWSER=1` only when the container can open a display.
