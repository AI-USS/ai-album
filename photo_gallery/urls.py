from django.urls import path
from . import views
from django.conf.urls.static import static 
from django.conf import settings 



urlpatterns = [
    path("", views.HomePageView.as_view(), name="home"),
    path("add", views.AddPageView.as_view(), name="add"),
    path("search", views.SearchPageView.as_view(), name="search"),
]
