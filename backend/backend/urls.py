# from django.contrib import admin
# from django.urls import path, include

# from django.http import HttpResponse

# def home(request):
#     return HttpResponse("Backend is running!")

# urlpatterns = [
#     path("", home),
#     path("admin/", admin.site.urls),
#     path("api/", include("api.urls")),
# ]

from django.conf import settings

from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse
from api import views
from django.conf.urls.static import static

def home(request):
    return HttpResponse("Backend is running!")

urlpatterns = [
    path("", home),
    path("admin/", admin.site.urls),
    path("api/", include("api.urls")),
    # path("app/", views.index, name="index"),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)