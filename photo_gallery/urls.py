from django.urls import path
from . import views, colorization_views
from django.conf.urls.static import static 
from django.conf import settings 



urlpatterns = [
    path("<int:pk>", views.PhotographicDetailView.as_view(), name="photographic_detail"),
    path("<int:pk>/original", colorization_views.source_image, name="original_image"),
    path("<int:pk>/reverse", colorization_views.reverse_image, name="reverse_image"),
    path("<int:pk>/colorize", colorization_views.start, name="colorization_start"),
    path("<int:pk>/colorization", colorization_views.status, name="colorization_status"),
    path("<int:pk>/colorized", colorization_views.image, name="colorized_image"),
    path("", views.home, name="home"),
    path("add", views.upload_image, name="add"),
    path("search", views.SearchPageView.as_view(), name="search"),
    path("learn", views.learn, name="learn"),
    path("<int:pk>/delete", views.PhotographicDeleteView.as_view(), name="photographic_delete"),
    path("<int:pk>/edit", views.PhotographicEditView.as_view(), name="photographic_edit"),
    path("get/ajax/recognize_face", views.recognize_face_at_photo, name="recognize_face"),
]
