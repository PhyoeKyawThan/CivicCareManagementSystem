from django.shortcuts import render
from django.http.request import HttpRequest

def index(request: HttpRequest):
    return render(request, 'issues/index.html')