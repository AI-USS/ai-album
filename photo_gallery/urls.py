from django.urls import path
from . import views
from django.conf.urls.static import static 
from django.conf import settings 



urlpatterns = [
    path("", views.home, name="home"),
    path("add", views.upload_image, name="add"),
    path("search", views.SearchPageView.as_view(), name="search"),
    path("get/ajax/recognize_face", views.recognize_face_at_photo, name="recognize_face"),
]
