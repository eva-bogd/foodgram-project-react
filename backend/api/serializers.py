import base64
from django.core.files.base import ContentFile
from djoser.serializers import UserCreateSerializer, UserSerializer
from rest_framework import serializers
from django.shortcuts import get_object_or_404
from rest_framework.validators import UniqueTogetherValidator

from recipes.models import (Tag, Ingredient, IngredientInRecipe, Recipe,
                            Subscribe, Favorite, ShoppingCart)
from users.models import User


class CustomUserSerializer(UserSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta(UserSerializer.Meta):
        model = User
        fields = ('id', 'email', 'first_name', 'last_name', 'is_subscribed')

    def get_is_subscribed(self, obj):
        user = self.context['request'].user
        return Subscribe.objects.filter(
            user_id=user.id, author_id=obj.id
        ).exists()


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = '__all__'


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class IngredientInRecipeGetSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source="ingredient.name")
    measurement_unit = serializers.CharField(
       source='ingredient.measurement_unit')

    class Meta:
        model = IngredientInRecipe
        fields = ('id', 'amount', 'name', 'measurement_unit',)
        # fields = '__all__'


class IngredientInRecipeCreateSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())

    class Meta:
        model = IngredientInRecipe
        fields = ('id', 'amount',)


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)
        return super().to_internal_value(data)


class RecipeGetSerializer(serializers.ModelSerializer):
    # author = serializers.SlugRelatedField(
    #      slug_field='username', read_only=True)
    author = CustomUserSerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    ingredients = IngredientInRecipeGetSerializer(many=True, read_only=True)
    image = Base64ImageField()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = ('id',
                  'tags',
                  'author',
                  'ingredients',
                  'is_favorited',
                  'is_in_shopping_cart',
                  'name',
                  'image',
                  'text',
                  'cooking_time',)

    def get_is_favorited(self, obj):
        user = self.context['request'].user
        return Favorite.objects.filter(
            user_id=user.id, recipe_id=obj.id
        ).exists()

    def get_is_in_shopping_cart(self, obj):
        user = self.context['request'].user
        return ShoppingCart.objects.filter(
            user_id=user.id, recipe_id=obj.id
        ).exists()


class RecipeModifySerializer(serializers.ModelSerializer):
    tags = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.all())
    ingredients = IngredientInRecipeCreateSerializer(many=True)
    #image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('ingredients',
                  'tags',
                  'name',
                  #'image',
                  'text',
                  'cooking_time',)


class RecipeShortLisTSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ['id', 'name', 'image', 'cooking_time']


class SubscribeSerializer(serializers.ModelSerializer):
    user = serializers.SlugRelatedField(
        read_only=True, slug_field='username',
        default=serializers.CurrentUserDefault())
    author = serializers.SlugRelatedField(
        slug_field='username',
        queryset=User.objects.all())
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = Subscribe
        fields = ('author', 'recipes', 'recipes_count')
        validators = [
            UniqueTogetherValidator(
                queryset=Subscribe.objects.all(),
                fields=('user', 'following'),
                message="You are already subscribed to this author."
            )]

    def get_recipes(self, obj):
        # user = self.context['request'].user
        # author = Subscribe.objects.filter(user_id=user.id)
        # recipes = Recipe.objects.filter(author=author)
        recipes = Recipe.objects.filter(author=obj.author)[:6]
        return RecipeGetSerializer(recipes, many=True).data

    def get_recipes_count(self, obj):
        return obj.author.recipes.count()

    def get_is_subscribed(self, obj):
        user = self.context['request'].user
        return Subscribe.objects.filter(
            user_id=user.id, author_id=obj.id
        ).exists()

    def validate_author(self, value):
        if value == self.context['request'].user:
            raise serializers.ValidationError(
                "You can't subscribe to yourself.")
        return value


class FavoriteSerializer(serializers.ModelSerializer):
    user = serializers.SlugRelatedField(
        read_only=True, slug_field='username'
    )
    recipe = RecipeShortLisTSerializer(many=True, read_only=True)

    class Meta:
        model = Favorite
        fields = ('id', 'users', 'recipe')

    def validate_add(self, attrs):
        recipe = get_object_or_404(
            Recipe, id=self.context['view'].kwargs.get('recipe_id'))
        user = self.context['request'].user
        if self.context['request'].method == 'POST':
            if Favorite.objects.filter(
                    recipe_id=recipe, user_id=user).exists():
                raise serializers.ValidationError(
                    "Recipe already exists in favorite.")
        return attrs

    def validate_delete(self, attrs):
        recipe = get_object_or_404(
            Recipe, id=self.context['view'].kwargs.get('recipe_id'))
        user = self.context['request'].user
        if self.context['request'].method == 'DELETE':
            if not Favorite.objects.filter(
                    recipe_id=recipe, user_id=user).exists():
                raise serializers.ValidationError(
                    "Recipe does not exist in favorite.")
        return attrs


class ShoppingCartSerializer(serializers.ModelSerializer):
    user = serializers.SlugRelatedField(
        read_only=True, slug_field='username')
    recipes = serializers.StringRelatedField(many=True, read_only=True)

    class Meta:
        model = ShoppingCart
        fields = ('id', 'user', 'recipes') # развернуть?

    def validate_add(self, attrs):
        recipe = get_object_or_404(
            Recipe, id=self.context['view'].kwargs.get('recipe_id'))
        user = self.context['request'].user
        if self.context['request'].method == 'POST':
            if ShoppingCart.objects.filter(
                    recipe_id=recipe, user_id=user).exists():
                raise serializers.ValidationError(
                    "Recipe already exists in shopping cart.")
        return attrs

    def validate_delete(self, attrs):
        recipe = get_object_or_404(
            Recipe, id=self.context['view'].kwargs.get('recipe_id'))
        user = self.context['request'].user
        if self.context['request'].method == 'DELETE':
            if not ShoppingCart.objects.filter(
                    recipe_id=recipe, user_id=user).exists():
                raise serializers.ValidationError(
                    "Recipe does not exist in shopping cart.")
        return attrs
