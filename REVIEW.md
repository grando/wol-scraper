# Code Review — wol-scraper

Review date: 2026-04-18. Current implementation reviewed against the project goals: simple, compact, readable, effective.
No files other than this one were modified.

---

## Overall Assessment

The project is in significantly better shape than the previous review. All major structural issues have been addressed: the extraction logic was consolidated into a single semantic DOM pass, page isolation is now correct, dependency pinning is in place, and `parsing-rules.md` is clean and well-structured. A few smaller issues remain, mostly in the `makefile` and the `plugins/` scaffolding. The core scraper logic is now compact and intentional.

---

## Progress Since Previous Review

| Previous issue | Status |
|---|---|
| Three overlapping extraction functions (`accessibility_text`, `body_text`, `first_text`) | **Resolved** — replaced with single `extract_meeting_page()` JS evaluate pass |
| `body_text()` wraps native Playwright call | **Resolved** — function gone entirely |
| Triple redundant wait + fixed sleep | **Resolved** — single `wait_for_function` on article content length |
| Single page reused across all URLs | **Resolved** — fresh `context.new_page()` + `page.close()` per URL in both crawl paths |
| CSV fieldnames hardcoded in two places | **Resolved** — `CSV_FIELD_ORDER` constant drives all CSV writing |
| No progress output | **Resolved** — `log(f"Scraping {url} ...")` in both `crawl()` and `crawl_deep()` |
| `locator.count()` double DOM query | **Resolved** — that code path no longer exists |
| Unpinned `playwright` dependency | **Resolved** — `requirements.txt` pins `playwright==1.44.0` |
| Redundant `COPY sample-urls.txt` in Dockerfile | **Resolved** — Dockerfile only copies `requirements.txt` and `scraper.py` |
| Planning questions mixed into `parsing-rules.md` | **Resolved** — file is clean: Decision Trace + rule set + regression cases |
| `CMD sleep infinity` (Dockerfile) | **Still present** — intentional for `make start/shell` workflow; see note below |
| `clean` only removes two hardcoded filenames | **Still present** |
| `plugin.json` all-TODO placeholders | **Still present** |

---

## scraper.py

### 1. `extract_meeting_page` embeds ~100 lines of JavaScript as a Python string

The entire DOM traversal lives in a single `page.evaluate()` call. One round-trip to the browser is efficient, and the decision trace in `parsing-rules.md` explicitly chose this over accessibility-tree reconstruction. The trade-off is real though: JavaScript errors inside the string produce opaque Python exceptions with no JS stack trace, and the JS cannot be linted, formatted, or unit-tested independently.

This is an acceptable trade-off for the current project scope, but it means any future edit to the extraction logic must be done carefully inside a raw string.

---

### 2. `raw_section3_items` and `raw_study_index` are returned but never read

`extract_meeting_page` returns two fields that `scrape_url()` never accesses:

```python
raw_section3_items: section3Items.map(...),
raw_study_index: studyIndex,
```

These appear to be development artifacts left from building and debugging the `study` / `living_*` split logic. They add noise to the JS return object and the `normalize_text` dict comprehension processes them on every scrape.

---

### 3. `transform_gems_note` and `transform_treasure_note` are identical

Both functions extract the first parenthesized expression from a string:

```python
def transform_gems_note(text: str) -> str:
    cleaned = normalize_text(text)
    if not cleaned:
        return ""
    match = re.match(r"^\(([^)]*)\)", cleaned)
    return f"({match.group(1)})" if match else ""

def transform_treasure_note(text: str) -> str:  # exact same body
    ...
```

They could share a single implementation (e.g., `extract_timing_label`) called by both sites in `build_gdoc_tesori_row`. Keeping two separate functions with identical bodies is a maintenance trap.

---

### 4. `is_valid_row` is called twice on the same data in `main()`

```python
rows_to_write = [row for row in rows if is_valid_row(row)]
...
skipped = sum(1 for row in rows if not is_valid_row(row))
```

Two passes over `rows` with the same predicate. A single pass collecting both sets would be cleaner and avoids calling `is_valid_row` twice per row.

---

### 5. `collect_page_links` iterates all `<a>` tags on the page

For navigation, only prev/next page links are needed. Iterating every anchor tag (potentially hundreds on a content-heavy page) just to find two navigation links adds unnecessary work. WOL navigation links are typically in a `.navLinks` or `nav` container. A more targeted selector would be faster and reduce the noise in `adjacent_page_link`.

---

### 6. `--deep` default of `1` creates silent semantic overlap

`--deep` defaults to `1` in `argparse`. The branching in `main()` is `if args.deep > 1`. This means passing `--deep 1` explicitly is silently treated as a non-deep scrape. The value `1` is overloaded: it means both "the default" and "follow one link." A cleaner design would make `--deep` optional with a `None` default, and only enter deep mode when the flag is explicitly provided.

---

### 7. `build_gdoc_tesori_row` uses magic positional column indices

Values are assigned by raw integer index:

```python
values[4] = transform_song_number(row.get("song_1", ""))
values[8] = normalize_text(row.get("bible_chapters", ""))
values[10] = combine_gdoc_cell(...)
```

Reading or modifying this requires manually counting positions against `GDOC_TESORI_HEADER`. A named mapping (dict keyed by header label, converted to a list at write time) would be safer and self-documenting.

---

## Dockerfile

### 8. `CMD sleep infinity` — still present, intentional but worth noting

The `CMD ["sleep", "infinity"]` default exists to support the `make start` / `make shell` workflow. When running the image standalone via `docker run` without `docker-compose`, the container starts and does nothing. The previous review suggested defaulting to `python scraper.py --help` for standalone use. The current behavior is not a bug, but it means the image is not self-documenting when used outside the compose workflow.

---

### 9. `COPY scraper.py` is shadowed by the compose volume mount

The Dockerfile bakes `scraper.py` into the image, but `docker-compose.yml` mounts `./:/app`, which shadows the COPY at runtime. This means:
- Via compose: edits to `scraper.py` are live immediately without rebuilding.
- Standalone `docker run`: the baked-in copy is used.

The two behaviors are not aligned. The compose-first workflow (per AGENTS.md) makes the COPY redundant for development but keeps the image self-contained for standalone distribution. This trade-off is reasonable but should be noted if the image is ever distributed.

---

## makefile

### 10. `clean` only removes two hardcoded filenames

```makefile
clean:
	rm -f output.csv test-output.csv
```

`make run OUTPUT=report.csv` leaves `report.csv` behind. A pattern glob would be more complete:

```makefile
clean:
	rm -f *.csv
```

---

### 11. `make test` and `make test-sample` are identical

Both targets run the exact same command:

```makefile
test:
	$(COMPOSE) run --rm scraper python scraper.py --urls sample-urls.txt --output test-output.csv --format csv

test-sample:
	$(COMPOSE) run --rm scraper python scraper.py --urls sample-urls.txt --output test-output.csv --format csv
```

One of them is redundant. Keep `test` as the canonical target and remove `test-sample`, or make `test-sample` an alias (`test-sample: test`).

---

## sample-urls.txt

### 12. Only 2 of 5 documented regression URLs are included

`parsing-rules.md` documents five example pages for Case 1 with different group sizes (section 2 = 3 or 4 items, section 3 living = 1 or 2 items):

```
202026161, 202026164, 202026165, 202026166, 202026167
```

`sample-urls.txt` lists only `202026161` and `202026164`. `make test` therefore does not exercise all documented regression cases. The remaining three URLs should be added to either `sample-urls.txt` or a dedicated `regression-urls.txt` run by a separate `make test-regression` target.

---

## plugins/wol-scraper

### 13. `plugin.json` is entirely unfilled scaffolding

Every field in `plugin.json` remains a `[TODO: ...]` placeholder. If this Codex plugin manifest is not intended to be published or used in the near future, the `plugins/` directory is workspace clutter. Consider either filling it in or removing it until it is needed.

---

## Summary Table

| # | File | Issue | Impact |
|---|------|-------|--------|
| 1 | scraper.py | Large JS string inside `page.evaluate()` — opaque errors, no linting | Maintainability |
| 2 | scraper.py | `raw_section3_items`, `raw_study_index` returned but never read | Minor noise, wasted processing |
| 3 | scraper.py | `transform_gems_note` and `transform_treasure_note` are identical | Maintenance trap |
| 4 | scraper.py | `is_valid_row` called twice on same data in `main()` | Minor inefficiency |
| 5 | scraper.py | `collect_page_links` iterates all page anchors | Unnecessary work per URL |
| 6 | scraper.py | `--deep 1` silently treated as non-deep mode | Confusing CLI semantics |
| 7 | scraper.py | `build_gdoc_tesori_row` uses magic column indices | Fragile to column reordering |
| 8 | Dockerfile | `CMD sleep infinity` — image not self-documenting standalone | Minor UX gap |
| 9 | Dockerfile | `COPY scraper.py` shadowed by compose volume mount | Inconsistent standalone vs compose behavior |
| 10 | makefile | `clean` only removes two hardcoded filenames | Incomplete cleanup |
| 11 | makefile | `make test` and `make test-sample` are identical | Redundant target |
| 12 | sample-urls.txt | Only 2 of 5 documented regression URLs included | Incomplete regression coverage |
| 13 | plugins/ | All `plugin.json` fields are TODO placeholders | Workspace clutter |

---

## Improvement Options

These are not required changes. They are options for advancing the project if the goals or scope expand.

### A. Extract the JavaScript into a separate file

Move the ~100-line JS string in `extract_meeting_page` into a standalone `extract.js` file loaded at startup:

```python
_EXTRACT_JS = Path(__file__).parent.joinpath("extract.js").read_text()

async def extract_meeting_page(page):
    data = await page.evaluate(_EXTRACT_JS)
    ...
```

Benefits: JS syntax highlighting and linting, independent testing of the extraction logic, cleaner diffs when the DOM shape changes.

---

### B. Parallel URL scraping

Currently URLs are scraped sequentially. For batch jobs (`--urls FILE` with many entries), `asyncio.gather` with a concurrency semaphore would reduce wall time significantly:

```python
semaphore = asyncio.Semaphore(4)
async def scrape_with_limit(url):
    async with semaphore:
        page = await context.new_page()
        try:
            return await scrape_url(page, url)
        finally:
            await page.close()

rows = await asyncio.gather(*[scrape_with_limit(u) for u in urls])
```

Cost: log output ordering becomes interleaved. Acceptable for a scraping tool.

---

### C. Extend the regression test set

Add the remaining three documented pages to `sample-urls.txt` (or a new `regression-urls.txt`) and wire them to `make test`. This costs one extra network round-trip per run but covers all documented section-size variations, making regressions detectable earlier.

---

### D. Named column mapping for gdoc-tesori

Replace magic positional indices in `build_gdoc_tesori_row` with a dict keyed by header label:

```python
mapping = {
    "cantico": transform_song_number(row.get("song_1", "")),
    "CAPITOLI BIBBIA": normalize_text(row.get("bible_chapters", "")),
    ...
}
header = GDOC_TESORI_HEADER
return [mapping.get(col, "") for col in header]
```

This makes the column assignment self-documenting and safe against header reordering.

---

### E. Local page cache for repeated runs

For development and iteration, a simple file-based HTML cache (keyed by URL) would avoid re-fetching pages already scraped. A `--cache-dir` option could point to a local folder where rendered page HTML is stored. This is only worth adding if the URL set grows and re-scraping becomes a friction point.

---

### F. Structured error reporting

Currently errors are stored as free-form strings in the `error` field. For programmatic use (e.g., filtering failed rows in a downstream pipeline), a structured error code (e.g., `navigation_failed`, `content_timeout`, `extraction_empty`) alongside the raw message would be more useful.

---

### G. `--dry-run` flag

A flag that validates input URLs and checks page reachability without writing any output. Useful for verifying a large input file before a long scrape job.
