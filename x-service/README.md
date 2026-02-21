# X-Service

This service scrapes recent tweets from X based on a query.

## Running the service

1.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
2.  Run the server:
    ```bash
    uvicorn main:app --reload
    ```

## API

### GET /x/recent-search

Scrapes for recent tweets.

**Query Parameters:**

*   `query` (required): The search query.
*   `min_faves` (optional): Minimum number of favorites.
*   `since` (optional): Start date for the search (e.g., YYYY-MM-DD).
*   `no_cache` (optional): Set to `true` to bypass the cache.

**Example:**

```
http://127.0.0.1:8000/x/recent-search?query=AI&min_faves=100
```
