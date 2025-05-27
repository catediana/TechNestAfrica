from django.shortcuts import render
from django.http import HttpResponse


def Orders(request):
    return HttpResponse ("Hello , please place your Order")
