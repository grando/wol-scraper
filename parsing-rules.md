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
- Replace page-specific fixed-id extraction with semantic section traversal inside the meeting article.
- Use section headings and nearby related content blocks as the primary extraction anchors instead of absolute xpaths.
- For each meeting part, collect the related text from nearby sibling blocks until the next `h3` or `h2` boundary.
- Keep `song_2` separate from the `living_*` slots.
- For variable section groups, keep fixed-width columns up to the documented maximum and leave missing slots empty.
- For note fields, aggregate all related non-heading blocks for the current part until the next heading boundary.
- Skip a page when any of `section_1`, `section_2`, or `section_3` is missing or empty, and report the number of skipped URLs.
- For deep direct-URL crawls, follow `next_week_page` links up to the requested depth, keep each parsed URL in output, and attach a validity flag to each page result.
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
- `https://wol.jw.org/it/wol/d/r6/lp-i/202026164`
- `https://wol.jw.org/it/wol/d/r6/lp-i/202026165`
- `https://wol.jw.org/it/wol/d/r6/lp-i/202026166`
- `https://wol.jw.org/it/wol/d/r6/lp-i/202026167`

Observed shape:
- The page title is available immediately after navigation.
- The main content is a meeting/program article with a `header`, followed by `h2` section headings and `h3` part headings.
- The article keeps the same three major sections:
  - `TESORI DELLA PAROLA DI DIO`
  - `EFFICACI NEL MINISTERO`
  - `VITA CRISTIANA`
- Each meeting part is represented by an `h3` heading followed by one or more nearby content blocks.
- The number of part headings in section 2 and section 3 can change from week to week.
- The first `Cantico` inside section 3 is the separate `song_2` field and is not part of the `living_*` group.
- The last meaningful part in section 3 is always `Studio biblico di congregazione`.
- `Commenti conclusivi` is outside the `living_*` and `study` extraction boundary and carries the separate `song_3`.

Observed group sizes in the current regression set:
- `202026164`: section 2 = 4 items, section 3 living = 1 item before study
- `202026165`: section 2 = 3 items, section 3 living = 2 items before study
- `202026166`: section 2 = 4 items, section 3 living = 2 items before study
- `202026167`: section 2 = 3 items, section 3 living = 2 items before study

What matters for extraction:
- Use the page URL as the primary identifier.
- Keep the field names stable across weeks even when the number of parts changes.
- Do not rely on brittle page ids such as `p19`, `p26`, or `p37`.
- Treat each meeting part as a heading anchor with a bounded related-content region.
- Use semantic section boundaries and relative traversal within the article.
- Keep the ministry and living subsection columns fixed-width:
  - `ministry_1`..`ministry_5` plus matching `_note` fields
  - `living_1`..`living_4` plus matching `_note` fields
- Stop living subsection extraction at `Studio biblico di congregazione`.
- Do not include `Commenti conclusivi` in the living or study fields.

Current scraper behavior:
- Navigate with Playwright using a browser context.
- Open a fresh Playwright page for each source URL.
- Navigate with `commit` and then wait for the rendered text body to become available.
- Extract the meeting article with one semantic Playwright pass.
- Read section headings by their visible labels.
- Within a section, collect `h3` part headings in order until the next `h2`.
- For each part, collect the related text from nearby sibling blocks until the next `h3` or `h2`.
- Use the first section-3 `Cantico` as `song_2`.
- Use the section-3 `Studio biblico di congregazione` heading as the study anchor and its related block as `study_material`.
- Use the `Commenti conclusivi` heading only to derive `song_3`.
- Keep previous/next page links derived from the navigation links on the page.

Regression checks:
- The sample page must still load without a navigation timeout.
- The sample page must still produce the requested fields.
- The scraper must keep `song_2` separate from `living_1`.
- The scraper must still fill empty ministry or living slots with empty strings rather than shifting columns.
- The scraper must stop section-3 living extraction at `Studio biblico di congregazione`.
- The scraper must not include `Commenti conclusivi` inside any living or study note field.
- The scraper must continue to work without `--disable-http2`.
- The sample page must continue to work with the minimal test set.

Field rules:
- `week`: first `h1` in the article header
- `bible_chapters`: first `h2` in the article header
- `song_1`: first heading in the article that contains a `Cantico`
- `section_1`: `h2` containing `TESORI DELLA PAROLA DI DIO`
- `treasures`: first `h3` inside section 1
- `gems`: second `h3` inside section 1
- `gems_notes`: related content after the `gems` heading until the next heading
- `reading`: third `h3` inside section 1
- `reading_material`: related content after the `reading` heading until the next heading
- `section_2`: `h2` containing `EFFICACI NEL MINISTERO`
- `ministry_*`: ordered `h3` headings inside section 2, up to 5 slots
- `ministry_*_note`: related content for each section-2 part until the next heading
- `section_3`: `h2` containing `VITA CRISTIANA`
- `song_2`: first `Cantico` heading inside section 3
- `living_*`: ordered section-3 `h3` headings after `song_2` and before `Studio biblico di congregazione`
- `living_*_note`: related content for each living part until the next heading
- `study`: section-3 heading containing `Studio biblico di congregazione`
- `study_material`: related content after the study heading until the next heading
- `song_3`: `Cantico` found inside the `Commenti conclusivi` heading
- `prev_week_page` and `next_week_page`: adjacent week links inferred from the page navigation links

### Case 2: section-count variants

Example pages:
- `https://wol.jw.org/it/wol/d/r6/lp-i/202026164`
- `https://wol.jw.org/it/wol/d/r6/lp-i/202026165`
- `https://wol.jw.org/it/wol/d/r6/lp-i/202026166`
- `https://wol.jw.org/it/wol/d/r6/lp-i/202026167`

Observed shape:
- Section 2 can expand or shrink without moving the section boundaries.
- Section 3 can expand or shrink before the study block.
- The final section-3 item is still `Studio biblico di congregazione`.
- The note for a part can span multiple nearby containers, not just one paragraph block.

Extraction rule:
- For section 2, collect every `h3` until the next `h2`, then map them left to right into `ministry_1`..`ministry_5`.
- For section 3, ignore the first `Cantico` heading for the `living_*` group, then collect `h3` parts until the `Studio biblico di congregazione` heading.
- Aggregate all nearby related content until the next heading instead of stopping at the first non-empty block.

Regression checks:
- `202026164` must populate 4 ministry slots and 1 living slot before study.
- `202026165` must populate 3 ministry slots and 2 living slots before study.
- `202026166` must populate 4 ministry slots and 2 living slots before study.
- `202026167` must populate 3 ministry slots and 2 living slots before study.

## New Cases

Add one section here for each new page type or edge case we learn.

Suggested format:

### Case N: <short name>

- Example page:
- Observed shape:
- Extraction rule:
- Regression checks:
- Notes:
