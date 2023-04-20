from django.contrib import admin

from .models import (Tag, Ingredient, IngredientInRecipe, Recipe,
                     Subscribe, Favorite, ShoppingCart)


# В списке рецептов вывести название и автора рецепта.
# Добавить фильтры по автору, названию рецепта, тегам.
# На странице рецепта вывести общее число добавлений этого рецепта в избранное.
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('author', 'name')  #'total_favorites')
    list_filter = ('author', 'name', 'tags')
    empty_value_display = '-empty-'

    # def total_favorites(self, obj):
    #     return obj.favorite_set.count()

    # total_favorites.admin_order_field = 'favorite_set__count'


# В список вывести название ингредиента и единицы измерения.
# Добавить фильтр по названию.
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')
    list_filter = ('name',)
    empty_value_display = '-empty-'


admin.site.register(Recipe, RecipeAdmin)
admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(IngredientInRecipe)
admin.site.register(Tag)
admin.site.register(Subscribe)
admin.site.register(Favorite)
admin.site.register(ShoppingCart)
