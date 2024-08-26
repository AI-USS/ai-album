from django.views.generic.base import TemplateView
from django.shortcuts import render


class HomePageView(TemplateView):
    template_name = "home.html"


class AddPageView(TemplateView):
    template_name = "add.html"

class SearchPageView(TemplateView):
    template_name = "search.html"