# WOL Scraper

Small Python + Playwright CLI for scraping Watchtower Online Library pages.

## Input And Output

- Input: a text file with one URL per line
- Output: a CSV file or a JSON list of page results
- If `--output` is omitted, the result is written to stdout

## Commands

```bash
make build
make start
make test
make run INPUT=sample-urls.txt OUTPUT=output.csv FORMAT=csv
make run INPUT=sample-urls.txt FORMAT=json
make stop
```

## Notes

- Run everything in Docker.
- Use `make` for the main workflow.
- Extraction prefers Playwright-native rendered-page APIs first.
- Update `scraper.py` when the final fields are defined.
- Use `FORMAT=json` with `make run` when you want JSON output from the CLI.
- Omit `OUTPUT` to stream the result to stdout.
