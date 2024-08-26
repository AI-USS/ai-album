from django.urls import path
from . import views
from django.conf.urls.static import static 
from django.conf import settings 



urlpatterns = [
    path("", views.home, name="home"),
    # path("add", views.AddPageView.as_view(), name="add"),
    path("search", views.SearchPageView.as_view(), name="search"),
    path('add', views.upload_image, name='upload_image'),

]
