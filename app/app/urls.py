from django.contrib import admin
from django.urls import path, include
from rest_framework_swagger.views import get_swagger_view
from django.conf.urls.static import static
from django.conf import settings

schema_view = get_swagger_view(title="Recipe project swagger")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("user/", include("user.urls")),
    path("recipe/", include("recipe.urls")),
    path("docs/", schema_view),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
