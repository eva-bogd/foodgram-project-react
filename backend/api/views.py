import io

from django.db.models import Sum
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from recipes.models import (Favorite, Ingredient, IngredientInRecipe, Recipe,
                            ShoppingCart, Subscribe, Tag)
from reportlab.pdfgen import canvas
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from users.models import User

from .filters import IngredientFilter, RecipeFilter
from .pagination import FoodgramPagination
from .permissions import ReadOnly, RecipePermission
from .serializers import (CustomUserSerializer, IngredientSerializer,
                          RecipeGetSerializer, RecipeModifySerializer,
                          RecipeShortLisTSerializer, SubscribeGetSerializer,
                          TagSerializer)


class CustomUserViewSet(UserViewSet):
    serializer_class = CustomUserSerializer
    queryset = User.objects.all()
    pagination_class = FoodgramPagination

    @action(methods=['get'],
            detail=False,
            url_path='subscriptions',
            permission_classes=[IsAuthenticated])
    def get_subscriptions(self, request):
        user = self.request.user
        queryset = User.objects.filter(
            subscribers__user=user
            ).prefetch_related('recipes')
        paginator = FoodgramPagination()
        result_page = paginator.paginate_queryset(queryset, request)
        serializer = SubscribeGetSerializer(
            result_page,
            context={'request': request}, many=True)
        return paginator.get_paginated_response(serializer.data)

    @action(methods=['post', 'delete'],
            detail=True,
            url_path='subscribe',
            permission_classes=[IsAuthenticated])
    def create_or_delete_subscription(self, request, *args, **kwargs):
        author = self.get_object()
        user = self.request.user
        if request.method == 'POST':
            if Subscribe.objects.filter(author=author, user=user).exists():
                return Response(
                    {'error': "Subscription already added."},
                    status=status.HTTP_400_BAD_REQUEST)
            if author == user:
                return Response(
                    {'error': "You can't subscribe to yourself."},
                    status=status.HTTP_400_BAD_REQUEST)
            Subscribe.objects.create(author=author, user=user)
            serializer = SubscribeGetSerializer(
                author,
                context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        if request.method == 'DELETE':
            if not Subscribe.objects.filter(author=author, user=user).exists():
                return Response(
                    {'error': "Subscription not found."},
                    status=status.HTTP_400_BAD_REQUEST)
            Subscribe.objects.filter(author=author, user=user).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [IsAdminUser | ReadOnly]


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter
    permission_classes = [IsAdminUser | ReadOnly]


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeGetSerializer
    pagination_class = FoodgramPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    permission_classes = [RecipePermission]

    def create_or_update(self, request, instance_id):
        serializer = RecipeModifySerializer(
            data=request.data,
            context={'request': request})
        if serializer.is_valid():
            ingredients = serializer.validated_data.pop('ingredients')
            tags = serializer.validated_data.pop('tags')

            if instance_id is None:
                user = request.user
                recipe = Recipe.objects.create(
                    author=user,
                    **serializer.validated_data)
            else:
                recipe = get_object_or_404(Recipe, id=instance_id)
                Recipe.objects.filter(
                    id=recipe.id).update(
                    **serializer.validated_data)
                recipe.refresh_from_db()
                IngredientInRecipe.objects.filter(recipe=recipe).delete()
                recipe.tags.clear()

            for ingredient in ingredients:
                IngredientInRecipe.objects.create(
                    ingredient=ingredient['id'],
                    amount=ingredient['amount'],
                    recipe=recipe)
            for tag in tags:
                recipe.tags.add(tag)

            response_serializer = RecipeGetSerializer(
                instance=recipe,
                context={'request': request})
            return Response(
                response_serializer.data, status=status.HTTP_201_CREATED)
        return Response(
            serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def create(self, request):
        return self.create_or_update(request, None)

    def update(self, request, *args, **kwargs):
        self.check_object_permissions(request, self.get_object())
        return self.create_or_update(request, kwargs['id'])

    @action(methods=['post', 'delete'],
            detail=True,
            url_path='shopping_cart',
            permission_classes=[IsAuthenticated])
    def create_or_delete_shopping_cart(self, request, *args, **kwargs):
        recipe = self.get_object()
        user = self.request.user
        if request.method == 'POST':
            if ShoppingCart.objects.filter(recipe=recipe, user=user).exists():
                return Response(
                    {'error': "Recipe already added."},
                    status=status.HTTP_400_BAD_REQUEST)
            ShoppingCart.objects.create(recipe=recipe, user=user)
            serializer = RecipeShortLisTSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        if request.method == 'DELETE':
            if not ShoppingCart.objects.filter(recipe=recipe,
                                               user=user).exists():
                return Response(
                    {'error': "Recipe not found."},
                    status=status.HTTP_400_BAD_REQUEST)
            ShoppingCart.objects.filter(recipe=recipe, user=user).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=['get'],
            detail=False,
            permission_classes=[IsAuthenticated])
    def download_shopping_cart(self, request):
        user = request.user
        shopping_cart = IngredientInRecipe.objects.filter(
            recipe__shopping_cart__user=user).values(
                'ingredient__name',
                'ingredient__measurement_unit').annotate(
                 amount=Sum('amount'))
        buffer = io.BytesIO()
        p = canvas.Canvas(buffer)
        pdfmetrics.registerFont(TTFont('arial', 'arial.ttf'))
        p.setFont('arial', 32)
        p.drawString(100, 750, "Shopping cart:")
        y = 700
        for item in shopping_cart:
            p.drawString(
                100, y, f"{item.get('ingredient__name')}: {item.get('amount')}"
                        f"{item.get('ingredient__measurement_unit')}")
        y -= 20
        p.showPage()
        p.save()
        buffer.seek(0)
        return FileResponse(buffer,
                            as_attachment=True,
                            filename='shopping_cart.pdf')

    @action(methods=['post', 'delete'],
            detail=True,
            url_path='favorite',
            permission_classes=[IsAuthenticated])
    def create_or_delete_favorite(self, request, *args, **kwargs):
        recipe = self.get_object()
        user = self.request.user
        if request.method == 'POST':
            if Favorite.objects.filter(recipe=recipe, user=user).exists():
                return Response(
                    {'error': "Recipe already added."},
                    status=status.HTTP_400_BAD_REQUEST)
            Favorite.objects.create(recipe=recipe, user=user)
            serializer = RecipeShortLisTSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        if request.method == 'DELETE':
            if not Favorite.objects.filter(recipe=recipe, user=user).exists():
                return Response(
                    {'error': "Recipe not found."},
                    status=status.HTTP_400_BAD_REQUEST)
            Favorite.objects.filter(recipe=recipe, user=user).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
