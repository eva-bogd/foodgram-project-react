import base64

from django.core.files.base import ContentFile
from django.shortcuts import get_object_or_404
from djoser.serializers import UserSerializer
from recipes.models import (Favorite, Ingredient, IngredientInRecipe, Recipe,
                            ShoppingCart, Subscribe, Tag)
from rest_framework import serializers
from users.models import User


class RecipeShortLisTSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time',)


class CustomUserSerializer(UserSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta(UserSerializer.Meta):
        model = User
        fields = ('id', 'email', 'first_name', 'last_name', 'is_subscribed',)

    def get_is_subscribed(self, obj):
        user = self.context['request'].user
        return Subscribe.objects.filter(
            user_id=user.id, author_id=obj.id
        ).exists()


class SubscribeGetSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()
    is_subscribed = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count',)
        read_only_fields = ['email', 'first_name', 'last_name']

    def get_recipes(self, obj):
        recipes_limit = self.context['request'].GET.get('recipes_limit')
        if recipes_limit is not None:
            recipes_limit = int(recipes_limit)
        recipes = obj.recipes.all()[:recipes_limit]
        serializer = RecipeShortLisTSerializer(recipes, many=True)
        return serializer.data

    def get_recipes_count(self, obj):
        return obj.recipes.count()

    def get_is_subscribed(self, obj):
        user = self.context['request'].user
        return Subscribe.objects.filter(
            user_id=user.id, author_id=obj.id
        ).exists()

    def validate_id(self, value):
        author = get_object_or_404(User, id=value)
        if author == self.context['request'].user:
            raise serializers.ValidationError(
                "You can't subscribe to yourself.")
        return value

    def create(self, validated_data):
        author = User.objects.get(id=validated_data.get('id'))
        user = self.context['request'].user
        if Subscribe.objects.filter(author=author, user=user).exists():
            raise serializers.ValidationError("Subscription already added.")
        Subscribe.objects.create(author=author, user=user)
        return author


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = '__all__'


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit',)


class IngredientInRecipeGetSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='ingredient.id')
    name = serializers.CharField(source='ingredient.name')
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit')

    class Meta:
        model = IngredientInRecipe
        fields = ('id', 'amount', 'name', 'measurement_unit',)


class IngredientInRecipeCreateSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all(),)
    amount = serializers.IntegerField()

    class Meta:
        model = IngredientInRecipe
        fields = ('id', 'amount',)


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        # if isinstance(data, str) and data.startswith('data:image'):
        if isinstance(data.get('image'), str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)
        return super().to_internal_value(data)


class RecipeGetSerializer(serializers.ModelSerializer):
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
    ingredients = IngredientInRecipeCreateSerializer(many=True)
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('ingredients',
                  'tags',
                  'name',
                  'image',
                  'text',
                  'cooking_time',)

    def bulk_create_ingredients(self, ingredients_data, recipe):
        IngredientInRecipe.objects.bulk_create(
            [IngredientInRecipe(
                recipe=recipe,
                ingredient=ingredient_data['id'],
                amount=ingredient_data['amount'])
                for ingredient_data in ingredients_data])

    def create(self, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        tags_data = validated_data.pop('tags')
        author = self.context.get('author')
        recipe = Recipe.objects.create(author=author, **validated_data)
        self.bulk_create_ingredients(ingredients_data, recipe)
        recipe.tags.set(tags_data)
        return recipe

    def update(self, instance, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        tags_data = validated_data.pop('tags')
        IngredientInRecipe.objects.filter(recipe=instance).delete()
        self.bulk_create_ingredients(ingredients_data, instance)
        instance.tags.clear()
        instance.tags.set(tags_data)
        super().update(instance=instance, validated_data=validated_data)
        return instance
