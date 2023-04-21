from rest_framework import viewsets, permissions, filters, mixins
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
                          SubscribeSerializer, CustomUserCreateSerializer,
                          CustomUserSerializer)
from .pagination import FoodgramPagination
from .filters import RecipeFilter, IngredientFilter


class CustomUserViewSet(UserViewSet):
    serializer_class = CustomUserSerializer
    queryset = User.objects.all()
    pagination_class = FoodgramPagination

    action_serializers = {
        'list': CustomUserSerializer,
        'retrieve': CustomUserSerializer,
        'create': CustomUserCreateSerializer,
    }

    def get_serializer_class(self):
        return self.action_serializers.get(self.action)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    pagination_class = FoodgramPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    action_serializers = {
        'list': RecipeGetSerializer,
        'retrieve': RecipeGetSerializer,
        'create': RecipeModifySerializer,
        'partial_update': RecipeModifySerializer,
        'destroy': RecipeModifySerializer
    }

    def get_serializer_class(self):
        return self.action_serializers.get(self.action)

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class ShoppingCartAndSubscribeBaseViewSet(mixins.ListModelMixin,
                                          mixins.RetrieveModelMixin,
                                          mixins.CreateModelMixin,
                                          mixins.DestroyModelMixin,
                                          viewsets.GenericViewSet):
    pass


class ShoppingCartViewSet(ShoppingCartAndSubscribeBaseViewSet):
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

    @action(detail=False, methods=['get'])
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


class SubscribeViewSet(ShoppingCartAndSubscribeBaseViewSet):
    serializer_class = SubscribeSerializer
    pagination_class = FoodgramPagination

    def get_queryset(self):
        user = self.request.user
        return user.subscriptions.all()

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def perform_destroy(self, serializer):
        serializer.delete(user=self.request.user)


class FavoriteBaseViewSet(mixins.CreateModelMixin,
                          mixins.DestroyModelMixin,
                          viewsets.GenericViewSet):
    pass


class FavoriteViewSet(FavoriteBaseViewSet):
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
