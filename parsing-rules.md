# Parsing Rules

Living document for page shapes, extraction rules, and regression cases.

## Purpose

- Keep the scraper robust and compact.
- Record every new page pattern we learn from test pages.
- Use this file to avoid regressions when the scraper is updated.
- Keep the regression example set small and purposeful.
- Keep a trace of applied review and parsing decisions so later changes can follow the same reasoning.

## Decision Trace

### 2026-04-18

Applied decisions for the current scraper behavior:
- Prefer Playwright-native extraction APIs over accessibility-tree reconstruction or separate HTML parsing when the page text is available directly from the rendered page.
- Try a page-specific xpath map first, then fall back to semantic extraction from rendered page text.
- For text fields, try xpath extraction first and then parse the rendered text when the xpath is absent or broken.
- For link fields, try xpath extraction first and then derive the page URL from the current week id when the link is not exposed in the live tree.
- For variable section groups, keep fixed-width columns up to the documented maximum and leave missing slots empty.
- For note fields, use the first non-heading block immediately after the item heading.
- Use `commit` navigation on WOL pages and wait for the rendered text to become available before extraction.
- Use a fresh Playwright page per URL so one failed or redirected page does not leak state into the next one.
- Keep lightweight CLI progress output during scraping.
- Pin the Playwright Python package version in Docker for reproducible builds.
- Keep the Docker base image on a distro-specific tag so the pinned Playwright install remains buildable.
- Do not disable HTTP/2 in the container browser for this page family, because it prevents the rendered content from loading fully.

## Test Set

Minimum current example set:
- `sample-urls.txt`
- `https://wol.jw.org/it/wol/d/r6/lp-i/202026161`

Rules for growing the set:
- Add a new URL only when it demonstrates a new page shape, edge case, or regression risk.
- Document the new case in this file before relying on it in code.
- Keep the set as small as possible while still covering all known cases.

## Current Rule Set

### Case 1: WOL meeting page

Example page:
- `https://wol.jw.org/it/wol/d/r6/lp-i/202026161`

Observed shape:
- The page title is available immediately after navigation.
- The main content is a meeting/program page with an `h1` heading.
- The page contains multiple section headings and link-heavy blocks.
- The page includes useful text in the visible body, even when specific container selectors are inconsistent.
- The `EFFICACI NEL MINISTERO` section has up to three numbered items on this variant.
- The `VITA CRISTIANA` section has a song item, one ministry/life item, the study block, and then closing comments.

What matters for extraction:
- Use the page URL as the primary identifier.
- Capture the requested semantic fields by xpath.
- Keep the field names stable even when xpaths change on another page case.
- Do not rely on one brittle selector such as a single `div` class.
- For page-specific fields, use xpath rules stored in this document and update them when a new case changes the structure.
- Keep the ministry and living subsection columns fixed-width:
  - `ministry_1`..`ministry_5` plus matching `_note` fields
  - `living_1`..`living_4` plus matching `_note` fields
- Stop living subsection extraction at `Studio biblico di congregazione` and do not include the closing comments block.

Current scraper behavior:
- Navigate with Playwright using a browser context.
- Open a fresh Playwright page for each source URL.
- Navigate with `commit` and then wait for the rendered text body to become available.
- Extract each field through a data-driven xpath map.
- For text fields, try `inner_text()` and then `text_content()`.
- For link fields, read `href` and normalize it to an absolute URL.
- If an xpath does not resolve for a field, fall back to the semantic rule recorded for that field.
- Keep the extraction helper generic so future cases only need new xpath rules and fallback rules.

Regression checks:
- The sample page must still load without a navigation timeout.
- The sample page must still produce the requested fields.
- The scraper must continue to return a CSV row even if a specific xpath is missing.
- The scraper must still populate the field via the documented fallback when the xpath is absent.
- The scraper must continue to work without `--disable-http2`.
- The sample page must continue to work with the minimal test set.

Open questions:
- Which other page cases should be added next?
- Do future cases reuse the same field names or introduce new ones?
- Which fields should be normalized further, for example trimming labels from headings?

### Case 1 field map

Use these xpaths for the current example page only. They may change for the next page case.

- `week` -> `//*[@id="p1"]`
- `bible_chapters` -> `//*[@id="p2"]`
- `song_1` -> `//*[@id="p3"]/a/strong`
- `treasures` -> `//*[@id="p5"]/strong`
- `gems` -> `//*[@id="p11"]/strong`
- `gems_notes` -> `//*[@id="p11"]` with `following_text`
- `reading` -> `//*[@id="p17"]`
- `reading_material` -> `//*[@id="p17"]` with `following_text`
- `section_1` -> `//*[@id="p4"]/strong`
- `section_2` -> `//*[@id="p19"]/strong`
- `section_3` -> `//*[@id="p26"]/strong`
- `song_2` -> `//*[@id="p27"]/a/strong`
- `song_3` -> `//*[@id="p47"]/span[2]/a/strong`
- `study` -> `//*[@id="p45"]/strong`
- `study_material` -> `//*[@id="p45"]` with `following_text`
- `prev_week_page` -> `//*[@id="publicationNavigation"]/div[3]/ul/li[1]/a`
- `next_week_page` -> `//*[@id="publicationNavigation"]/div[3]/ul/li[2]/a`

Case 1 section groups:
- `ministry_1` -> `4. Iniziare una conversazione`
- `ministry_2` -> `5. Iniziare una conversazione`
- `ministry_3` -> `6. Discorso`
- `ministry_4` -> empty
- `ministry_5` -> empty
- `living_1` -> `Cantico 80`
- `living_2` -> `8. Ti perderai qualcosa?`
- `living_3` -> `9. Studio biblico di congregazione`
- `living_4` -> empty

Notes:
- The note fields use the first text block after the item heading, such as `tt33`, `tt35`, `tt37`, `tt45`, or `tt55`.
- The exact note node may be a `DIV` or a `P`, but the extracted text should stay the same.

Generic rule:
- Keep the scraper data-driven.
- Define a page case as a list of field names and xpaths.
- When a new page shape appears, add a new case section here and update the xpath map in code.
- When an xpath is unstable or missing, define a fallback rule for the same field.
- Preserve the field names if the meaning stays the same, even when the xpath changes.

### Case 2: WOL meeting page, later week variant

Example page:
- `https://wol.jw.org/it/wol/d/r6/lp-i/202026164`

Observed shape:
- The page keeps the same overall structure as Case 1.
- `week`, `bible_chapters`, and section headings still match the same semantic positions.
- The page also exposes the `treasures`, `gems`, `reading`, and `study` blocks as direct heading anchors.
- The note/material fields are the first text block immediately after those headings.
- The song fields are exposed as `strong` text in body order rather than always appearing at the old song xpaths.
- The navigation links are still present, but the ids for the old song xpaths can be absent.
- The `EFFICACI NEL MINISTERO` section has four numbered items on this variant.
- The `VITA CRISTIANA` section still stops at the study block before the closing comments.

What matters for extraction:
- Reuse the same field names.
- Reuse the same section-heading xpaths where they still match.
- Use ordered `Cantico` strong text as the generic fallback for songs when the exact xpath is missing.
- Keep previous/next page links as absolute URLs.
- Use the heading xpath as the anchor for `following_text` fields and stop at the first non-heading block.
- Keep the ministry and living subsection columns fixed-width and empty-fill the missing slots.

Case 2 field map:
- `week` -> `//*[@id="p1"]`
- `bible_chapters` -> `//*[@id="p2"]`
- `song_1` -> `//*[@id="p3"]/a/strong`
- `treasures` -> `//*[@id="p5"]/strong`
- `gems` -> `//*[@id="p11"]/strong`
- `gems_notes` -> `//*[@id="p11"]` with `following_text`
- `reading` -> `//*[@id="p17"]`
- `reading_material` -> `//*[@id="p17"]` with `following_text`
- `study` -> `//*[@id="p37"]/strong`
- `study_material` -> `//*[@id="p37"]` with `following_text`
- `section_1` -> `//*[@id="p4"]/strong`
- `section_2` -> `//*[@id="p19"]/strong`
- `section_3` -> `//*[@id="p26"]/strong`
- `song_2` -> generic `Cantico` strong fallback, second match
- `song_3` -> generic `Cantico` strong fallback, third match
- `prev_week_page` -> `//*[@id="publicationNavigation"]/div[3]/ul/li[1]/a`
- `next_week_page` -> `//*[@id="publicationNavigation"]/div[3]/ul/li[2]/a`

Case 2 section groups:
- `ministry_1` -> `4. Iniziare una conversazione`
- `ministry_2` -> `5. Iniziare una conversazione`
- `ministry_3` -> `6. Iniziare una conversazione`
- `ministry_4` -> `7. Spiegare quello in cui si crede`
- `ministry_5` -> empty
- `living_1` -> `Cantico 80`
- `living_2` -> `8. Ti perderai qualcosa?`
- `living_3` -> `9. Studio biblico di congregazione`
- `living_4` -> empty

Notes:
- The note fields use the first text block after the item heading, such as `tt33`, `tt35`, `tt37`, `tt39`, `tt45`, or `tt55`.
- The exact note node may be a `DIV` or a `P`, but the extracted text should stay the same.

Regression checks:
- Case 2 must still populate all requested fields.
- Case 2 must still resolve the second and third song values even when the old song xpaths are absent.
- Case 2 must keep the note/material extraction bounded to the current section and not include the next heading block.
- Case 2 must keep the same CSV columns as Case 1.

## New Cases

Add one section here for each new page type or edge case we learn.

Suggested format:

### Case N: <short name>

- Example page:
- Observed shape:
- Extraction rule:
- Regression checks:
- Notes:
