from django.shortcuts import render
from django.http import HttpResponse

def Home(request):
    return HttpResponse("Hello welcome to TechNestAfrica where we provide quality poultry" \
                " products and digital services through smart farming, online ordering,"
                 " and tech-driven operations that encourage innovation, inclusion, and sustainability.")
    

