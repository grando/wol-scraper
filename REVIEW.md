# Code Review — wol-scraper

Review of the current implementation against the project goals: simple, compact, readable, effective.
No files other than this one were modified.

---

## Overall Assessment

The project skeleton is well-structured. The separation of concerns across `scraper.py`, `parsing-rules.md`, `Dockerfile`, `makefile`, and `docker-compose.yml` is clean and follows the AGENTS.md guidelines. The main issues are in `scraper.py`, where there is redundant extraction logic, unreliable wait strategies, and missed opportunities for simplicity.

---

## scraper.py

### 1. Three extraction functions do overlapping work

`accessibility_text()`, `body_text()`, and `first_text()` are all fallbacks for the same thing: the page's readable text. The `accessibility_text()` is called first but is the most expensive and noisiest — it does a full recursive tree walk and can return duplicate labels, button names, and aria metadata mixed with real content.

**Suggestion:** Invert the priority. Try specific selectors first (`first_text`), fall back to `page.inner_text("body")`, and drop `accessibility_text()` entirely unless a concrete need for it is found and documented in `parsing-rules.md`.

```python
# simpler, clearer order
row["content"] = (
    await first_text(page, CONTENT_SELECTORS)
    or await page.inner_text("body")
)
```

---

### 2. `body_text()` wraps a native Playwright method

`body_text()` calls `page.evaluate()` with a JS snippet to get `body.innerText`. Playwright already exposes this directly:

```python
# current
async def body_text(page) -> str:
    text = await page.evaluate(
        """() => {
            const body = document.body;
            ...
        }"""
    )
    return text
```

```python
# simpler replacement (no separate function needed)
text = (await page.inner_text("body")).strip()
```

The function can be deleted entirely.

---

### 3. The wait strategy is redundant and fragile

After navigation there are three sequential waits:
1. Wait for `h1` to appear.
2. Wait for `body.innerText.length > 1000`.
3. Hard `wait_for_timeout(1000)`.

The third is a fixed sleep that always runs regardless of page state. If the previous waits succeeded, the sleep is wasted time. If they failed (both are wrapped in bare `except`), the sleep doesn't compensate.

Also, `wait_until="commit"` fires as soon as HTTP headers arrive — very early for a JS-heavy SPA like WOL. `domcontentloaded` would be a more honest baseline.

**Suggestion:** Keep only the `body.innerText` length check, use `domcontentloaded`, and remove the fixed sleep.

```python
await page.goto(url, wait_until="domcontentloaded", timeout=NAVIGATION_TIMEOUT_MS)
try:
    await page.wait_for_function(
        "() => document.body && document.body.innerText.trim().length > 1000",
        timeout=CONTENT_READY_TIMEOUT_MS,
    )
except Exception:
    pass
```

---

### 4. Single reused page for all URLs

`crawl()` creates one `page` and reuses it across every URL. If one page leaves behind a dialog, a broken JS state, or a redirect, the next URL inherits it.

**Suggestion:** Create a fresh page per URL.

```python
for url in urls:
    page = await context.new_page()
    rows.append(await scrape_url(page, url))
    await page.close()
```

Cost is negligible for small URL sets, and it isolates failures cleanly.

---

### 5. CSV fieldnames are duplicated

`scrape_url()` builds the `row` dict with four keys. `crawl()` hardcodes the same four keys in `DictWriter`. If a field is added to one, the other must be updated manually.

**Suggestion:** Derive the fieldnames from the first row.

```python
if rows:
    writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
```

---

### 6. No progress output

For a CLI tool scraping a list of URLs, there is no feedback while running. A single `print` per URL makes the tool usable.

```python
print(f"Scraping {url} ...", flush=True)
```

---

### 7. `first_text()` uses `locator.count()` to check presence

`await locator.count()` triggers a DOM query just to decide whether to run another DOM query. It's simpler to just attempt `inner_text()` and handle the empty result.

```python
async def first_text(page, selectors: list[str]) -> str:
    for selector in selectors:
        try:
            text = (await page.locator(selector).first.inner_text(timeout=3000)).strip()
            if text:
                return text
        except Exception:
            continue
    return ""
```

---

## Dockerfile

### 8. No pinned dependency version

`pip install --no-cache-dir playwright` installs whatever the latest version is at build time. Image rebuilds at different times will produce different behavior.

**Suggestion:** Add a `requirements.txt` with a pinned version:

```
playwright==1.44.0
```

And in the Dockerfile:

```dockerfile
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
```

---

### 9. `COPY sample-urls.txt` is redundant

The `docker-compose.yml` mounts the entire workspace as a volume (`./:/app`), so `sample-urls.txt` is already available at runtime. The `COPY` line copies it into the image layer unnecessarily. It's harmless but adds noise.

---

### 10. Default `CMD` is `sleep infinity`

The container's default command is an idle sleep. This is useful for `make start` / `make shell` workflows, but it means running the image standalone does nothing useful. Consider defaulting to `--help`:

```dockerfile
CMD ["python", "scraper.py", "--help"]
```

This makes the image self-documenting when run without arguments.

---

## makefile

### 11. `clean` only covers two hardcoded filenames

```makefile
clean:
	rm -f output.csv test-output.csv
```

If someone runs `make run OUTPUT=report.csv`, `make clean` won't remove `report.csv`. A pattern glob would be more complete:

```makefile
clean:
	rm -f *.csv
```

---

## parsing-rules.md

### 12. Open questions belong in a separate planning note

The open questions in Case 1 ("Which exact pieces... should become CSV columns?") are planning notes, not parsing rules. They add noise when the file is consulted as a reference. Consider moving them to a separate `PLANNING.md` or an issue tracker, keeping `parsing-rules.md` focused on observed facts and regression checks.

---

## plugins/wol-scraper

### 13. `plugin.json` is entirely unfilled scaffolding

Every field in `plugin.json` is a `[TODO: ...]` placeholder. If this Codex plugin manifest is not intended to be published or used yet, consider either filling it in or removing the `plugins/` directory to reduce workspace clutter.

---

## Summary Table

| # | File | Issue | Impact |
|---|------|-------|--------|
| 1 | scraper.py | Accessibility tree used as primary extractor | Slow, noisy output |
| 2 | scraper.py | `body_text()` wraps a native Playwright call | Unnecessary complexity |
| 3 | scraper.py | Triple redundant wait + fixed sleep | Slow, unreliable |
| 4 | scraper.py | Single page reused across all URLs | State leaks between URLs |
| 5 | scraper.py | CSV fieldnames hardcoded twice | Fragile to field additions |
| 6 | scraper.py | No progress output | Poor CLI usability |
| 7 | scraper.py | `locator.count()` before `inner_text()` | Double DOM query |
| 8 | Dockerfile | Unpinned `playwright` dependency | Non-reproducible builds |
| 9 | Dockerfile | Redundant `COPY sample-urls.txt` | Minor image bloat |
| 10 | Dockerfile | `CMD sleep infinity` | Non-self-documenting image |
| 11 | makefile | `clean` only removes two hardcoded filenames | Incomplete cleanup |
| 12 | parsing-rules.md | Planning questions mixed with rules | Reduces reference clarity |
| 13 | plugins/ | All plugin.json fields are TODO placeholders | Workspace clutter |
