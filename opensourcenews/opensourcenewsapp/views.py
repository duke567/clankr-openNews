from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login


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