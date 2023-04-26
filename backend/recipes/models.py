from colorfield.fields import ColorField
from django.db import models
from django.contrib.auth import get_user_model

from django.core.validators import MinValueValidator


User = get_user_model()


class Tag(models.Model):
    name = models.CharField(
        verbose_name='Tag name',
        max_length=200,
        unique=True,
        blank=False)
    color = ColorField(
        verbose_name='Tag color',
        max_length=200,
        format='hex',
        blank=False)
    slug = models.SlugField(
        verbose_name='Tag slug',
        max_length=200,
        unique=True,
        blank=False)

    def __str__(self):
        return f'{self.name} #{self.slug}'


class Ingredient(models.Model):
    name = models.CharField(
        verbose_name='Ingredient name',
        max_length=200,
        blank=False)
    measurement_unit = models.CharField(
        verbose_name='Ingredient measurement unit',
        max_length=200,
        blank=False)

    class Meta:
        unique_together = ['name', 'measurement_unit']

    def __str__(self):
        return self.name


class Recipe(models.Model):
    author = models.ForeignKey(
        User,
        verbose_name='Recipe author',
        on_delete=models.CASCADE,
        related_name='recipes')
    name = models.CharField(
        verbose_name='Recipe name',
        max_length=200,
        blank=False)
    image = models.ImageField(
        verbose_name='Recipe image',
        upload_to='recipes/images/',
        blank=False)
    text = models.TextField(
        verbose_name='Description and instructions for cooking',
        blank=False)
    used_ingredients = models.ManyToManyField(
        Ingredient,
        through='IngredientInRecipe',
        verbose_name='Ingredients for cooking',
        related_name='recipes',
        blank=False)
    tags = models.ManyToManyField(
        Tag,
        verbose_name='Recipe tags')
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name='Cooking time in minutes',
        validators=[MinValueValidator(1)],
        blank=False)
    date_published = models.DateTimeField(
        verbose_name='Date published',
        auto_now_add=True)

    class Meta:
        ordering = ('-date_published',)

    def __str__(self):
        return self.name


class IngredientInRecipe(models.Model):
    ingredient = models.ForeignKey(
        Ingredient,
        verbose_name='Ingredient',
        on_delete=models.CASCADE)
    recipe = models.ForeignKey(
        Recipe,
        verbose_name='Recipe',
        on_delete=models.CASCADE,
        related_name='ingredients')
    amount = models.PositiveSmallIntegerField(
        verbose_name='Ingredient amount',
        validators=[MinValueValidator(1)],
        blank=False)

    def __str__(self):
        return f'{self.ingredient.name} - {self.amount}'


class Subscribe(models.Model):
    user = models.ForeignKey(
        User,
        verbose_name='Subscriber',
        on_delete=models.CASCADE,
        related_name='subscriptions'
    )
    author = models.ForeignKey(
        User,
        verbose_name='Author',
        on_delete=models.CASCADE,
        related_name='subscribers'
    )

    class Meta:
        unique_together = ['user', 'author']

    def __str__(self):
        return f'{self.user.username} - {self.author.username}'


class Favorite(models.Model):
    user = models.ForeignKey(
        User,
        verbose_name='Username',
        on_delete=models.CASCADE,
        related_name='favorites'
    )
    recipe = models.ForeignKey(
        Recipe,
        verbose_name='Favorite recipes',
        on_delete=models.CASCADE,
        related_name='favorites'
    )
    date_added = models.DateTimeField(
        verbose_name='Date added to favorites',
        auto_now_add=True)

    class Meta:
        unique_together = ['user', 'recipe']
        ordering = ('date_added',)

    def __str__(self):
        return f'{self.user.username}- {self.recipe}'


class ShoppingCart(models.Model):
    user = models.ForeignKey(
        User,
        verbose_name='Username',
        on_delete=models.CASCADE,
        related_name='shopping_cart'
    )
    recipe = models.ForeignKey(
        Recipe,
        verbose_name='Recipes in cart',
        on_delete=models.CASCADE,
        related_name='shopping_cart'
    )
    date_added = models.DateTimeField(
        verbose_name='Date added to cart',
        auto_now_add=True)

    class Meta:
        unique_together = ['user', 'recipe']
        ordering = ('date_added',)

    def __str__(self):
        return f'{self.user.username} - {self.recipe}'
