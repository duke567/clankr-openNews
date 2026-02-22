import json
import re
import os
from .models import Post, SourceTweet
try:
    from google import genai
except Exception:
    genai = None


prompt = """You are a professional news editor and data analyst.

You are given a JSON file containing tweets about a specific geographic region within a short time window.

Each tweet includes:
- text
- author
- time
- metrics:
    - lk (likes)
    - rt (retweets)
    - rp (replies)
- media (array of URLs, may be empty)

Your task is to identify ALL MAJOR real-world events based ONLY on repeated patterns in the tweets.

CRITICAL RULES:
- Use ONLY the information contained in the tweets.
- Do NOT add outside knowledge.
- Do NOT speculate.
- Ignore satire, memes, jokes, and one-off commentary.
- Only treat something as a major event if multiple independent tweets reference it.
- If tweets reference the same development in different ways, cluster them together.
- Each event must be supported by multiple tweets.

-----------------------------------
STEP 1 (Internal clustering — DO NOT OUTPUT):
-----------------------------------
1. Cluster tweets by topic.
2. Identify all clusters that represent:
   • official announcements
   • scheduled votes or referendums
   • policy changes
   • major political controversies
   • significant public actions or developments
3. Discard clusters that are minor, purely opinion-based, or supported by only one tweet.
4. For each valid event cluster, extract:
   • Key actors
   • Key announcements or claims
   • Dates or deadlines
   • Major public reaction themes

-----------------------------------
STEP 2 (Score Calculation — DO NOT OUTPUT STEPS):
-----------------------------------
For EACH event cluster separately:

1. Convert "lk" and "rt" to integers:
   - "1K" = 1000
   - "1.5K" = 1500
   - "2.6K" = 2600
   - Plain numbers = integer
   - Ignore invalid values

2. For each tweet in the cluster:
   TWEET_SCORE = lk + rt

3. EVENT_SCORE = sum of all TWEET_SCORE values in that cluster

4. Identify the tweet in the cluster with the highest TWEET_SCORE.
   From that tweet:
   - If it contains a non-empty media array,
     select ONE media URL (the first valid URL).
   - If no tweet in the cluster has media, return null.

-----------------------------------
STEP 3 (Output):
-----------------------------------
Return STRICTLY valid JSON.
Do NOT include markdown.
Do NOT include commentary.
Do NOT explain reasoning.
Do NOT include text outside JSON.

Return this exact structure:

{
  "events": [
    {
      "title": "Clear, specific headline summarizing the event",
      "subtitle": "One concise sentence explaining why this event matters",
      "article": "500–800 word neutral, informative article explaining what happened, who is involved, why it matters, what is scheduled next (if mentioned), and how the public is reacting. Use only tweet information.",
      "score": <numeric total engagement score for this event>,
      "media": "single media URL from highest scoring tweet in this event or null"
    }
  ]
}

Order events by highest score first.

If no major events can be identified, return:

{
  "events": []
}"""


HARDCODED_GEMINI_API_KEY = "AIzaSyCXgsi05636tRnt9OBj0ilb85Z8wTYjFMY"

client = None
if genai is not None:
    try:
        api_key = os.environ.get("GEMINI_API_KEY", HARDCODED_GEMINI_API_KEY).strip()
        if api_key:
            client = genai.Client(api_key=api_key)
    except Exception:
        client = None

def extract_json(text: str) -> dict:
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError("No JSON found in Gemini response.")
    return json.loads(match.group(0))

def analyze_events(tweets_obj: dict) -> list:
    # Fallback path when google-genai isn't installed/configured.
    if client is None:
        tweets = tweets_obj.get("results", []) or []
        if not tweets:
            return []
        top = tweets[:8]
        combined = " ".join((t.get("text") or "").strip() for t in top if t.get("text"))
        title = combined[:120] or "Live Event Summary"
        subtitle = f"Digest based on {len(top)} recently scraped tweets."
        article = combined[:2400] or "No tweet text was available for this event."
        score = 0
        for t in top:
            m = t.get("metrics", {}) or {}
            for key in ("lk", "rt", "rp"):
                raw = str(m.get(key, "0")).upper().replace(",", "").strip()
                try:
                    if raw.endswith("K"):
                        score += int(float(raw[:-1]) * 1000)
                    elif raw.endswith("M"):
                        score += int(float(raw[:-1]) * 1_000_000)
                    else:
                        score += int(float(raw or 0))
                except ValueError:
                    pass
        media = None
        for t in top:
            items = t.get("media") or []
            if items:
                media = items[0]
                break
        return [
            {
                "title": title,
                "subtitle": subtitle,
                "article": article,
                "score": score,
                "media": media,
            }
        ]

    full_input = prompt + "\n\nTWEET DATA:\n" + json.dumps(tweets_obj)

    response = client.models.generate_content(
        model="gemini-3-flash-preview",
        contents=full_input,
        config={"temperature": 0.2},
    )

    parsed = extract_json(response.text)
    return parsed.get("events", [])


def _metric_to_int(value):
    if value is None:
        return 0
    if isinstance(value, (int, float)):
        return int(value)
    clean = str(value).replace(",", "").strip().upper()
    if not clean:
        return 0
    try:
        if clean.endswith("K"):
            return int(float(clean[:-1]) * 1000)
        if clean.endswith("M"):
            return int(float(clean[:-1]) * 1_000_000)
        return int(float(clean))
    except ValueError:
        return 0


def _tweet_engagement(tweet):
    metrics = tweet.get("metrics", {}) or {}
    return (
        _metric_to_int(metrics.get("lk"))
        + _metric_to_int(metrics.get("rt"))
        + _metric_to_int(metrics.get("rp"))
    )


def _event_keywords(event):
    text = f"{event.get('title', '')} {event.get('subtitle', '')}".lower()
    words = re.findall(r"[a-z0-9]{4,}", text)
    stop = {"with", "from", "this", "that", "have", "will", "they", "about", "their", "into", "after"}
    return {w for w in words if w not in stop}


def _build_fallback_event(tweets):
    top = tweets[:10]
    combined = " ".join((t.get("text") or "").strip() for t in top if t.get("text"))
    score = sum(_tweet_engagement(t) for t in top)
    media = None
    for t in top:
        items = t.get("media") or []
        if items:
            media = items[0]
            break
    return {
        "title": (combined[:120] or "Live Event Summary"),
        "subtitle": f"Digest based on {len(top)} recently scraped tweets.",
        "article": (combined[:4000] or "No tweet text was available for this event."),
        "score": score,
        "media": media,
        "__source_tweets": top,
    }


def _select_tweets_for_event(event, tweets):
    keywords = _event_keywords(event)
    scored = []
    for tw in tweets:
        text = (tw.get("text") or "").lower()
        kw_hits = sum(1 for kw in keywords if kw in text)
        engagement = _tweet_engagement(tw)
        score = kw_hits * 10 + engagement
        scored.append((score, kw_hits, tw))

    scored.sort(key=lambda it: it[0], reverse=True)
    matching = [item for item in scored if item[1] > 0]

    selected = []
    seen = set()

    if matching:
        for _, _, tw in matching[:25]:
            key = (tw.get("author"), tw.get("time"), tw.get("text"))
            if key not in seen:
                seen.add(key)
                selected.append(tw)

    # Ensure at least 10 source tweets are attached when available.
    min_target = min(10, len(scored))
    if len(selected) < min_target:
        for _, _, tw in scored:
            key = (tw.get("author"), tw.get("time"), tw.get("text"))
            if key in seen:
                continue
            seen.add(key)
            selected.append(tw)
            if len(selected) >= min_target:
                break

    if selected:
        return selected
    return [it[2] for it in scored[:15]]


def process_scrape(data: dict):
    tweets = data.get("results", []) or []
    try:
        events = analyze_events(data)
    except Exception as e:
        print(f"Error analyzing events: {e}")
        events = []

    if not events and tweets:
        events = [_build_fallback_event(tweets)]

    created_posts = []

    for ev in events:
        try:
            # 1. Handle the Score (Ensure it's a clean Integer)
            # We strip commas or "K" just in case Gemini forgets Step 2 of your prompt
            raw_score = ev.get("score", 0)
            if isinstance(raw_score, str):
                # Basic cleaning: remove "K", commas, and handle decimals
                clean_score = raw_score.replace(',', '').upper()
                if 'K' in clean_score:
                    clean_score = int(float(clean_score.replace('K', '')) * 1000)
                else:
                    clean_score = int(float(clean_score))
            else:
                clean_score = int(raw_score)

            # 2. Handle the Media (Ensure it's a valid URL or empty string)
            # URLField in Django expects a valid URL format or an empty string
            media_url = ev.get("media")
            if not media_url or str(media_url).lower() in ["null", "none", "nan"]:
                media_url = ""
            elif not str(media_url).lower().startswith(("http://", "https://")):
                media_url = ""

            selected_tweets = ev.get("__source_tweets") if isinstance(ev, dict) else None
            if not isinstance(selected_tweets, list) or not selected_tweets:
                selected_tweets = _select_tweets_for_event(ev, tweets)

            # Prefer model score, but never keep 0 if source tweets have engagement.
            tweet_score_total = sum(_tweet_engagement(tw) for tw in selected_tweets)
            final_score = max(int(clean_score), int(tweet_score_total))

            # 3. Create the Post with Slicing
            # This prevents "Data too long" errors if the AI gets chatty
            post = Post.objects.create(
                title=str(ev.get("title", "Untitled Event"))[:200],
                subtitle=str(ev.get("subtitle", ""))[:300],
                article=ev.get("article", ""),
                score=final_score,
                media=media_url
            )
            for tweet in selected_tweets:
                SourceTweet.objects.create(post=post, raw=tweet)
            created_posts.append(post)

        except Exception as e:
            # If one event is malformed, log it and move to the next 
            # so you don't lose the whole batch of tweets.
            print(f"Error processing event '{ev.get('title')}': {e}")
            continue

    return created_posts
