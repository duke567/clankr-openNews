import asyncio
import os
import re
import urllib.parse

try:
    from playwright.async_api import TimeoutError, async_playwright
except Exception:
    TimeoutError = Exception
    async_playwright = None

# Temporary hardcoded credentials for hackathon speed.
# Replace/rotate these before any real deployment.
X_AUTH_TOKEN = os.getenv(
    "X_AUTH_TOKEN",
    "0adfaf5a0cd6e00b8f343bb4bf002682c7a6fb7c",
).strip()
X_CT0 = os.getenv(
    "X_CT0",
    "fcca802079ed4ea4e4386d64471563d8e88fbd5a44c52011f8abe84b7121211d11098cac476d894e8c03387b7e638680a53e02fc5bf3147ffb550577d62759631543d3e09df1e584b345829ba86096d5",
).strip()
TWEET_TARGET_COUNT = int(os.getenv("TWEET_TARGET_COUNT", "40"))
SCRAPE_MAX_ATTEMPTS = int(os.getenv("SCRAPE_MAX_ATTEMPTS", "15"))
SCRAPE_WAIT_SELECTOR_MS = int(os.getenv("SCRAPE_WAIT_SELECTOR_MS", "20000"))
SCRAPE_SLEEP_SECONDS = float(os.getenv("SCRAPE_SLEEP_SECONDS", "1.5"))


def _parse_tweet_text(raw_text: str) -> dict:
    lines = [line.strip() for line in raw_text.split("\n") if line.strip()]
    try:
        stat_pattern = re.compile(r"^[\d\.,]+[KMB]?$")
        potential_stats = [line for line in lines if stat_pattern.match(line)]
        metrics = {"rp": "0", "rt": "0", "lk": "0"}
        if len(potential_stats) >= 3:
            metrics = {
                "rp": potential_stats[0],
                "rt": potential_stats[1],
                "lk": potential_stats[2],
            }
        content = " ".join(lines[4:]).split("From ")[0].split("show more")[0].strip()
        return {
            "author": f"{lines[0]} ({lines[1]})" if len(lines) >= 2 else "Unknown",
            "time": lines[3] if len(lines) > 3 else "now",
            "text": content,
            "metrics": metrics,
        }
    except Exception:
        return {"text": raw_text.replace("\n", " ")[:200], "metrics": {"rp": "0", "rt": "0", "lk": "0"}}


async def scrape_recent(
    full_query: str,
    target_count: int | None = None,
    max_attempts: int | None = None,
    wait_selector_ms: int | None = None,
    sleep_seconds: float | None = None,
) -> dict:
    if async_playwright is None:
        return {
            "query": full_query,
            "count": 0,
            "results": [],
            "error": "Playwright is not installed. Run: pip install playwright && python -m playwright install chromium",
        }

    if not X_AUTH_TOKEN or not X_CT0:
        return {"query": full_query, "count": 0, "results": [], "error": "Missing X_AUTH_TOKEN/X_CT0 env vars."}

    target_count = max(1, int(target_count or TWEET_TARGET_COUNT))
    max_attempts = max(1, int(max_attempts or SCRAPE_MAX_ATTEMPTS))
    wait_selector_ms = max(1000, int(wait_selector_ms or SCRAPE_WAIT_SELECTOR_MS))
    sleep_seconds = max(0.1, float(sleep_seconds or SCRAPE_SLEEP_SECONDS))

    encoded_query = urllib.parse.quote(full_query)
    url = f"https://x.com/search?q={encoded_query}&src=typed_query&f=live"

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 1280, "height": 900},
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
            ),
        )
        await context.add_cookies(
            [
                {"name": "auth_token", "value": X_AUTH_TOKEN, "domain": ".x.com", "path": "/"},
                {"name": "ct0", "value": X_CT0, "domain": ".x.com", "path": "/"},
            ]
        )

        page = await context.new_page()
        results = []
        seen_texts = set()

        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            try:
                await page.wait_for_selector('article[data-testid="tweet"]', timeout=wait_selector_ms)
            except TimeoutError:
                content = await page.content()
                await browser.close()
                if "No results for" in content:
                    return {"query": full_query, "count": 0, "results": []}
                if "Sign in to X" in content:
                    return {"query": full_query, "count": 0, "results": [], "error": "X auth failed."}
                return {"query": full_query, "count": 0, "results": [], "error": "Tweet load timeout."}

            for i in range(max_attempts):
                tweet_els = await page.query_selector_all('article[data-testid="tweet"]')
                for el in tweet_els:
                    try:
                        raw_text = await el.inner_text()
                        if "Replying to" in raw_text or raw_text in seen_texts:
                            continue
                        seen_texts.add(raw_text)
                        tweet_data = _parse_tweet_text(raw_text)

                        media_urls = []
                        try:
                            images = await el.query_selector_all('div[data-testid="tweetPhoto"] img')
                            for img in images:
                                src = await img.get_attribute("src")
                                if src:
                                    media_urls.append(src)
                            video = await el.query_selector('div[data-testid="videoPlayer"] video')
                            if video:
                                poster = await video.get_attribute("poster")
                                if poster:
                                    media_urls.append(poster)
                        except Exception:
                            pass

                        tweet_data["media"] = media_urls
                        results.append(tweet_data)
                    except Exception:
                        continue

                if len(results) >= target_count:
                    break
                await page.mouse.wheel(0, 2500)
                await asyncio.sleep(sleep_seconds)

            await browser.close()
            return {"query": full_query, "count": len(results), "results": results}
        except Exception as exc:
            await browser.close()
            return {"query": full_query, "count": 0, "results": [], "error": str(exc)}


def scrape_recent_sync(
    full_query: str,
    target_count: int | None = None,
    max_attempts: int | None = None,
    wait_selector_ms: int | None = None,
    sleep_seconds: float | None = None,
) -> dict:
    try:
        return asyncio.run(
            scrape_recent(
                full_query,
                target_count=target_count,
                max_attempts=max_attempts,
                wait_selector_ms=wait_selector_ms,
                sleep_seconds=sleep_seconds,
            )
        )
    except RuntimeError:
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(
                scrape_recent(
                    full_query,
                    target_count=target_count,
                    max_attempts=max_attempts,
                    wait_selector_ms=wait_selector_ms,
                    sleep_seconds=sleep_seconds,
                )
            )
        finally:
            loop.close()
