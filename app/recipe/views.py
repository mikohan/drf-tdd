from rest_framework.decorators import action
from rest_framework.response import Response

from rest_framework import viewsets, mixins, status

from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated


from core.models import Recipe, Tag, Ingredient
from recipe.serializers import (  # type: ignore
    RecipeImageSerializer,
    RecipeSerializer,
    TagSerializer,
    IngredientSerializer,
    RecipeDetailSerializer,
)


class BaseRcepieAttrViewSet(
    viewsets.GenericViewSet, mixins.ListModelMixin, mixins.CreateModelMixin
):
    """Base viewset for user owned recipe attributes"""

    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        """Return objects for the current authenticated user only"""
        assign_only = bool(int(self.request.query_params.get("assigned_only", 0)))  # type: ignore
        queryset = self.queryset
        if assign_only:
            queryset = queryset.filter(recipe__isnull=False)  # type: ignore
        return queryset.filter(user=self.request.user).order_by("-name").distinct()  # type: ignore

    def perform_create(self, serializer):
        """Create a new object"""
        serializer.save(user=self.request.user)


class TagViewSet(BaseRcepieAttrViewSet):
    """Manage tags in the database"""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class IngredientViewSet(BaseRcepieAttrViewSet):
    """Manage ingredients in the database"""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer


class RecipeViewSet(viewsets.ModelViewSet):
    """Mange recipes in database"""

    serializer_class = RecipeSerializer
    queryset = Recipe.objects.all()
    permission_classes = (IsAuthenticated,)
    authentication_classes = (TokenAuthentication,)

    def _params_to_ints(self, qs):
        """Conert a lis of strig IDs to a list of integers"""
        return [int(str_id) for str_id in qs.split(",")]

    def get_queryset(self):
        """Retrieve the tecipes for the authenticated users only"""
        tags = self.request.query_params.get("tags")  # type: ignore
        ingredients = self.request.query_params.get("ingredients")  # type: ignore
        queryset = self.queryset
        if tags:
            tags_ids = self._params_to_ints(tags)
            queryset = queryset.filter(tags__id__in=tags_ids)
        if ingredients:
            ingredients_ids = self._params_to_ints(ingredients)
            queryset = queryset.filter(ingredients__id__in=ingredients_ids)

        return queryset.filter(user=self.request.user)

    def get_serializer_class(self):
        """Return appropriate serializer class"""
        if self.action == "retrieve":
            return RecipeDetailSerializer
        elif self.action == "upload_image":
            return RecipeImageSerializer
        return self.serializer_class

    def perform_create(self, serializer):
        """Create a new recipe"""

        serializer.save(user=self.request.user)

    @action(methods=["POST"], detail=True, url_path="upload-image")
    def upload_image(self, request, pk=None):
        """Upload an image to a recipe"""
        recipe = self.get_object()
        serializer = self.get_serializer(recipe, data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status.HTTP_400_BAD_REQUEST)
