from rest_framework import viewsets, permissions, filters, mixins, status, serializers
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
                          RecipeShortLisTSerializer,
                          SubscribeSerializer,
                          CustomUserSerializer,
                          IngredientInRecipeGetSerializer,)
                          # ShoppingCartSerializer,)
                          # FavoriteSerializer,
from .mixins import CreateDestroyViewSet, ListCreateDestroyBaseViewSet
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
            serializer = RecipeGetSerializer(instance=recipe,
                                             context={'request': request})
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


class ShoppingCartViewSet(ListCreateDestroyBaseViewSet):
    queryset = Recipe.objects.all()
    # Доступно только авторизованным пользователям

    @action(methods=['post', 'delete'], detail=True, url_path='shopping_cart')
    def create_or_delete(self, request, *args, **kwargs):
        recipe = self.get_object()
        user = self.request.user
        if request.method == 'POST':
            if ShoppingCart.objects.filter(recipe=recipe, user=user).exists():
                return Response({'error': 'Recipe already added.'}, status=status.HTTP_400_BAD_REQUEST)
            ShoppingCart.objects.create(recipe=recipe, user=user)
            serializer = RecipeShortLisTSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        if request.method == 'DELETE':
            if not ShoppingCart.objects.filter(recipe=recipe, user=user).exists():
                return Response({'error': 'Recipe not found.'}, status=status.HTTP_400_BAD_REQUEST)
            ShoppingCart.objects.filter(recipe=recipe, user=user).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    # @action(methods=['get'], detail=False, url_path='download_shopping_cart')
    @action(methods=['get'], detail=False, url_path='download_shopping_cart/', url_name='download_shopping_cart')
    def download_shopping_cart(self, request):
        # # Получаем список покупок
        # shopping_cart = ShoppingCart.objects.filter(user=self.request.user).select_related('recipe')
        # # Создаем PDF-файл в памяти
        # buffer = io.BytesIO()
        # p = canvas.Canvas(buffer)
        # # Выводим список покупок в PDF-файл
        # p.drawString(100, 750, "Sopping cart:")
        # y = 700
        # for item in shopping_cart:
        #     p.drawString(100, y, item.recipe)
        #     y -= 20
        # # Закрываем PDF-файл и отправляем его пользователю
        # p.showPage()
        # p.save()
        # buffer.seek(0)
        # response = FileResponse(buffer, as_attachment=True,
        #                         filename='shopping_cart.pdf')
        # return response
        return Response('text')


class FavoriteViewSet(CreateDestroyViewSet):
    queryset = Recipe.objects.all()

    @action(methods=['post', 'delete'], detail=True, url_path='favorite')
    def create_or_delete(self, request, *args, **kwargs):
        recipe = self.get_object()
        user = self.request.user
        if request.method == 'POST':
            if Favorite.objects.filter(recipe=recipe, user=user).exists():
                return Response({'error': 'Recipe already added.'}, status=status.HTTP_400_BAD_REQUEST)
            Favorite.objects.create(recipe=recipe, user=user)
            serializer = RecipeShortLisTSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        if request.method == 'DELETE':
            if not Favorite.objects.filter(recipe=recipe, user=user).exists():
                return Response({'error': 'Recipe not found.'}, status=status.HTTP_400_BAD_REQUEST)
            Favorite.objects.filter(recipe=recipe, user=user).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)


class SubscribeViewSet(ListCreateDestroyBaseViewSet):
    serializer_class = SubscribeSerializer
    pagination_class = FoodgramPagination

    def get_queryset(self):
        user = self.request.user
        return user.subscriptions.all()

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def perform_destroy(self, serializer):
        serializer.delete(user=self.request.user)
