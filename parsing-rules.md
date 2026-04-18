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
- Try stable content containers first, then fall back to `body` text from Playwright.
- For known content containers, try rendered text first and then DOM text content if rendered text is still unavailable.
- If Playwright `inner_text("body")` times out on WOL, fall back to an in-page `document.body.innerText` read through Playwright.
- Use `domcontentloaded` plus a text-readiness check instead of layering multiple waits with a fixed sleep.
- Fall back to `commit` navigation when a WOL page does not reach `domcontentloaded` within the navigation timeout.
- After navigation, wait for the page `body` element before attempting content extraction.
- Use a fresh Playwright page per URL so one failed or redirected page does not leak state into the next one.
- Keep lightweight CLI progress output during scraping.
- Pin the Playwright Python package version in Docker for reproducible builds.
- Keep the Docker base image on a distro-specific tag so the pinned Playwright install remains buildable.

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

What matters for extraction:
- Use the page URL as the primary identifier.
- Capture the page title.
- Capture the meaningful body content for later field extraction.
- Do not rely on one brittle selector such as a single `div` class.
- Prefer Playwright-native rendered-text extraction first. Add separate HTML parsing only when a documented case shows that Playwright text extraction is insufficient.

Current scraper behavior:
- Navigate with Playwright using a browser context.
- Open a fresh Playwright page for each source URL.
- Wait for `domcontentloaded` and then for visible body text to become substantial when possible.
- Fall back to `commit` for navigation when `domcontentloaded` does not complete in time on WOL.
- Wait for the page `body` element before running extraction reads.
- Extract title.
- Try known content containers first.
- For those containers, prefer `inner_text()` and then fall back to `text_content()`.
- Fall back to Playwright `inner_text("body")`.
- If that body-text read times out, fall back to an in-page body-text read through Playwright evaluation.
- Avoid accessibility-tree extraction unless a future documented case requires it.

Regression checks:
- The sample page must still load without a navigation timeout.
- The sample page must still produce a title.
- The scraper must continue to return a CSV row even if a specific selector is missing.
- The scraper must still produce content when container-specific selectors fail and only `body` text is usable.
- The sample page must continue to work with the minimal test set.

Open questions:
- Which exact pieces of the meeting page should become CSV columns?
- Should section headings, scripture references, comments, and questions be split into separate fields?
- Should we keep a raw `content` column as a fallback even after the structured fields are defined?

## New Cases

Add one section here for each new page type or edge case we learn.

Suggested format:

### Case N: <short name>

- Example page:
- Observed shape:
- Extraction rule:
- Regression checks:
- Notes:
