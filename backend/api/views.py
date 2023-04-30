import io

from django.db.models import Sum
from django.http import FileResponse
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from recipes.models import (Favorite, Ingredient, IngredientInRecipe, Recipe,
                            ShoppingCart, Subscribe, Tag)
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
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
            subscribers__user=user).prefetch_related('recipes')
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
            serializer = SubscribeGetSerializer(
                data={'id': kwargs['id']},
                context={'request': request})
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        if request.method == 'DELETE':
            subscription = Subscribe.objects.filter(author=author, user=user)
            if not subscription.exists():
                return Response(
                    {'error': "Subscription not found."},
                    status=status.HTTP_400_BAD_REQUEST)
            subscription.delete()
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

    """
    Helper method to create or update a recipe.
    Args:
    request (Request): The HTTP request object.
    instance_id (int): The id of the recipe instance to be updated, if any.
    Returns:
    Response: Serialized data of the created or updated recipe,
    or an error message.
    """

    def create_or_update_recipe(self, request, instance):
        request.serializer = RecipeModifySerializer(
            instance=instance,
            data=request.data,
            context={'request': request,
                     'author': request.user})
        request.serializer.is_valid(raise_exception=True)
        request.serializer.save()
        response_serializer = RecipeGetSerializer(
            request.serializer.instance,
            context={'request': request})
        if request.method == 'POST':
            return Response(
                response_serializer.data, status=status.HTTP_201_CREATED)
        if request.method == 'PATCH':
            return Response(
                response_serializer.data, status=status.HTTP_200_OK)

    def create(self, request):
        return self.create_or_update_recipe(request, None)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        self.check_object_permissions(request, instance)
        return self.create_or_update_recipe(request, instance)

    @action(methods=['post', 'delete'],
            detail=True,
            url_path='shopping_cart',
            permission_classes=[IsAuthenticated])
    def create_or_delete_shopping_cart(self, request, *args, **kwargs):
        recipe = self.get_object()
        user = self.request.user
        shopping_cart = ShoppingCart.objects.filter(recipe=recipe, user=user)
        if request.method == 'POST':
            if shopping_cart.exists():
                return Response(
                    {'error': "Recipe already added."},
                    status=status.HTTP_400_BAD_REQUEST)
            ShoppingCart.objects.create(recipe=recipe, user=user)
            serializer = RecipeShortLisTSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        if request.method == 'DELETE':
            if not shopping_cart.exists():
                return Response(
                    {'error': "Recipe not found."},
                    status=status.HTTP_400_BAD_REQUEST)
            shopping_cart.delete()
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
        p.setFont('arial', 16)
        p.drawString(100, 750, "Список покупок:")
        page_w, page_h = A4
        line_h = page_h - 100
        for item in shopping_cart:
            line_h -= 28
            p.setStrokeColor('black')
            p.rect(90, line_h - 2, 16, 16, fill=0, stroke=1)
            text = (f"{item['ingredient__name']} - {item['amount']}"
                    f" {item['ingredient__measurement_unit']}")
            p.drawString(120, line_h, text)
            p.setStrokeColor('lightgrey')
            p.line(80, line_h - 8, page_w - 80, line_h - 8)
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
        favorite = Favorite.objects.filter(recipe=recipe, user=user)
        if request.method == 'POST':
            if favorite.exists():
                return Response(
                    {'error': "Recipe already added."},
                    status=status.HTTP_400_BAD_REQUEST)
            Favorite.objects.create(recipe=recipe, user=user)
            serializer = RecipeShortLisTSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        if request.method == 'DELETE':
            if not favorite.exists():
                return Response(
                    {'error': "Recipe not found."},
                    status=status.HTTP_400_BAD_REQUEST)
            favorite.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
