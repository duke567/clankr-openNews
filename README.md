# OpenNews – HackED 2026 Project

OpenNews is a prototype news aggregator built at **HackED 2026**—the University of Alberta’s 48‑hour student‑run hackathon held 20‑22 February 2026:contentReference[oaicite:0]{index=0}.  Our team wanted to explore whether generative AI could help citizens keep up with rapidly developing local events.  The result is a full‑stack demo that scrapes public posts from X (formerly Twitter), clusters them into real‑world events and generates concise articles summarising why they matter.

## Why OpenNews?

Social media platforms like X are often the first place where local developments break, yet they are noisy and hard to follow.  OpenNews automatically:

- **Scrapes live tweets.** A Playwright‑powered scraper runs searches on X using an authenticated session and extracts each post’s author, timestamp, text, engagement metrics and media:contentReference[oaicite:1]{index=1}:contentReference[oaicite:2]{index=2}.
- **Clusters posts into events.** A custom event engine uses engagement scores to cluster tweets referring to the same development.  It ranks events by the sum of likes and retweets:contentReference[oaicite:3]{index=3}:contentReference[oaicite:4]{index=4}.
- **Generates summaries.** A prompt to Google Gemini describes each event and asks the model to return a headline, one‑sentence subtitle, 500–800‑word article and overall score:contentReference[oaicite:5]{index=5}:contentReference[oaicite:6]{index=6}.  When generative AI isn’t available, a fallback summarises the top tweets and calculates a score:contentReference[oaicite:7]{index=7}.
- **Serves news feeds.** A Django backend stores each generated post with title, subtitle, article, score and media link in a `Post` model:contentReference[oaicite:8]{index=8}.  Users can view a timeline of events, read details and regenerate summaries by excluding certain source tweets:contentReference[oaicite:9]{index=9}.

## Architecture

OpenNews is organised into three services:

### 1. Django backend (`opensourcenews`)

- **Models:** The `Post` model stores the generated headline, subtitle, article and engagement score, while `SourceTweet` stores the raw tweet JSON associated with a post:contentReference[oaicite:10]{index=10}.
- **API & views:** The backend exposes endpoints for authentication, a timeline feed, individual post details, regeneration and deletion.  The `timeline_page` view loads recent posts and allows users to trigger new scrapes with configurable query parameters:contentReference[oaicite:11]{index=11}.  API endpoints also return JSON representations of posts and their source tweets:contentReference[oaicite:12]{index=12}.
- **Event engine:** `event_engine.py` contains the prompt and logic for clustering tweets and creating `Post` objects.  It converts likes/retweets into numeric scores, selects media from the most engaging tweet and uses Google Gemini to produce neutral, informative articles:contentReference[oaicite:13]{index=13}:contentReference[oaicite:14]{index=14}.
- **Scraper integration:** The backend can ingest scraping results via `/api/ingest-scrape` and also provides `/api/scrape-and-ingest` which triggers the scraper synchronously and then stores the generated posts:contentReference[oaicite:15]{index=15}.

### 2. X‑Service microservice (`x-service`)

To separate scraping concerns, we created a lightweight FastAPI service that exposes two endpoints:

- **`GET /x/recent-search`** – runs a recent search on X for a given query and returns raw tweets:contentReference[oaicite:16]{index=16}.
- **`POST /x/scrape-and-ingest`** – scrapes tweets and immediately forwards the JSON payload to the Django backend’s ingestion endpoint:contentReference[oaicite:17]{index=17}.

The service can be run locally with `uvicorn main:app --reload`:contentReference[oaicite:18]{index=18}.  It requires a `DJANGO_INGEST_URL` environment variable to point at the backend and uses cached cookies (`X_AUTH_TOKEN`, `X_CT0`) for authenticated scraping.

### 3. Angular front‑end (`open‑source`)

The user interface is built with Angular CLI 21.1.4:contentReference[oaicite:19]{index=19}.  It provides a responsive timeline page where users can sign up, log in, run custom queries and read or regenerate event summaries.  Development commands are standard Angular ones: `ng serve` to run a local server and `ng build` to produce an optimised build:contentReference[oaicite:20]{index=20}.

## Prerequisites

OpenNews was prototyped quickly for a hackathon, so you’ll need a few tools installed:

- **Python 3.10+** with `pip`.
- **Node.js 18+** and **Angular CLI**.
- **Playwright** for Python and a Chromium browser (install with `pip install playwright` and `python -m playwright install chromium`).
- **Google Gemini API key** (set `GEMINI_API_KEY`) if you want AI‑generated summaries.  Otherwise, the fallback summarisation logic will be used:contentReference[oaicite:21]{index=21}.
- **X (Twitter) session cookies** (`X_AUTH_TOKEN` and `X_CT0`) to enable scraping:contentReference[oaicite:22]{index=22}.

## ⚙️ Full Setup Guide

Follow these steps to run OpenNews locally.

### 1️⃣ Clone the Repository

```bash
git clone https://github.com/your-username/clankr-openNews.git
cd clankr-openNews
```

### 2️⃣ Backend Setup (Django)

```bash
cd opensourcenews
python -m venv env
source env/bin/activate        # On Windows: env\Scripts\activate
pip install -r ../requirements.txt

python manage.py migrate
python manage.py runserver 8000
```

Backend will run at:
http://127.0.0.1:8000/

Create an account at:
http://127.0.0.1:8000/signup/

Timeline available at:
http://127.0.0.1:8000/timeline/

### 3️⃣ Scraper Microservice Setup

Open a new terminal:

```bash
cd x-service
pip install -r requirements.txt

export DJANGO_INGEST_URL=http://127.0.0.1:8000/api/ingest-scrape/
export X_AUTH_TOKEN=your_token_here
export X_CT0=your_token_here

uvicorn main:app --reload --port 8001
```

Scraper will run at:
http://127.0.0.1:8001/

### 4️⃣ Frontend Setup (Angular)

Open a new terminal:

```bash
cd open-source
npm install
ng serve --open
```

Frontend runs at:
http://localhost:4200/
