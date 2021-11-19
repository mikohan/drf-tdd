from django.urls import path, include
from .views import IngredientViewSet, TagViewSet
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register("tags", TagViewSet)
router.register("ingredients", IngredientViewSet)

app_name = "recipe"

urlpatterns = [path("", include(router.urls))]
