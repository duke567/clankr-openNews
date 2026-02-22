import json
import re
import os
from google import genai
from .models import Post


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


# client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
client = genai.Client(api_key="AIzaSyCKRW-A4nKhChe9NuAkRT9dXerGBjaUURc")

def extract_json(text: str) -> dict:
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError("No JSON found in Gemini response.")
    return json.loads(match.group(0))

def analyze_events(tweets_obj: dict) -> list:
    full_input = prompt + "\n\nTWEET DATA:\n" + json.dumps(tweets_obj)

    response = client.models.generate_content(
        model="gemini-3-flash-preview",
        contents=full_input,
        config={"temperature": 0.2},
    )

    parsed = extract_json(response.text)
    return parsed.get("events", [])


def process_scrape(data: dict):
    events = analyze_events(data)
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

            # 3. Create the Post with Slicing
            # This prevents "Data too long" errors if the AI gets chatty
            post = Post.objects.create(
                title=str(ev.get("title", "Untitled Event"))[:200],
                subtitle=str(ev.get("subtitle", ""))[:300],
                article=ev.get("article", ""),
                score=clean_score,
                media=media_url
            )
            created_posts.append(post)

        except Exception as e:
            # If one event is malformed, log it and move to the next 
            # so you don't lose the whole batch of tweets.
            print(f"Error processing event '{ev.get('title')}': {e}")
            continue

    return created_posts