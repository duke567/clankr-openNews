import os
import json
import time
import asyncio
import urllib.parse
import re
from collections import OrderedDict, deque
from threading import Lock
from typing import Optional

from fastapi import FastAPI, HTTPException, Query, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from playwright.async_api import async_playwright, TimeoutError
from rich.console import Console
from rich.table import Table
import requests

app = FastAPI()
console = Console()

# --- CONFIGURATION ---
X_AUTH_TOKEN = os.getenv("X_AUTH_TOKEN", "0adfaf5a0cd6e00b8f343bb4bf002682c7a6fb7c")
X_CT0 = os.getenv("X_CT0", "fcca802079ed4ea4e4386d64471563d8e88fbd5a44c52011f8abe84b7121211d11098cac476d894e8c03387b7e638680a53e02fc5bf3147ffb550577d62759631543d3e09df1e584b345829ba86096d5")
CACHE_TTL_SECONDS = 300
TWEET_TARGET_COUNT = 40
EXPORT_DIR = "exports"
DJANGO_INGEST_URL = os.getenv("DJANGO_INGEST_URL", "http://127.0.0.1:8000/api/ingest-scrape/")

if not os.path.exists(EXPORT_DIR):
    os.makedirs(EXPORT_DIR)

_cache: OrderedDict[str, dict] = OrderedDict()
_lock = Lock()

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["GET"], allow_headers=["*"])

def parse_tweet_text(raw_text: str) -> dict:
    lines = [line.strip() for line in raw_text.split('\n') if line.strip()]
    try:
        stat_pattern = re.compile(r'^[\d\.,]+[KMB]?$')
        potential_stats = [l for l in lines if stat_pattern.match(l)]
        metrics = {"rp": "0", "rt": "0", "lk": "0"}
        if len(potential_stats) >= 3:
            metrics = {"rp": potential_stats[0], "rt": potential_stats[1], "lk": potential_stats[2]}
        content = " ".join(lines[4:]).split("From ")[0].split("show more")[0].strip()
        return {
            "author": f"{lines[0]} ({lines[1]})",
            "time": lines[3] if len(lines) > 3 else "now",
            "text": content,
            "metrics": metrics
        }
    except:
        return {"text": raw_text.replace("\n", " ")[:200], "metrics": {"rp":"-","rt":"-","lk":"-"}}

def render_terminal_table(query: str, results: list):
    table = Table(title=f"🚀 [bold cyan]{len(results)} Tweets Found for:[/] {query}", show_lines=True)
    table.add_column("Time", style="dim", width=10)
    table.add_column("Author", style="green", width=25)
    table.add_column("Content", style="white")
    table.add_column("Media", style="cyan", justify="center", width=8)
    table.add_column("Stats (Rp/Rt/Lk)", style="magenta", justify="center", width=15)
    for r in results:
        m = r.get("metrics", {})
        media_count = len(r.get("media", []))
        media_str = str(media_count) if media_count > 0 else "-"
        table.add_row(r.get("time"), r.get("author"), r.get("text")[:150] + "...", media_str, f"{m['rp']} / {m['rt']} / {m['lk']}")
    console.print("\n", table)

async def _execute_scrape(full_query: str) -> dict:
    encoded_query = urllib.parse.quote(full_query)
    url = f"https://x.com/search?q={encoded_query}&src=typed_query&f=live"
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        # Use a very standard Mac Chrome context
        context = await browser.new_context(
            viewport={'width': 1280, 'height': 900},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        
        await context.add_cookies([
            {'name': 'auth_token', 'value': X_AUTH_TOKEN, 'domain': '.x.com', 'path': '/'},
            {'name': 'ct0', 'value': X_CT0, 'domain': '.x.com', 'path': '/'}
        ])

        page = await context.new_page()
        results = []
        seen_texts = set()

        try:
            with console.status(f"[bold yellow]Searching X for: {full_query}...", spinner="bouncingBar"):
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                
                # Initial wait for the first batch
                try:
                    await page.wait_for_selector('article[data-testid="tweet"]', timeout=20000)
                except TimeoutError:
                    content = await page.content()
                    if "No results for" in content:
                        console.print(f"[yellow]Search returned 0 results (verified).[/]")
                        await browser.close()
                        return {"query": full_query, "count": 0, "results": []}
                    
                    if "Sign in to X" in content:
                        console.print(f"[red]Authentication Failed: Redirected to login.[/]")
                        # We still return empty, but log the specific error

                    console.print(f"[red]Timeout waiting for tweets (Unknown cause).[/]")
                    await page.screenshot(path="scrape_timeout.png")
                    await browser.close()
                    return {"query": full_query, "count": 0, "results": []}

                # --- DYNAMIC SCROLL LOOP ---
                max_attempts = 15  # Limit scrolls so we don't loop forever
                for i in range(max_attempts):
                    tweet_els = await page.query_selector_all('article[data-testid="tweet"]')
                    
                    new_found = 0
                    for el in tweet_els:
                        try:
                            raw_text = await el.inner_text()
                            if "Replying to" in raw_text or raw_text in seen_texts:
                                continue
                            
                            seen_texts.add(raw_text)
                            tweet_data = parse_tweet_text(raw_text)

                            # Extract Media
                            media_urls = []
                            try:
                                images = await el.query_selector_all('div[data-testid="tweetPhoto"] img')
                                for img in images:
                                    src = await img.get_attribute("src")
                                    if src: media_urls.append(src)
                                video = await el.query_selector('div[data-testid="videoPlayer"] video')
                                if video:
                                    poster = await video.get_attribute("poster")
                                    if poster: media_urls.append(poster)
                            except: pass
                            
                            tweet_data["media"] = media_urls
                            results.append(tweet_data)
                            new_found += 1
                        except:
                            continue # Element might have unmounted during scroll

                    if len(results) >= TWEET_TARGET_COUNT:
                        break
                    
                    # Scroll down with a "human" flick
                    await page.mouse.wheel(0, 2500)
                    # Random sleep between 1.5 and 2.5 seconds
                    await asyncio.sleep(1.5 + (0.1 * (i % 10))) 

            await browser.close()
            return {"query": full_query, "count": len(results), "results": results}
        except Exception as e:
            await page.screenshot(path="scrape_failure.png")
            await browser.close()
            raise e


def _persist_export(data: dict) -> str:
    filename = f"scrape_{int(time.time())}.json"
    filepath = os.path.join(EXPORT_DIR, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    return filepath


def _ingest_into_django(data: dict) -> dict:
    try:
        response = requests.post(DJANGO_INGEST_URL, json=data, timeout=60)
        ok = response.status_code >= 200 and response.status_code < 300
        body = None
        try:
            body = response.json()
        except Exception:
            body = response.text
        return {"ok": ok, "status_code": response.status_code, "response": body}
    except Exception as exc:
        return {"ok": False, "error": str(exc), "status_code": 0}

@app.get("/x/recent-search")
async def recent_search(
    query: str = Query(...),
    min_faves: Optional[int] = None,
    since: Optional[str] = None,
    no_cache: bool = Query(False, description="Set to true to bypass the cache for this request"),
):
    full_query = query
    if min_faves: full_query += f" min_faves:{min_faves}"
    if since: full_query += f" since:{since}"
    
    now = time.time()
    if not no_cache:
        with _lock:
            cached = _cache.get(full_query)
            if cached and cached["expires_at"] > now:
                render_terminal_table(full_query, cached["data"]["results"])
                return cached["data"]

    data = await _execute_scrape(full_query)
    
    if "error" in data:
        console.print(f"[red]Error:[/] {data['error']}")
        return data

    _persist_export(data)
    
    render_terminal_table(full_query, data["results"])
    
    if not no_cache:
        with _lock:
            _cache[full_query] = {"data": data, "expires_at": now + CACHE_TTL_SECONDS}
    return data


@app.post("/x/scrape-and-ingest")
async def scrape_and_ingest(
    query: str = Query(...),
    min_faves: Optional[int] = None,
    since: Optional[str] = None,
    no_cache: bool = Query(False),
):
    full_query = query
    if min_faves:
        full_query += f" min_faves:{min_faves}"
    if since:
        full_query += f" since:{since}"

    now = time.time()
    data = None
    if not no_cache:
        with _lock:
            cached = _cache.get(full_query)
            if cached and cached["expires_at"] > now:
                data = cached["data"]

    if data is None:
        data = await _execute_scrape(full_query)
        _persist_export(data)
        render_terminal_table(full_query, data.get("results", []))
        if not no_cache:
            with _lock:
                _cache[full_query] = {"data": data, "expires_at": now + CACHE_TTL_SECONDS}

    ingest_result = _ingest_into_django(data)
    status_code = 200 if ingest_result.get("ok") else 502
    return Response(
        content=json.dumps(
            {
                "query": full_query,
                "scraped_count": data.get("count", 0),
                "ingest": ingest_result,
            }
        ),
        media_type="application/json",
        status_code=status_code,
    )
