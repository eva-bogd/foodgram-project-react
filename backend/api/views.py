from rest_framework import viewsets, permissions, status
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet

import io
from django.http import FileResponse
from reportlab.pdfgen import canvas
# from django.utils.encoding import smart_str

from recipes.models import (Tag, Ingredient, IngredientInRecipe, Recipe,
                            Subscribe, Favorite, ShoppingCart)
from users.models import User
from .serializers import (TagSerializer, IngredientSerializer,
                          IngredientInRecipeGetSerializer,
                          RecipeGetSerializer, RecipeModifySerializer,
                          RecipeShortLisTSerializer,
                          CustomUserSerializer, SubscribeGetSerializer,
                          )
from .pagination import FoodgramPagination
from .filters import RecipeFilter, IngredientFilter


class CustomUserViewSet(UserViewSet):
    serializer_class = CustomUserSerializer
    queryset = User.objects.all()
    pagination_class = FoodgramPagination


    @action(methods=['get'], detail=False, url_path='subscriptions')
    def get_subscriptions(self, request):
        user = self.request.user
        queryset = User.objects.filter(subscribers__user=user).prefetch_related('recipes')
        paginator = FoodgramPagination()
        result_page = paginator.paginate_queryset(queryset, request)
        serializer = SubscribeGetSerializer(result_page, context={'request': request}, many=True)
        return paginator.get_paginated_response(serializer.data)

    @action(methods=['post', 'delete'], detail=True, url_path='subscribe')
    def create_or_delete_subscription(self, request, *args, **kwargs):
        author = self.get_object()
        user = self.request.user
        if request.method == 'POST':
            if Subscribe.objects.filter(author=author, user=user).exists():
                return Response({'error': "Subscription already added."}, status=status.HTTP_400_BAD_REQUEST)
            if author == user:
                return Response({'error': "You can't subscribe to yourself."}, status=status.HTTP_400_BAD_REQUEST)
            Subscribe.objects.create(author=author, user=user)
            serializer = SubscribeGetSerializer(author, context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        if request.method == 'DELETE':
            if not Subscribe.objects.filter(author=author, user=user).exists():
                return Response({'error': "Subscription not found."}, status=status.HTTP_400_BAD_REQUEST)
            Subscribe.objects.filter(author=author, user=user).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

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

    def create_recipe(self, request):
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

    def update_recipe(self, request, *args, **kwargs):
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

    @action(methods=['post', 'delete'], detail=True, url_path='shopping_cart')
    def create_or_delete_shopping_cart(self, request, *args, **kwargs):
        recipe = self.get_object()
        user = self.request.user
        if request.method == 'POST':
            if ShoppingCart.objects.filter(recipe=recipe, user=user).exists():
                return Response({'error': "Recipe already added."}, status=status.HTTP_400_BAD_REQUEST)
            ShoppingCart.objects.create(recipe=recipe, user=user)
            serializer = RecipeShortLisTSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        if request.method == 'DELETE':
            if not ShoppingCart.objects.filter(recipe=recipe, user=user).exists():
                return Response({'error': "Recipe not found."}, status=status.HTTP_400_BAD_REQUEST)
            ShoppingCart.objects.filter(recipe=recipe, user=user).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    # @action(methods=['get'], detail=False, url_path='download_shopping_cart/', url_name='download_shopping_cart')
    @action(methods=['get'], detail=False)
    def download_shopping_cart(self, request):
        # Получаем список покупок
        shopping_cart = ShoppingCart.objects.filter(user=self.request.user).select_related('recipe')
        # Создаем PDF-файл в памяти
        buffer = io.BytesIO()
        p = canvas.Canvas(buffer)
        # Выводим список покупок в PDF-файл
        # p.setFont('DejaVuSans', 12)  # Указываем шрифт
        p.drawString(100, 750, "Shopping cart:")
        y = 700
        for item in shopping_cart:
            # p.drawString(100, y, item.recipe)
            p.drawString(100, y, str(item.recipe))
            # p.drawString(100, y, str(item.recipe).encode('utf-8'))
            # p.drawString(100, y, smart_str(item.recipe.name))
            y -= 20
        # Закрываем PDF-файл и отправляем его пользователю
        p.showPage()
        p.save()
        buffer.seek(0)
        response = FileResponse(buffer, as_attachment=True,
                                filename='shopping_cart.pdf')
        return response
        # return Response('text')

    @action(methods=['post', 'delete'], detail=True, url_path='favorite')
    def create_or_delete_favorite(self, request, *args, **kwargs):
        recipe = self.get_object()
        user = self.request.user
        if request.method == 'POST':
            if Favorite.objects.filter(recipe=recipe, user=user).exists():
                return Response({'error': "Recipe already added."}, status=status.HTTP_400_BAD_REQUEST)
            Favorite.objects.create(recipe=recipe, user=user)
            serializer = RecipeShortLisTSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        if request.method == 'DELETE':
            if not Favorite.objects.filter(recipe=recipe, user=user).exists():
                return Response({'error': "Recipe not found."}, status=status.HTTP_400_BAD_REQUEST)
            Favorite.objects.filter(recipe=recipe, user=user).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
