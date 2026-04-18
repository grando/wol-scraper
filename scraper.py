import argparse
import asyncio
import csv
from pathlib import Path

from playwright.async_api import TimeoutError, async_playwright


USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)
NAVIGATION_TIMEOUT_MS = 120000
CONTENT_READY_TIMEOUT_MS = 60000

# Edit these selectors when you identify the exact fields to extract.
CONTENT_SELECTORS = [
    "div.meetingContent",
    "article",
    "main",
    "body",
]


def read_urls(path: Path) -> list[str]:
    return [
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]


async def first_text(page, selectors: list[str]) -> str:
    for selector in selectors:
        try:
            text = (await page.locator(selector).first.inner_text(timeout=3000)).strip()
            if text:
                return text
        except Exception:  # noqa: BLE001
            pass
        try:
            text = (await page.locator(selector).first.text_content(timeout=3000) or "").strip()
            if text:
                return text
        except Exception:  # noqa: BLE001
            continue
    return ""


async def scrape_url(page, url: str) -> dict[str, str]:
    row = {
        "source_url": url,
        "title": "",
        "content": "",
        "error": "",
    }

    try:
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=NAVIGATION_TIMEOUT_MS)
        except TimeoutError:
            await page.goto(url, wait_until="commit", timeout=NAVIGATION_TIMEOUT_MS)
        try:
            await page.locator("body").first.wait_for(timeout=CONTENT_READY_TIMEOUT_MS)
        except Exception:  # noqa: BLE001
            pass
        try:
            await page.wait_for_function(
                "() => document.body && document.body.innerText.trim().length > 1000",
                timeout=CONTENT_READY_TIMEOUT_MS,
            )
        except Exception:  # noqa: BLE001
            pass
        row["title"] = await page.title()
        try:
            body_text = (await page.inner_text("body", timeout=3000)).strip()
        except Exception:  # noqa: BLE001
            body_text = (
                await page.evaluate(
                    """() => {
                        const body = document.body;
                        return body ? (body.innerText || "").trim() : "";
                    }"""
                )
            ).strip()
        row["content"] = (
            await first_text(page, CONTENT_SELECTORS)
            or body_text
        )
    except Exception as exc:  # noqa: BLE001
        row["error"] = str(exc)

    return row


async def crawl(urls: list[str], output_path: Path) -> None:
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(
            headless=True,
            args=["--disable-http2", "--no-sandbox", "--disable-dev-shm-usage"],
        )
        context = await browser.new_context(user_agent=USER_AGENT)

        rows = []
        for url in urls:
            print(f"Scraping {url} ...", flush=True)
            page = await context.new_page()
            try:
                rows.append(await scrape_url(page, url))
            finally:
                await page.close()

        await browser.close()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        fieldnames = list(rows[0].keys()) if rows else ["source_url", "title", "content", "error"]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Scrape a list of URLs and write the extracted data to a CSV file."
    )
    parser.add_argument("--urls", required=True, help="Text file with one URL per line.")
    parser.add_argument("--output", required=True, help="CSV file to write.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    urls = read_urls(Path(args.urls))
    asyncio.run(crawl(urls, Path(args.output)))


if __name__ == "__main__":
    main()
