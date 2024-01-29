from __future__ import annotations
import sys

import django.conf
from django.http import HttpRequest, HttpResponse, JsonResponse
from users.forms import RegisterForm, LoginForm, ChangeInfoForm
from django.shortcuts import render, redirect
from django_htmx.middleware import HtmxDetails
from django.contrib import messages
from django.urls import reverse
from users import oauth42
from django.contrib import auth
from django.contrib.auth import authenticate, get_user_model
from django.core.exceptions import ValidationError


User = get_user_model()


class HtmxHttpRequest(HttpRequest):
    htmx: HtmxDetails

def register(request: HtmxHttpRequest) -> HttpResponse:
    template = 'auth/register.html'
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            auth.login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            messages.success(request, "Account created successfully")
            return redirect(reverse('index'))
    else:
        form = RegisterForm()
    return render(request, template, {'form': form})

def login(request: HtmxHttpRequest) -> HttpResponse:
    template = 'auth/login.html'
    if request.method == 'POST':
        form = LoginForm(data=request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('email')
            password = form.cleaned_data.get('password')
            try:
                user = authenticate(request, email=email, password=password)
                if user is not None:
                    auth.login(request, user)
                    messages.success(request, "Logged in successfully")
                    return redirect(reverse('index'))
            except ValidationError as e:
                form = LoginForm(data=request.POST)
                form.add_error(None, str(e))
                return render(request, template, {'form': form})
    else:
        form = LoginForm()
    return render(request, template, {'form': form})

def oauth42_redirected(request):
    code = request.GET.get('code', None)
    try:
        redirect_uri = django.conf.settings.OAUTH_REDIRECT_URL
        token = oauth42.get_user_token(code, redirect_uri)
        credentials = oauth42.get_user_data(token)
        user = authenticate(request, **credentials, backend='users.auth.OAuthBackend')
        auth.login(request, user)
    except oauth42.AuthError as e:
        form = LoginForm(data=request.POST)
        form.add_error(None, str(e))
        return render(request, 'auth/login.html', {'form': form})        
    return redirect('index')

def logout(request: HtmxHttpRequest) -> HttpResponse:
    if request.method == 'POST':
        auth.logout(request)
        messages.success(request, "Logged out successfully")
    return render(request, "fullindex.html")

def get_oauth_uri(request):
    redirect_uri = django.conf.settings.OAUTH_REDIRECT_URL
    url = oauth42.create_oauth_uri(redirect_uri)
    return JsonResponse(url, safe=False)

def settings(request):
    template = "account/account.html"
    content_type = request.GET.get('content_type')

    if request.method == 'POST':
        user = request.user
        form = ChangeInfoForm(request.POST)

        try:
            if form.is_valid():
                username = form.cleaned_data['username']
                email = form.cleaned_data['email']
                if username:
                    user.username = username
                if email:
                    user.email = email
                user.save()
            else:
                return render(request, "account/fullinfo.html", {'form': form})
        except ValidationError as e:
            print("_______error")
            form.add_error(None, str(e))
    else:
        if request.htmx:
            if content_type == 'stats':
                template = "account/stats.html"
            elif content_type == 'info':
                form = ChangeInfoForm()
                return render(request, "account/info.html", {'form': form})
            elif content_type == 'friends':
                template = "account/friends.html"

    return render(request, template)