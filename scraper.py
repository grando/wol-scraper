import argparse
import asyncio
import csv
from pathlib import Path

from playwright.async_api import async_playwright


USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)
NAVIGATION_TIMEOUT_MS = 120000
CONTENT_READY_TIMEOUT_MS = 60000
SETTLE_TIMEOUT_MS = 1000

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
        locator = page.locator(selector)
        if await locator.count():
            text = (await locator.first.inner_text()).strip()
            if text:
                return text
    return ""


async def body_text(page) -> str:
    text = await page.evaluate(
        """() => {
            const body = document.body;
            const text = body ? (body.innerText || body.textContent || "") : "";
            return text ? text.trim() : "";
        }"""
    )
    return text


async def accessibility_text(page) -> str:
    try:
        snapshot = await page.accessibility.snapshot(interesting_only=False)
    except Exception:  # noqa: BLE001
        return ""

    def collect(node) -> list[str]:
        if not node:
            return []

        parts = []
        name = (node.get("name") or "").strip()
        value = node.get("value")
        if name:
            parts.append(name)
        if isinstance(value, str) and value.strip() and value.strip() != name:
            parts.append(value.strip())
        for child in node.get("children") or []:
            parts.extend(collect(child))
        return parts

    return "\n".join(part for part in collect(snapshot) if part).strip()


async def scrape_url(page, url: str) -> dict[str, str]:
    row = {
        "source_url": url,
        "title": "",
        "content": "",
        "error": "",
    }

    try:
        await page.goto(url, wait_until="commit", timeout=NAVIGATION_TIMEOUT_MS)
        try:
            await page.locator("h1").first.wait_for(timeout=CONTENT_READY_TIMEOUT_MS)
        except Exception:  # noqa: BLE001
            pass
        try:
            await page.wait_for_function(
                "() => document.body && document.body.innerText.trim().length > 1000",
                timeout=CONTENT_READY_TIMEOUT_MS,
            )
        except Exception:  # noqa: BLE001
            pass
        await page.wait_for_timeout(SETTLE_TIMEOUT_MS)
        row["title"] = await page.title()
        row["content"] = (
            await accessibility_text(page)
            or await body_text(page)
            or await first_text(page, CONTENT_SELECTORS)
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
        page = await context.new_page()

        rows = []
        for url in urls:
            rows.append(await scrape_url(page, url))

        await browser.close()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["source_url", "title", "content", "error"])
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
