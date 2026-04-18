# WOL Scraper

Small Python + Playwright CLI for scraping Watchtower Online Library pages.

## Input And Output

- Input: a text file with one URL per line
- Output: a CSV file with the extracted data

## Commands

```bash
make build
make start
make test
make run INPUT=sample-urls.txt OUTPUT=output.csv
make stop
```

## Notes

- Run everything in Docker.
- Use `make` for the main workflow.
- Update `scraper.py` when the final fields are defined.
