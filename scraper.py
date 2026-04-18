import argparse
import asyncio
import csv
import json
import re
import sys
from pathlib import Path
from urllib.parse import urljoin

try:
    from playwright.async_api import async_playwright
except ModuleNotFoundError:  # pragma: no cover - only hit when dependencies are missing
    async_playwright = None


USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)
NAVIGATION_TIMEOUT_MS = 120000
FIELD_READY_TIMEOUT_MS = 60000

CSV_FIELD_ORDER = [
    "source_url",
    "valid",
    "week",
    "bible_chapters",
    "song_1",
    "section_1",
    "treasures",
    "gems",
    "gems_notes",
    "reading",
    "reading_material",
    "section_2",
    "ministry_1",
    "ministry_1_note",
    "ministry_2",
    "ministry_2_note",
    "ministry_3",
    "ministry_3_note",
    "ministry_4",
    "ministry_4_note",
    "ministry_5",
    "ministry_5_note",
    "section_3",
    "song_2",
    "living_1",
    "living_1_note",
    "living_2",
    "living_2_note",
    "living_3",
    "living_3_note",
    "living_4",
    "living_4_note",
    "study",
    "study_material",
    "song_3",
    "prev_week_page",
    "next_week_page",
    "error",
]

WELCOME_TEXT = """WOL Scraper

Small Python + Playwright CLI for Watchtower Online Library pages.

Main options:
  --urls FILE        Read one URL per line from a text file
  URLS               Pass one or more direct URLs on the command line
  --output FILE      Write output to a file; omit it to print to stdout
  --format csv|json  Choose CSV or JSON output (default: csv)
  --deep N           Follow next_week_page links from one direct URL (1-50)
  --show-browser     Open the browser window when a display is available

Common uses:
  scraper.py --urls sample-urls.txt --output output.csv
  scraper.py https://wol.jw.org/it/wol/d/r6/lp-i/202026164
  scraper.py https://wol.jw.org/it/wol/d/r6/lp-i/202026164 --deep 3
"""


def read_urls(path: Path) -> list[str]:
    return [
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]


def normalize_text(text: str) -> str:
    return " ".join(text.split()).strip()


def title_prefix(title: str) -> str:
    for separator in (" — ", " - ", " | "):
        if separator in title:
            return normalize_text(title.split(separator, 1)[0])
    return normalize_text(title)


async def collect_page_links(page) -> list[dict[str, str]]:
    links = []
    link_locator = page.locator("a")
    link_count = await link_locator.count()
    for index in range(link_count):
        element = link_locator.nth(index)
        try:
            text = await element.inner_text(timeout=1000)
        except Exception:  # noqa: BLE001
            text = ""
        if not text:
            try:
                text = await element.text_content(timeout=1000)
            except Exception:  # noqa: BLE001
                text = ""
        href = await element.get_attribute("href")
        links.append(
            {
                "index": index,
                "text": normalize_text(text or ""),
                "href": normalize_text(href or ""),
            }
        )
    return links


def adjacent_page_link(url: str, links: list[dict[str, str]], direction: str) -> str:
    current_match = re.search(r"/(\d+)$", url)
    if not current_match:
        return ""

    current_id = int(current_match.group(1))
    candidates = []
    for link in links:
        href = link.get("href") or ""
        match = re.search(r"/(\d+)$", href)
        if not match:
            continue
        page_id = int(match.group(1))
        if page_id == current_id:
            continue
        candidates.append((page_id, href))

    if direction == "prev":
        previous = [item for item in candidates if item[0] < current_id]
        if previous:
            return urljoin(url, max(previous, key=lambda item: item[0])[1])
    if direction == "next":
        following = [item for item in candidates if item[0] > current_id]
        if following:
            return urljoin(url, min(following, key=lambda item: item[0])[1])
    return ""


async def extract_meeting_page(page) -> dict[str, object]:
    data = await page.evaluate(
        """() => {
            const article = document.querySelector('article#article, article.document, article');
            if (!article) {
                return {};
            }
            const scope = article.querySelector('.scalableui') || article;
            const contentRoot = scope.querySelector('.bodyTxt') || scope;

            const clean = (value) => (value || '').replace(/\\s+/g, ' ').trim();
            const cloneAndText = (node) => {
                if (!node) {
                    return '';
                }
                const clone = node.cloneNode(true);
                clone.querySelectorAll(
                    '.dc-screenReaderText, textarea, label, script, style, noscript'
                ).forEach((item) => item.remove());
                return clean(clone.innerText || clone.textContent || '');
            };
            const topLevelNode = (node) => {
                let current = node;
                while (current && current.parentElement && current.parentElement !== contentRoot) {
                    current = current.parentElement;
                }
                return current;
            };
            const headingText = (node) => clean(node ? (node.innerText || node.textContent || '') : '');
            const canticoFromHeading = (node) => {
                if (!node) {
                    return '';
                }
                const candidates = [...node.querySelectorAll('strong')]
                    .map((item) => clean(item.innerText || item.textContent || ''));
                for (const text of candidates) {
                    if (/^Cantico\\s+\\d+/i.test(text)) {
                        return text;
                    }
                }
                const fallback = headingText(node);
                const match = fallback.match(/Cantico\\s+\\d+/i);
                return match ? clean(match[0]) : '';
            };
            const collectRelatedText = (heading) => {
                const start = topLevelNode(heading);
                if (!start) {
                    return '';
                }
                const parts = [];
                for (let current = start.nextElementSibling; current; current = current.nextElementSibling) {
                    if (current.querySelector('h2, h3') || /^(H2|H3)$/.test(current.tagName)) {
                        break;
                    }
                    const text = cloneAndText(current);
                    if (text) {
                        parts.push(text);
                    }
                }
                return clean(parts.join(' '));
            };
            const findSectionHeading = (label) =>
                [...contentRoot.querySelectorAll('h2')].find((node) => headingText(node).includes(label)) || null;
            const collectSectionItems = (sectionHeading) => {
                const sectionTop = topLevelNode(sectionHeading);
                if (!sectionTop) {
                    return [];
                }
                const items = [];
                for (let current = sectionTop.nextElementSibling; current; current = current.nextElementSibling) {
                    const heading = /^(H2|H3)$/.test(current.tagName)
                        ? current
                        : current.querySelector('h2, h3');
                    if (!heading) {
                        continue;
                    }
                    if (heading.tagName === 'H2') {
                        break;
                    }
                    const title = headingText(heading);
                    if (!title) {
                        continue;
                    }
                    items.push({
                        title,
                        note: collectRelatedText(heading),
                        cantico: canticoFromHeading(heading),
                    });
                }
                return items;
            };

            const section1 = findSectionHeading('TESORI DELLA PAROLA DI DIO');
            const section2 = findSectionHeading('EFFICACI NEL MINISTERO');
            const section3 = findSectionHeading('VITA CRISTIANA');
            const header = scope.querySelector('header') || scope;
            const weekHeading = header.querySelector('h1');
            const chaptersHeading = header.querySelector('h2');
            const allH3 = [...contentRoot.querySelectorAll('h3')];
            const allSongs = allH3.map((node) => canticoFromHeading(node)).filter(Boolean);
            const section1Items = collectSectionItems(section1);
            const section2Items = collectSectionItems(section2);
            const section3Items = collectSectionItems(section3);
            const studyIndex = section3Items.findIndex((item) =>
                item.title.includes('Studio biblico di congregazione')
            );
            const commentHeading = allH3.find((node) => headingText(node).includes('Commenti conclusivi')) || null;

            let song2 = '';
            let livingItems = [];
            let study = { title: '', note: '' };
            if (section3Items.length > 0) {
                const maybeSong = section3Items[0].cantico;
                const contentItems = maybeSong ? section3Items.slice(1) : section3Items.slice();
                song2 = maybeSong;
                const contentStudyIndex = contentItems.findIndex((item) =>
                    item.title.includes('Studio biblico di congregazione')
                );
                if (contentStudyIndex >= 0) {
                    livingItems = contentItems.slice(0, contentStudyIndex);
                    study = contentItems[contentStudyIndex];
                } else {
                    livingItems = contentItems;
                }
            }

            return {
                week: headingText(weekHeading),
                bible_chapters: headingText(chaptersHeading),
                song_1: allSongs[0] || '',
                section_1: headingText(section1),
                treasures: section1Items[0]?.title || '',
                gems: section1Items[1]?.title || '',
                gems_notes: section1Items[1]?.note || '',
                reading: section1Items[2]?.title || '',
                reading_material: section1Items[2]?.note || '',
                section_2: headingText(section2),
                ministry_items: section2Items.map((item) => ({ title: item.title, note: item.note })),
                section_3: headingText(section3),
                song_2: song2,
                living_items: livingItems.map((item) => ({ title: item.title, note: item.note })),
                study: study.title || '',
                study_material: study.note || '',
                song_3: canticoFromHeading(commentHeading),
                raw_section3_items: section3Items.map((item) => ({ title: item.title, note: item.note })),
                raw_study_index: studyIndex,
            };
        }"""
    )
    return {key: normalize_text(value) if isinstance(value, str) else value for key, value in data.items()}


def fill_group(row: dict[str, str], prefix: str, items: list[dict[str, str]], max_items: int) -> None:
    for index in range(max_items):
        title_key = f"{prefix}_{index + 1}"
        note_key = f"{prefix}_{index + 1}_note"
        row[title_key] = ""
        row[note_key] = ""
        if index < len(items):
            row[title_key] = normalize_text(items[index].get("title", ""))
            row[note_key] = normalize_text(items[index].get("note", ""))


async def scrape_url(page, url: str) -> dict[str, str]:
    row = {name: "" for name in CSV_FIELD_ORDER}
    row["source_url"] = url

    try:
        await page.goto(url, wait_until="commit", timeout=NAVIGATION_TIMEOUT_MS)
        try:
            await page.wait_for_function(
                """() => {
                    const article = document.querySelector('article#article, article.document, article');
                    return article && article.innerText && article.innerText.trim().length > 1000;
                }""",
                timeout=FIELD_READY_TIMEOUT_MS,
            )
        except Exception:  # noqa: BLE001
            pass

        extracted = await extract_meeting_page(page)
        page_title = await page.title()
        links = await collect_page_links(page)

        row["week"] = extracted.get("week", "") or title_prefix(page_title)
        row["bible_chapters"] = extracted.get("bible_chapters", "")
        row["song_1"] = extracted.get("song_1", "")
        row["section_1"] = extracted.get("section_1", "")
        row["treasures"] = extracted.get("treasures", "")
        row["gems"] = extracted.get("gems", "")
        row["gems_notes"] = extracted.get("gems_notes", "")
        row["reading"] = extracted.get("reading", "")
        row["reading_material"] = extracted.get("reading_material", "")
        row["section_2"] = extracted.get("section_2", "")
        row["section_3"] = extracted.get("section_3", "")
        row["song_2"] = extracted.get("song_2", "")
        row["study"] = extracted.get("study", "")
        row["study_material"] = extracted.get("study_material", "")
        row["song_3"] = extracted.get("song_3", "")
        row["prev_week_page"] = adjacent_page_link(url, links, "prev")
        row["next_week_page"] = adjacent_page_link(url, links, "next")

        fill_group(row, "ministry", extracted.get("ministry_items", []), 5)
        fill_group(row, "living", extracted.get("living_items", []), 4)
    except Exception as exc:  # noqa: BLE001
        row["error"] = str(exc)

    row["valid"] = is_valid_row(row)
    return row


async def launch_browser(playwright, show_browser: bool):
    return await playwright.chromium.launch(
        headless=not show_browser,
        args=["--no-sandbox", "--disable-dev-shm-usage"],
    )


async def crawl(urls: list[str], show_browser: bool) -> list[dict[str, str]]:
    async with async_playwright() as playwright:
        browser = await launch_browser(playwright, show_browser)
        context = await browser.new_context(user_agent=USER_AGENT)

        rows = []
        for url in urls:
            print(f"Scraping {url} ...", file=sys.stderr, flush=True)
            page = await context.new_page()
            try:
                rows.append(await scrape_url(page, url))
            finally:
                await page.close()

        await browser.close()

    return rows


async def crawl_deep(start_url: str, depth: int, show_browser: bool) -> list[dict[str, str]]:
    async with async_playwright() as playwright:
        browser = await launch_browser(playwright, show_browser)
        context = await browser.new_context(user_agent=USER_AGENT)

        rows = []
        seen = set()
        current_url = start_url
        for _ in range(depth):
            if current_url in seen:
                break
            seen.add(current_url)
            print(f"Scraping {current_url} ...", file=sys.stderr, flush=True)

            page = await context.new_page()
            try:
                row = await scrape_url(page, current_url)
            finally:
                await page.close()

            rows.append(row)
            next_url = row.get("next_week_page", "").strip()
            if not next_url:
                break
            current_url = next_url

        await browser.close()

    return rows


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Scrape a list of URLs and write the extracted data to CSV or JSON."
    )
    parser.add_argument(
        "--urls",
        dest="urls_file",
        help="Text file with one URL per line. Optional when URLs are passed directly.",
    )
    parser.add_argument("urls", nargs="*", help="One or more URLs to scrape directly.")
    parser.add_argument(
        "--output",
        help="Output file to write. If omitted, the result is written to stdout.",
    )
    parser.add_argument(
        "--format",
        choices=("csv", "json"),
        default="csv",
        help="Output format to write (default: csv).",
    )
    parser.add_argument(
        "--deep",
        type=int,
        default=1,
        help="Number of linked pages to parse for a single direct URL (1-50, default: 1).",
    )
    parser.add_argument(
        "--show-browser",
        action="store_true",
        help="Open Playwright in headed mode when a display is available.",
    )
    return parser.parse_args()


def collect_urls(args: argparse.Namespace) -> list[str]:
    urls = []
    if args.urls_file:
        urls.extend(read_urls(Path(args.urls_file)))
    urls.extend(args.urls)
    if not urls:
        raise SystemExit("Provide --urls FILE or one or more direct URLs.")
    return urls


def collect_direct_url(args: argparse.Namespace) -> str:
    if args.urls_file:
        raise SystemExit("--deep can only be used with a direct URL, not with --urls.")
    if len(args.urls) != 1:
        raise SystemExit("--deep can only be used with one direct URL.")
    return args.urls[0]


def is_valid_row(row: dict[str, str]) -> bool:
    return all(row.get(field, "").strip() for field in ("section_1", "section_2", "section_3"))


def write_csv(rows: list[dict[str, str]], output_path: Path) -> None:
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELD_ORDER)
        writer.writeheader()
        writer.writerows(rows)


def write_csv_stdout(rows: list[dict[str, str]]) -> None:
    writer = csv.DictWriter(sys.stdout, fieldnames=CSV_FIELD_ORDER)
    writer.writeheader()
    writer.writerows(rows)


def write_json(rows: list[dict[str, str]], output_path: Path) -> None:
    output_path.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")


def write_json_stdout(rows: list[dict[str, str]]) -> None:
    print(json.dumps(rows, ensure_ascii=False, indent=2))


def print_welcome() -> None:
    print(WELCOME_TEXT.strip())


def main() -> None:
    if len(sys.argv) == 1:
        print_welcome()
        return

    if async_playwright is None:
        raise SystemExit("Playwright is not installed. Run 'make host-install' or use Docker.")

    args = parse_args()
    if not 1 <= args.deep <= 50:
        raise SystemExit("--deep must be between 1 and 50.")

    if args.deep > 1:
        start_url = collect_direct_url(args)
        rows = asyncio.run(crawl_deep(start_url, args.deep, args.show_browser))
        rows_to_write = rows
    else:
        urls = collect_urls(args)
        rows = asyncio.run(crawl(urls, args.show_browser))
        rows_to_write = [row for row in rows if is_valid_row(row)]

    skipped = sum(1 for row in rows if not is_valid_row(row))
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        if args.format == "csv":
            write_csv(rows_to_write, output_path)
        else:
            write_json(rows_to_write, output_path)
    else:
        if args.format == "csv":
            write_csv_stdout(rows_to_write)
        else:
            write_json_stdout(rows_to_write)
    print(f"Skipped {skipped} invalid URL(s).", file=sys.stderr)


if __name__ == "__main__":
    main()
