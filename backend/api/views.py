from rest_framework import viewsets, permissions, filters, mixins, status
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet

import io
from django.http import FileResponse
from reportlab.pdfgen import canvas


from recipes.models import (Tag, Ingredient, IngredientInRecipe, Recipe,
                            Subscribe, Favorite, ShoppingCart)
from users.models import User
from .serializers import (TagSerializer, IngredientSerializer,
                          RecipeGetSerializer, RecipeModifySerializer,
                          ShoppingCartSerializer, FavoriteSerializer,
                          SubscribeSerializer, CustomUserSerializer,
                          IngredientInRecipeGetSerializer)
from .mixins import CreateDestroyViewSet, ListRetrieveCreateDestroyBaseViewSet
from .pagination import FoodgramPagination
from .filters import RecipeFilter, IngredientFilter


class CustomUserViewSet(UserViewSet):
    serializer_class = CustomUserSerializer
    queryset = User.objects.all()
    pagination_class = FoodgramPagination


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter


class IngredientInRecipeViewSet(viewsets.ModelViewSet):
    queryset = IngredientInRecipe.objects.all().prefetch_related(
        'ingredient', 'recipe')
    serializer_class = IngredientInRecipeGetSerializer


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeGetSerializer
    pagination_class = FoodgramPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def create(self, request):
        serializer = RecipeModifySerializer(data=request.data)
        if serializer.is_valid():
            ingredients_data = serializer.validated_data.pop('ingredients')
            tags_data = serializer.validated_data.pop('tags')
            author = request.user
            recipe = Recipe.objects.create(
                        author=author,
                        **serializer.validated_data)
            for ingredient_data in ingredients_data:
                IngredientInRecipe.objects.create(
                                recipe=recipe,
                                ingredient=ingredient_data['id'],
                                amount=ingredient_data['amount'])
            for tag_data in tags_data:
                recipe.tags.add(tag_data)
            serializer = RecipeGetSerializer(instance=recipe)
            return Response(serializer.data, status.HTTP_201_CREATED)
        return Response(serializer.errors, status.HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):
        serializer = RecipeModifySerializer(request.data)
        if serializer.is_valid():
            ingredients_data = serializer.validated_data.pop('ingredients')
            tags_data = serializer.validated_data.pop('tags')
            recipe = get_object_or_404(Recipe, id=kwargs['id'])
            Recipe.objects.filter(
                id=recipe.id).update(**serializer.validated_data)
            IngredientInRecipe.objects.filter(recipe=recipe).delete()
            for ingredient_data in ingredients_data:
                IngredientInRecipe.objects.create(
                                recipe=recipe,
                                ingredient=ingredient_data['id'],
                                amount=ingredient_data['amount'])
            recipe.tags.clear()
            for tag_data in tags_data:
                recipe.tags.add(tag_data)
            serializer = RecipeGetSerializer(instance=recipe)
            return Response(serializer.data, status.HTTP_201_CREATED)
        return Response(serializer.errors, status.HTTP_400_BAD_REQUEST)


class ShoppingCartViewSet(ListRetrieveCreateDestroyBaseViewSet):
    # queryset = ShoppingCart.objects.all
    serializer_class = ShoppingCartSerializer
    # Доступно только авторизованным пользователям

    def get_queryset(self):
        user = self.request.user
        return user.shopping_cart.all()

    def perform_create(self, serializer):
        recipe_id = self.kwargs.get('recipe_id')
        serializer.save(user=self.request.user, recipe_id=recipe_id)

    def perform_destroy(self, serializer):
        recipe_id = self.kwargs.get('recipe_id')
        serializer.delete(user=self.request.user, recipe_id=recipe_id)

    # @action(detail=False, methods=['get'])
    def download_shopping_cart(self, request):
        # Получаем список покупок
        shopping_cart = self.get_queryset
        # Создаем PDF-файл в памяти
        buffer = io.BytesIO()
        p = canvas.Canvas(buffer)
        # Выводим список покупок в PDF-файл
        p.drawString(100, 750, "Sopping cart:")
        y = 700
        for item in shopping_cart:
            p.drawString(100, y, item.name)
            y -= 20
        # Закрываем PDF-файл и отправляем его пользователю
        p.showPage()
        p.save()
        buffer.seek(0)
        response = FileResponse(buffer, as_attachment=True,
                                filename='shopping_cart.pdf')
        return response


class SubscribeViewSet(ListRetrieveCreateDestroyBaseViewSet):
    serializer_class = SubscribeSerializer
    pagination_class = FoodgramPagination

    def get_queryset(self):
        user = self.request.user
        return user.subscriptions.all()

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def perform_destroy(self, serializer):
        serializer.delete(user=self.request.user)


class FavoriteViewSet(CreateDestroyViewSet):
    serializer_class = FavoriteSerializer
    # фильтрация ??

    def get_queryset(self):
        user = self.request.user
        return user.favorites.all()

    def perform_create(self, serializer):
        recipe_id = self.kwargs.get('recipe_id')
        serializer.save(user=self.request.user, recipe_id=recipe_id)

    def perform_destroy(self, serializer):
        recipe_id = self.kwargs.get('recipe_id')
        serializer.delete(user=self.request.user, recipe_id=recipe_id)
