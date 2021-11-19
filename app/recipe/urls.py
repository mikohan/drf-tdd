from django.urls import path, include
from .views import TagViewSet
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register("tags", TagViewSet)

app_name = "recipe"

urlpatterns = [path("", include(router.urls), name="tag-list")]
