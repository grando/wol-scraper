import argparse
import asyncio
import csv
import json
import re
import sys
from pathlib import Path
from urllib.parse import urljoin

from playwright.async_api import TimeoutError, async_playwright


USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)
NAVIGATION_TIMEOUT_MS = 120000
FIELD_READY_TIMEOUT_MS = 60000

PAGE_RULES = [
    {
        "name": "meeting_page_202026161",
        "url_pattern": re.compile(r"^https://wol\.jw\.org/it/wol/d/r6/lp-i/202026161$"),
        "ready_xpath": '//*[@id="p1"]',
        "fields": [
            {
                "name": "week",
                "xpath": '//*[@id="p1"]',
                "kind": "text",
                "fallback": "title_prefix",
            },
            {
                "name": "bible_chapters",
                "xpath": '//*[@id="p2"]',
                "kind": "text",
                "fallback": "scripture_link",
            },
            {
                "name": "song_1",
                "xpath": '//*[@id="p3"]/a/strong',
                "kind": "text",
                "fallback": "cantico_index",
                "fallback_index": 0,
            },
            {
                "name": "treasures",
                "xpath": '//*[@id="p5"]/strong',
                "kind": "text",
            },
            {
                "name": "gems",
                "xpath": '//*[@id="p11"]/strong',
                "kind": "text",
            },
            {
                "name": "gems_notes",
                "xpath": '//*[@id="p11"]',
                "kind": "following_text",
            },
            {
                "name": "reading",
                "xpath": '//*[@id="p17"]',
                "kind": "text",
            },
            {
                "name": "reading_material",
                "xpath": '//*[@id="p17"]',
                "kind": "following_text",
            },
            {
                "name": "section_1",
                "xpath": '//*[@id="p4"]/strong',
                "kind": "text",
                "fallback": "heading_index",
                "fallback_index": 0,
            },
            {
                "name": "section_2",
                "xpath": '//*[@id="p19"]/strong',
                "kind": "text",
                "fallback": "heading_index",
                "fallback_index": 1,
            },
            {
                "name": "section_3",
                "xpath": '//*[@id="p26"]/strong',
                "kind": "text",
                "fallback": "heading_index",
                "fallback_index": 2,
            },
            {
                "name": "song_2",
                "xpath": '//*[@id="p27"]/a/strong',
                "kind": "text",
                "fallback": "cantico_index",
                "fallback_index": 1,
            },
            {
                "name": "song_3",
                "xpath": '//*[@id="p47"]/span[2]/a/strong',
                "kind": "text",
                "fallback": "cantico_index",
                "fallback_index": 2,
            },
            {
                "name": "study",
                "xpath": '//*[@id="p45"]/strong',
                "kind": "text",
            },
            {
                "name": "study_material",
                "xpath": '//*[@id="p45"]',
                "kind": "following_text",
            },
            {
                "name": "prev_week_page",
                "xpath": '//*[@id="publicationNavigation"]/div[3]/ul/li[1]/a',
                "kind": "href",
                "fallback": "adjacent_page_link",
                "direction": "prev",
            },
            {
                "name": "next_week_page",
                "xpath": '//*[@id="publicationNavigation"]/div[3]/ul/li[2]/a',
                "kind": "href",
                "fallback": "adjacent_page_link",
                "direction": "next",
            },
        ],
        "section_groups": [
            {
                "anchor_text": "EFFICACI NEL MINISTERO",
                "prefix": "ministry",
                "max_items": 5,
            },
            {
                "anchor_text": "VITA CRISTIANA",
                "prefix": "living",
                "max_items": 4,
                "stop_title_contains": "Studio biblico di congregazione",
            },
        ],
    },
    {
        "name": "meeting_page_202026164",
        "url_pattern": re.compile(r"^https://wol\.jw\.org/it/wol/d/r6/lp-i/202026164$"),
        "ready_xpath": '//*[@id="p1"]',
        "fields": [
            {
                "name": "week",
                "xpath": '//*[@id="p1"]',
                "kind": "text",
                "fallback": "title_prefix",
            },
            {
                "name": "bible_chapters",
                "xpath": '//*[@id="p2"]',
                "kind": "text",
                "fallback": "scripture_link",
            },
            {
                "name": "song_1",
                "xpath": '//*[@id="p3"]/a/strong',
                "kind": "text",
                "fallback": "cantico_index",
                "fallback_index": 0,
            },
            {
                "name": "treasures",
                "xpath": '//*[@id="p5"]/strong',
                "kind": "text",
            },
            {
                "name": "gems",
                "xpath": '//*[@id="p11"]/strong',
                "kind": "text",
            },
            {
                "name": "gems_notes",
                "xpath": '//*[@id="p11"]',
                "kind": "following_text",
            },
            {
                "name": "reading",
                "xpath": '//*[@id="p17"]',
                "kind": "text",
            },
            {
                "name": "reading_material",
                "xpath": '//*[@id="p17"]',
                "kind": "following_text",
            },
            {
                "name": "section_1",
                "xpath": '//*[@id="p4"]/strong',
                "kind": "text",
                "fallback": "heading_index",
                "fallback_index": 0,
            },
            {
                "name": "section_2",
                "xpath": '//*[@id="p19"]/strong',
                "kind": "text",
                "fallback": "heading_index",
                "fallback_index": 1,
            },
            {
                "name": "section_3",
                "xpath": '//*[@id="p26"]/strong',
                "kind": "text",
                "fallback": "heading_index",
                "fallback_index": 2,
            },
            {
                "name": "study",
                "xpath": '//*[@id="p37"]/strong',
                "kind": "text",
            },
            {
                "name": "study_material",
                "xpath": '//*[@id="p37"]',
                "kind": "following_text",
            },
            {
                "name": "song_2",
                "xpath": '//*[@id="p27"]/a/strong',
                "kind": "text",
                "fallback": "cantico_index",
                "fallback_index": 1,
            },
            {
                "name": "song_3",
                "xpath": '//*[@id="p47"]/span[2]/a/strong',
                "kind": "text",
                "fallback": "cantico_index",
                "fallback_index": 2,
            },
            {
                "name": "prev_week_page",
                "xpath": '//*[@id="publicationNavigation"]/div[3]/ul/li[1]/a',
                "kind": "href",
                "fallback": "adjacent_page_link",
                "direction": "prev",
            },
            {
                "name": "next_week_page",
                "xpath": '//*[@id="publicationNavigation"]/div[3]/ul/li[2]/a',
                "kind": "href",
                "fallback": "adjacent_page_link",
                "direction": "next",
            },
        ],
        "section_groups": [
            {
                "anchor_text": "EFFICACI NEL MINISTERO",
                "prefix": "ministry",
                "max_items": 5,
            },
            {
                "anchor_text": "VITA CRISTIANA",
                "prefix": "living",
                "max_items": 4,
                "stop_title_contains": "Studio biblico di congregazione",
            },
        ],
    },
    {
        "name": "meeting_page_generic",
        "url_pattern": re.compile(r"^https://wol\.jw\.org/it/wol/d/r6/lp-i/\d+$"),
        "ready_xpath": '//*[@id="p1"]',
        "fields": [
            {
                "name": "week",
                "xpath": '//*[@id="p1"]',
                "kind": "text",
                "fallback": "title_prefix",
            },
            {
                "name": "bible_chapters",
                "xpath": '//*[@id="p2"]',
                "kind": "text",
                "fallback": "scripture_link",
            },
            {
                "name": "song_1",
                "xpath": '//*[@id="p3"]/a/strong',
                "kind": "text",
                "fallback": "cantico_index",
                "fallback_index": 0,
            },
            {
                "name": "section_1",
                "xpath": '//*[@id="p4"]/strong',
                "kind": "text",
                "fallback": "heading_index",
                "fallback_index": 0,
            },
            {
                "name": "section_2",
                "xpath": '//*[@id="p19"]/strong',
                "kind": "text",
                "fallback": "heading_index",
                "fallback_index": 1,
            },
            {
                "name": "section_3",
                "xpath": '//*[@id="p26"]/strong',
                "kind": "text",
                "fallback": "heading_index",
                "fallback_index": 2,
            },
            {
                "name": "song_2",
                "xpath": '//*[@id="p27"]/a/strong',
                "kind": "text",
                "fallback": "cantico_index",
                "fallback_index": 1,
            },
            {
                "name": "song_3",
                "xpath": '//*[@id="p47"]/span[2]/a/strong',
                "kind": "text",
                "fallback": "cantico_index",
                "fallback_index": 2,
            },
            {
                "name": "prev_week_page",
                "xpath": '//*[@id="publicationNavigation"]/div[3]/ul/li[1]/a',
                "kind": "href",
                "fallback": "adjacent_page_link",
                "direction": "prev",
            },
            {
                "name": "next_week_page",
                "xpath": '//*[@id="publicationNavigation"]/div[3]/ul/li[2]/a',
                "kind": "href",
                "fallback": "adjacent_page_link",
                "direction": "next",
            },
        ],
        "section_groups": [],
    }
]

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


def read_urls(path: Path) -> list[str]:
    return [
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]


def normalize_text(text: str) -> str:
    return " ".join(text.split()).strip()


def select_rule(url: str) -> dict:
    for rule in PAGE_RULES:
        if rule["url_pattern"].match(url):
            return rule
    return PAGE_RULES[0]


def title_prefix(title: str) -> str:
    for separator in (" — ", " - ", " | "):
        if separator in title:
            return normalize_text(title.split(separator, 1)[0])
    return normalize_text(title)


async def collect_page_state(page) -> dict:
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

    strongs = []
    strong_locator = page.locator("strong")
    strong_count = await strong_locator.count()
    for index in range(strong_count):
        element = strong_locator.nth(index)
        try:
            text = await element.inner_text(timeout=1000)
        except Exception:  # noqa: BLE001
            text = ""
        if not text:
            try:
                text = await element.text_content(timeout=1000)
            except Exception:  # noqa: BLE001
                text = ""
        strongs.append(
            {
                "index": index,
                "text": normalize_text(text or ""),
            }
        )

    headings = []
    heading_locator = page.locator("h3")
    heading_count = await heading_locator.count()
    for index in range(heading_count):
        element = heading_locator.nth(index)
        try:
            text = await element.inner_text(timeout=1000)
        except Exception:  # noqa: BLE001
            text = ""
        if not text:
            try:
                text = await element.text_content(timeout=1000)
            except Exception:  # noqa: BLE001
                text = ""
        headings.append({"index": index, "text": normalize_text(text or ""), "level": 3})

    return {"title": await page.title(), "links": links, "strongs": strongs, "headings": headings}


def pick_link_texts(links: list[dict], pattern: re.Pattern[str]) -> list[str]:
    return [normalize_text(link["text"]) for link in links if pattern.search(normalize_text(link["text"]))]


def pick_semantic_links(links: list[dict]) -> list[dict]:
    blocked_prefixes = (
        "Cantico",
        "mwb",
        "lmd",
        "th",
        "w0",
        "it ",
        "Pubblicazioni",
        "Italiano",
        "Condividi",
        "Impostazioni",
        "Accedi",
        "Disconnetti",
        "JW.ORG",
        "BIBLIOTECA ONLINE",
        "Guardar",
    )
    return [
        link
        for link in links
        if link["text"]
        and len(link["text"]) > 2
        and not link["text"].startswith(blocked_prefixes)
    ]


def pick_cantico_texts(strongs: list[dict]) -> list[str]:
    matches = []
    for strong in strongs:
        text = normalize_text(strong.get("text", ""))
        if re.match(r"^Cantico\s+\d+", text):
            matches.append(text)
    return matches


async def extract_following_text(locator) -> str:
    element = await locator.element_handle()
    if not element:
        return ""

    text = await element.evaluate(
        """(node) => {
            const nodes = [...document.querySelectorAll('[id^="p"], [id^="tt"]')];
            const startIndex = nodes.findIndex((item) => item.id === node.id);
            if (startIndex < 0) {
                return '';
            }
            for (let index = startIndex + 1; index < nodes.length; index += 1) {
                const current = nodes[index];
                if (/^H[1-6]$/.test(current.tagName)) {
                    break;
                }
                const clone = current.cloneNode(true);
                clone.querySelectorAll('.dc-screenReaderText').forEach((item) => item.remove());
                const value = (clone.innerText || clone.textContent || '').replace(/\\s+/g, ' ').trim();
                if (value) {
                    return value;
                }
            }
            return '';
        }"""
    )
    return normalize_text(text or "")


async def extract_section_group(page, group: dict) -> list[dict[str, str]]:
    heading_locator = page.locator("h2").filter(has_text=group["anchor_text"]).first
    if await heading_locator.count() == 0:
        return []

    heading = await heading_locator.element_handle()
    if not heading:
        return []

    items = await heading.evaluate(
        """(node, config) => {
            const clean = (value) => (value || '').replace(/\\s+/g, ' ').trim();
            const textFrom = (current) => {
                const clone = current.cloneNode(true);
                clone.querySelectorAll('.dc-screenReaderText').forEach((item) => item.remove());
                return clean(clone.innerText || clone.textContent || '');
            };
            const nodes = [...document.querySelectorAll('[id^="p"], [id^="tt"]')];
            const startIndex = nodes.findIndex((item) => item.id === node.id);
            const nextBlockText = (currentId) => {
                const currentIndex = nodes.findIndex((item) => item.id === currentId);
                if (currentIndex < 0) {
                    return '';
                }
                for (let index = currentIndex + 1; index < nodes.length; index += 1) {
                    const sibling = nodes[index];
                    if (/^H[1-6]$/.test(sibling.tagName)) {
                        return '';
                    }
                    const value = textFrom(sibling);
                    if (value) {
                        return value;
                    }
                }
                return '';
            };

            const items = [];
            if (startIndex < 0) {
                return items;
            }
            for (let index = startIndex + 1; index < nodes.length; index += 1) {
                const current = nodes[index];
                if (current.tagName === 'H2') {
                    break;
                }
                if (current.tagName === 'H3') {
                    const title = textFrom(current);
                    if (title) {
                        items.push({ title, note: nextBlockText(current.id) });
                        if (config.stopTitleContains && title.includes(config.stopTitleContains)) {
                            break;
                        }
                        if (items.length >= config.maxItems) {
                            break;
                        }
                    }
                }
            }
            return items;
        }""",
        {
            "maxItems": group["max_items"],
            "stopTitleContains": group.get("stop_title_contains", ""),
        },
    )

    return [
        {
            "title": normalize_text(item.get("title", "")),
            "note": normalize_text(item.get("note", "")),
        }
        for item in items
        if normalize_text(item.get("title", ""))
    ]


def fallback_field_value(url: str, field: dict, state: dict) -> str:
    fallback = field.get("fallback")
    if fallback == "title_prefix":
        return title_prefix(state.get("title", ""))

    if fallback == "heading_index":
        index = field.get("fallback_index", 0)
        headings = [
            normalize_text(item["text"])
            for item in state.get("headings", [])
            if item.get("level") == 3 and normalize_text(item["text"])
        ]
        if 0 <= index < len(headings):
            return headings[index]
        return ""

    if fallback == "cantico_index":
        index = field.get("fallback_index", 0)
        songs = pick_cantico_texts(state.get("strongs", []))
        if 0 <= index < len(songs):
            return songs[index]
        return ""

    if fallback == "scripture_link":
        for link in pick_semantic_links(state.get("links", [])):
            text = normalize_text(link["text"])
            if re.search(r"\d", text) and not text.startswith("Cantico") and text.isupper():
                return text
        return ""

    if fallback == "adjacent_page_link":
        direction = field.get("direction")
        current_match = re.search(r"/(\d+)$", url)
        if not current_match:
            return ""

        current_id = int(current_match.group(1))
        candidates = []
        for link in state.get("links", []):
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

    return ""


async def extract_field(page, field: dict, state: dict) -> str:
    locator = page.locator(f"xpath={field['xpath']}")
    if await locator.count() > 0:
        element = locator.first
        if field["kind"] == "href":
            href = await element.get_attribute("href")
            if href:
                return urljoin(page.url, href.strip())
        if field["kind"] == "following_text":
            text = await extract_following_text(element)
            if text:
                return text
        else:
            try:
                text = await element.inner_text(timeout=3000)
            except Exception:  # noqa: BLE001
                try:
                    text = await element.text_content(timeout=3000)
                except Exception:  # noqa: BLE001
                    text = ""
            if text:
                return normalize_text(text)

    return fallback_field_value(page.url, field, state)


async def scrape_url(page, url: str) -> dict[str, str]:
    rule = select_rule(url)
    row = {name: "" for name in CSV_FIELD_ORDER}
    row["source_url"] = url

    try:
        await page.goto(url, wait_until="commit", timeout=NAVIGATION_TIMEOUT_MS)
        try:
            await page.wait_for_function(
                """() => document.body && document.body.innerText.trim().length > 1000""",
                timeout=FIELD_READY_TIMEOUT_MS,
            )
        except Exception:  # noqa: BLE001
            pass

        state = await collect_page_state(page)
        for field in rule["fields"]:
            row[field["name"]] = await extract_field(page, field, state)
        for group in rule.get("section_groups", []):
            items = await extract_section_group(page, group)
            for index in range(group["max_items"]):
                item_name = f'{group["prefix"]}_{index + 1}'
                note_name = f'{group["prefix"]}_{index + 1}_note'
                if index < len(items):
                    row[item_name] = items[index]["title"]
                    row[note_name] = items[index]["note"]
    except Exception as exc:  # noqa: BLE001
        row["error"] = str(exc)

    row["valid"] = is_valid_row(row)
    return row


async def crawl(urls: list[str]) -> list[dict[str, str]]:
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"],
        )
        context = await browser.new_context(user_agent=USER_AGENT)

        rows = []
        for url in urls:
            page = await context.new_page()
            try:
                rows.append(await scrape_url(page, url))
            finally:
                await page.close()

        await browser.close()

    return rows


async def crawl_deep(start_url: str, depth: int) -> list[dict[str, str]]:
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"],
        )
        context = await browser.new_context(user_agent=USER_AGENT)

        rows = []
        seen = set()
        current_url = start_url
        for _ in range(depth):
            if current_url in seen:
                break
            seen.add(current_url)

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


def main() -> None:
    args = parse_args()
    if not 1 <= args.deep <= 50:
        raise SystemExit("--deep must be between 1 and 50.")

    if args.deep > 1:
        start_url = collect_direct_url(args)
        rows = asyncio.run(crawl_deep(start_url, args.deep))
        rows_to_write = rows
    else:
        urls = collect_urls(args)
        rows = asyncio.run(crawl(urls))
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
