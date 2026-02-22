import json

from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_exempt
from django.views.decorators.http import require_GET, require_POST
from .event_engine import process_scrape


def sign_up(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("login")
    else:
        form = UserCreationForm()

    return render(request, "opensourcenewsapp/register.html", {"form": form})

def log_in(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect("welcome")
    else:
        print("nothing")
        form = AuthenticationForm()

    return render(request, "opensourcenewsapp/login.html", {"form": form})



@login_required
def welcome(request):
    return render(request, "opensourcenewsapp/welcome.html", {"user": request.user})


def _request_data(request):
    if request.content_type and "application/json" in request.content_type:
        try:
            return json.loads(request.body.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return {}
    return request.POST


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

@csrf_exempt
def ingest_scrape(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)

    data = json.loads(request.body)
    process_scrape(data)

    return JsonResponse({"ok": True})