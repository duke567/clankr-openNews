import json

from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_POST

from .event_engine import analyze_events, process_scrape
from .models import Post
from .x_scraper import scrape_recent_sync


def home(request):
    if request.user.is_authenticated:
        return redirect("timeline_page")
    return redirect("login")


def sign_up(request):
    if request.user.is_authenticated:
        return redirect("timeline_page")

    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("timeline_page")
    else:
        form = UserCreationForm()

    return render(request, "opensourcenewsapp/register.html", {"form": form})


def log_in(request):
    if request.user.is_authenticated:
        return redirect("timeline_page")

    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect("timeline_page")
    else:
        form = AuthenticationForm()

    return render(request, "opensourcenewsapp/login.html", {"form": form})


@login_required
def log_out_page(request):
    logout(request)
    return render(request, "opensourcenewsapp/logged_out.html")


@login_required
def welcome(request):
    return redirect("timeline_page")


@login_required
def timeline_page(request):
    scrape_result = None
    notice = str(request.GET.get("notice", "")).strip()
    scrape_defaults = {
        "query": "ai",
        "language": "en",
        "min_faves": "",
        "since": "",
        "target_count": "12",
        "max_attempts": "5",
        "wait_selector_ms": "7000",
        "sleep_seconds": "0.35",
    }
    if request.method == "POST":
        scrape_defaults = {
            "query": str(request.POST.get("query", "ai")),
            "language": str(request.POST.get("language", "en")),
            "min_faves": str(request.POST.get("min_faves", "")),
            "since": str(request.POST.get("since", "")),
            "target_count": str(request.POST.get("target_count", "12")),
            "max_attempts": str(request.POST.get("max_attempts", "5")),
            "wait_selector_ms": str(request.POST.get("wait_selector_ms", "7000")),
            "sleep_seconds": str(request.POST.get("sleep_seconds", "0.35")),
        }
        scrape_result = _run_scrape_and_ingest(request.POST)

    candidates = Post.objects.order_by("-id")[:300]
    posts = [p for p in candidates if _is_valid_post(p)]
    return render(
        request,
        "opensourcenewsapp/timeline.html",
        {
            "posts": posts,
            "username": request.user.username,
            "scrape_result": scrape_result,
            "scrape_defaults": scrape_defaults,
            "notice": notice,
        },
    )


@login_required
def post_detail_page(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if not _is_valid_post(post):
        return redirect("timeline_page")

    error = None
    notice = str(request.GET.get("notice", "")).strip()
    if request.method == "POST":
        remove_ids = request.POST.getlist("remove_ids")
        action = str(request.POST.get("action", "regenerate")).strip().lower()

        normalized_ids = _normalize_remove_ids(remove_ids)
        if not normalized_ids:
            error = "Select at least one tweet first."
        elif action == "remove":
            removed = _exclude_source_tweets(post, normalized_ids)
            return redirect(f"/post/{post.id}/?notice=Removed-{removed}-tweet(s)")
        else:
            error = _regenerate_post_from_tweets(post, normalized_ids)
            if error is None:
                return redirect(f"/post/{post.id}/?notice=Summary-regenerated")

    tweets = list(post.source_tweets.order_by("id"))
    included_count = sum(1 for tw in tweets if not tw.excluded)

    return render(
        request,
        "opensourcenewsapp/post_detail.html",
        {
            "post": post,
            "tweets": tweets,
            "included_count": included_count,
            "error": error,
            "notice": notice,
        },
    )


@login_required
@require_POST
def delete_post_summary(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    post.delete()
    return redirect("/timeline/?notice=Summary+deleted")


def _request_data(request):
    if request.content_type and "application/json" in request.content_type:
        try:
            return json.loads(request.body.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return {}
    return request.POST


def _run_scrape_and_ingest(data):
    query = str(data.get("query", "")).strip()
    if not query:
        return {"ok": False, "status": 400, "error": "query is required"}

    full_query = query
    min_faves = str(data.get("min_faves", "")).strip()
    since = str(data.get("since", "")).strip()
    if min_faves:
        full_query += f" min_faves:{min_faves}"
    if since:
        full_query += f" since:{since}"

    language = str(data.get("language", "en")).strip().lower()
    allowed_languages = {"en", "es", "fr", "de", "pt", "ja", "hi", "ar", "ko", "zh"}
    if language == "any":
        pass
    elif language in allowed_languages:
        full_query += f" lang:{language}"
    elif "lang:" not in full_query.lower():
        # Safe default.
        full_query += " lang:en"

    # Fast defaults; can be overridden.
    target_count = data.get("target_count", 12)
    max_attempts = data.get("max_attempts", 5)
    wait_selector_ms = data.get("wait_selector_ms", 7000)
    sleep_seconds = data.get("sleep_seconds", 0.35)

    scrape_data = scrape_recent_sync(
        full_query,
        target_count=target_count,
        max_attempts=max_attempts,
        wait_selector_ms=wait_selector_ms,
        sleep_seconds=sleep_seconds,
    )
    if scrape_data.get("error"):
        return {
            "ok": False,
            "status": 502,
            "query": full_query,
            "scrape": scrape_data,
            "message": "Scrape failed before ingest.",
        }

    scraped_count = int(scrape_data.get("count", 0) or 0)
    if scraped_count == 0:
        return {
            "ok": False,
            "status": 200,
            "query": full_query,
            "scraped_count": 0,
            "created_count": 0,
            "created_post_ids": [],
            "message": "No tweets matched this query. Try a broader query or remove min_faves/since.",
        }

    created_posts = process_scrape(scrape_data)
    return {
        "ok": True,
        "status": 200,
        "query": full_query,
        "scraped_count": scraped_count,
        "created_count": len(created_posts),
        "created_post_ids": [post.id for post in created_posts],
    }


@ensure_csrf_cookie
@require_GET
def api_auth_csrf(request):
    return JsonResponse({"ok": True})


@require_POST
def api_auth_login(request):
    data = _request_data(request)
    form = AuthenticationForm(
        request,
        data={"username": data.get("username", ""), "password": data.get("password", "")},
    )
    if not form.is_valid():
        message = form.errors.get("__all__", ["Invalid username or password."])[0]
        return JsonResponse({"ok": False, "message": message, "errors": form.errors}, status=400)

    user = form.get_user()
    login(request, user)
    return JsonResponse({"ok": True, "user": {"id": user.id, "username": user.username}})


@require_POST
def api_auth_register(request):
    data = _request_data(request)
    form = UserCreationForm(
        {
            "username": data.get("username", ""),
            "password1": data.get("password1", ""),
            "password2": data.get("password2", ""),
        }
    )
    if not form.is_valid():
        errors = form.errors
        message = (
            errors.get("username", [None])[0]
            or errors.get("password1", [None])[0]
            or errors.get("password2", [None])[0]
            or "Registration failed."
        )
        return JsonResponse({"ok": False, "message": message, "errors": errors}, status=400)

    user = form.save()
    return JsonResponse({"ok": True, "user": {"id": user.id, "username": user.username}})


@ensure_csrf_cookie
@require_GET
def api_auth_me(request):
    if not request.user.is_authenticated:
        return JsonResponse({"authenticated": False, "user": None})
    return JsonResponse(
        {"authenticated": True, "user": {"id": request.user.id, "username": request.user.username}}
    )


@require_POST
def api_auth_logout(request):
    logout(request)
    return JsonResponse({"ok": True})


def _serialize_post(post):
    return {
        "id": post.id,
        "user_id": 1,
        "title": post.title,
        "subtitle": post.subtitle,
        "content": post.article,
        "views_count": post.score,
        "thumbnail": post.media,
        "created_at": timezone.now().isoformat(),
        "author": {"id": 1, "username": "system", "display_name": "OpenNews"},
    }


def _is_valid_post(post):
    title = (post.title or "").strip()
    article = (post.article or "").strip()
    return bool(title or article)


def _serialize_source_tweet(source_tweet):
    raw = source_tweet.raw or {}
    return {
        "id": source_tweet.id,
        "excluded": source_tweet.excluded,
        "author": raw.get("author", ""),
        "time": raw.get("time", ""),
        "text": raw.get("text", ""),
        "metrics": raw.get("metrics", {}),
        "media": raw.get("media", []),
    }


def _event_score_to_int(raw_score):
    if isinstance(raw_score, (int, float)):
        return int(raw_score)
    score_text = str(raw_score or "").replace(",", "").strip().upper()
    if not score_text:
        return 0
    try:
        if score_text.endswith("K"):
            return int(float(score_text[:-1]) * 1000)
        if score_text.endswith("M"):
            return int(float(score_text[:-1]) * 1_000_000)
        return int(float(score_text))
    except ValueError:
        return 0


def _tweet_metric_to_int(value):
    if value is None:
        return 0
    if isinstance(value, (int, float)):
        return int(value)
    text = str(value).replace(",", "").strip().upper()
    if not text:
        return 0
    try:
        if text.endswith("K"):
            return int(float(text[:-1]) * 1000)
        if text.endswith("M"):
            return int(float(text[:-1]) * 1_000_000)
        return int(float(text))
    except ValueError:
        return 0


def _tweets_engagement_total(tweet_rows):
    total = 0
    for tw in tweet_rows:
        raw = tw.raw or {}
        metrics = raw.get("metrics", {}) or {}
        total += _tweet_metric_to_int(metrics.get("lk"))
        total += _tweet_metric_to_int(metrics.get("rt"))
        total += _tweet_metric_to_int(metrics.get("rp"))
    return total


def _normalize_remove_ids(remove_ids):
    normalized = []
    for item in remove_ids:
        text = str(item).strip()
        if text.isdigit():
            normalized.append(int(text))
    return normalized


def _exclude_source_tweets(post, remove_ids):
    ids = _normalize_remove_ids(remove_ids)
    if not ids:
        return 0
    updated = post.source_tweets.filter(id__in=ids, excluded=False).update(excluded=True)
    return int(updated)


def _regenerate_post_from_tweets(post, remove_ids):
    _exclude_source_tweets(post, remove_ids)

    remaining_rows = list(post.source_tweets.filter(excluded=False).order_by("id"))
    remaining = [tw.raw for tw in remaining_rows]
    if not remaining:
        return "No tweets left to regenerate from."

    payload = {"query": f"post-{post.id}-regenerate", "count": len(remaining), "results": remaining}
    events = analyze_events(payload)
    if not events:
        return "AI could not generate a new summary from remaining tweets."

    best = max(events, key=lambda ev: _event_score_to_int(ev.get("score", 0)))
    media_url = best.get("media")
    if not media_url or str(media_url).lower() in {"null", "none", "nan"}:
        media_url = ""

    post.title = str(best.get("title", post.title))[:200]
    post.subtitle = str(best.get("subtitle", ""))[:300]
    post.article = best.get("article", post.article)
    generated_score = _event_score_to_int(best.get("score", post.score))
    fallback_score = _tweets_engagement_total(remaining_rows)
    post.score = max(generated_score, fallback_score)
    post.media = media_url
    post.save(update_fields=["title", "subtitle", "article", "score", "media"])
    return None


@require_GET
def api_posts_timeline(request):
    try:
        limit = int(request.GET.get("limit", 50))
    except ValueError:
        limit = 50
    limit = max(1, min(limit, 200))
    candidates = Post.objects.order_by("-id")[: max(limit * 5, 100)]
    valid_posts = [p for p in candidates if _is_valid_post(p)][:limit]
    return JsonResponse({"data": [_serialize_post(p) for p in valid_posts]})


@require_GET
def api_post_detail(request, post_id):
    try:
        post = Post.objects.get(id=post_id)
    except Post.DoesNotExist:
        return JsonResponse({"error": "Post not found"}, status=404)
    if not _is_valid_post(post):
        return JsonResponse({"error": "Post not found"}, status=404)
    return JsonResponse(_serialize_post(post))


@require_GET
def api_user_profile(request, username):
    candidates = Post.objects.order_by("-id")[:250]
    posts = [p for p in candidates if _is_valid_post(p)][:50]
    return JsonResponse(
        {
            "user": {"id": 1, "username": username, "display_name": username},
            "posts": [_serialize_post(p) for p in posts],
        }
    )


@require_GET
def api_post_tweets(request, post_id):
    try:
        post = Post.objects.get(id=post_id)
    except Post.DoesNotExist:
        return JsonResponse({"error": "Post not found"}, status=404)

    tweets = post.source_tweets.order_by("id")
    return JsonResponse({"data": [_serialize_source_tweet(tw) for tw in tweets]})


@require_POST
def api_post_regenerate(request, post_id):
    try:
        post = Post.objects.get(id=post_id)
    except Post.DoesNotExist:
        return JsonResponse({"error": "Post not found"}, status=404)

    data = _request_data(request)
    remove_ids = data.get("remove_ids", []) if isinstance(data, dict) else []
    if not isinstance(remove_ids, list):
        remove_ids = []

    error = _regenerate_post_from_tweets(post, remove_ids)
    if error:
        return JsonResponse({"error": error}, status=400)

    tweets = post.source_tweets.order_by("id")
    return JsonResponse(
        {
            "post": _serialize_post(post),
            "tweets": [_serialize_source_tweet(tw) for tw in tweets],
        }
    )


@csrf_exempt
def ingest_scrape(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)

    data = json.loads(request.body)
    process_scrape(data)

    return JsonResponse({"ok": True})


@csrf_exempt
def api_scrape_and_ingest(request):
    if request.method not in {"GET", "POST"}:
        return JsonResponse({"error": "GET or POST required"}, status=405)

    if request.method == "GET":
        data = request.GET
    else:
        data = _request_data(request)

    result = _run_scrape_and_ingest(data)
    status = int(result.pop("status", 200))
    return JsonResponse(result, status=status)
