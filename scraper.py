from playwright.async_api import async_playwright
import json
import asyncio

async def crawl_page(url):
    async with async_playwright() as p:
        # Launch the browser
        browser = await p.chromium.launch(headless=True, args=['--disable-http2'])

        # Create a new browser context with a custom user agent
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        )
        
        # Create a new page in the context
        page = await context.new_page()

        # Navigate to the page
        await page.goto(url, wait_until='load')

        # Extract the title of the page
        title = await page.title()

        # Extract meeting content
        meeting_content = await page.inner_text('div.meetingContent')

        # Output data as JSON
        data = {
            'title': title,
            'meeting_content': meeting_content
        }

        # Save to a JSON file
        with open('output.json', 'w') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

        print("Data extracted and saved to output.json")

        await browser.close()

# URL to crawl
url = "https://wol.jw.org/it/wol/meetings/r6/lp-i/2024/41"

asyncio.run(crawl_page(url))
