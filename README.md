# WOL Scraper

Small Python + Playwright CLI for scraping Watchtower Online Library pages.

## Input And Output

- Input: a text file with one URL per line, or one or more direct URLs on the command line
- Output: a CSV file, a JSON list of page results, or the `gdoc-tesori` CSV layout
- If `--output` is omitted, the result is written to stdout
- Progress messages and errors go to stderr, so stdout can be piped into other commands
- `--deep` is only for a single direct URL, with values from 1 to 50
- In deep mode, the CLI follows `next_week_page` links and skips invalid pages while continuing the crawl
- `--show-browser` opens Playwright in headed mode when the container has a display available
- If you run the script with no arguments, it prints a short welcome page with the main options and examples

## Commands

```bash
make build
make start
make host-install
make test
make run INPUT=sample-urls.txt OUTPUT=output.csv FORMAT=csv
make run INPUT=sample-urls.txt FORMAT=json
make run INPUT=sample-urls.txt FORMAT=gdoc-tesori
make run URL=https://wol.jw.org/it/wol/d/r6/lp-i/202026161 FORMAT=csv
make run URL=https://wol.jw.org/it/wol/d/r6/lp-i/202026161 DEEP=3 FORMAT=json
make run URL=https://wol.jw.org/it/wol/d/r6/lp-i/202026161 SHOW_BROWSER=1
wol-scraper --urls sample-urls.txt --output output.csv
make stop
```

## Notes

- Run everything in Docker.
- Use `make` for the main workflow.
- Extraction prefers Playwright-native rendered-page APIs first.
- Update `scraper.py` when the final fields are defined.
- Use `FORMAT=json` with `make run` when you want JSON output from the CLI.
- Use `FORMAT=gdoc-tesori` when you want the Google Docs-friendly CSV layout.
- In `gdoc-tesori`, the `gems` cell appends only the timing label from `gems_notes`, for example `2. Gemme spirituali (10 min)`.
- In `gdoc-tesori`, `song_1`, `song_2`, and `song_3` keep only the song number.
- In `gdoc-tesori`, each `living_*_note` keeps only the first sentence, up to the first period.
- In `gdoc-tesori`, `study_material` removes the leading timing label when it is not `(30 min)`.
- Omit `OUTPUT` to stream the result to stdout.
- Use shell pipes freely; logs and errors are written to stderr.
- Use `URL=...` with `make run` when you want to scrape a direct URL without a file.
- Use `DEEP=...` only with `URL=...`.
- Use `SHOW_BROWSER=1` only when the container can open a display.
- Use `make host-install` to prepare the local `.venv` and create the `~/.local/bin/wol-scraper` symlink when the directory exists.
